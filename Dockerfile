# Investment Auto - 포트폴리오 자동 리밸런싱 시스템
# Multi-stage build for optimized image size

# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM python:3.11-slim as builder

WORKDIR /build

# 의존성 설치를 위한 시스템 패키지
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
RUN pip install --no-cache-dir --user psycopg2-binary pyjwt

# =============================================================================
# Stage 2: Runtime
# =============================================================================
FROM python:3.11-slim as runtime

WORKDIR /app

# 런타임 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser

# Builder에서 설치한 패키지 복사
COPY --from=builder /root/.local /home/appuser/.local

# 애플리케이션 파일 복사
COPY --chown=appuser:appuser Scripts/ /app/Scripts/
COPY --chown=appuser:appuser Config/ /app/Config/
COPY --chown=appuser:appuser requirements.txt /app/

# PATH 설정
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 비루트 사용자로 실행
USER appuser

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# 기본 포트
EXPOSE 5000

# 기본 명령어
CMD ["python", "Scripts/apps/portfolio_rebalancing.py", \
     "--mode", "schedule", \
     "--web-port", "5000", \
     "--db-mode"]

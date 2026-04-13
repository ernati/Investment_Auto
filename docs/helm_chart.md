# Helm Chart 설명서

## 개요

Investment Auto Helm Chart는 포트폴리오 자동 리밸런싱 시스템을 Kubernetes 환경에 배포하기 위한 패키지입니다.

## Chart 정보

| 항목 | 값 |
|------|-----|
| Chart 이름 | investment-auto |
| 버전 | 1.0.0 |
| App 버전 | 1.0.0 |
| 유형 | application |

## 파일 구조

```
helm/
├── Chart.yaml           # Chart 메타데이터
├── values.yaml          # 기본 설정값
├── .helmignore          # 패키징 제외 파일
└── templates/
    ├── _helpers.tpl     # 템플릿 헬퍼 함수
    ├── configmap.yaml   # ConfigMap 리소스
    ├── deployment.yaml  # Deployment 리소스
    ├── ingress.yaml     # Ingress 리소스
    ├── namespace.yaml   # Namespace 리소스
    ├── NOTES.txt        # 설치 후 메시지
    ├── postgresql-zalando.yaml  # Zalando PostgreSQL
    ├── secret.yaml      # Secret 리소스
    ├── service.yaml     # Service 리소스
    └── serviceaccount.yaml  # ServiceAccount 리소스
```

## templates 파일 설명

### _helpers.tpl

템플릿 전체에서 사용하는 헬퍼 함수들을 정의합니다:

| 함수 | 설명 |
|------|------|
| `investment-auto.name` | Chart 이름 (63자 제한) |
| `investment-auto.fullname` | 릴리스 포함 전체 이름 |
| `investment-auto.chart` | Chart 이름+버전 |
| `investment-auto.labels` | 공통 라벨 |
| `investment-auto.selectorLabels` | 셀렉터 라벨 |
| `investment-auto.serviceAccountName` | ServiceAccount 이름 |
| `investment-auto.databaseHost` | DB 호스트 자동 결정 |
| `investment-auto.databaseSecretName` | DB Secret 이름 |
| `investment-auto.kisSecretName` | KIS API Secret 이름 |
| `investment-auto.configMapName` | ConfigMap 이름 |

### configmap.yaml

애플리케이션 설정을 담는 ConfigMap입니다:

- 환경 변수 형식의 설정
- `database.json` 파일 형식의 설정 (마운트용)

**환경 변수:**
- `APP_MODE`: 실행 모드
- `APP_INTERVAL`: 스케줄 간격
- `APP_ENVIRONMENT`: demo/real 환경
- `DB_*`: 데이터베이스 설정

### deployment.yaml

애플리케이션 Pod를 관리하는 Deployment입니다:

**주요 기능:**
- 컨테이너 이미지 설정
- 실행 명령어 및 인자 설정
- 환경 변수 주입 (ConfigMap, Secret)
- 볼륨 마운트 (설정 파일)
- 헬스체크 (Liveness/Readiness Probe)
- 리소스 제한

**환경 변수 소스:**
- ConfigMap: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_SSLMODE`
- Secret: `DB_PASSWORD`, `KIS_APP_KEY`, `KIS_APP_SECRET`, `UPBIT_*`

### secret.yaml

민감한 정보를 저장하는 Secret입니다:

**KIS Secret:**
- `KIS_APP_KEY`: KIS API 앱 키
- `KIS_APP_SECRET`: KIS API 앱 시크릿
- `UPBIT_ACCESS_KEY`: Upbit 액세스 키 (선택)
- `UPBIT_SECRET_KEY`: Upbit 시크릿 키 (선택)

**Database Secret:**
- `password`: DB 사용자 비밀번호
- `postgres-password`: PostgreSQL 관리자 비밀번호

### service.yaml

Pod에 대한 네트워크 접근을 제공하는 Service입니다:

| 설정 | 기본값 |
|------|--------|
| Type | ClusterIP |
| Port | 80 |
| Target Port | 5000 |

### ingress.yaml

외부에서 서비스에 접근하기 위한 Ingress입니다:

**기능:**
- 도메인 기반 라우팅
- TLS 종료 (선택)
- Path 기반 라우팅

**Annotations:**
- `nginx.ingress.kubernetes.io/rewrite-target`: URL 재작성
- `nginx.ingress.kubernetes.io/ssl-redirect`: HTTPS 리다이렉트
- `cert-manager.io/cluster-issuer`: 인증서 발급자

### postgresql-zalando.yaml

Zalando PostgreSQL Operator를 사용한 DB 클러스터 정의:

```yaml
apiVersion: "acid.zalan.do/v1"
kind: postgresql
spec:
  teamId: acid
  numberOfInstances: 1-3
  volume:
    size: 5Gi
  users:
    appuser: []
  databases:
    appdb: appuser
```

**참고:** `zalandoPostgresql.enabled: true`일 때만 생성됩니다.

### namespace.yaml

애플리케이션용 Namespace를 생성합니다.

### serviceaccount.yaml

Pod 실행을 위한 ServiceAccount를 생성합니다.

## Values 설정

### 애플리케이션 설정

```yaml
app:
  name: investment-auto
  replicaCount: 1
  
  image:
    repository: ghcr.io/yourusername/investment-auto
    tag: latest
    pullPolicy: Always
  
  mode: schedule          # once 또는 schedule
  interval: 60            # 체크 간격 (초)
  environment: demo       # demo 또는 real
  
  web:
    enabled: true
    port: 5000
  
  dbMode: true            # DB 저장 활성화
  
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi
```

### 헬스체크 설정

```yaml
app:
  livenessProbe:
    enabled: true
    path: /api/health
    initialDelaySeconds: 30
    periodSeconds: 30
    timeoutSeconds: 5
    failureThreshold: 3
  
  readinessProbe:
    enabled: true
    path: /api/health
    initialDelaySeconds: 15
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 3
```

### PostgreSQL 설정 (Bitnami)

```yaml
postgresql:
  enabled: true
  
  auth:
    username: appuser
    database: appdb
    existingSecret: investment-auto-db-secret
    secretKeys:
      adminPasswordKey: postgres-password
      userPasswordKey: password
  
  primary:
    persistence:
      enabled: true
      size: 5Gi
```

### Ingress 설정

```yaml
ingress:
  enabled: true
  className: nginx
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: investment.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: investment-auto-tls
      hosts:
        - investment.yourdomain.com
```

### Secret 설정

```yaml
secrets:
  kis:
    appKey: ""        # Base64 인코딩 전 값
    appSecret: ""
  upbit:
    accessKey: ""
    secretKey: ""
  database:
    password: ""
    postgresPassword: ""
```

## 사용법

### 로컬 테스트 (템플릿 렌더링)

```bash
helm template investment-auto ./deployment/helm \
  -f ./deployment/helm/values.yaml
```

### 직접 배포

```bash
# 설치
helm install investment-auto ./deployment/helm \
  -f ./deployment/helm/values.yaml \
  -n investment-auto --create-namespace

# 업그레이드
helm upgrade investment-auto ./deployment/helm \
  -f ./deployment/helm/values.yaml \
  -n investment-auto

# 삭제
helm uninstall investment-auto -n investment-auto
```

### 값 오버라이드

```bash
# 파일로 오버라이드
helm install investment-auto ./deployment/helm \
  -f values.yaml \
  -f values-prod.yaml \
  -n investment-auto

# 명령줄로 오버라이드
helm install investment-auto ./deployment/helm \
  --set app.environment=real \
  --set app.replicaCount=2 \
  -n investment-auto
```

## 의존성

이 Chart는 다음 의존성을 가집니다:

| Chart | 버전 | 조건 |
|-------|------|------|
| postgresql (Bitnami) | 12.x.x | `postgresql.enabled: true` |

의존성 업데이트:

```bash
helm dependency update ./deployment/helm
```

## 문제 해결

### Chart 유효성 검사

```bash
helm lint ./deployment/helm
```

### 렌더링된 매니페스트 확인

```bash
helm template investment-auto ./deployment/helm | kubectl apply --dry-run=client -f -
```

### 특정 템플릿만 렌더링

```bash
helm template investment-auto ./deployment/helm -s templates/deployment.yaml
```

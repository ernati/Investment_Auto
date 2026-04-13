# ArgoCD 배포 가이드

## 개요

Investment Auto 애플리케이션을 ArgoCD를 통해 Kubernetes 클러스터에 자동 배포하는 방법을 설명합니다.

**특징**: Docker 이미지 빌드 불필요! Python 공식 이미지 + Git Clone 방식으로 간단하게 배포합니다.

## 배포 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub Repository                        │
│              (git@github.com:ernati/Investment_Auto.git)         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ 코드 Push (main 브랜치)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                            ArgoCD                                │
│  ┌─────────────────┐    ┌─────────────────────────────────────┐ │
│  │   AppProject    │    │         ApplicationSet              │ │
│  │ investment-auto │────│    deployment/helm 디렉토리 감시    │ │
│  └─────────────────┘    └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ Helm Chart 배포
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                            │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                  Namespace: investment-auto                  ││
│  │                                                              ││
│  │  [Pod 시작 시]                                               ││
│  │  ┌──────────────────────────────────────────────────────┐   ││
│  │  │ initContainer (python:3.11-slim)                     │   ││
│  │  │  1. apt-get install git                              │   ││
│  │  │  2. git clone Investment_Auto                        │   ││
│  │  │  3. pip install -r requirements.txt                  │   ││
│  │  └──────────────────────────────────────────────────────┘   ││
│  │                          │                                   ││
│  │                          ▼                                   ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       ││
│  │  │  Container   │  │   Service    │  │   Ingress    │       ││
│  │  │ python:3.11  │──│   ClusterIP  │──│    nginx     │       ││
│  │  │  (실행)      │  │   Port 80    │  │  TLS 적용    │       ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘       ││
│  │         │                                                    ││
│  │         │ hostPath 마운트                                    ││
│  │         ▼                                                    ││
│  │  ┌──────────────────────────────────────────────────────┐   ││
│  │  │ 1. /home/ernati/Services/Investment_Auto/Config/     │   ││
│  │  │    ├── config.json                                   │   ││
│  │  │    ├── config_basic.json                             │   ││
│  │  │    ├── config_advanced.json                          │   ││
│  │  │    └── database.json                                 │   ││
│  │  │                                                      │   ││
│  │  │ 2. /home/ernati/Services/Investment_Auto/            │   ││
│  │  │    Scripts/modules/demo_data/                        │   ││
│  │  │    └── cash_*.json (현금/포지션 데이터)              │   ││
│  │  └──────────────────────────────────────────────────────┘   ││
│  │         │                                                    ││
│  │         │ DB 연결                                            ││
│  │         ▼                                                    ││
│  │  ┌──────────────┐                                            ││
│  │  │  PostgreSQL  │                                            ││
│  │  │  StatefulSet │                                            ││
│  │  │  Port 5432   │                                            ││
│  │  └──────────────┘                                            ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 배포 흐름

1. **코드 Push** → `main` 브랜치에 코드 Push
2. **ArgoCD 감지** → `deployment/helm` 변경 감지
3. **Helm 배포** → Pod 생성 시 자동으로 Git clone + pip install
4. **앱 실행** → portfolio_rebalancing.py 실행

## 디렉토리 구조

```
Investment_Auto/
└── deployment/
    ├── Invest-Auto-appproject.yaml    # ArgoCD AppProject 정의
    ├── Invest-Auto-Applicationset.yaml # ArgoCD ApplicationSet 정의
    └── helm/
        ├── Chart.yaml                  # Helm Chart 메타데이터
        ├── values.yaml                 # 기본 설정값
        └── templates/
            ├── _helpers.tpl            # 헬퍼 템플릿
            ├── configmap.yaml          # ConfigMap
            ├── deployment.yaml         # 애플리케이션 Deployment
            ├── ingress.yaml            # Ingress 설정
            ├── namespace.yaml          # Namespace 생성
            ├── postgresql-zalando.yaml # Zalando PostgreSQL (선택)
            ├── secret.yaml             # Secret 관리
            ├── service.yaml            # Service 정의
            └── serviceaccount.yaml     # ServiceAccount
```

## 사전 요구사항

1. **Kubernetes 클러스터**: v1.25 이상 권장
2. **ArgoCD**: v2.8 이상 권장
3. **Nginx Ingress Controller**: 외부 접근용
4. **cert-manager**: TLS 인증서 자동 발급 (선택)
5. **호스트 폴더 준비**: 운영 서버에 다음 경로가 존재해야 함
   ```
   /home/ernati/Services/Investment_Auto/Config/
   ├── config.json           # KIS API 설정
   ├── config_basic.json     # 기본 설정
   ├── config_advanced.json  # 고급 설정
   └── database.json         # DB 연결 설정
   
   /home/ernati/Services/Investment_Auto/Scripts/modules/demo_data/
   └── cash_*.json           # 현금/포지션 데이터 파일
   ```

## 설치 단계

### 1. ArgoCD 설치 (미설치 시)

```bash
# ArgoCD 네임스페이스 생성 및 설치
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# ArgoCD CLI 설치 (선택)
# Windows: choco install argocd-cli
# macOS: brew install argocd
```

### 2. Git 저장소 등록 (SSH)

```bash
# SSH 키 생성 (없는 경우)
ssh-keygen -t ed25519 -C "argocd@investment-auto"

# ArgoCD에 SSH 키로 Git 저장소 등록
argocd repo add git@github.com:ernati/Investment_Auto.git \
  --ssh-private-key-path ~/.ssh/id_ed25519

# 또는 kubectl로 직접 Secret 생성
kubectl create secret generic investment-auto-repo \
  --from-file=sshPrivateKey=~/.ssh/id_ed25519 \
  -n argocd
kubectl label secret investment-auto-repo -n argocd \
  argocd.argoproj.io/secret-type=repository
kubectl annotate secret investment-auto-repo -n argocd \
  "url=git@github.com:ernati/Investment_Auto.git"
```

> **참고**: GitHub 저장소 Settings > Deploy keys에 SSH 공개키(`~/.ssh/id_ed25519.pub`)를 등록해야 합니다.

### 3. AppProject 생성

```bash
kubectl apply -f deployment/Invest-Auto-appproject.yaml
```

### 4. Namespace 생성

```bash
kubectl create namespace investment-auto
```

> **참고**: 설정 파일(config.json, database.json 등)은 호스트의 `/home/ernati/Services/Investment_Auto/Config/` 폴더에서 자동으로 마운트됩니다. K8s Secret 생성이 필요 없습니다.

### 5. ApplicationSet 배포

```bash
kubectl apply -f deployment/Invest-Auto-Applicationset.yaml
```

### 6. 배포 확인

```bash
# ArgoCD UI에서 확인
argocd app list

# 또는 kubectl로 확인
kubectl get applications -n argocd
kubectl get pods -n investment-auto

# Pod 로그 확인 (initContainer 포함)
kubectl logs -n investment-auto <pod-name> -c git-clone  # init 로그
kubectl logs -n investment-auto <pod-name>               # 앱 로그
```

## 설정 커스터마이징

### values.yaml 주요 설정

| 설정 | 설명 | 기본값 |
|------|------|--------|
| `app.image.repository` | Python 이미지 | `python` |
| `app.image.tag` | Python 버전 | `3.11-slim` |
| `app.git.repository` | Git 저장소 URL | `https://github.com/ernati/Investment_Auto.git` |
| `app.git.branch` | Git 브랜치 | `main` |
| `app.hostConfig.path` | 호스트 Config 폴더 경로 | `/home/ernati/Services/Investment_Auto/Config` |
| `app.hostDemoData.path` | 호스트 demo_data 폴더 경로 | `/home/ernati/Services/Investment_Auto/Scripts/modules/demo_data` |
| `app.mode` | 실행 모드 (once/schedule) | `schedule` |
| `app.environment` | 환경 (demo/real) | `demo` |
| `app.web.port` | 웹 서버 포트 | `5000` |
| `app.dbMode` | DB 모드 활성화 | `true` |
| `postgresql.enabled` | Bitnami PostgreSQL 사용 | `true` |
| `ingress.enabled` | Ingress 활성화 | `true` |
| `ingress.hosts[0].host` | 외부 도메인 | `investment.yourdomain.com` |

### 환경별 values 파일

프로덕션 환경용 설정 파일을 별도로 생성할 수 있습니다:

```yaml
# values-prod.yaml
app:
  environment: real
  replicaCount: 2
  
ingress:
  hosts:
    - host: investment.production.com
      paths:
        - path: /
          pathType: Prefix
```

ApplicationSet에서 해당 파일을 사용하려면:

```yaml
source:
  helm:
    valueFiles:
      - values.yaml
      - values-prod.yaml
```

## PostgreSQL 설정

### 옵션 1: Bitnami Helm Chart (기본)

`values.yaml`에서 `postgresql.enabled: true`로 설정하면 Bitnami PostgreSQL StatefulSet이 자동 배포됩니다.

### 옵션 2: Zalando PostgreSQL Operator

고가용성이 필요한 경우 Zalando Operator를 사용할 수 있습니다:

1. Zalando Operator 설치:
```bash
kubectl apply -k github.com/zalando/postgres-operator/manifests
```

2. values.yaml 수정:
```yaml
postgresql:
  enabled: false

zalandoPostgresql:
  enabled: true
  numberOfInstances: 3
```

## Ingress 설정

### TLS 인증서 자동 발급 (cert-manager 사용 시)

```yaml
ingress:
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  tls:
    - secretName: investment-auto-tls
      hosts:
        - investment.yourdomain.com
```

### 수동 TLS 인증서 설정

```bash
kubectl create secret tls investment-auto-tls \
  --cert=path/to/cert.crt \
  --key=path/to/cert.key \
  -n investment-auto
```

## 트러블슈팅

### ArgoCD Sync 실패

```bash
# 상세 로그 확인
argocd app get investment-auto --show-operation

# 수동 Sync 시도
argocd app sync investment-auto
```

### Pod 시작 실패

```bash
# Pod 상태 확인
kubectl get pods -n investment-auto
kubectl describe pod <pod-name> -n investment-auto
kubectl logs <pod-name> -n investment-auto
```

### 데이터베이스 연결 실패

```bash
# PostgreSQL Pod 상태 확인
kubectl get pods -n investment-auto -l app.kubernetes.io/name=postgresql

# 연결 테스트
kubectl exec -it <investment-auto-pod> -n investment-auto -- \
  python -c "import psycopg2; print('OK')"
```

## 롤백

### ArgoCD를 통한 롤백

```bash
# 히스토리 확인
argocd app history investment-auto

# 특정 버전으로 롤백
argocd app rollback investment-auto <revision>
```

### Helm을 통한 롤백 (수동 배포 시)

```bash
helm rollback investment-auto <revision> -n investment-auto
```

## 참고 자료

- [ArgoCD 공식 문서](https://argo-cd.readthedocs.io/)
- [Helm 공식 문서](https://helm.sh/docs/)
- [Bitnami PostgreSQL Chart](https://github.com/bitnami/charts/tree/main/bitnami/postgresql)
- [Zalando PostgreSQL Operator](https://github.com/zalando/postgres-operator)

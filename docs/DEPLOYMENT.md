# 배포 가이드

## 개요

이 문서는 PDF to EPUB 변환기 애플리케이션의 배포 방법을 설명합니다. 개발 환경부터 프로덕션 환경까지 다양한 배포 옵션을 제공합니다.

## 아키텍처 개요

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Redis         │    │   Celery        │
│   (API Server)  │◄──►│   (Message      │◄──►│   (Task Queue)  │
│                 │    │   Broker)       │    │                 │
│                 │    │                 │    │                 │
│ - /api/v1/      │    │                 │    │ - conversion_   │
│   /start        │    │                 │    │   task          │
│ - /status/{id}  │    │                 │    │ - retry_task    │
│ - /download/{id}│    │                 │    │ - cancel_task   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Celery        │
                       │   Workers       │
                       │                 │
                       │ - PDF 분석      │
                       │ - OCR 처리      │
                       │ - EPUB 생성     │
                       │ - 결과 저장     │
                       └─────────────────┘
```

## 사전 요구사항

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.10+ (로컬 개발용)
- Node.js 18+ (프론트엔드 개발용)

## 개발 환경 설정

### 1. 로컬 개발 환경

#### 백엔드 설정

```bash
# 1. 백엔드 디렉토리로 이동
cd backend

# 2. Python 가상 환경 생성
python -m venv venv

# 3. 가상 환경 활성화
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate     # Windows

# 4. 의존성 설치
pip install -r requirements.txt

# 5. 환경 변수 설정
cp .env.example .env
# .env 파일에 필요한 변수 설정

# 6. Celery Worker 실행 (별도 터미널)
celery -A app.celery_config:celery_app worker --loglevel=info --concurrency=4

# 7. Celery Beat 실행 (별도 터미널)
celery -A app.celery_config:celery_app beat --loglevel=info

# 8. 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 프론트엔드 설정

```bash
# 1. 프론트엔드 디렉토리로 이동
cd frontend

# 2. 의존성 설치
npm install

# 3. 환경 변수 설정
cp .env.example .env
# .env 파일에 필요한 변수 설정

# 4. 개발 서버 실행
npm run dev
```

### 2. Docker 개발 환경

```bash
# 1. Docker Compose로 전체 서비스 시작
docker-compose up -d

# 2. 로그 확인
docker-compose logs -f

# 3. 서비스 스톱
docker-compose down

# 4. 특정 서비스 재시작
docker-compose restart celery_worker

# 5. Celery Flower 모니터링 대시보드 접속
# http://localhost:5555
```

## 프로덕션 환경 설정

### 1. Docker Compose 프로덕션 배포

```bash
# 1. 프로덕션용 docker-compose.yml 생성
cp docker-compose.yml docker-compose.prod.yml

# 2. 프로덕션 설정 수정
# - 환경 변수 설정
# - 볼륨 마운트 설정
# - 보안 설정 추가

# 3. 프로덕션 서비스 시작
docker-compose -f docker-compose.prod.yml up -d

# 4. 상태 확인
docker-compose -f docker-compose.prod.yml ps

# 5. 로그 확인
docker-compose -f docker-compose.prod.yml logs -f
```

### 2. Kubernetes 배포

#### Kubernetes 매니페스트 파일

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: pdf-to-epub
```

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: pdf-to-epub
data:
  .env: |
    DEBUG=false
    DATABASE_URL=postgresql://user:password@postgres:5432/pdf_to_epub
    REDIS_URL=redis://redis:6379/0
    SECURITY_API_KEY=your-production-api-key
```

```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: pdf-to-epub
type: Opaque
data:
  database-password: <base64-encoded-password>
  redis-password: <base64-encoded-password>
  api-key: <base64-encoded-api-key>
```

```yaml
# k8s/postgres.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: pdf-to-epub
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: pdf_to_epub
        - name: POSTGRES_USER
          value: user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-password
        ports:
        - containerPort: 5372
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
```

```yaml
# k8s/redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: pdf-to-epub
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-storage
          mountPath: /data
      volumes:
      - name: redis-storage
        persistentVolumeClaim:
          claimName: redis-pvc
```

```yaml
# k8s/web.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: pdf-to-epub
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: your-registry/pdf-to-epub-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://user:$(POSTGRES_PASSWORD)@postgres:5432/pdf_to_epub"
        - name: REDIS_URL
          value: "redis://:$(REDIS_PASSWORD)@redis:6379/0"
        - name: DEBUG
          value: "false"
        volumeMounts:
        - name: app-config
          mountPath: /app/.env
          subPath: .env
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: app-config
        configMap:
          name: app-config
```

```yaml
# k8s/celery-worker.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
  namespace: pdf-to-epub
spec:
  replicas: 3
  selector:
    matchLabels:
      app: celery-worker
  template:
    metadata:
      labels:
        app: celery-worker
    spec:
      containers:
      - name: celery-worker
        image: your-registry/pdf-to-epub-backend:latest
        command: ["celery", "-A", "app.celery_config:celery_app", "worker", "--loglevel=info", "--concurrency=4"]
        env:
        - name: DATABASE_URL
          value: "postgresql://user:$(POSTGRES_PASSWORD)@postgres:5432/pdf_to_epub"
        - name: REDIS_URL
          value: "redis://:$(REDIS_PASSWORD)@redis:6379/0"
        - name: DEBUG
          value: "false"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
      volumes:
      - name: app-config
        configMap:
          name: app-config
```

```yaml
# k8s/celery-beat.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-beat
  namespace: pdf-to-epub
spec:
  replicas: 1
  selector:
    matchLabels:
      app: celery-beat
  template:
    metadata:
      labels:
        app: celery-beat
    spec:
      containers:
      - name: celery-beat
        image: your-registry/pdf-to-epub-backend:latest
        command: ["celery", "-A", "app.celery_config:celery_app", "beat", "--loglevel=info"]
        env:
        - name: DATABASE_URL
          value: "postgresql://user:$(POSTGRES_PASSWORD)@postgres:5432/pdf_to_epub"
        - name: REDIS_URL
          value: "redis://:$(REDIS_PASSWORD)@redis:6379/0"
        - name: DEBUG
          value: "false"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
      volumes:
      - name: app-config
        configMap:
          name: app-config
```

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
  namespace: pdf-to-epub
spec:
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: pdf-to-epub-ingress
  namespace: pdf-to-epub
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - pdf-to-epub.example.com
    secretName: pdf-to-epub-tls
  rules:
  - host: pdf-to-epub.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

### 3. 배포 스크립트

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

# 환경 변수 설정
NAMESPACE="pdf-to-epub"
IMAGE_TAG="latest"
REGISTRY="your-registry"

# Docker 이미지 빌드
echo "Building Docker images..."
docker build -f docker/backend.Dockerfile -t ${REGISTRY}/pdf-to-epub-backend:${IMAGE_TAG} .

# Docker 이미지 푸시
echo "Pushing Docker images..."
docker push ${REGISTRY}/pdf-to-epub-backend:${IMAGE_TAG}

# Kubernetes 배포
echo "Deploying to Kubernetes..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/web.yaml
kubectl apply -f k8s/celery-worker.yaml
kubectl apply -f k8s/celery-beat.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# 배포 상태 확인
echo "Checking deployment status..."
kubectl get pods -n ${NAMESPACE}
kubectl get services -n ${NAMESPACE}
kubectl get ingress -n ${NAMESPACE}

echo "Deployment completed successfully!"
```

## 모니터링 및 로깅

### 1. Celery Flower 모니터링

```bash
# Flower 대시보드 접속
http://localhost:5555

# 또는 프로덕션 환경에서
http://pdf-to-epub.example.com/flower/
```

### 2. 로깅

```bash
# Docker 컨테이너 로그 확인
docker-compose logs -f web
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat

# Kubernetes Pod 로그 확인
kubectl logs -f deployment/web -n pdf-to-epub
kubectl logs -f deployment/celery-worker -n pdf-to-epub
kubectl logs -f deployment/celery-beat -n pdf-to-epub
```

### 3. 메트릭 모니터링

```python
# app/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client.core import CollectorRegistry
import time

# 메트릭 정의
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_JOBS = Gauge('active_jobs_total', 'Number of active conversion jobs')
COMPLETED_JOBS = Counter('completed_jobs_total', 'Total completed jobs')
FAILED_JOBS = Counter('failed_jobs_total', 'Total failed jobs')

def record_request(method, endpoint):
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()

def record_request_duration(duration):
    REQUEST_DURATION.observe(duration)

def update_active_jobs(count):
    ACTIVE_JOBS.set(count)

def record_completed_job():
    COMPLETED_JOBS.inc()

def record_failed_job():
    FAILED_JOBS.inc()
```

## 백업 및 복구

### 1. 데이터베이스 백업

```bash
# PostgreSQL 백업
pg_dump -h localhost -U user pdf_to_epub > backup_$(date +%Y%m%d_%H%M%S).sql

# 또는 Docker를 사용한 백업
docker exec postgres_container pg_dump -U user pdf_to_epub > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2. Redis 백업

```bash
# Redis 데이터 덤프
docker exec redis_container redis-cli BGSAVE
docker exec redis_container redis-cli --rdb /data/dump.rdb

# 또는 Redis 데이터 백업
docker exec redis_container redis-cli --rdb /data/backup_$(date +%Y%m%d_%H%M%S).rdb
```

### 3. 파일 백업

```bash
# 변환 결과 파일 백업
tar -czf conversion_results_backup_$(date +%Y%m%d_%H%M%S).tar.gz /path/to/output_dir
```

## 성능 최적화

### 1. Celery Worker 최적화

```python
# app/celery_config.py
celery_app.conf.update(
    # 워커 최적화 설정
    worker_prefetch_multiplier=1,  # 워커당 동시 처리 작업 수
    worker_max_tasks_per_child=1000,  # 워커당 최대 작업 수
    worker_max_memory_per_child="512MB",  # 워커당 최대 메모리
    task_acks_late=True,  # 작업 완료 후 확인
    worker_hijack_root_logger=False,  # 로깅 설정
)
```

### 2. Redis 최적화

```bash
# redis.conf 설정
maxmemory 2gb
maxmemory-policy allkeys-lru
timeout 300
tcp-keepalive 60
```

### 3. 데이터베이스 최적화

```sql
-- 인덱스 생성
CREATE INDEX idx_conversions_created_at ON conversions(created_at);
CREATE INDEX idx_conversions_status ON conversions(status);

-- 쿼리 최적화
EXPLAIN ANALYZE SELECT * FROM conversions WHERE status = 'completed' ORDER BY created_at DESC;
```

## 보안 설정

### 1. API 키 관리

```bash
# 환경 변수 설정
export SECURITY_API_KEY="your-secure-api-key-here"

# 또는 Kubernetes Secret
kubectl create secret generic api-key --from-literal=key=your-secure-api-key-here
```

### 2. SSL/TLS 설정

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name pdf-to-epub.example.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
}
```

### 3. 방화벽 설정

```bash
# 방화벽 규칙
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 5432/tcp   # PostgreSQL
ufw allow 6379/tcp   # Redis
ufw enable
```

## 문제 해결

### 1. 일반적인 문제

#### Celery Worker가 시작되지 않음

```bash
# Celery Worker 상태 확인
celery -A app.celery_config:celery_app inspect ping

# 로그 확인
docker-compose logs celery_worker
```

#### Redis 연결 실패

```bash
# Redis 연결 테스트
docker exec redis_container redis-cli ping

# Redis 로그 확인
docker-compose logs redis
```

#### 데이터베이스 연결 실패

```bash
# 데이터베이스 연결 테스트
docker exec postgres_container psql -U user -d pdf_to_epub -c "SELECT 1"

# 데이터베이스 로그 확인
docker-compose logs db
```

### 2. 성능 문제

#### 작업 처리 지연

```bash
# 큐 상태 확인
celery -A app.celery_config:celery_app inspect active
celery -A app.celery_config:celery_app inspect reserved

# 워커 상태 확인
docker stats
```

#### 메모리 사용량 과다

```bash
# 메모리 사용량 확인
docker stats --no-stream

# Celery Worker 메모리 제한 확인
docker-compose exec celery_worker cat /proc/self/status | grep VmRSS
```

### 3. 모니터링 스크립트

```bash
#!/bin/bash
# scripts/monitor.sh

echo "=== System Status ==="
echo "Uptime: $(uptime)"
echo "Disk Usage: $(df -h /)"
echo "Memory Usage: $(free -h)"

echo -e "\n=== Docker Status ==="
docker-compose ps

echo -e "\n=== Celery Status ==="
celery -A app.celery_config:celery_app inspect stats

echo -e "\n=== Database Status ==="
docker-compose exec db pg_isready -U user -d pdf_to_epub

echo -e "\n=== Redis Status ==="
docker-compose exec redis redis-cli ping
```

## 업데이트 및 롤백

### 1. 업데이트

```bash
# 이미지 업데이트
docker-compose pull

# 서비스 재시작
docker-compose up -d --force-recreate

# Kubernetes 업데이트
kubectl set image deployment/web web=your-registry/pdf-to-epub-backend:v2.0.0
kubectl rollout status deployment/web
```

### 2. 롤백

```bash
# Docker 롤백
docker-compose down
docker-compose up -d --force-recreate --rollback

# Kubernetes 롤백
kubectl rollout undo deployment/web
kubectl rollout status deployment/web
```

이 배포 가이드는 PDF to EPUB 변환기 애플리케이션의 다양한 배포 시나리오를 다룹니다. 특정 환경에 맞게 설정을 조정하여 사용하시기 바랍니다.
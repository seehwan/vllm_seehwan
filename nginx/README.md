# Nginx Configuration

vLLM 챗봇 서비스의 리버스 프록시 및 로드 밸런싱을 담당하는 Nginx 설정입니다.

## 🌐 주요 기능

### 리버스 프록시

- **Frontend 서비스** (React): `http://frontend:3000`
- **Gateway 서비스** (FastAPI): `http://gateway:8080`
- **정적 파일** 캐싱 및 최적화

### SSE 스트리밍 최적화

- **버퍼링 비활성화**: 실시간 스트리밍 지원
- **연결 유지**: HTTP/1.1 Keep-Alive
- **타임아웃 설정**: 긴 스트리밍 세션 지원

### 보안 헤더

- **X-Frame-Options**: 클릭재킹 방지
- **X-Content-Type-Options**: MIME 타입 스니핑 방지
- **X-XSS-Protection**: XSS 공격 방지

## 📁 파일 구조

```
nginx/
├── nginx.conf              # 메인 설정 파일
└── ssl/                   # SSL 인증서 디렉토리
    ├── cert.pem           # SSL 인증서 (선택사항)
    └── key.pem            # SSL 개인키 (선택사항)
```

## ⚙️ 핵심 설정

### 업스트림 서버

```nginx
upstream frontend {
    server frontend:3000;
}

upstream gateway {
    server gateway:8080;
}
```

### 메인 서버 블록

```nginx
server {
    listen 80;
    server_name localhost;

    # 보안 헤더
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # 라우팅 설정
    location / {
        proxy_pass http://frontend;
    }

    location /api/ {
        proxy_pass http://gateway;
        # SSE 스트리밍 최적화
    }
}
```

### SSE 스트리밍 최적화 설정

```nginx
location /api/ {
    proxy_pass http://gateway;

    # 기본 프록시 헤더
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # SSE 스트리밍 최적화
    proxy_buffering off;                # 버퍼링 비활성화
    proxy_cache off;                   # 캐싱 비활성화
    proxy_read_timeout 3600s;          # 읽기 타임아웃 1시간
    proxy_connect_timeout 60s;         # 연결 타임아웃
    proxy_send_timeout 60s;            # 전송 타임아웃

    # HTTP/1.1 연결 유지
    proxy_http_version 1.1;
    proxy_set_header Connection "";

    # 청크 전송 인코딩
    chunked_transfer_encoding on;

    # 버퍼링 비활성화 헤더
    add_header X-Accel-Buffering no;
}
```

## 🔒 SSL/TLS 설정

### Let's Encrypt 인증서

```bash
# Certbot 설치
sudo apt-get install certbot python3-certbot-nginx

# 인증서 발급
sudo certbot --nginx -d yourdomain.com

# 자동 갱신 설정
sudo crontab -e
# 추가: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 수동 SSL 설정

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # SSL 보안 설정
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS 설정
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

## 🚀 성능 최적화

### Gzip 압축

```nginx
# gzip 설정 (이미 적용됨)
gzip on;
gzip_vary on;
gzip_min_length 10240;
gzip_proxied any;
gzip_types
    text/plain
    text/css
    text/xml
    text/javascript
    application/json
    application/javascript
    application/xml+rss
    application/atom+xml
    image/svg+xml;
```

### 정적 파일 캐싱

```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    proxy_pass http://frontend;
    expires 1y;
    add_header Cache-Control "public, immutable";

    # ETag 설정
    etag on;
}
```

### 연결 최적화

```nginx
# worker 프로세스 설정
worker_processes auto;
worker_connections 1024;

# Keep-alive 설정
keepalive_timeout 65;
keepalive_requests 100;

# TCP 최적화
sendfile on;
tcp_nopush on;
tcp_nodelay on;
```

## 📊 로깅 및 모니터링

### 로그 형식

```nginx
log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                '$status $body_bytes_sent "$http_referer" '
                '"$http_user_agent" "$http_x_forwarded_for"';

log_format detailed '$remote_addr - $remote_user [$time_local] '
                   '"$request" $status $body_bytes_sent '
                   '"$http_referer" "$http_user_agent" '
                   'rt=$request_time uct="$upstream_connect_time" '
                   'uht="$upstream_header_time" urt="$upstream_response_time"';
```

### 로그 분석

```bash
# 실시간 로그 모니터링
docker compose logs -f nginx

# 에러 로그 확인
docker compose exec nginx tail -f /var/log/nginx/error.log

# 접속 통계
docker compose exec nginx tail -f /var/log/nginx/access.log | grep -E "(GET|POST)"

# 응답 시간 분석
tail -f /var/log/nginx/access.log | awk '{print $NF}' | grep -E "^[0-9]"
```

## 🔧 로드 밸런싱

### 다중 Gateway 인스턴스

```nginx
upstream gateway {
    # 라운드 로빈 (기본)
    server gateway-1:8080;
    server gateway-2:8080;
    server gateway-3:8080;

    # 가중치 기반
    # server gateway-1:8080 weight=3;
    # server gateway-2:8080 weight=1;

    # IP 해시 (세션 고정)
    # ip_hash;

    # 최소 연결
    # least_conn;
}
```

### 헬스체크

```nginx
upstream gateway {
    server gateway-1:8080 max_fails=3 fail_timeout=30s;
    server gateway-2:8080 max_fails=3 fail_timeout=30s;
    server gateway-3:8080 backup;  # 백업 서버
}
```

## 🛡️ 보안 강화

### Rate Limiting

```nginx
# Rate limit 설정
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

server {
    # API 요청 제한
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://gateway;
    }

    # 로그인 요청 제한
    location /api/auth/login {
        limit_req zone=login burst=5;
        proxy_pass http://gateway;
    }
}
```

### IP 화이트리스트

```nginx
# 관리자 페이지 접근 제한
location /admin/ {
    allow 192.168.1.0/24;  # 내부 네트워크만 허용
    allow 10.0.0.0/8;
    deny all;

    proxy_pass http://gateway;
}
```

### DDoS 방어

```nginx
# 연결 수 제한
limit_conn_zone $binary_remote_addr zone=conn_limit_per_ip:10m;
limit_conn_zone $server_name zone=conn_limit_per_server:10m;

server {
    limit_conn conn_limit_per_ip 20;
    limit_conn conn_limit_per_server 1000;
}
```

## 🚀 배포 및 운영

### Docker Compose 통합

```yaml
# docker-compose.yml에서 Nginx 설정
nginx:
  image: nginx:alpine
  container_name: nginx-proxy
  restart: unless-stopped
  ports:
    - '80:80'
    - '443:443'
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf
    - ./nginx/ssl:/etc/nginx/ssl
  depends_on:
    - frontend
    - gateway
```

### 설정 검증

```bash
# 설정 파일 문법 검사
docker compose exec nginx nginx -t

# 설정 다시 로드 (재시작 없이)
docker compose exec nginx nginx -s reload

# 프로세스 상태 확인
docker compose exec nginx ps aux | grep nginx
```

## 🐛 트러블슈팅

### 일반적인 문제

#### 1. 502 Bad Gateway

```bash
# 업스트림 서버 상태 확인
curl -f http://frontend:3000  # 컨테이너 내부에서
curl -f http://gateway:8080/health

# 네트워크 연결 확인
docker compose exec nginx ping frontend
docker compose exec nginx ping gateway
```

#### 2. SSL 인증서 오류

```bash
# 인증서 유효성 검사
openssl x509 -in /path/to/cert.pem -text -noout

# 인증서와 키 매칭 확인
openssl x509 -noout -modulus -in cert.pem | openssl md5
openssl rsa -noout -modulus -in key.pem | openssl md5
```

#### 3. 스트리밍 중단

```bash
# 버퍼 설정 확인
grep -r "proxy_buffering" /etc/nginx/

# 타임아웃 설정 확인
grep -r "timeout" /etc/nginx/nginx.conf
```

### 로그 분석

#### 에러 로그 패턴 분석

```bash
# 자주 발생하는 에러 확인
grep "ERROR" /var/log/nginx/error.log | head -20

# 업스트림 연결 실패
grep "upstream" /var/log/nginx/error.log

# 타임아웃 에러
grep "timeout" /var/log/nginx/error.log
```

#### 성능 분석

```bash
# 응답 시간 분포
awk '{print $NF}' /var/log/nginx/access.log | sort -n | uniq -c

# 상위 요청 URL
awk '{print $7}' /var/log/nginx/access.log | sort | uniq -c | sort -nr | head -10

# HTTP 상태 코드 분포
awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c
```

## 📈 모니터링 설정

### Prometheus 메트릭

```nginx
# nginx-prometheus-exporter 사용
location /nginx_status {
    stub_status on;
    access_log off;
    allow 127.0.0.1;
    deny all;
}
```

### 커스텀 메트릭

```bash
# Docker Compose에 nginx-exporter 추가
nginx-exporter:
  image: nginx/nginx-prometheus-exporter
  ports:
    - "9113:9113"
  command:
    - -nginx.scrape-uri=http://nginx/nginx_status
```

이제 Nginx가 vLLM 챗봇 서비스의 견고한 프론트엔드 프록시 역할을 완벽히 수행할 수 있습니다!

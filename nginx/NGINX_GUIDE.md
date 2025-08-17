# 🌐 Nginx 리버스 프록시 설정 가이드

vLLM 챗봇 서비스를 위한 고성능 웹 서버 및 리버스 프록시 설정입니다.

## ✨ **핵심 기능 개요**

### 🔄 **리버스 프록시 (Reverse Proxy)**
- **Frontend 서비스**: React SPA를 `http://frontend:3000`에서 서빙
- **Gateway API**: FastAPI를 `http://gateway:8080`에서 프록시
- **Load Balancing**: 멀티 인스턴스 환경에서 부하 분산 지원  
- **Failover**: 서버 장애 시 자동 전환 (max_fails, fail_timeout)

### 🚀 **스트리밍 최적화**
- **SSE 스트리밍**: Server-Sent Events 실시간 전송 최적화
- **버퍼링 비활성화**: 즉시 응답 전달 (proxy_buffering off)
- **연결 유지**: HTTP/1.1 Keep-Alive 활용
- **긴 세션 지원**: Chat API는 최대 30분 타임아웃 설정

### 🛡️ **보안 및 성능 최적화**  
- **Rate Limiting**: DDoS 방어 (API 10req/s, Chat 5req/s)
- **보안 헤더**: XSS, CSRF, Content Type 보호
- **Gzip 압축**: 네트워크 대역폭 60-80% 절약  
- **정적 파일 캐싱**: 브라우저 캐시 활용으로 로딩 속도 향상

## 📁 **디렉토리 구조**

```
nginx/
├── nginx.conf              # 메인 설정 파일 (270+ 라인, 완전 최적화)
├── NGINX_GUIDE.md         # 이 문서
└── ssl/                   # SSL 인증서 디렉토리 (선택사항)
    ├── cert.pem           # SSL 인증서
    └── key.pem            # SSL 개인키
```

## ⚡ **고급 성능 최적화 설정**

### 🎯 **Rate Limiting (속도 제한)**
```nginx
# DDoS 방어 및 서버 부하 방지
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;    # API 호출 제한
limit_req_zone $binary_remote_addr zone=chat:10m rate=5r/s;    # Chat API 더 엄격
limit_conn_zone $binary_remote_addr zone=conn_limit_per_ip:10m; # 연결 수 제한

# 적용 예시:
location /api/chat {
    limit_req zone=chat burst=10 nodelay;  # 버스트 허용 + 즉시 처리
    # ... 나머지 설정
}
```

### 🗜️ **Gzip 압축 최적화**
```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;    # 1KB 이상만 압축 (효율성)
gzip_comp_level 6;       # 압축 레벨 (1-9, 6이 최적)
gzip_types
    text/plain text/css text/javascript
    application/json application/javascript
    font/truetype font/opentype
    image/svg+xml;
```

### 📦 **정적 파일 캐싱 전략**  
```nginx
# JavaScript/CSS: 1년 캐시 (immutable)
location ~* \.(js|css|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# 이미지: 30일 캐시  
location ~* \.(png|jpg|jpeg|gif|ico|svg|webp)$ {
    expires 30d;
    add_header Cache-Control "public";
}
```

### 🔌 **업스트림 연결 풀**
```nginx  
upstream gateway {
    server gateway:8080 max_fails=3 fail_timeout=30s;
    keepalive 32;  # 연결 풀 유지 (성능 향상)
}

upstream frontend {
    server frontend:3000 max_fails=3 fail_timeout=30s; 
    keepalive 16;
}
```

## 🛡️ **보안 설정 강화**

### 🔒 **보안 헤더 (Security Headers)**
```nginx
# 기본 보안 헤더 (모든 응답에 적용)
add_header X-Frame-Options DENY always;                        # 클릭재킹 방지
add_header X-Content-Type-Options nosniff always;              # MIME 스니핑 방지  
add_header X-XSS-Protection "1; mode=block" always;            # XSS 방어
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# CSP (Content Security Policy) - 스크립트 주입 방지
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; connect-src 'self' ws: wss:;" always;

# HTTPS 전용 추가 헤더
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
```

### 🚫 **접근 제어**
```nginx
# 숨겨진 파일 접근 차단
location ~ /\. {
    deny all;
    access_log off;
    log_not_found off;
}

# 백업/임시 파일 차단  
location ~ ~$ {
    deny all;
    access_log off;
    log_not_found off;
}

# 관리용 엔드포인트 IP 제한
location /nginx_status {
    allow 127.0.0.1;           # 로컬호스트
    allow 10.0.0.0/8;          # Docker 네트워크
    allow 172.16.0.0/12;       # Docker 네트워크 
    allow 192.168.0.0/16;      # 로컬 네트워크
    deny all;
}
```

## 🌊 **SSE 스트리밍 특화 설정**

### ⚡ **실시간 스트리밍 최적화**
```nginx
location /api/chat {
    # Rate Limiting (Chat API는 더 엄격)
    limit_req zone=chat burst=10 nodelay;
    
    # 스트리밍에 최적화된 특별 설정
    proxy_buffering off;           # 버퍼링 완전 비활성화
    proxy_request_buffering off;   # 요청 버퍼링도 비활성화
    proxy_cache off;               # 캐시 비활성화
    
    # 긴 스트리밍 세션 지원
    proxy_read_timeout 1800s;      # 30분 (긴 대화)
    proxy_send_timeout 300s;       # 5분 전송 타임아웃
    
    # HTTP/1.1 연결 유지
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_set_header Cache-Control no-cache;
    
    # 청크 전송 활성화
    chunked_transfer_encoding on;
    add_header X-Accel-Buffering no;  # Nginx 버퍼링 강제 비활성화
}
```

### 📊 **스트리밍 성능 모니터링**
```nginx
# 스트리밍 전용 로그 형식
log_format streaming '$remote_addr [$time_local] "$request" '
                    '$status $body_bytes_sent '
                    'rt=$request_time ut="$upstream_response_time" '
                    'connection="$connection" '
                    'conn_reqs="$connection_requests"';

# Chat API에 적용                    
location /api/chat {
    access_log /var/log/nginx/streaming.log streaming;
    # ... 나머지 설정
}
```

## ⚙️ **핵심 설정 상세**

### 🔄 **업스트림 서버 설정**

```nginx
upstream frontend {
    server frontend:3000 max_fails=3 fail_timeout=30s;
    # 필요시 추가 서버: server frontend2:3000 backup;
    keepalive 16;  # 업스트림 연결 풀
}

upstream gateway {
    server gateway:8080 max_fails=3 fail_timeout=30s;
    # 필요시 추가 서버: server gateway2:8080 backup;
    keepalive 32;  # API 서버는 더 많은 연결 풀
}
```

### 🌐 **메인 서버 블록**

```nginx
server {
    listen 80;
    server_name localhost;
    
    # 연결 제한
    limit_conn conn_limit_per_ip 20;

    # 보안 헤더
    add_header X-Frame-Options DENY always;
```

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

## � **배포 및 운영 가이드**

### 📦 **Docker Compose 통합**

```yaml
# docker-compose.yml에서 Nginx 설정
services:
  nginx:
    image: nginx:alpine
    container_name: vllm-nginx
    restart: unless-stopped
    ports:
      - '80:80'
      - '443:443'
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - nginx_logs:/var/log/nginx
    depends_on:
      - frontend
      - gateway
    networks:
      - vllm_network
    command: >
      sh -c "nginx -t && exec nginx -g 'daemon off;'"

volumes:
  nginx_logs:

networks:
  vllm_network:
    driver: bridge
```

### ⚙️ **설정 검증 및 관리**

```bash
# 1. 설정 파일 문법 검사
docker compose exec nginx nginx -t

# 2. 설정 다시 로드 (재시작 없이)
docker compose exec nginx nginx -s reload

# 3. Nginx 프로세스 상태 확인
docker compose exec nginx ps aux | grep nginx

# 4. 설정 파일 백업
cp nginx/nginx.conf nginx/nginx.conf.backup.$(date +%Y%m%d)

# 5. 실시간 로그 모니터링
docker compose logs -f nginx
```

### 📊 **성능 튜닝 가이드**

#### **워커 프로세스 최적화**
```nginx
# nginx.conf 상단 (CPU 코어 수에 맞춰 조정)
worker_processes auto;                    # CPU 코어 수만큼 자동 설정
worker_rlimit_nofile 65535;              # 파일 디스크립터 제한
worker_connections 1024;                 # 워커당 동시 연결 수
```

#### **메모리 사용량 최적화**
```bash
# 현재 메모리 사용량 확인
docker stats nginx --no-stream

# Nginx 메모리 사용량 분석
docker compose exec nginx ps aux | awk '/nginx/{sum+=$6} END {print "Total Memory: " sum/1024 " MB"}'
```

## 🔍 **고급 트러블슈팅**

### 🚨 **일반적인 문제와 해결방법**

#### **1. 502 Bad Gateway (가장 흔한 문제)**
```bash
# 원인 진단 순서:
# 1) 업스트림 서버 상태 확인
docker compose ps
curl -f http://localhost:8080/health  # Gateway 직접 확인
curl -f http://localhost:3000         # Frontend 직접 확인

# 2) 네트워크 연결 확인
docker compose exec nginx ping gateway
docker compose exec nginx ping frontend

# 3) 업스트림 설정 확인
docker compose exec nginx nginx -T | grep -A 5 "upstream"

# 4) 로그에서 구체적 오류 확인
docker compose logs nginx | grep -i error
docker compose logs gateway | tail -50
```

#### **2. 스트리밍 중단/지연 문제**
```bash
# Chat API 스트리밍 테스트
curl -N -H "Accept: text/event-stream" \
     -H "Content-Type: application/json" \
     -d '{"messages":[{"role":"user","content":"Hello"}],"model":"current","stream":true}' \
     http://localhost/api/chat

# 버퍼링 설정 확인
docker compose exec nginx nginx -T | grep -i buffer

# 타임아웃 설정 확인  
docker compose exec nginx nginx -T | grep -i timeout
```

#### **3. SSL/HTTPS 인증서 문제**
```bash
# 인증서 유효성 검사
openssl x509 -in nginx/ssl/cert.pem -text -noout

# 인증서와 키 매칭 확인
openssl x509 -noout -modulus -in nginx/ssl/cert.pem | openssl md5
openssl rsa -noout -modulus -in nginx/ssl/key.pem | openssl md5

# 인증서 만료일 확인
openssl x509 -in nginx/ssl/cert.pem -noout -dates
```

#### **4. Rate Limiting 오류 (429 Too Many Requests)**
```bash
# Rate limit 상태 확인
docker compose exec nginx nginx -T | grep -A 3 "limit_req_zone"

# Rate limit 로그 확인
docker compose logs nginx | grep "limiting requests"

# 임시로 Rate limit 비활성화 (디버깅용)
# nginx.conf에서 limit_req 라인 주석 처리 후:
docker compose exec nginx nginx -s reload
```

### 📈 **성능 진단 및 최적화**

#### **응답 시간 분석**
```bash
# 1. Nginx 액세스 로그에서 응답시간 분포 확인
docker compose exec nginx awk '{print $(NF-1)}' /var/log/nginx/access.log | \
sort -n | awk '
{
    a[NR]=$1
}
END {
    print "Min: " a[1] 
    print "25%: " a[int(NR*0.25)]
    print "50%: " a[int(NR*0.5)]
    print "75%: " a[int(NR*0.75)]
    print "95%: " a[int(NR*0.95)]
    print "Max: " a[NR]
}'

# 2. 가장 느린 요청들 확인
docker compose logs nginx | grep -E "request_time=[0-9]+\.[0-9]+" | \
sort -t= -k2 -nr | head -10

# 3. 업스트림 응답시간 vs 전체 응답시간 비교
docker compose logs nginx | grep -o 'rt=[0-9]*\.[0-9]* ut="[0-9]*\.[0-9]*"' | \
head -20
```

#### **리소스 사용량 모니터링**
```bash
# 실시간 리소스 모니터링 (5초 간격)
while true; do
  echo "=== $(date) ==="
  echo "Nginx CPU/Memory:"
  docker stats nginx --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
  echo ""
  echo "Connection Count:"
  docker compose exec nginx netstat -ant | grep :80 | wc -l
  echo ""
  sleep 5
done
```

### 🔧 **운영 중 설정 변경**

#### **무중단 설정 업데이트**
```bash
# 1. 설정 파일 백업
cp nginx/nginx.conf nginx/nginx.conf.backup

# 2. 설정 파일 수정 (에디터로)
nano nginx/nginx.conf

# 3. 문법 검사
docker compose exec nginx nginx -t

# 4. 설정 리로드 (무중단)
docker compose exec nginx nginx -s reload

# 5. 변경사항 확인
docker compose logs nginx | tail -10
```

#### **긴급 복구**
```bash
# 설정 오류로 인한 서비스 중단 시:
# 1. 백업 설정으로 즉시 복구
cp nginx/nginx.conf.backup nginx/nginx.conf
docker compose restart nginx

# 2. 또는 기본 설정으로 임시 복구
docker compose exec nginx sh -c 'echo "
events { worker_connections 1024; }
http {
  upstream gateway { server gateway:8080; }
  upstream frontend { server frontend:3000; }
  server {
    listen 80;
    location / { proxy_pass http://frontend; }
    location /api/ { proxy_pass http://gateway; }
  }
}" > /etc/nginx/nginx.conf && nginx -s reload'
```

---

## 📚 **추가 참고 자료**

### **성능 벤치마킹**
- [scripts/benchmark.sh](../scripts/benchmark.sh) - 전체 시스템 성능 테스트
- [k6/load-test.js](../k6/load-test.js) - K6를 이용한 부하 테스트

### **관련 문서**  
- [Gateway API 문서](../gateway/GATEWAY_GUIDE.md) - API 서버 상세 명세
- [Frontend 가이드](../frontend/FRONTEND_GUIDE.md) - React 애플리케이션 설정
- [운영 가이드](../OPERATIONS.md) - 전체 시스템 운영 매뉴얼

### **공식 문서**
- [Nginx 공식 문서](http://nginx.org/en/docs/)
- [Nginx Rate Limiting](https://www.nginx.com/blog/rate-limiting-nginx/)
- [SSL 설정 가이드](https://ssl-config.mozilla.org/)

---

### 🎯 **Nginx 설정 완료!**

이제 Nginx가 vLLM 챗봇 서비스를 위한 **상용급 웹 서버**로 완벽하게 구성되었습니다:

✅ **고성능 리버스 프록시** (업스트림 로드밸런싱)  
✅ **SSE 스트리밍 최적화** (실시간 채팅 지원)  
✅ **보안 강화** (Rate Limiting, 보안 헤더, 접근 제어)  
✅ **성능 최적화** (Gzip, 캐싱, 연결 풀)  
✅ **운영 친화적** (로깅, 모니터링, 트러블슈팅)  
✅ **확장 가능** (SSL, 다중 인스턴스 지원)

이제 **마지막 단계인 전체 프로젝트 종합 검토**로 넘어가겠습니다!
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

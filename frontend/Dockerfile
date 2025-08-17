FROM node:20-alpine

WORKDIR /app

# npm을 최신 버전으로 업데이트
RUN npm install -g npm@latest

# 패키지 파일 복사 및 설치
COPY package*.json ./
RUN npm ci --omit=dev

# 소스 코드 복사
COPY . .

# 빌드
RUN npm run build

# 프로덕션용 서버 설정
FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]

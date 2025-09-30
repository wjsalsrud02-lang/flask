# 베이스 이미지 선택
FROM python:3.13-slim

# 작업 디렉토리 생성 및 이동
WORKDIR /app

# 종속성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 전체 프로젝트 복사
COPY . .

# Flask 환경변수 설정
ENV FLASK_APP=pybo:create_app
ENV FLASK_ENV=production

# 포트 오픈
EXPOSE 5000

# 앱 실행
CMD ["flask", "run", "--host=0.0.0.0"]
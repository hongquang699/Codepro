FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/judge-system

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    python3 \
    python3-pip \
    openjdk-17-jdk-headless \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir psutil pyyaml requests 'cryptography>=43.0.0' 'boto3>=1.35,<2' 'redis>=5,<6'

WORKDIR /app

COPY . /app

EXPOSE 9999

CMD ["python3", "judge-system/judge-server/main.py"]

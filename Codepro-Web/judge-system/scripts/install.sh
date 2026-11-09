#!/bin/bash
set -eo pipefail

echo "=== Installing CodeProOJ Judge System Dependencies ==="

# Update package lists
if command -v apt-get &> /dev/null; then
    apt-get update
    apt-get install -y curl ca-certificates
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash -
    apt-get update
    apt-get install -y \
        build-essential \
        gcc \
        g++ \
        python3 \
        python3-pip \
        python3-venv \
        pypy3 \
        openjdk-17-jdk \
        rustc \
        golang-go \
        nodejs \
        fp-compiler \
        curl \
        jq
fi

# Python dependencies
pip install --upgrade pip
pip install psutil pyyaml

echo "=== CodeProOJ Judge System Dependencies Installed Successfully ==="

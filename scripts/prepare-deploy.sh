#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

mkdir -p problem-data contest-data storage judge-system/logs

if [ ! -e .env ]; then
    cp .env.example .env
    chmod 600 .env
    echo 'Created .env; fill its secrets and domain settings before starting Compose.'
fi

if [ ! -e config/admin_ip_whitelist.json ]; then
    cp config/admin_ip_whitelist.example.json config/admin_ip_whitelist.json
    chmod 600 config/admin_ip_whitelist.json
    echo 'Created admin_ip_whitelist.json; set the authorized administrator IPs.'
fi

echo 'Deployment directories are ready. Existing data and configuration were preserved.'

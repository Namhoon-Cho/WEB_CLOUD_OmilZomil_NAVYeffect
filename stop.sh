#/bin/bash

# 스크립트 설명: 서비스를 중지하기 위한 스크립트
# DB 포함 모든 컨테이너를 일시 중지

echo [+] Checking build files...
if [ -f .env.lock ] ; then
    :
else
    echo "[!] Please run 'build.sh' first!"
    exit
fi

echo [+] Stopping docker container

sudo docker-compose --env-file .env.lock stop
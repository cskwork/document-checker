#!/bin/bash
# 이 스크립트는 API 서버와 메인 애플리케이션을 동시에 실행합니다.

# API 서버 (src/user_interface/app.py) 실행
echo "API 서버 (app.py)를 시작합니다..."
python -m src.user_interface.app &
APP_PID=$!

# 메인 애플리케이션 (main.py) 실행
echo "메인 애플리케이션 (main.py)을 시작합니다..."
python main.py &
MAIN_PID=$!

# 두 프로세스가 종료될 때까지 대기
wait $APP_PID
wait $MAIN_PID

# 스크립트 종료 시 모든 백그라운드 프로세스 종료
trap 'kill $(jobs -p)' EXIT

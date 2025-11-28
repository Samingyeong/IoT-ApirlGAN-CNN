@echo off
REM 모든 데이터베이스에서 LayersModelDB 컬렉션 찾아서 변환

echo ========================================
echo 전체 데이터베이스 변환 실행
echo ========================================
echo.
echo 이 스크립트는 359개의 데이터베이스에서
echo LayersModelDB 컬렉션을 찾아 자동으로 변환합니다.
echo.
echo 주의: 시간이 오래 걸릴 수 있습니다!
echo.
pause

call venv\Scripts\activate.bat

python scripts\convert_all_databases.py

pause



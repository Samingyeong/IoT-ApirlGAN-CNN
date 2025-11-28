@echo off
REM Windows 가상환경 설정 스크립트

echo ========================================
echo 가상환경 설정 스크립트
echo ========================================
echo.

REM Python 설치 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python이 설치되어 있지 않습니다.
    echo.
    echo Python을 설치해주세요:
    echo   1. https://www.python.org/downloads/ 에서 다운로드
    echo   2. 설치 시 "Add Python to PATH" 옵션 체크
    echo.
    pause
    exit /b 1
)

echo [1/4] Python 버전 확인...
python --version
echo.

echo [2/4] 가상환경 생성 중...
if exist venv (
    echo 이미 venv 폴더가 존재합니다.
    echo 기존 가상환경을 삭제하고 새로 만들까요? (Y/N)
    set /p answer="> "
    if /i "%answer%"=="Y" (
        echo 기존 가상환경 삭제 중...
        rmdir /s /q venv
    ) else (
        echo 기존 가상환경을 사용합니다.
        goto activate
    )
)

python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] 가상환경 생성 실패
    pause
    exit /b 1
)
echo ✓ 가상환경 생성 완료
echo.

:activate
echo [3/4] 가상환경 활성화 중...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] 가상환경 활성화 실패
    pause
    exit /b 1
)
echo ✓ 가상환경 활성화 완료
echo.

echo [4/4] 필수 라이브러리 설치 중...
echo.

echo - pymongo 설치 중...
pip install --upgrade pip
pip install pymongo

echo - Pillow 설치 중...
pip install Pillow

echo - 기타 유틸리티 설치 중...
pip install numpy

echo.
echo ========================================
echo ✓ 가상환경 설정 완료!
echo ========================================
echo.
echo 다음 단계:
echo   1. 가상환경이 이미 활성화되었습니다.
echo   2. MongoDB 데이터 확인:
echo      python scripts\check_mongodb_data.py
echo.
echo 가상환경 비활성화: deactivate
echo.
pause




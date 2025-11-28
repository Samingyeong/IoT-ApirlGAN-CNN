# PowerShell 가상환경 설정 스크립트

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "가상환경 설정 스크립트" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Python 설치 확인
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Python이 설치되어 있지 않습니다." -ForegroundColor Red
    Write-Host ""
    Write-Host "Python을 설치해주세요:" -ForegroundColor Yellow
    Write-Host "  1. https://www.python.org/downloads/ 에서 다운로드"
    Write-Host "  2. 설치 시 'Add Python to PATH' 옵션 체크"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[1/4] Python 버전 확인..." -ForegroundColor Green
Write-Host $pythonVersion
Write-Host ""

# 가상환경 생성
Write-Host "[2/4] 가상환경 생성 중..." -ForegroundColor Green
if (Test-Path "venv") {
    Write-Host "이미 venv 폴더가 존재합니다." -ForegroundColor Yellow
    $answer = Read-Host "기존 가상환경을 삭제하고 새로 만들까요? (Y/N)"
    if ($answer -eq "Y" -or $answer -eq "y") {
        Write-Host "기존 가상환경 삭제 중..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force venv
    } else {
        Write-Host "기존 가상환경을 사용합니다." -ForegroundColor Yellow
        goto activate
    }
}

python -m venv venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] 가상환경 생성 실패" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "✓ 가상환경 생성 완료" -ForegroundColor Green
Write-Host ""

:activate
# 가상환경 활성화
Write-Host "[3/4] 가상환경 활성화 중..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] 가상환경 활성화 실패" -ForegroundColor Red
    Write-Host ""
    Write-Host "PowerShell 실행 정책 문제일 수 있습니다." -ForegroundColor Yellow
    Write-Host "다음 명령어를 관리자 권한으로 실행해주세요:" -ForegroundColor Yellow
    Write-Host "  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "✓ 가상환경 활성화 완료" -ForegroundColor Green
Write-Host ""

# 필수 라이브러리 설치
Write-Host "[4/4] 필수 라이브러리 설치 중..." -ForegroundColor Green
Write-Host ""

Write-Host "- pip 업그레이드 중..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

Write-Host "- pymongo 설치 중..." -ForegroundColor Yellow
pip install pymongo --quiet

Write-Host "- Pillow 설치 중..." -ForegroundColor Yellow
pip install Pillow --quiet

Write-Host "- numpy 설치 중..." -ForegroundColor Yellow
pip install numpy --quiet

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ 가상환경 설정 완료!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "다음 단계:" -ForegroundColor Yellow
Write-Host "  1. 가상환경이 이미 활성화되었습니다."
Write-Host "  2. MongoDB 데이터 확인:"
Write-Host "     python scripts\check_mongodb_data.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "가상환경 비활성화: deactivate" -ForegroundColor Gray
Write-Host ""




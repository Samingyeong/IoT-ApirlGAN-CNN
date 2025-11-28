@echo off
REM 패키지 설치 확인

echo ========================================
echo 패키지 설치 확인
echo ========================================
echo.

call venv\Scripts\activate.bat

echo [1] numpy 확인...
python -c "import numpy; print('[OK] numpy', numpy.__version__)" 2>nul || echo [FAIL] numpy

echo.
echo [2] opencv-python 확인...
python -c "import cv2; print('[OK] opencv-python', cv2.__version__)" 2>nul || echo [FAIL] opencv-python

echo.
echo [3] torch 확인...
python -c "import torch; print('[OK] torch', torch.__version__)" 2>nul || echo [FAIL] torch

echo.
echo [4] timm 확인...
python -c "import timm; print('[OK] timm')" 2>nul || echo [FAIL] timm

echo.
echo [5] transformers 확인...
python -c "import transformers; print('[OK] transformers')" 2>nul || echo [FAIL] transformers

echo.
echo [6] PIL 확인...
python -c "from PIL import Image; print('[OK] Pillow')" 2>nul || echo [FAIL] Pillow

echo.
echo ========================================
echo 확인 완료!
echo ========================================
pause

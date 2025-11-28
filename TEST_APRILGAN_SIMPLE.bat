@echo off
REM 간단한 AprilGAN 테스트 (기본 설정)

echo ========================================
echo AprilGAN 제로샷 테스트 (간단 버전)
echo ========================================
echo.

call venv\Scripts\activate.bat

REM 기본 데이터베이스
set TEST_DB=20210914_1755_D160

echo 테스트 데이터: %TEST_DB%
echo.

cd VAND-APRIL-GAN

python test.py --mode zero_shot --dataset mvtec --data_path ..\data\processed\%TEST_DB% --save_path ..\results\test_%TEST_DB% --config_path ./open_clip/model_configs/ViT-L-14-336.json --checkpoint_path ./exps/pretrained/mvtec_pretrained.pth --model ViT-L-14-336 --features_list 6 12 18 24 --pretrained openai --image_size 518

cd ..

echo.
echo 완료!
pause



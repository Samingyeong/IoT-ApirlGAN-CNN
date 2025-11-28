# 체크포인트 모델 불일치 오류 해결

## 문제

체크포인트(`mvtec_pretrained.pth`)와 모델 설정이 일치하지 않습니다.

### 체크포인트 정보
- 모델: `ViT-L-14-336`
- features_list: `[6, 12, 18, 24]` (4개 레이어)
- image_size: `518`
- pretrained: `openai`
- 입력 크기: 1024, 출력 크기: 768

### 잘못된 설정 (이전)
- 모델: `ViT-B-16`
- features_list: `[3, 6, 9]` (3개 레이어)
- image_size: `224`
- pretrained: `laion400m_e32`
- 입력 크기: 768, 출력 크기: 512

## 해결

`TEST_APRILGAN_SIMPLE.bat`를 수정하여 체크포인트에 맞는 설정을 사용하도록 변경했습니다.

### 올바른 설정
```cmd
--model ViT-L-14-336
--features_list 6 12 18 24
--pretrained openai
--image_size 518
--config_path ./open_clip/model_configs/ViT-L-14-336.json
```

## 참고

- `mvtec_pretrained.pth`: ViT-L-14-336 모델로 학습됨
- `visa_pretrained.pth`: ViT-L-14-336 모델로 학습됨

두 체크포인트 모두 동일한 모델 구조를 사용합니다.



# 금속 3D 프린팅 결함 검출 및 분류 프로젝트

AprilGAN + CNN 구조를 활용한 결함 검출 및 분류 시스템 (Federated Learning 지원)

## 프로젝트 구조

```
iot_aprilgan/
├── data/
│   └── processed/          # 변환된 데이터 (MongoDB → AprilGAN 형식)
├── scripts/
│   ├── convert_mongodb_to_aprillgan.py  # MongoDB 데이터 변환
│   ├── convert_all_databases.py         # 전체 DB 변환
│   └── setup_venv.bat                    # 가상환경 설정
├── VAND-APRIL-GAN/         # AprilGAN 모델 코드
├── src/
│   ├── data/               # 데이터 처리 유틸리티
│   └── evaluation/         # 평가 유틸리티
├── results/                # 테스트 결과
└── venv/                   # Python 가상환경
```

## 빠른 시작

### 1. 가상환경 활성화
```cmd
call venv\Scripts\activate.bat
```

### 2. 패키지 설치 확인
```cmd
CHECK_INSTALL.bat
```

### 3. AprilGAN 테스트 실행
```cmd
TEST_APRILGAN_SIMPLE.bat
```

## 주요 스크립트

- **`RUN_ALL_DATABASES.bat`**: 전체 데이터베이스 변환 실행
- **`TEST_APRILGAN_SIMPLE.bat`**: AprilGAN 제로샷 테스트
- **`CHECK_INSTALL.bat`**: 패키지 설치 확인

## 데이터 변환

MongoDB 데이터를 AprilGAN 형식으로 변환:
```cmd
python scripts/convert_mongodb_to_aprillgan.py --db [DB명] --collection LayersModelDB
```

## 다음 단계

자세한 내용은 `NEXT_STEPS.md`를 참고하세요.

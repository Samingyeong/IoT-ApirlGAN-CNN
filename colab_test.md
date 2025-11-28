## Colab에서 `iot_aprilgan` 실행하기 (README_COLAB)

이 문서는 로컬 PC에서 작업하던 `iot_aprilgan` 프로젝트를 **Google Colab + GPU** 환경으로 옮겨서 실행하는 방법을 단계별로 설명합니다.  
아래 순서를 **위에서부터 차례대로** 따라 하시면 됩니다.

---

## 0. 사전 준비

- **필수 조건**
  - 구글 계정
  - Google Drive 사용 가능
  - Colab 접속 가능: `https://colab.research.google.com`

- **프로젝트 구조 (로컬 예시)**  
  - `d:\iot_aprilgan\`
    - `VAND-APRIL-GAN\`
    - `data\processed\` (이미 MongoDB → AprilGAN으로 변환된 데이터)
    - `scripts\` 등

---

## 1. 로컬 프로젝트 압축하기

1. 윈도우 탐색기에서 `d:\`로 이동.
2. `iot_aprilgan` 폴더를 **마우스 오른쪽 클릭** → **보내기 → 압축(zip) 폴더**.
3. 예를 들어 `iot_aprilgan.zip` 이름으로 바탕화면 또는 원하는 위치에 저장.

> **Tip**: 용량이 너무 크면, 우선 테스트에 필요한 DB만 `data/processed`에 남기고 압축해도 됩니다.  
> 예: `data/processed/20210914_1755_D160
# 금속 3D 프린팅 결함 검출 프로젝트 - 프로젝트 요약

## ✅ 프로젝트 가능성 평가

### 🎯 **결론: 매우 높은 실현 가능성**

프로젝트는 **기술적으로 완전히 실현 가능**하며, 다음과 같은 이유로 높은 성공 가능성을 가집니다:

1. ✅ **바운딩 박스 데이터 처리 변환 가능**
2. ✅ **AprilGAN + CNN 파이프라인 구현 가능**
3. ✅ **연합학습 프레임워크 통합 가능**
4. ✅ **Non-IID 환경 시뮬레이션 가능**

---

## 🔍 바운딩 박스 데이터 처리 가능성

### **질문: AprilGAN을 바운딩 박스 데이터로 처리할 수 있나요?**

**답변: 네, 가능합니다!** 두 가지 접근 방식이 있습니다:

#### ✅ 방법 1: 바운딩 박스 → 마스크 변환 (권장)

```
입력: JSON 바운딩 박스
  ↓
변환: 바운딩 박스 → 마스크 이미지
  ↓
AprilGAN: 기존 마스크 기반 코드 그대로 사용
  ↓
출력: Anomaly Map
```

**장점:**
- 원본 코드 구조를 최대한 유지
- 픽셀 단위 정확한 이상 탐지 가능
- 기존 평가 지표 그대로 사용 가능

**구현 상태:**
- ✅ `src/data/bbox_to_mask.py` - 변환 유틸리티 구현 완료

#### ✅ 방법 2: Anomaly Map → 바운딩 박스 변환

```
AprilGAN: Anomaly Map 생성
  ↓
변환: Anomaly Map → 바운딩 박스
  ↓
출력: 바운딩 박스 형식 결과
```

**장점:**
- 출력 결과를 바운딩 박스로 제공
- IoU 기반 매칭으로 CNN 학습 데이터 생성 용이

**구현 상태:**
- ✅ `src/evaluation/anomaly_map_to_bbox.py` - 변환 유틸리티 구현 완료
- ✅ `src/evaluation/iou_matching.py` - IoU 매칭 로직 구현 완료

#### ✅ 방법 3: 하이브리드 방식 (최종 권장)

```
입력: JSON 바운딩 박스 → 마스크 변환
  ↓
AprilGAN: 제로샷 이상 탐지
  ↓
출력: Anomaly Map → 바운딩 박스 변환
  ↓
매칭: IoU 기반으로 JSON 라벨과 매칭
  ↓
CNN 학습 데이터: 매칭 결과 기반 생성
```

---

## 🎯 프로젝트 방향성

### 현재 상태

- ✅ GitHub 저장소 클론 완료: `VAND-APRIL-GAN/`
- ✅ 바운딩 박스 변환 유틸리티 구현 완료
- ✅ IoU 매칭 로직 구현 완료
- ✅ 프로젝트 구조 설계 완료

### 다음 단계 (우선순위 순)

#### 1단계: 데이터 변환 파이프라인 구축 ⏳
- [ ] JSON 바운딩 박스 파서 구현 (일부 완료)
- [ ] 바운딩 박스 → 마스크 변환 함수 (✅ 완료)
- [ ] meta.json 생성 스크립트
- [ ] 원본 AprilGAN 코드 테스트

#### 2단계: AprilGAN 바운딩 박스 출력 모드 추가 ⏳
- [ ] test.py에 바운딩 박스 출력 옵션 추가
- [ ] 커스텀 데이터셋 로더 생성
- [ ] 바운딩 박스 기반 평가 지표 추가

#### 3단계: CNN 분류 모델 설계 ⏳
- [ ] ResNet 기반 분류 모델 구현
- [ ] False Positive 라벨 처리 로직
- [ ] 데이터 로더 구현 (AprilGAN 검출 영역)

#### 4단계: 연합학습 프레임워크 통합 ⏳
- [ ] Flower/FedML 선택 및 설치
- [ ] 클라이언트-서버 구조 구현
- [ ] Non-IID 데이터 분배 시뮬레이션

---

## 📋 핵심 구현 전략

### 1. 데이터 처리 파이프라인

```python
# 입력: JSON 바운딩 박스
json_label = {
    "image_path": "image.jpg",
    "annotations": [
        {"bbox": [x1, y1, x2, y2], "label": "Super Elevation"}
    ]
}

# 1단계: 바운딩 박스 → 마스크 변환
mask = bbox_to_mask(image_path, json_label['annotations'])

# 2단계: AprilGAN 실행 (기존 코드 사용)
anomaly_map = aprillgan.predict(image)

# 3단계: Anomaly Map → 바운딩 박스
detected_bboxes = anomaly_map_to_bboxes(anomaly_map)

# 4단계: IoU 매칭
matched_data = match_detections_with_labels(
    detected_bboxes,
    json_label['annotations'],
    iou_threshold=0.5
)

# 결과:
# - 매칭 성공: 실제 결함 유형 라벨
# - 매칭 실패: 'False Positive' 라벨
```

### 2. AprilGAN + CNN 파이프라인

```
원본 이미지 (JPG)
    ↓
[AprilGAN] 제로샷 이상 탐지
    ├─ DINOv2 Vision Transformer 기반
    ├─ 추가 학습 없이 바로 사용
    └─ 이상 영역 검출 (바운딩박스)
    ↓
[AprilGAN 평가] (독립 평가)
    ├─ 검출 결과 vs JSON Ground Truth 비교
    ├─ Precision, Recall, F1-Score, IoU 계산
    └─ 제로샷 모델의 성능 측정
    ↓
[CNN 학습 데이터 생성]
    ├─ AprilGAN 검출 영역 직접 사용
    ├─ JSON 라벨과 IoU 기반 매칭
    ├─ 매칭 성공: 실제 결함 유형 라벨
    └─ 매칭 실패: 'False Positive' 라벨
    ↓
[CNN] 결함 유형 분류 (연합학습)
    ├─ AprilGAN 검출 영역 패치 입력
    ├─ JSON 라벨을 정답지로 학습/평가
    └─ 모든 검출 결과 포함 (실제 배포 시나리오 반영)
```

### 3. 연합학습 구조

```
[클라이언트 1]        [클라이언트 2]        [클라이언트 N]
(주로 결함A)         (주로 결함B)         (주로 결함C)
    ↓                     ↓                     ↓
AprilGAN 실행        AprilGAN 실행        AprilGAN 실행
(제로샷, 동일)       (제로샷, 동일)       (제로샷, 동일)
    ↓                     ↓                     ↓
CNN 로컬 학습        CNN 로컬 학습        CNN 로컬 학습
(Non-IID 데이터)     (Non-IID 데이터)     (Non-IID 데이터)
    ↓                     ↓                     ↓
가중치 전송 ─────────────────────────────────→ [서버]
                                                    ↓
                                            가중치 평균 계산
                                            (Federated Averaging)
                                                    ↓
가중치 수신 ←───────────────────────────────────────
    ↓
평균화된 가중치로 모델 업데이트
```

---

## 🔧 기술적 구현 사항

### 바운딩 박스 데이터 형식 가정

프로젝트는 다음 형식의 JSON을 지원합니다:

```json
{
  "image_path": "path/to/image.jpg",
  "annotations": [
    {
      "bbox": [x1, y1, x2, y2],  // 또는 [x, y, width, height]
      "label": "Super Elevation",
      "confidence": 1.0
    }
  ]
}
```

### 주요 수정 포인트

1. **데이터셋 로더** (`dataset.py`)
   - 바운딩 박스 입력 지원 추가
   - 마스크 변환 로직 통합

2. **테스트 스크립트** (`test.py`)
   - 바운딩 박스 출력 모드 추가
   - IoU 기반 평가 지표 추가

3. **평가 모듈** (새로 생성)
   - `anomaly_map_to_bbox.py` - Anomaly Map → 바운딩 박스 변환
   - `iou_matching.py` - IoU 매칭 및 CNN 학습 데이터 생성

---

## ⚠️ 주의사항 및 제약사항

### 1. 제로샷 성능
- **도전**: 금속 3D 프린팅 도메인 특화 데이터에 대한 제로샷 성능이 기대만큼 나오지 않을 수 있음
- **해결책**: 도메인별 프롬프트 튜닝 또는 파인튜닝 고려

### 2. 데이터 부족
- **도전**: 제한된 데이터로 인한 CNN 분류 성능 저하 가능
- **해결책**: 데이터 증강, 전이 학습, Few-shot 학습 활용

### 3. False Positive 처리
- **중요**: AprilGAN 오검출도 학습 데이터에 포함하여 실제 배포 환경 반영
- **구현**: IoU 매칭 실패 시 'False Positive' 라벨 할당

---

## 📊 기대 효과

1. **제로샷 이상 탐지**: 추가 학습 없이 즉시 사용 가능
2. **결함 분류 정확도 향상**: CNN + 연합학습으로 성능 개선
3. **데이터 프라이버시 보장**: 가중치만 공유
4. **Non-IID 환경 대응**: 현실적인 산업 환경 시뮬레이션
5. **확장 가능성**: 다른 산업 도메인에도 적용 가능

---

## 📚 참고 문서

- **종합 분석**: `PROJECT_ANALYSIS.md` - 프로젝트 전체 분석 및 기술적 세부사항
- **구현 가이드**: `IMPLEMENTATION_GUIDE.md` - 단계별 구현 가이드 및 코드 예시
- **원본 저장소**: `VAND-APRIL-GAN/` - 클론된 원본 GitHub 저장소

---

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# 원본 저장소 의존성 설치
cd VAND-APRIL-GAN
pip install -r requirements.txt

# 추가 의존성 설치
pip install scipy scikit-image  # anomaly_map_to_bbox.py에서 사용
```

### 2. 데이터 변환 테스트
```python
from src.data.bbox_to_mask import convert_json_to_masks

convert_json_to_masks(
    json_dir='data/raw/labels',
    image_dir='data/raw/images',
    output_dir='data/processed/masks'
)
```

### 3. 바운딩 박스 변환 테스트
```python
from src.evaluation.anomaly_map_to_bbox import anomaly_map_to_bboxes
import numpy as np

# 예시: anomaly_map (224x224)
anomaly_map = np.random.rand(224, 224)
bboxes = anomaly_map_to_bboxes(anomaly_map, threshold=0.5)
print(f"검출된 바운딩 박스: {bboxes}")
```

---

## 📝 결론

**프로젝트는 매우 실현 가능하며, 다음 단계로 진행할 준비가 되었습니다:**

1. ✅ 바운딩 박스 데이터 처리 변환 가능
2. ✅ AprilGAN 모델 수정 가능
3. ✅ 연합학습 통합 가능
4. ✅ 전체 파이프라인 설계 완료

**다음 단계:**
1. 실제 데이터로 데이터 변환 파이프라인 테스트
2. AprilGAN 바운딩 박스 출력 모드 추가
3. CNN 분류 모델 구현
4. 연합학습 프레임워크 통합

---

## ❓ 자주 묻는 질문

### Q1: 바운딩 박스 데이터만으로 AprilGAN을 사용할 수 있나요?
**A**: 네, 바운딩 박스를 마스크로 변환하거나, anomaly_map을 바운딩 박스로 변환하는 방식으로 가능합니다.

### Q2: 원본 코드를 많이 수정해야 하나요?
**A**: 최소한의 수정으로 가능합니다. 주로 데이터셋 로더와 출력 형식만 수정하면 됩니다.

### Q3: 연합학습은 필수인가요?
**A**: 아니요, 먼저 로컬 학습으로 파이프라인을 검증한 후 연합학습을 추가할 수 있습니다.

### Q4: 제로샷 성능이 좋지 않으면?
**A**: AprilGAN을 파인튜닝하거나, 프롬프트 엔지니어링을 통해 성능을 개선할 수 있습니다.

---

**작성일**: 2025-01-27  
**프로젝트 상태**: 초기 설계 및 핵심 유틸리티 구현 완료




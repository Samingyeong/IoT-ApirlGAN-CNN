# 구현 가이드: 금속 3D 프린팅 결함 검출 프로젝트

이 문서는 프로젝트의 단계별 구현 가이드를 제공합니다.

## 📁 프로젝트 구조 생성

먼저 프로젝트 디렉토리 구조를 생성합니다:

```bash
mkdir -p src/{data,models/{aprillgan,cnn},federated,evaluation,utils}
mkdir -p configs scripts docs
```

---

## 🔄 Phase 1: 데이터 변환 파이프라인

### 1.1 바운딩 박스 → 마스크 변환

**파일**: `src/data/bbox_to_mask.py` (이미 생성됨)

**사용 방법**:
```python
from src.data.bbox_to_mask import convert_json_to_masks

# JSON 디렉토리에서 마스크 생성
convert_json_to_masks(
    json_dir='data/raw/labels',
    image_dir='data/raw/images',
    output_mask_dir='data/processed/masks'
)
```

### 1.2 meta.json 생성

AprilGAN이 사용하는 `meta.json` 형식으로 변환:

```python
# src/data/create_meta_json.py 작성 필요
import json
import os
from pathlib import Path

def create_meta_json_for_3d_printing(data_root: str, output_path: str):
    """
    3D 프린팅 데이터를 AprilGAN 형식의 meta.json으로 변환
    """
    meta = {'train': {}, 'test': {}}
    
    # 데이터 구조 예시:
    # data/
    #   train/
    #     image1.jpg + image1.json
    #   test/
    #     image2.jpg + image2.json
    
    for phase in ['train', 'test']:
        phase_dir = os.path.join(data_root, phase)
        if not os.path.exists(phase_dir):
            continue
        
        # 클래스별로 분류 (결함 유형별)
        class_info = []
        
        for img_file in os.listdir(phase_dir):
            if not img_file.endswith(('.jpg', '.jpeg', '.png')):
                continue
            
            json_file = os.path.splitext(img_file)[0] + '.json'
            json_path = os.path.join(phase_dir, json_file)
            
            # JSON에서 라벨 정보 읽기
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    label_data = json.load(f)
                
                # 어노테이션이 있는지 확인
                has_anomaly = len(label_data.get('annotations', [])) > 0
                
                # 마스크 경로 (생성된 마스크)
                mask_file = os.path.splitext(img_file)[0] + '_mask.png'
                mask_path = os.path.join(data_root, 'masks', phase, mask_file)
                
                info = {
                    'img_path': f'{phase}/{img_file}',
                    'mask_path': f'masks/{phase}/{mask_file}' if has_anomaly else '',
                    'cls_name': '3d_printing',  # 또는 결함 유형별로 분류
                    'specie_name': label_data.get('defect_type', 'unknown') if has_anomaly else 'good',
                    'anomaly': 1 if has_anomaly else 0
                }
                class_info.append(info)
        
        meta[phase]['3d_printing'] = class_info
    
    # JSON 저장
    with open(output_path, 'w') as f:
        json.dump(meta, f, indent=4)
```

---

## 🔍 Phase 2: AprilGAN 수정

### 2.1 바운딩 박스 출력 모드 추가

**파일**: `VAND-APRIL-GAN/test.py` 수정

`test()` 함수에 바운딩 박스 출력 옵션 추가:

```python
# test.py에 추가할 내용
from src.evaluation.anomaly_map_to_bbox import (
    anomaly_map_to_bboxes,
    post_process_bboxes
)

# test() 함수 내부, anomaly_map 생성 후:
if args.output_bbox:
    # anomaly_map을 바운딩 박스로 변환
    bboxes = anomaly_map_to_bboxes(
        anomaly_map[0],
        threshold=args.bbox_threshold,
        min_area=args.min_bbox_area
    )
    
    # 후처리
    processed_bboxes = post_process_bboxes(
        bboxes,
        image_size=(img_size, img_size),
        nms_threshold=args.nms_threshold
    )
    
    # 결과 저장
    result['detected_bboxes'] = processed_bboxes
```

### 2.2 커스텀 데이터셋 로더 생성

**파일**: `src/data/dataset_loader.py`

```python
# AprilGAN의 dataset.py를 기반으로 3D 프린팅 데이터용 로더 생성
from VAND_APRIL_GAN.dataset import MVTecDataset
import torch.utils.data as data
from PIL import Image
import numpy as np
import json
import os

class Printing3DDataset(MVTecDataset):
    """3D 프린팅 데이터용 데이터셋 클래스"""
    
    def __init__(self, root, transform, target_transform, aug_rate=0, mode='test', **kwargs):
        # 부모 클래스 초기화
        super().__init__(root, transform, target_transform, aug_rate, mode)
        # 추가적인 초기화 작업
```

---

## 🎯 Phase 3: CNN 분류 모델

### 3.1 CNN 모델 구현

**파일**: `src/models/cnn_classifier.py`

```python
import torch
import torch.nn as nn
import torchvision.models as models

class DefectClassifier(nn.Module):
    """결함 유형 분류 CNN 모델"""
    
    def __init__(self, num_classes: int, backbone: str = 'resnet18', pretrained: bool = True):
        super().__init__()
        
        # 백본 선택
        if backbone == 'resnet18':
            self.backbone = models.resnet18(pretrained=pretrained)
            num_features = self.backbone.fc.in_features
            self.backbone.fc = nn.Identity()
        elif backbone == 'resnet34':
            self.backbone = models.resnet34(pretrained=pretrained)
            num_features = self.backbone.fc.in_features
            self.backbone.fc = nn.Identity()
        elif backbone == 'resnet50':
            self.backbone = models.resnet50(pretrained=pretrained)
            num_features = self.backbone.fc.in_features
            self.backbone.fc = nn.Identity()
        else:
            raise ValueError(f"지원하지 않는 백본: {backbone}")
        
        # 분류 헤드
        self.classifier = nn.Sequential(
            nn.Linear(num_features, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, num_classes)
        )
    
    def forward(self, x):
        features = self.backbone(x)
        logits = self.classifier(features)
        return logits
```

### 3.2 CNN 학습 데이터 생성

**파일**: `src/data/cnn_dataset.py`

```python
from torch.utils.data import Dataset
from PIL import Image
import torch
import json
import os
from src.evaluation.iou_matching import generate_cnn_training_data

class CNNDefectDataset(Dataset):
    """CNN 학습용 데이터셋 - AprilGAN 검출 영역 사용"""
    
    def __init__(self, image_root, detection_results, transform=None):
        """
        Args:
            image_root: 이미지 디렉토리
            detection_results: AprilGAN 검출 결과 (매칭된 바운딩 박스)
            transform: 이미지 변환
        """
        self.image_root = image_root
        self.detections = detection_results
        self.transform = transform
    
    def __len__(self):
        return len(self.detections)
    
    def __getitem__(self, idx):
        det = self.detections[idx]
        
        # 이미지 로드
        img_path = det['image_path']
        img = Image.open(os.path.join(self.image_root, img_path)).convert('RGB')
        
        # 바운딩 박스 영역 크롭
        bbox = det['bbox']
        x1, y1, x2, y2 = bbox
        patch = img.crop((x1, y1, x2, y2))
        
        # 변환 적용
        if self.transform:
            patch = self.transform(patch)
        
        # 라벨 (결함 유형 인덱스)
        label = det['gt_label']
        label_idx = self.label_to_idx.get(label, 0)
        
        return patch, label_idx
```

---

## 🤝 Phase 4: 연합학습 통합

### 4.1 Flower 프레임워크 설치

```bash
pip install flwr
```

### 4.2 클라이언트 구현

**파일**: `src/federated/client.py`

```python
import flwr as fl
import torch
from src.models.cnn_classifier import DefectClassifier

class FederatedClient(fl.client.NumPyClient):
    """연합학습 클라이언트"""
    
    def __init__(self, model, trainloader, valloader, device):
        self.model = model
        self.trainloader = trainloader
        self.valloader = valloader
        self.device = device
    
    def get_parameters(self, config):
        """서버에 가중치 전송"""
        return [val.cpu().numpy() for _, val in self.model.state_dict().items()]
    
    def set_parameters(self, parameters):
        """서버로부터 가중치 수신"""
        params_dict = zip(self.model.state_dict().keys(), parameters)
        state_dict = {k: torch.tensor(v) for k, v in params_dict}
        self.model.load_state_dict(state_dict, strict=True)
    
    def fit(self, parameters, config):
        """로컬 학습"""
        self.set_parameters(parameters)
        # 학습 코드
        train(self.model, self.trainloader, self.device, epochs=config['epochs'])
        return self.get_parameters(config={}), len(self.trainloader), {}
    
    def evaluate(self, parameters, config):
        """로컬 평가"""
        self.set_parameters(parameters)
        loss, accuracy = test(self.model, self.valloader, self.device)
        return float(loss), len(self.valloader), {"accuracy": float(accuracy)}
```

### 4.3 서버 구현

**파일**: `src/federated/server.py`

```python
import flwr as fl

# Federated Averaging 전략 사용
strategy = fl.server.strategy.FedAvg(
    fraction_fit=1.0,  # 모든 클라이언트 참여
    fraction_evaluate=1.0,
    min_fit_clients=2,  # 최소 클라이언트 수
    min_evaluate_clients=2,
    min_available_clients=2,
)

# 서버 시작
fl.server.start_server(
    server_address="localhost:8080",
    config=fl.server.ServerConfig(num_rounds=10),
    strategy=strategy
)
```

---

## 📊 Phase 5: 평가 및 모니터링

### 5.1 통합 평가 스크립트

**파일**: `scripts/evaluate_pipeline.py`

```python
"""
전체 파이프라인 평가:
1. AprilGAN 이상 탐지 평가
2. CNN 분류 평가
3. 통합 성능 평가
"""

from src.evaluation.aprillgan_eval import evaluate_aprillgan
from src.evaluation.cnn_eval import evaluate_cnn
from src.evaluation.iou_matching import evaluate_detection_performance

def evaluate_full_pipeline():
    # 1. AprilGAN 평가
    aprillgan_results = evaluate_aprillgan(...)
    
    # 2. IoU 매칭 및 CNN 학습 데이터 생성
    matched_data = generate_cnn_training_data(...)
    
    # 3. CNN 평가
    cnn_results = evaluate_cnn(...)
    
    # 4. 통합 결과 리포트
    print(f"AprilGAN Precision: {aprillgan_results['precision']:.2f}")
    print(f"CNN Accuracy: {cnn_results['accuracy']:.2f}")
```

---

## 🚀 실행 순서

### 1. 데이터 준비
```bash
# 바운딩 박스 → 마스크 변환
python -m src.data.bbox_to_mask \
    --json-dir data/raw/labels \
    --image-dir data/raw/images \
    --output-dir data/processed/masks

# meta.json 생성
python -m src.data.create_meta_json \
    --data-root data/processed \
    --output data/processed/meta.json
```

### 2. AprilGAN 테스트
```bash
cd VAND-APRIL-GAN
bash test_zero_shot.sh  # 바운딩 박스 출력 모드 추가 필요
```

### 3. CNN 학습 데이터 생성
```python
# scripts/prepare_cnn_data.py 실행
python scripts/prepare_cnn_data.py \
    --aprillgan-results results/aprillgan/bboxes.json \
    --gt-labels data/raw/labels \
    --output data/cnn/train_data.json
```

### 4. CNN 로컬 학습 (테스트)
```bash
python scripts/train_cnn.py \
    --data-dir data/cnn \
    --epochs 50 \
    --batch-size 32
```

### 5. 연합학습 실행
```bash
# 터미널 1: 서버 시작
python src/federated/server.py

# 터미널 2-N: 클라이언트 시작 (각 클라이언트마다)
python src/federated/client.py --client-id 1 --data-dir data/client1
python src/federated/client.py --client-id 2 --data-dir data/client2
```

---

## 📝 다음 단계

1. ✅ 바운딩 박스 → 마스크 변환 (완료)
2. ✅ anomaly_map → 바운딩 박스 변환 (완료)
3. ✅ IoU 매칭 로직 (완료)
4. ⏳ meta.json 생성 스크립트
5. ⏳ AprilGAN 바운딩 박스 출력 모드 추가
6. ⏳ CNN 모델 구현
7. ⏳ 연합학습 프레임워크 통합

---

## 🔗 참고 자료

- [VAND-APRIL-GAN 원본 저장소](https://github.com/ByChelsea/VAND-APRIL-GAN)
- [Flower 연합학습 프레임워크](https://flower.dev/)
- [Federated Averaging 논문](https://arxiv.org/abs/1602.05629)




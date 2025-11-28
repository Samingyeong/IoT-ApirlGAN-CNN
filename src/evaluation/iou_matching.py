"""
IoU 기반으로 AprilGAN 검출 결과와 JSON 라벨을 매칭하는 유틸리티

이 모듈은 AprilGAN이 검출한 바운딩 박스와 Ground Truth JSON 라벨을 매칭하여
CNN 학습 데이터를 생성합니다.
"""

import json
from typing import List, Dict, Tuple, Optional
import numpy as np


def calculate_iou(bbox1: List[int], bbox2: List[int]) -> float:
    """
    두 바운딩 박스의 IoU (Intersection over Union) 계산
    
    Args:
        bbox1: [x1, y1, x2, y2] 형식의 바운딩 박스
        bbox2: [x1, y1, x2, y2] 형식의 바운딩 박스
    
    Returns:
        float: IoU 값 (0~1)
    """
    x1_1, y1_1, x2_1, y2_1 = bbox1
    x1_2, y1_2, x2_2, y2_2 = bbox2
    
    # 교집합 영역
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)
    
    if x2_i < x1_i or y2_i < y1_i:
        return 0.0
    
    intersection = (x2_i - x1_i) * (y2_i - y1_i)
    
    # 각 바운딩 박스의 면적
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union = area1 + area2 - intersection
    
    if union == 0:
        return 0.0
    
    return intersection / union


def match_detections_with_labels(
    detections: List[Dict],
    ground_truth_labels: List[Dict],
    iou_threshold: float = 0.5
) -> List[Dict]:
    """
    AprilGAN 검출 결과와 Ground Truth 라벨을 IoU 기반으로 매칭
    
    Args:
        detections: AprilGAN 검출 결과
                    [{"bbox": [x1, y1, x2, y2], "score": 0.85, ...}, ...]
        ground_truth_labels: JSON에서 로드한 Ground Truth 라벨
                             [{"bbox": [x1, y1, x2, y2], "label": "...", ...}, ...]
        iou_threshold: 매칭으로 인정할 최소 IoU 임계값
    
    Returns:
        List[Dict]: 매칭된 검출 결과
                    [
                        {
                            "bbox": [x1, y1, x2, y2],
                            "score": 0.85,
                            "matched": True/False,
                            "gt_label": "..." or None,
                            "iou": 0.75 or 0.0
                        },
                        ...
                    ]
    """
    matched_detections = []
    used_gt_indices = set()
    
    # 각 검출 결과에 대해 최적의 Ground Truth 찾기
    for det in detections:
        det_bbox = det['bbox']
        best_iou = 0.0
        best_gt_idx = None
        best_gt_label = None
        
        # 모든 Ground Truth와 IoU 계산
        for gt_idx, gt in enumerate(ground_truth_labels):
            if gt_idx in used_gt_indices:
                continue
            
            gt_bbox = gt['bbox']
            iou = calculate_iou(det_bbox, gt_bbox)
            
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = gt_idx
                best_gt_label = gt.get('label', 'unknown')
        
        # 매칭 여부 결정
        is_matched = best_iou >= iou_threshold
        
        matched_det = {
            'bbox': det_bbox,
            'score': det.get('score', 0.0),
            'matched': is_matched,
            'gt_label': best_gt_label if is_matched else None,
            'iou': best_iou,
            **{k: v for k, v in det.items() if k not in ['bbox', 'score']}
        }
        
        # False Positive 처리: 매칭 실패 시
        if not is_matched:
            matched_det['gt_label'] = 'False Positive'
        
        matched_detections.append(matched_det)
        
        # 매칭된 Ground Truth는 다음 검출에서 제외 (1:1 매칭)
        if is_matched and best_gt_idx is not None:
            used_gt_indices.add(best_gt_idx)
    
    return matched_detections


def load_ground_truth_from_json(json_path: str, image_path: Optional[str] = None) -> List[Dict]:
    """
    JSON 파일에서 Ground Truth 라벨 로드
    
    Args:
        json_path: JSON 라벨 파일 경로
        image_path: 이미지 경로 (필요시 경로 확인용)
    
    Returns:
        List[Dict]: Ground Truth 바운딩 박스 리스트
                    [{"bbox": [x1, y1, x2, y2], "label": "...", ...}, ...]
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    annotations = []
    
    # 다양한 JSON 형식 지원
    if 'annotations' in data:
        for ann in data['annotations']:
            bbox = ann.get('bbox', [])
            if bbox:
                annotations.append({
                    'bbox': bbox,
                    'label': ann.get('label', 'unknown'),
                    'confidence': ann.get('confidence', 1.0),
                    **{k: v for k, v in ann.items() if k not in ['bbox', 'label', 'confidence']}
                })
    elif isinstance(data, list):
        # 리스트 형식
        annotations = data
    
    return annotations


def generate_cnn_training_data(
    detections: List[Dict],
    ground_truth_labels: List[Dict],
    iou_threshold: float = 0.5
) -> Dict:
    """
    CNN 학습 데이터 생성
    
    Args:
        detections: AprilGAN 검출 결과
        ground_truth_labels: Ground Truth 라벨
        iou_threshold: IoU 임계값
    
    Returns:
        Dict: 학습 데이터 통계 및 매칭 결과
            {
                "total_detections": 100,
                "matched_count": 80,
                "false_positive_count": 20,
                "label_distribution": {...},
                "matched_detections": [...]
            }
    """
    matched_detections = match_detections_with_labels(
        detections, ground_truth_labels, iou_threshold
    )
    
    # 통계 계산
    matched_count = sum(1 for d in matched_detections if d['matched'])
    false_positive_count = sum(1 for d in matched_detections if not d['matched'])
    
    # 라벨 분포
    label_distribution = {}
    for det in matched_detections:
        label = det['gt_label']
        label_distribution[label] = label_distribution.get(label, 0) + 1
    
    return {
        'total_detections': len(matched_detections),
        'matched_count': matched_count,
        'false_positive_count': false_positive_count,
        'label_distribution': label_distribution,
        'matched_detections': matched_detections
    }


def evaluate_detection_performance(
    detections: List[Dict],
    ground_truth_labels: List[Dict],
    iou_threshold: float = 0.5
) -> Dict:
    """
    검출 성능 평가
    
    Args:
        detections: AprilGAN 검출 결과
        ground_truth_labels: Ground Truth 라벨
        iou_threshold: IoU 임계값
    
    Returns:
        Dict: 평가 지표
            {
                "precision": 0.85,
                "recall": 0.90,
                "f1_score": 0.87,
                "tp": 80,
                "fp": 20,
                "fn": 10
            }
    """
    matched_detections = match_detections_with_labels(
        detections, ground_truth_labels, iou_threshold
    )
    
    # True Positive, False Positive 계산
    tp = sum(1 for d in matched_detections if d['matched'])
    fp = sum(1 for d in matched_detections if not d['matched'])
    
    # False Negative: 매칭되지 않은 Ground Truth
    matched_gt_indices = set()
    for det in matched_detections:
        if det['matched']:
            # 매칭된 GT 찾기 (간단화된 버전)
            for i, gt in enumerate(ground_truth_labels):
                if i not in matched_gt_indices:
                    iou = calculate_iou(det['bbox'], gt['bbox'])
                    if iou >= iou_threshold:
                        matched_gt_indices.add(i)
                        break
    
    fn = len(ground_truth_labels) - len(matched_gt_indices)
    
    # Precision, Recall, F1 계산
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'tp': tp,
        'fp': fp,
        'fn': fn,
        'total_gt': len(ground_truth_labels),
        'total_detections': len(detections)
    }


if __name__ == '__main__':
    # 사용 예시
    # AprilGAN 검출 결과 (예시)
    detections = [
        {'bbox': [10, 10, 50, 50], 'score': 0.9},
        {'bbox': [100, 100, 150, 150], 'score': 0.8},
        {'bbox': [200, 200, 250, 250], 'score': 0.7},  # False Positive
    ]
    
    # Ground Truth 라벨 (예시)
    ground_truth = [
        {'bbox': [12, 12, 52, 52], 'label': 'Super Elevation'},
        {'bbox': [105, 105, 155, 155], 'label': 'Crack'},
        # 세 번째 검출은 매칭되지 않음 (False Positive)
    ]
    
    # 매칭
    matched = match_detections_with_labels(detections, ground_truth, iou_threshold=0.5)
    
    for i, det in enumerate(matched):
        print(f"검출 {i+1}:")
        print(f"  바운딩 박스: {det['bbox']}")
        print(f"  점수: {det['score']:.2f}")
        print(f"  매칭: {det['matched']}")
        print(f"  라벨: {det['gt_label']}")
        print(f"  IoU: {det['iou']:.2f}")
        print()
    
    # 성능 평가
    metrics = evaluate_detection_performance(detections, ground_truth)
    print("성능 지표:")
    print(f"  Precision: {metrics['precision']:.2f}")
    print(f"  Recall: {metrics['recall']:.2f}")
    print(f"  F1 Score: {metrics['f1_score']:.2f}")




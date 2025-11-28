"""
AprilGAN의 anomaly_map을 바운딩 박스 형식으로 변환하는 유틸리티

이 모듈은 AprilGAN이 생성한 픽셀 단위 이상 탐지 결과를 바운딩 박스로 변환합니다.
"""

import numpy as np
from typing import List, Dict, Tuple
from scipy import ndimage
from skimage import measure, morphology


def anomaly_map_to_bboxes(
    anomaly_map: np.ndarray,
    threshold: float = 0.5,
    min_area: int = 10,
    use_connected_components: bool = True
) -> List[Dict]:
    """
    이상 탐지 맵(anomaly_map)을 바운딩 박스 리스트로 변환
    
    Args:
        anomaly_map: 이상 점수 맵 (H, W) 또는 (1, H, W) 형태
        threshold: 이상 영역으로 판단할 임계값 (0~1)
        min_area: 최소 영역 크기 (픽셀 수). 이보다 작은 영역은 무시
        use_connected_components: 연결된 컴포넌트 사용 여부
    
    Returns:
        List[Dict]: 바운딩 박스 리스트
                   [{"bbox": [x1, y1, x2, y2], "score": 0.85, "area": 100}, ...]
    """
    # 입력 정규화
    if len(anomaly_map.shape) == 3:
        anomaly_map = anomaly_map.squeeze(0)
    
    # 0~1 범위로 정규화
    if anomaly_map.max() > 1.0:
        anomaly_map = (anomaly_map - anomaly_map.min()) / (anomaly_map.max() - anomaly_map.min())
    
    # 임계값 적용하여 이진화
    binary_map = (anomaly_map >= threshold).astype(np.uint8)
    
    if not use_connected_components:
        # 단순하게 전체 영역을 하나의 바운딩 박스로
        coords = np.where(binary_map > 0)
        if len(coords[0]) == 0:
            return []
        
        y_min, y_max = coords[0].min(), coords[0].max()
        x_min, x_max = coords[1].min(), coords[1].max()
        
        avg_score = anomaly_map[y_min:y_max+1, x_min:x_max+1].mean()
        area = (y_max - y_min + 1) * (x_max - x_min + 1)
        
        return [{
            'bbox': [int(x_min), int(y_min), int(x_max), int(y_max)],
            'score': float(avg_score),
            'area': int(area)
        }]
    
    # 연결된 컴포넌트 분석
    labeled_map, num_features = ndimage.label(binary_map)
    
    bboxes = []
    for i in range(1, num_features + 1):
        # 각 컴포넌트의 좌표 찾기
        component_mask = (labeled_map == i)
        coords = np.where(component_mask)
        
        if len(coords[0]) < min_area:
            continue
        
        y_min, y_max = coords[0].min(), coords[0].max()
        x_min, x_max = coords[1].min(), coords[1].max()
        
        # 해당 영역의 평균 이상 점수
        region_scores = anomaly_map[component_mask]
        avg_score = region_scores.mean()
        max_score = region_scores.max()
        
        area = component_mask.sum()
        
        bboxes.append({
            'bbox': [int(x_min), int(y_min), int(x_max), int(y_max)],
            'score': float(avg_score),
            'max_score': float(max_score),
            'area': int(area)
        })
    
    # 점수 기준으로 정렬 (높은 점수 순)
    bboxes.sort(key=lambda x: x['score'], reverse=True)
    
    return bboxes


def post_process_bboxes(
    bboxes: List[Dict],
    image_size: Tuple[int, int],
    nms_threshold: float = 0.5,
    min_score: float = 0.3
) -> List[Dict]:
    """
    바운딩 박스 후처리: NMS 적용 및 필터링
    
    Args:
        bboxes: 바운딩 박스 리스트
        image_size: 이미지 크기 (height, width)
        nms_threshold: NMS IoU 임계값
        min_score: 최소 점수 임계값
    
    Returns:
        List[Dict]: 후처리된 바운딩 박스 리스트
    """
    if not bboxes:
        return []
    
    # 최소 점수 필터링
    filtered_bboxes = [bb for bb in bboxes if bb['score'] >= min_score]
    
    if not filtered_bboxes:
        return []
    
    # NMS (Non-Maximum Suppression) 적용
    def calculate_iou(bbox1: List[int], bbox2: List[int]) -> float:
        """두 바운딩 박스의 IoU 계산"""
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
    
    # NMS 구현
    keep = []
    while filtered_bboxes:
        # 가장 높은 점수의 바운딩 박스 선택
        best = filtered_bboxes.pop(0)
        keep.append(best)
        
        # 나머지 바운딩 박스와 IoU 계산하여 제거
        filtered_bboxes = [
            bb for bb in filtered_bboxes
            if calculate_iou(best['bbox'], bb['bbox']) < nms_threshold
        ]
    
    return keep


def resize_bbox(bbox: List[int], original_size: Tuple[int, int], new_size: Tuple[int, int]) -> List[int]:
    """
    바운딩 박스를 새로운 이미지 크기에 맞게 리사이즈
    
    Args:
        bbox: [x1, y1, x2, y2] 형식의 바운딩 박스
        original_size: 원본 이미지 크기 (width, height)
        new_size: 새로운 이미지 크기 (width, height)
    
    Returns:
        List[int]: 리사이즈된 바운딩 박스
    """
    x1, y1, x2, y2 = bbox
    orig_w, orig_h = original_size
    new_w, new_h = new_size
    
    scale_x = new_w / orig_w
    scale_y = new_h / orig_h
    
    new_x1 = int(x1 * scale_x)
    new_y1 = int(y1 * scale_y)
    new_x2 = int(x2 * scale_x)
    new_y2 = int(y2 * scale_y)
    
    return [new_x1, new_y1, new_x2, new_y2]


if __name__ == '__main__':
    # 사용 예시
    # anomaly_map은 AprilGAN의 출력 (numpy array)
    anomaly_map = np.random.rand(224, 224)  # 예시 데이터
    
    # 바운딩 박스로 변환
    bboxes = anomaly_map_to_bboxes(anomaly_map, threshold=0.5, min_area=10)
    
    # 후처리
    processed_bboxes = post_process_bboxes(
        bboxes,
        image_size=(224, 224),
        nms_threshold=0.5,
        min_score=0.3
    )
    
    print(f"검출된 바운딩 박스 수: {len(processed_bboxes)}")
    for i, bbox in enumerate(processed_bboxes):
        print(f"  {i+1}: {bbox}")




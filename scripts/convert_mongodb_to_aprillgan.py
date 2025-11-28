"""
MongoDB 데이터를 AprilGAN 형식으로 변환하는 파이프라인

사용법:
    python scripts/convert_mongodb_to_aprillgan.py
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import time

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pymongo import MongoClient
from PIL import Image, ImageDraw, ImageFont
import io
import base64

# MongoDB 연결 정보
MONGODB_CONFIG = {
    'host': 'keties.iptime.org',
    'port': 50002,
    'user': 'KETI_readAnyDB',
    'pw': 'madcoder'
}


def connect_mongodb():
    """MongoDB 연결"""
    # admin으로 인증
    connection_string = f"mongodb://{MONGODB_CONFIG['user']}:{MONGODB_CONFIG['pw']}@{MONGODB_CONFIG['host']}:{MONGODB_CONFIG['port']}/admin?authSource=admin"
    
    print(f"🔌 MongoDB 연결 시도 중...")
    print(f"   Host: {MONGODB_CONFIG['host']}")
    print(f"   Port: {MONGODB_CONFIG['port']}\n")
    
    client = MongoClient(connection_string, serverSelectionTimeoutMS=10000)
    client.admin.command('ping')
    print("✅ MongoDB 연결 성공!\n")
    return client


def extract_image_from_gridfs(client: MongoClient, db_name: str, layer_num: int, image_type: str = 'vision') -> Optional[bytes]:
    """
    GridFS에서 이미지 가져오기
    
    Args:
        client: MongoDB 클라이언트
        db_name: 데이터베이스 이름
        layer_num: 레이어 번호
        image_type: 'vision' (전체 이미지) 또는 'tag' (결함 영역)
    
    Returns:
        이미지 바이너리 데이터 또는 None
    """
    try:
        from gridfs import GridFS
        
        db = client[db_name]
        gridfs_collection = f"{db_name}_{image_type}"
        
        fs = GridFS(db, collection=gridfs_collection)
        
        # LayerIdx로 검색
        files = list(fs.find({"metadata.LayerIdx": layer_num}))
        
        if not files:
            # 파일명으로도 검색 시도
            files = list(fs.find({"filename": {"$regex": f"{layer_num}Layer"}}))
        
        if files:
            # vision 타입: FirstShot 우선 선택
            if image_type == 'vision':
                first_shot = [f for f in files if 'FirstShot' in (f.filename or '')]
                if first_shot:
                    return first_shot[0].read()
                elif files:
                    return files[0].read()
            else:
                # tag 타입: 첫 번째 파일
                return files[0].read()
        
        return None
    except Exception as e:
        return None


def extract_image_from_gridfs(client: MongoClient, db_name: str, layer_num: int, image_type: str = 'vision') -> Optional[bytes]:
    """
    GridFS에서 이미지 가져오기
    
    Args:
        client: MongoDB 클라이언트
        db_name: 데이터베이스 이름
        layer_num: 레이어 번호
        image_type: 'vision' (전체 이미지) 또는 'tag' (결함 영역)
    
    Returns:
        이미지 바이너리 데이터 또는 None
    """
    try:
        from gridfs import GridFS
        
        db = client[db_name]
        gridfs_collection = f"{db_name}_{image_type}"
        
        fs = GridFS(db, collection=gridfs_collection)
        
        # LayerIdx로 검색
        files = list(fs.find({"metadata.LayerIdx": layer_num}))
        
        if not files:
            # 파일명으로도 검색 시도
            files = list(fs.find({"filename": {"$regex": f"{layer_num}Layer"}}))
        
        if files:
            # vision 타입: FirstShot 우선 선택
            if image_type == 'vision':
                first_shot = [f for f in files if 'FirstShot' in (f.filename or '')]
                if first_shot:
                    return first_shot[0].read()
                elif files:
                    return files[0].read()
            else:
                # tag 타입: 첫 번째 파일
                return files[0].read()
        
        return None
    except Exception as e:
        return None


def extract_image_from_document(doc: Dict, client: MongoClient = None, db_name: str = None) -> Optional[bytes]:
    """
    MongoDB 문서에서 이미지 데이터 추출
    
    방법:
    1. GridFS에서 전체 레이어 이미지 가져오기 (우선)
    2. 문서 내부 재귀 탐색 (폴백)
    
    Args:
        doc: MongoDB 문서
        client: MongoDB 클라이언트 (GridFS 사용 시 필요)
        db_name: 데이터베이스 이름 (GridFS 사용 시 필요)
    """
    # 방법 1: GridFS에서 가져오기 (우선)
    if client and db_name:
        layer_num = doc.get('LayerNum')
        if layer_num:
            # vision GridFS에서 전체 이미지 가져오기
            image_data = extract_image_from_gridfs(client, db_name, layer_num, 'vision')
            if image_data:
                return image_data
    
    # 방법 2: 문서 내부 재귀 탐색 (기존 로직, 폴백)
    def find_image_recursive(obj, depth=0, max_depth=3):
        """재귀적으로 이미지 데이터 찾기"""
        if depth > max_depth:
            return None
        
        if isinstance(obj, bytes):
            # bytes 데이터가 일정 크기 이상이면 이미지로 간주
            if len(obj) > 1000:  # 최소 1KB 이상
                try:
                    # PIL로 이미지인지 확인
                    from PIL import Image
                    img = Image.open(io.BytesIO(obj))
                    img.verify()  # 이미지 검증
                    return obj
                except:
                    pass
        
        if isinstance(obj, dict):
            # dict 내부 재귀 탐색
            for key, value in obj.items():
                result = find_image_recursive(value, depth + 1, max_depth)
                if result:
                    return result
                
                # 특정 키 이름 패턴 확인
                if 'image' in key.lower() or 'data' in key.lower() or 'binary' in key.lower():
                    if isinstance(value, bytes) and len(value) > 1000:
                        try:
                            from PIL import Image
                            img = Image.open(io.BytesIO(value))
                            img.verify()
                            return value
                        except:
                            pass
                    elif isinstance(value, str):
                        try:
                            decoded = base64.b64decode(value)
                            if len(decoded) > 1000:
                                from PIL import Image
                                img = Image.open(io.BytesIO(decoded))
                                img.verify()
                                return decoded
                        except:
                            pass
        
        elif isinstance(obj, list):
            # 리스트 내부 재귀 탐색
            for item in obj:
                result = find_image_recursive(item, depth + 1, max_depth)
                if result:
                    return result
        
        return None
    
    # 방법 1: 재귀적 탐색
    image_data = find_image_recursive(doc)
    if image_data:
        return image_data
    
    # 방법 2: 일반적인 필드명 직접 확인
    for field in ['ScanningImageModel', 'DepositionImageModel', 'Image', 'image', 'ImageData', 'imageData', 'data', 'Data']:
        if field in doc:
            model_data = doc[field]
            
            if isinstance(model_data, dict):
                # dict의 모든 값을 재귀 탐색
                for key, value in model_data.items():
                    result = find_image_recursive(value)
                    if result:
                        return result
            elif isinstance(model_data, bytes) and len(model_data) > 1000:
                try:
                    from PIL import Image
                    img = Image.open(io.BytesIO(model_data))
                    img.verify()
                    return model_data
                except:
                    pass
            elif isinstance(model_data, str):
                try:
                    decoded = base64.b64decode(model_data)
                    if len(decoded) > 1000:
                        from PIL import Image
                        img = Image.open(io.BytesIO(decoded))
                        img.verify()
                        return decoded
                except:
                    pass
    
    return None


def get_bounding_boxes_from_document(doc: Dict) -> List[Dict]:
    """
    MongoDB 문서에서 바운딩 박스 정보 추출
    
    실제 구조:
    - ScanningImageModel / DepositionImageModel의 TagBoxes, DetectionBoxes 리스트
    - 각 박스는 dict 형태로 좌표 정보 포함 가능
    """
    bboxes = []
    
    # 방법 1: ScanningImageModel / DepositionImageModel의 TagBoxes, DetectionBoxes
    for model_field in ['ScanningImageModel', 'DepositionImageModel']:
        if model_field in doc:
            model_data = doc[model_field]
            
            if isinstance(model_data, dict):
                # TagBoxes와 DetectionBoxes 확인
                for box_field in ['TagBoxes', 'DetectionBoxes', 'tagBoxes', 'detectionBoxes']:
                    if box_field in model_data:
                        boxes = model_data[box_field]
                        
                        if isinstance(boxes, list):
                            for box_item in boxes:
                                if isinstance(box_item, dict):
                                    # 바운딩 박스 좌표 추출
                                    bbox = None
                                    
                                    # 방법 1: StartPoint와 EndPoint 사용 (실제 구조)
                                    if 'StartPoint' in box_item and 'EndPoint' in box_item:
                                        start = box_item['StartPoint']
                                        end = box_item['EndPoint']
                                        if isinstance(start, dict) and isinstance(end, dict):
                                            x1 = start.get('X', start.get('x', 0))
                                            y1 = start.get('Y', start.get('y', 0))
                                            x2 = end.get('X', end.get('x', 0))
                                            y2 = end.get('Y', end.get('y', 0))
                                            
                                            if x1 != 0 or y1 != 0 or x2 != 0 or y2 != 0:
                                                bbox = [x1, y1, x2, y2]
                                    
                                    # 방법 2: 기존 bbox 필드 확인
                                    if not bbox:
                                        if 'bbox' in box_item:
                                            bbox = box_item['bbox']
                                        elif 'BBox' in box_item:
                                            bbox = box_item['BBox']
                                        elif 'boundingBox' in box_item:
                                            bbox = box_item['boundingBox']
                                        elif all(k in box_item for k in ['x1', 'y1', 'x2', 'y2']):
                                            bbox = [box_item['x1'], box_item['y1'], box_item['x2'], box_item['y2']]
                                        elif all(k in box_item for k in ['left', 'top', 'right', 'bottom']):
                                            bbox = [box_item['left'], box_item['top'], box_item['right'], box_item['bottom']]
                                    
                                    if bbox and isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
                                        # Comment 필드에서 결함 유형 이름 추출
                                        comment = box_item.get('Comment', '')
                                        defect_type = comment if comment else box_item.get('label', 'unknown')
                                        
                                        bboxes.append({
                                            'bbox': list(bbox),
                                            'label': defect_type,
                                            'label_type': box_item.get('LabelType', doc.get('LabelType', 0)),
                                            'confidence': box_item.get('confidence', box_item.get('DetectionProb', 1.0))
                                        })
    
    # 방법 2: 직접 bbox 필드
    for bbox_field in ['bbox', 'BBox', 'boundingBox', 'BoundingBox']:
        if bbox_field in doc:
            bbox = doc[bbox_field]
            if isinstance(bbox, list) and len(bbox) >= 4:
                bboxes.append({
                    'bbox': bbox,
                    'label': doc.get('LabelType', doc.get('label', 'unknown')),
                    'confidence': doc.get('DetectionProb', 1.0)
                })
            break
    
    # 방법 3: annotations 리스트
    if 'annotations' in doc and isinstance(doc['annotations'], list):
        for ann in doc['annotations']:
            if isinstance(ann, dict):
                bbox = ann.get('bbox') or ann.get('BBox') or ann.get('boundingBox')
                if bbox and isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
                    bboxes.append({
                        'bbox': list(bbox),
                        'label': ann.get('label', ann.get('LabelType', 'unknown')),
                        'confidence': ann.get('confidence', 1.0)
                    })
    
    return bboxes


def download_and_organize_images(
    client: MongoClient,
    collection_name: str,
    db_name: str = "admin",
    output_dir: str = "data/processed",
    max_defect: Optional[int] = None,
    max_normal: Optional[int] = None
) -> Dict:
    """
    MongoDB에서 이미지를 다운로드하고 AprilGAN 형식으로 구조화
    
    구조:
    data/processed/
        train/
            good/
                <images>
        test/
            good/
                <images>
            defect_<labeltype>/
                <images>
        ground_truth/
            defect_<labeltype>/
                <masks>
    """
    db = client[db_name]  # admin 데이터베이스
    collection = db[collection_name]  # LayersModelDB 컬렉션
    
    output_path = Path(output_dir)
    
    # 디렉토리 구조 생성
    train_good_dir = output_path / "train" / "good"
    test_good_dir = output_path / "test" / "good"
    test_defect_dirs = {}  # LabelType별 디렉토리
    ground_truth_dirs = {}  # LabelType별 마스크 디렉토리
    
    train_good_dir.mkdir(parents=True, exist_ok=True)
    test_good_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("MongoDB 데이터 → AprilGAN 형식 변환")
    print("=" * 60)
    print(f"\n출력 디렉토리: {output_dir}")
    print()
    
    # 통계
    stats = {
        'total_processed': 0,
        'defect_count': 0,
        'normal_count': 0,
        'image_saved': 0,
        'bbox_found': 0,
        'errors': 0
    }
    
    # IsLabeled=True 데이터 (결함 있음)
    print("🔴 결함 있는 데이터 처리 중...")
    defect_query = {"IsLabeled": True}
    
    if max_defect:
        defect_docs = list(collection.find(defect_query).limit(max_defect))
    else:
        defect_docs = list(collection.find(defect_query))
    
    print(f"   총 {len(defect_docs)}개 문서 발견")
    
    for idx, doc in enumerate(defect_docs, 1):
        try:
            # 이미지 추출 (GridFS 사용)
            image_data = extract_image_from_document(doc, client=client, db_name=db_name)
            
            if not image_data:
                stats['errors'] += 1
                if idx <= 3:
                    print(f"   ⚠️  [{idx}] 이미지 데이터 없음")
                    # 디버깅: 문서 구조 출력
                    print(f"      필드: {list(doc.keys())[:10]}")
                    # ScanningImageModel 상세 확인
                    if 'ScanningImageModel' in doc:
                        sim = doc['ScanningImageModel']
                        print(f"      ScanningImageModel: {type(sim).__name__}")
                        if isinstance(sim, dict):
                            print(f"        dict 키: {list(sim.keys())[:5]}")
                            # dict 내부 값 확인
                            for k, v in list(sim.items())[:2]:
                                print(f"          {k}: {type(v).__name__}")
                                if isinstance(v, bytes):
                                    print(f"            크기: {len(v)} bytes")
                                elif isinstance(v, str) and len(str(v)) < 100:
                                    print(f"            값: {str(v)[:50]}")
                continue
            
            # 이미지 저장
            layer_num = doc.get('LayerNum', idx)
            label_type = doc.get('LabelType', 0)
            doc_id = str(doc.get('_id', idx))
            
            # 결함 유형 정보 추출
            defect_names = []
            for model_field in ['ScanningImageModel', 'DepositionImageModel']:
                if model_field in doc:
                    model = doc[model_field]
                    if isinstance(model, dict):
                        for box_field in ['TagBoxes', 'DetectionBoxes']:
                            if box_field in model:
                                boxes = model[box_field]
                                if isinstance(boxes, list):
                                    for box in boxes:
                                        if isinstance(box, dict):
                                            comment = box.get('Comment', '')
                                            if comment and comment not in defect_names:
                                                defect_names.append(comment)
            
            # 결함 유형 이름 결정
            defect_type = defect_names[0] if defect_names else f"LabelType_{label_type}"
            defect_type_safe = defect_type.replace(' ', '_').replace('/', '_')
            defect_type_safe = ''.join(c if c.isalnum() or c == '_' else '_' for c in defect_type_safe)
            
            # 디렉토리 생성 (결함 유형별)
            defect_type_name = f"defect_{defect_type_safe}" if defect_type_safe else f"defect_{label_type}"
            if defect_type_name not in test_defect_dirs:
                test_defect_dir = output_path / "test" / defect_type_name
                test_defect_dir.mkdir(parents=True, exist_ok=True)
                test_defect_dirs[defect_type_name] = test_defect_dir
                
                ground_truth_dir = output_path / "ground_truth" / defect_type_name
                ground_truth_dir.mkdir(parents=True, exist_ok=True)
                ground_truth_dirs[defect_type_name] = ground_truth_dir
            
            # 바운딩 박스 확인 및 시각화 (이미지 저장 전에!)
            bboxes = get_bounding_boxes_from_document(doc)
            if bboxes:
                stats['bbox_found'] += len(bboxes)
                
                # 바운딩 박스를 이미지에 그리기
                try:
                    from PIL import ImageDraw, ImageFont
                    img = Image.open(io.BytesIO(image_data))
                    draw = ImageDraw.Draw(img)
                    
                    for bbox_info in bboxes:
                        bbox = bbox_info['bbox']
                        label = bbox_info.get('label', 'defect')
                        
                        # 바운딩 박스 그리기
                        x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
                        draw.rectangle([x1, y1, x2, y2], outline='red', width=3)
                        
                        # 라벨 텍스트 그리기
                        try:
                            font = ImageFont.truetype("arial.ttf", 20)
                        except:
                            try:
                                font = ImageFont.load_default()
                            except:
                                font = None
                        
                        if font:
                            text = f"{label}"
                            # 텍스트 배경
                            text_bbox = draw.textbbox((x1, y1-25), text, font=font)
                            draw.rectangle(text_bbox, fill='red')
                            draw.text((x1, y1-25), text, fill='white', font=font)
                    
                    # 시각화된 이미지로 업데이트
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format='JPEG', quality=95)
                    image_data = img_bytes.getvalue()
                    
                except Exception as e:
                    # 시각화 실패해도 계속 진행 (원본 이미지 그대로 저장)
                    pass
            
            # 이미지 파일명 (결함 유형 포함)
            defect_type_short = defect_type.replace(' ', '_')[:30]  # 파일명 길이 제한
            defect_type_safe_file = ''.join(c if c.isalnum() or c in ['_', '-'] else '_' for c in defect_type_short)
            img_filename = f"layer_{layer_num}_{defect_type_safe_file}_{doc_id}.jpg"
            img_path = test_defect_dirs[defect_type_name] / img_filename
            
            # 이미지 저장 (시각화된 이미지)
            with open(img_path, 'wb') as f:
                f.write(image_data)
            
            stats['image_saved'] += 1
            stats['defect_count'] += 1
            
            # 결함 유형 정보 출력 (처음 몇 개만)
            if idx <= 5:
                bbox_count = len(bboxes) if bboxes else 0
                print(f"   [{idx}] Layer {layer_num}: {defect_type} (바운딩 박스: {bbox_count}개)")
            
            if idx % 100 == 0:
                print(f"   진행: {idx}/{len(defect_docs)} 완료")
                
        except Exception as e:
            stats['errors'] += 1
            if idx <= 5:
                print(f"   ❌ [{idx}] 오류: {str(e)}")
            continue
    
    print(f"   ✅ 결함 데이터 처리 완료: {stats['defect_count']}개 저장")
    
    # IsLabeled=False 데이터 (결함 없음)
    print("\n🟢 결함 없는 데이터 처리 중...")
    normal_query = {"IsLabeled": False}
    
    if max_normal:
        normal_docs = list(collection.find(normal_query).limit(max_normal))
    else:
        normal_docs = list(collection.find(normal_query))
    
    print(f"   총 {len(normal_docs)}개 문서 발견")
    
    # train과 test로 분할 (80:20)
    train_count = int(len(normal_docs) * 0.8)
    
    for idx, doc in enumerate(normal_docs, 1):
        try:
            # 이미지 추출 (GridFS 사용)
            image_data = extract_image_from_document(doc, client=client, db_name=db_name)
            
            if not image_data:
                stats['errors'] += 1
                continue
            
            layer_num = doc.get('LayerNum', idx)
            doc_id = str(doc.get('_id', idx))
            
            # train 또는 test 디렉토리 선택
            if idx <= train_count:
                target_dir = train_good_dir
            else:
                target_dir = test_good_dir
            
            img_filename = f"layer_{layer_num}_{doc_id}.jpg"
            img_path = target_dir / img_filename
            
            with open(img_path, 'wb') as f:
                f.write(image_data)
            
            stats['image_saved'] += 1
            stats['normal_count'] += 1
            
            if idx % 100 == 0:
                print(f"   진행: {idx}/{len(normal_docs)} 완료")
                
        except Exception as e:
            stats['errors'] += 1
            continue
    
    print(f"   ✅ 정상 데이터 처리 완료: {stats['normal_count']}개 저장")
    print(f"      (Train: {train_count}개, Test: {len(normal_docs) - train_count}개)")
    
    stats['total_processed'] = len(defect_docs) + len(normal_docs)
    
    # 통계 출력
    print("\n" + "=" * 60)
    print("📊 변환 통계")
    print("=" * 60)
    print(f"  전체 처리: {stats['total_processed']}개")
    print(f"  이미지 저장: {stats['image_saved']}개")
    print(f"  결함 있음: {stats['defect_count']}개")
    print(f"  결함 없음: {stats['normal_count']}개")
    print(f"  바운딩 박스 발견: {stats['bbox_found']}개")
    print(f"  오류: {stats['errors']}개")
    print("=" * 60)
    
    return stats


def create_meta_json(output_dir: str = "data/processed", collection_name: str = "LayersModelDB", db_name: str = ""):
    """
    AprilGAN 형식의 meta.json 생성
    
    MVTec AD 형식:
    {
        "train": {
            "bottle": [
                {
                    "img_path": "...",
                    "mask_path": "...",
                    "cls_name": "...",
                    "specie_name": "...",
                    "anomaly": 0 or 1
                }
            ]
        },
        "test": { ... }
    }
    """
    output_path = Path(output_dir)
    meta = {"train": {}, "test": {}}
    
    # 클래스 이름 (금속 3D 프린팅)
    cls_name = "3d_printing"
    
    print(f"\n📝 meta.json 생성 중...")
    
    # Train 데이터 (정상만)
    train_good_dir = output_path / "train" / "good"
    if train_good_dir.exists():
        train_files = list(train_good_dir.glob("*.jpg")) + list(train_good_dir.glob("*.png"))
        train_info = []
        
        for img_file in train_files:
            train_info.append({
                "img_path": f"train/good/{img_file.name}",
                "mask_path": "",
                "cls_name": cls_name,
                "specie_name": "good",
                "anomaly": 0
            })
        
        meta["train"][cls_name] = train_info
        print(f"  Train: {len(train_info)}개")
    
    # Test 데이터
    test_dir = output_path / "test"
    if test_dir.exists():
        test_info = []
        
        # 정상 데이터
        test_good_dir = test_dir / "good"
        if test_good_dir.exists():
            good_files = list(test_good_dir.glob("*.jpg")) + list(test_good_dir.glob("*.png"))
            for img_file in good_files:
                test_info.append({
                    "img_path": f"test/good/{img_file.name}",
                    "mask_path": "",
                    "cls_name": cls_name,
                    "specie_name": "good",
                    "anomaly": 0
                })
        
        # 결함 데이터
        for defect_dir in test_dir.iterdir():
            if defect_dir.is_dir() and defect_dir.name != "good":
                defect_files = list(defect_dir.glob("*.jpg")) + list(defect_dir.glob("*.png"))
                defect_type = defect_dir.name  # defect_0, defect_1 등
                
                for img_file in defect_files:
                    # 마스크 파일명 생성
                    mask_name = img_file.stem + "_mask.png"
                    mask_path = f"ground_truth/{defect_type}/{mask_name}"
                    
                    test_info.append({
                        "img_path": f"test/{defect_type}/{img_file.name}",
                        "mask_path": mask_path,
                        "cls_name": cls_name,
                        "specie_name": defect_type,
                        "anomaly": 1
                    })
        
        meta["test"][cls_name] = test_info
        print(f"  Test: {len(test_info)}개")
    
    # meta.json 저장
    meta_path = output_path / "meta.json"
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ meta.json 저장 완료: {meta_path}")
    
    return meta_path


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MongoDB 데이터를 AprilGAN 형식으로 변환')
    parser.add_argument('--db', type=str, required=True,
                        help='데이터베이스 이름 (예: 20210909_2131_D160)')
    parser.add_argument('--collection', type=str, default='LayersModelDB',
                        help='컬렉션 이름 (기본: LayersModelDB)')
    parser.add_argument('--output-dir', type=str, default='data/processed',
                        help='출력 디렉토리 (기본: data/processed)')
    parser.add_argument('--max-defect', type=int, default=None,
                        help='최대 결함 이미지 개수 (기본: 전체)')
    parser.add_argument('--max-normal', type=int, default=None,
                        help='최대 정상 이미지 개수 (기본: 전체)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("MongoDB → AprilGAN 데이터 변환 파이프라인")
    print("=" * 60)
    print()
    
    # MongoDB 연결
    client = connect_mongodb()
    
    try:
        # 데이터베이스 및 컬렉션 이름
        db_name = args.db
        collection_name = args.collection
        
        print(f"📂 데이터베이스: {db_name}")
        print(f"📋 컬렉션: {collection_name}\n")
        
        # 해당 데이터베이스 접근
        target_db = client[db_name]
        collection = target_db[collection_name]
        
        try:
            # IsLabeled 필드 확인
            sample = collection.find_one({"IsLabeled": {"$exists": True}})
            if sample:
                total = collection.count_documents({})
                true_count = collection.count_documents({"IsLabeled": True})
                false_count = collection.count_documents({"IsLabeled": False})
                print(f"✅ IsLabeled 필드 확인 완료!")
                print(f"   전체: {total}개, IsLabeled=True: {true_count}개, IsLabeled=False: {false_count}개\n")
            else:
                print(f"⚠️  IsLabeled 필드를 찾을 수 없습니다.")
                print(f"   컬렉션 '{collection_name}'에 접근은 가능하지만 IsLabeled 필드가 없습니다.")
                return
        except Exception as e:
            print(f"❌ 컬렉션 '{collection_name}' 접근 실패: {e}")
            return
        
        # 이미지 다운로드 및 구조화
        stats = download_and_organize_images(
            client,
            collection_name,
            db_name=db_name,  # 실제 데이터베이스 이름
            output_dir=args.output_dir,
            max_defect=args.max_defect,
            max_normal=args.max_normal
        )
        
        # meta.json 생성
        meta_path = create_meta_json(args.output_dir, collection_name, db_name)
        
        print("\n" + "=" * 60)
        print("✅ 변환 완료!")
        print("=" * 60)
        print(f"\n출력 디렉토리: {args.output_dir}")
        print(f"meta.json: {meta_path}")
        print("\n다음 단계:")
        print("  1. AprilGAN으로 데이터 테스트")
        print("  2. 바운딩 박스 → 마스크 변환 (필요시)")
        print("  3. CNN 분류 모델 학습 준비")
        
    finally:
        client.close()
        print("\n🔌 MongoDB 연결 종료")


if __name__ == '__main__':
    main()


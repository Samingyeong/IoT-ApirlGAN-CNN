"""
모든 데이터베이스의 LayersModelDB 컬렉션에서 데이터 변환

사용법:
    python scripts/convert_all_databases.py
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pymongo import MongoClient
# 직접 import해서 인코딩 문제 방지
from scripts.convert_mongodb_to_aprillgan import (
    connect_mongodb,
    download_and_organize_images,
    create_meta_json
)

HOST = 'keties.iptime.org'
PORT = 50002
USER = 'KETI_readAnyDB'
PASSWORD = 'madcoder'

def find_all_layers_databases():
    """모든 데이터베이스에서 LayersModelDB 컬렉션 찾기"""
    conn_str = f"mongodb://{USER}:{PASSWORD}@{HOST}:{PORT}/admin?authSource=admin"
    client = MongoClient(conn_str, serverSelectionTimeoutMS=10000)
    
    databases_with_layers = []
    
    try:
        client.admin.command('ping')
        
        all_dbs = client.list_database_names()
        system_dbs = ['admin', 'config', 'local']
        user_dbs = [db for db in all_dbs if db not in system_dbs]
        
        print(f"📊 총 {len(user_dbs)}개의 데이터베이스 확인 중...\n")
        
        for db_name in user_dbs:
            try:
                db = client[db_name]
                collections = db.list_collection_names()
                
                if 'LayersModelDB' in collections:
                    collection = db['LayersModelDB']
                    sample = collection.find_one({"IsLabeled": {"$exists": True}})
                    
                    if sample:
                        try:
                            total = collection.count_documents({})
                            true_count = collection.count_documents({"IsLabeled": True})
                            false_count = collection.count_documents({"IsLabeled": False})
                        except:
                            # 권한 오류 등의 경우 스킵
                            continue
                        
                        databases_with_layers.append({
                            'db_name': db_name,
                            'total': total,
                            'defect': true_count,
                            'normal': false_count
                        })
            except:
                continue
        
        return databases_with_layers
    finally:
        client.close()


def main():
    print("=" * 60)
    print("모든 데이터베이스 → LayersModelDB 컬렉션 변환")
    print("=" * 60)
    print()
    
    # 모든 데이터베이스 찾기
    databases = find_all_layers_databases()
    
    if not databases:
        print("❌ LayersModelDB 컬렉션을 찾을 수 없습니다.")
        return
    
    print(f"✅ {len(databases)}개의 데이터베이스 발견!\n")
    
    for i, db_info in enumerate(databases, 1):
        print(f"[{i}/{len(databases)}] {db_info['db_name']}")
        print(f"   전체: {db_info['total']}개, 결함: {db_info['defect']}개, 정상: {db_info['normal']}개")
    
    print("\n" + "=" * 60)
    print("변환 시작")
    print("=" * 60)
    print()
    
    # MongoDB 클라이언트 연결 (재사용)
    client = connect_mongodb()
    
    success_count = 0
    fail_count = 0
    
    # 각 데이터베이스 변환
    for i, db_info in enumerate(databases, 1):
        db_name = db_info['db_name']
        output_dir = f"data/processed/{db_name}"
        
        print(f"\n[{i}/{len(databases)}] {db_name} 변환 중...")
        print("-" * 60)
        
        try:
            # 직접 함수 호출 (인코딩 문제 방지)
            stats = download_and_organize_images(
                client=client,
                collection_name='LayersModelDB',
                db_name=db_name,
                output_dir=output_dir
            )
            
            # meta.json 생성
            create_meta_json(output_dir, 'LayersModelDB', db_name)
            
            print(f"[OK] {db_name} 변환 완료")
            print(f"     이미지 저장: {stats.get('image_saved', 0)}개")
            print(f"     결함: {stats.get('defect_count', 0)}개, 정상: {stats.get('normal_count', 0)}개")
            print(f"     바운딩 박스: {stats.get('bbox_found', 0)}개")
            if stats.get('errors', 0) > 0:
                print(f"     에러: {stats.get('errors', 0)}개")
            
            success_count += 1
            
        except Exception as e:
            print(f"[ERROR] {db_name} 변환 실패: {str(e)}")
            fail_count += 1
            continue
    
    client.close()
    
    print("\n" + "=" * 60)
    print(f"변환 완료: 성공 {success_count}개, 실패 {fail_count}개")
    print("=" * 60)


if __name__ == '__main__':
    main()


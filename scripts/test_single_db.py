"""단일 데이터베이스 변환 테스트"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.convert_mongodb_to_aprillgan import connect_mongodb, download_and_organize_images
import argparse

def main():
    parser = argparse.ArgumentParser(description='단일 데이터베이스 변환 테스트')
    parser.add_argument('--db', type=str, default='20210909_2131_D160', help='데이터베이스 이름')
    parser.add_argument('--collection', type=str, default='LayersModelDB', help='컬렉션 이름')
    parser.add_argument('--output-dir', type=str, default='data/test_single', help='출력 디렉토리')
    parser.add_argument('--max-defect', type=int, default=5, help='최대 결함 이미지 개수')
    parser.add_argument('--max-normal', type=int, default=5, help='최대 정상 이미지 개수')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("단일 데이터베이스 변환 테스트")
    print("=" * 60)
    print(f"\n데이터베이스: {args.db}")
    print(f"컬렉션: {args.collection}")
    print(f"출력 디렉토리: {args.output_dir}")
    print(f"최대 결함: {args.max_defect}개")
    print(f"최대 정상: {args.max_normal}개")
    print()
    
    # MongoDB 연결
    client = connect_mongodb()
    
    # 변환 실행
    stats = download_and_organize_images(
        client=client,
        collection_name=args.collection,
        db_name=args.db,
        output_dir=args.output_dir,
        max_defect=args.max_defect,
        max_normal=args.max_normal
    )
    
    # 결과 출력
    print("\n" + "=" * 60)
    print("변환 결과:")
    print("=" * 60)
    print(f"  이미지 저장: {stats.get('image_saved', 0)}개")
    print(f"  결함 이미지: {stats.get('defect_count', 0)}개")
    print(f"  정상 이미지: {stats.get('normal_count', 0)}개")
    print(f"  에러: {stats.get('errors', 0)}개")
    print()
    
    if stats.get('image_saved', 0) > 0:
        print("[OK] 변환 성공! 다음 단계로 진행할 수 있습니다.")
        return 0
    else:
        print("[ERROR] 이미지가 저장되지 않았습니다. 문제를 확인해주세요.")
        return 1

if __name__ == '__main__':
    sys.exit(main())



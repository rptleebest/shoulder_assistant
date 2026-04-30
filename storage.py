# storage.py
import sqlite3
import csv
import json
from datetime import datetime
import os

def init_storage(db_path="patients_data.db"):
    """데이터베이스를 초기화하고 필요한 테이블을 생성합니다."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            answers TEXT,
            results TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_to_db(answers, results, db_path="patients_data.db"):
    """설문 응답과 분석 결과를 데이터베이스에 저장합니다."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 딕셔너리를 문자열(JSON)로 변환하여 저장
    answers_json = json.dumps(answers, ensure_ascii=False)
    results_json = json.dumps(results, ensure_ascii=False)
    
    cursor.execute('''
        INSERT INTO evaluations (timestamp, answers, results)
        VALUES (?, ?, ?)
    ''', (timestamp, answers_json, results_json))
    
    conn.commit()
    conn.close()
    print(f"\n[안내] 평가 결과가 데이터베이스(patients_data.db)에 안전하게 저장되었습니다.")

def export_to_csv(answers, results, csv_path="patients_export.csv"):
    """결과를 엑셀에서 열어볼 수 있는 CSV 파일로 추가 저장합니다."""
    file_exists = os.path.exists(csv_path)
    
    with open(csv_path, mode='a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
        # 파일이 처음 만들어질 때만 제목 줄 작성
        if not file_exists:
            writer.writerow(["검사일시", "나이", "성별", "통증부위", "의심질환", "위험신호(RedFlags)"])
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        age = answers.get("age", "")
        sex = answers.get("sex", "")
        pain_side = answers.get("pain_side", "")
        
        # 질환명과 점수만 보기 좋게 묶기
        diags = [f"{name}({data['score']}점)" for name, data in results.get("diagnoses", {}).items() if data['score'] > 0]
        diagnoses_str = ", ".join(diags)
        red_flags_str = ", ".join(results.get("red_flags", []))
        
        writer.writerow([timestamp, age, sex, pain_side, diagnoses_str, red_flags_str])
# config_loader.py
import csv
import yaml
from pathlib import Path

def load_questions(csv_path: str):
    questions = []
    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(f"질문 파일을 찾을 수 없습니다: {csv_path}")

    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 엑셀(CSV)의 빈 줄 방어 로직
            if not row.get("order") or not str(row.get("order")).strip(): 
                continue
                
            row["order"] = int(row["order"])
            row["required"] = str(row.get("required", "")).strip().lower() in ["yes", "y", "true", "1"]
            row["options"] = [opt.strip() for opt in row.get("options", "").split("|") if opt.strip()]
            row["condition_field"] = row.get("condition_field", "").strip()
            row["condition_value"] = row.get("condition_value", "").strip()
            questions.append(row)

    questions.sort(key=lambda x: x["order"])
    return questions

def load_yaml(yaml_path: str):
    path = Path(yaml_path)

    if not path.exists():
        raise FileNotFoundError(f"YAML 파일을 찾을 수 없습니다: {yaml_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    if not isinstance(data, dict):
        data = {}

    # 💡 [핵심] YAML 하이픈(-) 누락 자동 복구 로직
    # 사용자가 YAML 작성 시 하이픈을 빼먹어도 파이썬이 알아서 목록(List)으로 고쳐줍니다.
    if 'diagnoses' in data and isinstance(data['diagnoses'], dict):
        for d_name, d_data in data['diagnoses'].items():
            if isinstance(d_data, dict) and 'score_rules' in d_data:
                if isinstance(d_data['score_rules'], dict):
                    d_data['score_rules'] = [d_data['score_rules']]
                    
    if 'red_flags' in data and isinstance(data['red_flags'], list):
        for rf in data['red_flags']:
            if isinstance(rf, dict) and 'rules' in rf:
                if isinstance(rf['rules'], dict):
                    rf['rules'] = [rf['rules']]

    return data
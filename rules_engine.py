# rules_engine.py

def validate_rule_keys(questions, rules):
    valid_keys = {q['key'] for q in questions}
    for diag_name, diag_data in rules.get('diagnoses', {}).items():
        for rule in diag_data.get('score_rules', []):
            if rule['field'] not in valid_keys:
                print(f"경고: '{diag_name}'의 규칙 필드 '{rule['field']}'가 질문 목록에 없습니다.")
    for rf in rules.get('red_flags', []):
        for rule in rf.get('rules', []):
            if rule['field'] not in valid_keys:
                print(f"경고: 레드플래그 '{rf['name']}'의 필드 '{rule['field']}'가 질문 목록에 없습니다.")
    return True

def _evaluate_condition(answer_val, operator, rule_val):
    if answer_val is None or answer_val == "":
        return False
    try:
        if operator == "==":
            return str(answer_val) == str(rule_val)
        elif operator == ">=":
            return float(answer_val) >= float(rule_val)
        elif operator == "<=":
            return float(answer_val) <= float(rule_val)
    except ValueError:
        return False
    return False

def calculate_scores(answers, rules):
    diagnoses = {}
    recommendations = {"physical_tests": set(), "imaging_tests": set()}
    red_flags = []

    # 1. 질환별 점수, 만점, 확률 계산 (수정된 부분!)
    for diag_name, diag_data in rules.get('diagnoses', {}).items():
        score = 0
        max_score = 0  # 이 질환의 만점
        
        for rule in diag_data.get('score_rules', []):
            max_score += rule.get('score', 0) # 만점 누적
            ans = answers.get(rule['field'])
            if _evaluate_condition(ans, rule['operator'], rule['value']):
                score += rule['score']
                
        # 확률(%) 계산 (소수점 버림)
        probability = 0
        if max_score > 0:
            probability = int((score / max_score) * 100)

        diagnoses[diag_name] = {
            'score': score, 
            'max_score': max_score, 
            'probability': probability,
            'description': diag_data.get('description', '')
        }
        
        if score > 0:
            recs = diag_data.get('recommendations', {})
            recommendations["physical_tests"].update(recs.get('physical_tests', []))
            recommendations["imaging_tests"].update(recs.get('imaging_tests', []))

    # 2. 레드플래그 확인
    for rf in rules.get('red_flags', []):
        logic = rf.get('logic', 'all')
        conditions_met = []
        for rule in rf.get('rules', []):
            ans = answers.get(rule['field'])
            conditions_met.append(_evaluate_condition(ans, rule['operator'], rule['value']))
            
        if logic == 'all' and all(conditions_met) and conditions_met:
            red_flags.append(rf['name'])
        elif logic == 'any' and any(conditions_met):
            red_flags.append(rf['name'])

    return {
        "diagnoses": diagnoses,
        "recommendations": {
            "physical_tests": list(recommendations["physical_tests"]),
            "imaging_tests": list(recommendations["imaging_tests"])
        },
        "red_flags": red_flags
    }

def calculate_probabilities(diagnoses_scores):
    return diagnoses_scores

def rank_diagnoses(diagnoses_scores):
    # 확률(%)이 높은 순서대로 우선 정렬하도록 변경
    return sorted(diagnoses_scores.items(), key=lambda x: x[1]['probability'], reverse=True)
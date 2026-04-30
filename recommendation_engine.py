# recommendation_engine.py

def evaluate_red_flags(answers, rules):
    """응답(answers)과 규칙(rules)을 비교하여 위험 신호(Red Flags)를 평가합니다."""
    red_flags_detected = []
    
    for rf in rules.get('red_flags', []):
        logic = rf.get('logic', 'all')
        conditions_met = []
        
        for rule in rf.get('rules', []):
            ans = answers.get(rule['field'])
            matched = False
            
            if ans is not None and ans != "":
                if rule['operator'] == '==':
                    matched = (str(ans) == str(rule['value']))
                elif rule['operator'] == '>=':
                    try: matched = (float(ans) >= float(rule['value']))
                    except ValueError: pass
                elif rule['operator'] == '<=':
                    try: matched = (float(ans) <= float(rule['value']))
                    except ValueError: pass
                    
            conditions_met.append(matched)
            
        if logic == 'all' and all(conditions_met) and conditions_met:
            red_flags_detected.append(rf['name'])
        elif logic == 'any' and any(conditions_met):
            red_flags_detected.append(rf['name'])
            
    return red_flags_detected

def merge_recommendations(diagnoses_scores, rules):
    """의심되는 질환들을 바탕으로 추천되는 검사 항목을 중복 없이 모아줍니다."""
    merged = {"physical_tests": set(), "imaging_tests": set()}
    
    for diag_name, diag_info in diagnoses_scores.items():
        if diag_info.get('score', 0) > 0:
            diag_rule = rules.get('diagnoses', {}).get(diag_name, {})
            recs = diag_rule.get('recommendations', {})
            
            merged["physical_tests"].update(recs.get("physical_tests", []))
            merged["imaging_tests"].update(recs.get("imaging_tests", []))
            
    return {
        "physical_tests": list(merged["physical_tests"]),
        "imaging_tests": list(merged["imaging_tests"])
    }
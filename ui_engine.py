# ui_engine.py
import os

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# ▼ 여기가 수정되었습니다. (title 인자 추가)
def print_header(title="어깨 통증 평가 프로그램 - 최종 PC 마스터 버전"):
    clear_screen()
    print("="*50)
    print(f"   {title}   ")
    print("="*50)
    print(" * 'back' 입력 : 이전 질문으로 이동")
    print(" * 'quit' 입력 : 프로그램 종료")
    print("-" * 50)

def run_questionnaire(questions):
    answers = {}
    history = []
    i = 0
    
    while i < len(questions):
        q = questions[i]
        
        # 조건부 질문 건너뛰기
        if q.get("condition_field") and q.get("condition_value"):
            if answers.get(q["condition_field"]) != q["condition_value"]:
                i += 1
                continue

        print(f"\n[{q.get('section', '질문')}] {q.get('question', '')}")
        if q.get('help_text'):
            print(f"참고: {q['help_text']}")
            
        if q.get('type') == 'choice':
            for idx, opt in enumerate(q.get('options', []), 1):
                print(f"{idx}. {opt}")
                
        while True:
            prompt = "선택 번호" if q.get('type') == 'choice' else "입력"
            user_input = input(f"{prompt} (back/quit) > ").strip()
            
            if user_input.lower() == 'quit':
                print("프로그램을 종료합니다.")
                exit()
                
            if user_input.lower() == 'back':
                if history:
                    i = history.pop()
                    break
                else:
                    print("첫 번째 질문입니다. 뒤로 갈 수 없습니다.")
                    continue
                    
            if q.get('type') == 'choice':
                if user_input.isdigit():
                    idx = int(user_input) - 1
                    if 0 <= idx < len(q.get('options', [])):
                        answers[q['key']] = q['options'][idx]
                        history.append(i)
                        i += 1
                        break
                print("올바른 번호를 선택해주세요.")
            else:
                if user_input:
                    answers[q['key']] = user_input
                    history.append(i)
                    i += 1
                    break
                else:
                    print("값을 입력해주세요.")
    return answers

def display_results(results):
    print("\n" + "="*50)
    print("               [ 최 종  결 과 ]               ")
    print("="*50)
    
    print("\n🚨 [주의] 본 결과는 참고용이며 의학적 진단을 대체할 수 없습니다.\n")
    
    red_flags = results.get("red_flags", [])
    if red_flags:
        print("❗ [위험 신호 감지] 즉각적인 진료가 권장됩니다!")
        for rf in red_flags:
            print(f"  - {rf}")
        print("-" * 50)
        
    print("[의심되는 질환 및 점수]")
    diagnoses = results.get("diagnoses", {})
    if diagnoses:
        sorted_diags = sorted(diagnoses.items(), key=lambda x: x[1]['score'], reverse=True)
        for name, data in sorted_diags:
            if data['score'] > 0:
                print(f"  - {name}: {data['score']}점")
    else:
        print("  - 특정 질환 기준에 부합하는 항목이 적습니다.")
        
    print("\n[추천 검사]")
    recs = results.get("recommendations", {"physical_tests": set(), "imaging_tests": set()})
    
    print("  <이학적 검사>")
    for t in recs.get("physical_tests", []):
        print(f"   * {t}")
        
    print("  <영상/특수 검사>")
    for t in recs.get("imaging_tests", []):
        print(f"   * {t}")
    print("="*50)
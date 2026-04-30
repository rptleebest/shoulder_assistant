# main.py

from config_loader import load_questions, load_yaml
from ui_engine import print_header, run_questionnaire, display_results
from rules_engine import validate_rule_keys, calculate_scores, calculate_probabilities, rank_diagnoses
from recommendation_engine import evaluate_red_flags, merge_recommendations
from storage import init_storage, save_to_db, export_to_csv
from ml_engine import run_ml_prediction

QUESTIONS_PATH = "config/questions.csv"
RULES_PATH = "config/rules.yaml"

def main():
    print_header("어깨 통증 평가 프로그램 - 최종 PC 마스터 버전")

    try:
        init_storage()

        questions = load_questions(QUESTIONS_PATH)
        rules = load_yaml(RULES_PATH)

        errors = validate_rule_keys(questions, rules)
        if errors:
            print("\n설정 파일 오류가 발견되었습니다.")
            for err in errors:
                print(" -", err)
            print("\nquestions.csv와 rules.yaml의 key 이름을 맞춘 뒤 다시 실행해주세요.")
            return

        answers = run_questionnaire(questions)

        if answers is None:
            print("\n사용자가 프로그램을 종료했습니다.")
            return

        score_results = calculate_scores(answers, rules)
        probabilities = calculate_probabilities(score_results)
        ranked = rank_diagnoses(score_results, probabilities)
        red_flags = evaluate_red_flags(answers, rules)
        recommendations = merge_recommendations(ranked, score_results, top_n=3)
        ml_result = run_ml_prediction(answers)

        result = {
            "red_flags": red_flags,
            "ranked_diagnoses": ranked,
            "recommendations": recommendations,
            "ml_result": ml_result
        }

        display_results(result)

        save_to_db(answers, result)
        csv_path = export_to_csv(answers, result)

        print(f"\n저장 완료: data/records.db")
        print(f"CSV 저장 완료: {csv_path}")
        print("\n프로그램을 종료합니다.")

    except FileNotFoundError as e:
        print(f"\n파일 오류: {e}")
    except Exception as e:
        print(f"\n예상치 못한 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    main()
# app.py
import streamlit as st
import os
from config_loader import load_questions, load_yaml
from rules_engine import calculate_scores, rank_diagnoses
from recommendation_engine import evaluate_red_flags, merge_recommendations
from storage import save_to_db, init_storage

# 페이지 기본 설정
st.set_page_config(page_title="어깨 통증 평가 프로그램", page_icon="🩺", layout="centered")

# 데이터 로드 및 초기화 (한 번만 실행되도록 캐싱)
@st.cache_resource
def load_all_data():
    questions = load_questions("config/questions.csv")
    rules = load_yaml("config/rules.yaml")
    init_storage("patients_data.db")
    return questions, rules

questions, rules = load_all_data()

# 세션 상태(상태 저장소) 초기화
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
    st.session_state.answers = {}
    st.session_state.history = []
    st.session_state.is_completed = False

# 다음 질문 찾기 로직 (조건부 건너뛰기)
def get_next_valid_index(start_idx):
    idx = start_idx
    while idx < len(questions):
        q = questions[idx]
        cond_field = q.get("condition_field")
        cond_val = q.get("condition_value")
        # 조건이 있는데, 환자의 답변과 조건이 일치하지 않으면 건너뜀
        if cond_field and cond_val:
            if st.session_state.answers.get(cond_field) != cond_val:
                idx += 1
                continue
        break
    return idx

# UI 화면 그리기
st.title("🩺 어깨 통증 평가 프로그램")
st.markdown("---")

# --- 설문 진행 중 화면 ---
if not st.session_state.is_completed:
    # 진행률 표시
    progress = st.session_state.current_index / len(questions)
    st.progress(progress, text=f"진행 상황 (전체 {len(questions)}문항 중)")

    # 현재 질문 가져오기
    q = questions[st.session_state.current_index]
    
    st.subheader(f"[{q.get('section', '질문')}]")
    st.markdown(f"### {q.get('question', '')}")
    
    if q.get('help_text'):
        st.info(f"💡 {q['help_text']}")

    st.write("") # 여백

    # 입력 폼
    user_input = None
    if q.get('type') == 'choice':
        options = q.get('options', [])
        # 라디오 버튼으로 직관적인 선택 제공
        user_input = st.radio("선택해주세요:", options, index=None)
    else:
        user_input = st.text_input("값을 입력해주세요:")

    st.write("")
    st.write("")

        # 하단 버튼 배치 (이전 / 다음) - 간격을 줄이고 버튼을 큼직하게 수정
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.session_state.history:
            # use_container_width=True 를 추가하여 버튼이 칸에 꽉 차게 만듭니다.
            if st.button("⬅️ 이전 질문", use_container_width=True):
                st.session_state.current_index = st.session_state.history.pop()
                st.rerun()

    with col2:
        # 마찬가지로 꽉 차게 만들고, type="primary"로 파란색 강조를 유지합니다.
        if st.button("다음 ➡️", type="primary", use_container_width=True):
            if q.get('required') and not user_input:
                st.warning("이 문항은 필수 응답입니다.")
            else:
                # 응답 저장
                st.session_state.answers[q['key']] = user_input
                st.session_state.history.append(st.session_state.current_index)
                
                # 다음 유효한 질문 찾기
                next_idx = get_next_valid_index(st.session_state.current_index + 1)
                
                if next_idx >= len(questions):
                    st.session_state.is_completed = True
                else:
                    st.session_state.current_index = next_idx
                st.rerun()

# --- 설문 완료 및 결과 화면 ---
else:
    st.success("🎉 모든 평가가 완료되었습니다!")
    
    # 분석 엔진 가동 (여기서 2개 들어가던 오류를 1개로 수정 완료!)
    results = calculate_scores(st.session_state.answers, rules)
    sorted_diags = rank_diagnoses(results["diagnoses"]) 
    results["red_flags"] = evaluate_red_flags(st.session_state.answers, rules)
    results["recommendations"] = merge_recommendations(results["diagnoses"], rules)
    
    # DB 저장
    save_to_db(st.session_state.answers, results)

     # 1. 환자 정보 표시 (추가된 부분)
    p_name = st.session_state.answers.get('name', '익명')
    p_age = st.session_state.answers.get('age', '?')
    st.info(f"👤 **환자명:** {p_name} 님 | **나이:** {p_age}세")
    
    st.caption("🚨 [주의] 본 결과는 참고용이며 의학적 진단을 대체할 수 없습니다.")

    # 2. 위험 신호 (Red Flags)
    if results["red_flags"]:
        st.error("❗ **위험 신호 감지 (즉각적인 진료 권장)**")
        for rf in results["red_flags"]:
            st.markdown(f"- {rf}")
    st.divider()

    # 3. 의심 질환 및 맞춤형 추천 검사 (임상적 조언 반영)
    st.subheader("🔍 의심 질환 및 필요 감별 검사")
    has_disease = False
    
    for name, data in sorted_diags:
        if data['score'] > 0:
            has_disease = True
            
            # 질환명과 점수 게이지 바
            st.markdown(f"#### **{name}**")
            st.progress(data['probability'] / 100.0, text=f"의심 확률: {data['probability']}% ({data['score']}/{data['max_score']}점)")
            st.caption(f"_{data['description']}_")
            
            # 해당 질환 확인에 필요한 검사만 노출
            diag_rule = rules.get('diagnoses', {}).get(name, {})
            recs = diag_rule.get('recommendations', {})
            
            phys_tests = ", ".join(recs.get("physical_tests", []))
            img_tests = ", ".join(recs.get("imaging_tests", []))
            
            st.markdown(f"> **🩺 이 질환 감별을 위한 권장 검사**")
            if phys_tests: st.markdown(f"> - **이학적 검사:** {phys_tests}")
            if img_tests: st.markdown(f"> - **영상/특수 검사:** {img_tests}")
            st.write("") # 여백
    
    if not has_disease:
        st.info("특정 질환 기준에 뚜렷하게 부합하는 항목이 없습니다.")
    st.divider()

    # 4. 하단 제어 버튼 (PDF 저장 안내 및 초기화)
    col1, col2 = st.columns(2)
    with col1:
        # Streamlit 전용 버튼과 자바스크립트 인쇄 명령어 연결
        if st.button("🖨️ 결과지 PDF로 저장 / 인쇄하기", use_container_width=True):
            st.components.v1.html("<script>window.parent.print();</script>", width=0, height=0)
        st.caption("화면이 잘리거나 버튼이 작동하지 않으면 키보드 `Ctrl + P`를 누르세요.")
        
    with col2:
        if st.button("🔄 새로운 환자 평가 시작", type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()
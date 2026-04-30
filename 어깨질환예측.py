import streamlit as st
from typing import Dict, List, Tuple

st.set_page_config(page_title="어깨 통증 평가 알고리즘 MVP", layout="wide")

# =========================================================
# 상수 정의
# =========================================================
DISEASES = [
    "회전근개 관련 통증",
    "견봉하 충돌/점액낭염",
    "유착성 관절낭염",
    "완전층 회전근개 파열 의심",
    "AC joint 병변",
    "견관절 골관절염",
    "경추성 방사통/신경근병증",
    "석회성 건염",
]

DISCLAIMER = """
본 도구는 교육 및 의사결정지원용 MVP입니다.
최종 진단을 확정하지 않으며, 임상적 판단을 대체하지 않습니다.
레드플래그 또는 비전형적 증상이 있으면 전문의 평가가 우선입니다.
"""

# =========================================================
# 상태 초기화
# =========================================================
def init_session():
    if "step" not in st.session_state:
        st.session_state.step = 1

    default_data = {
        # 기본 정보
        "age": 50,
        "sex": "여성",
        "affected_side": "우측",
        "duration": "2~6주",

        # 과거력 / 위험인자
        "diabetes": False,
        "thyroid_disease": False,
        "cancer_history": False,
        "immunocompromised": False,
        "recent_infection": False,
        "steroid_use": False,

        # 레드플래그 / 병력
        "trauma": False,
        "fever": False,
        "weight_loss": False,
        "night_pain": False,
        "rest_pain": False,
        "warmth_redness": False,
        "progressive_weakness": False,

        # 통증 양상
        "overhead_pain": False,
        "lateral_pain": False,
        "anterior_pain": False,
        "superior_pain": False,
        "posterior_pain": False,
        "radiating_pain": False,
        "neck_pain": False,
        "numbness": False,
        "acute_severe_pain": False,
        "repetitive_use": False,

        # 기능 / ROM
        "cannot_raise_arm": False,
        "difficulty_reaching_back": False,
        "sleep_disturbance": False,
        "active_rom_limited": False,
        "passive_rom_limited": False,
        "external_rotation_limited": False,
        "stiffness": False,
        "severe_loss_of_motion": False,

        # 기본 진찰
        "painful_arc": False,
        "abduction_weakness": False,
        "external_rotation_weakness": False,
        "ac_tenderness": False,
        "crepitus": False,
        "pain_with_neck_motion": False,
        "neuro_deficit": False,

        # 선택 이학적 검사
        "hawkins": False,
        "neer": False,
        "jobe": False,
        "drop_arm": False,
        "er_lag": False,
        "cross_body": False,
        "spurling": False,

        # 기존 영상/검사
        "xray_done": False,
        "xray_calcification": False,
    }

    if "data" not in st.session_state:
        st.session_state.data = default_data.copy()
    else:
        for k, v in default_data.items():
            if k not in st.session_state.data:
                st.session_state.data[k] = v


# =========================================================
# 유틸
# =========================================================
def init_scores() -> Dict[str, int]:
    return {d: 0 for d in DISEASES}


def duration_is_chronic(duration: str) -> bool:
    return duration in ["6주~3개월", ">3개월"]


def gradual_onset(data: Dict) -> bool:
    return not data.get("trauma", False)


def sudden_weakness(data: Dict) -> bool:
    return data.get("cannot_raise_arm", False) and data.get("trauma", False)


def normalize_probabilities(scores: Dict[str, int]) -> Dict[str, float]:
    non_negative = {k: max(v, 0) for k, v in scores.items()}
    total = sum(non_negative.values())
    if total == 0:
        return {k: 0.0 for k in non_negative}
    return {k: round(v / total * 100, 1) for k, v in non_negative.items()}


def sort_rank(scores: Dict[str, int], probs: Dict[str, float]) -> List[Tuple[str, int, float]]:
    items = [(d, scores[d], probs[d]) for d in scores]
    items.sort(key=lambda x: (x[2], x[1]), reverse=True)
    return items


# =========================================================
# 레드플래그 판정
# =========================================================
def check_red_flags(data: Dict) -> List[str]:
    flags = []

    # 감염 의심
    if (data.get("fever") or data.get("recent_infection") or data.get("immunocompromised")) and data.get("warmth_redness"):
        flags.append("감염 의심: 발열/감염위험 + 국소 열감/홍반")

    # 골절/탈구/중증 외상
    if data.get("trauma") and (data.get("severe_loss_of_motion") or data.get("cannot_raise_arm")):
        flags.append("외상성 중증 병변 의심: 골절/탈구/급성 파열 가능성")

    # 종양 의심
    if data.get("cancer_history") and (data.get("night_pain") or data.get("rest_pain") or data.get("weight_loss")):
        flags.append("종양성 병변 의심: 암 병력 + 야간통/휴식통/체중감소")

    # 신경학적 중증
    if data.get("progressive_weakness") or data.get("neuro_deficit"):
        flags.append("중증 신경학적 이상 의심: 진행성 근력저하 또는 객관적 신경학적 이상")

    return flags


# =========================================================
# 근거 문구 생성
# =========================================================
def build_reason_map(data: Dict) -> Dict[str, List[str]]:
    age = data.get("age", 0)
    reasons = {d: [] for d in DISEASES}

    # 회전근개 관련 통증
    if age >= 40:
        reasons["회전근개 관련 통증"].append("40세 이상")
    if data.get("overhead_pain"):
        reasons["회전근개 관련 통증"].append("overhead activity 시 악화")
    if data.get("lateral_pain"):
        reasons["회전근개 관련 통증"].append("외측 어깨 통증")
    if data.get("night_pain"):
        reasons["회전근개 관련 통증"].append("야간통")
    if data.get("painful_arc"):
        reasons["회전근개 관련 통증"].append("painful arc")
    if data.get("abduction_weakness") or data.get("external_rotation_weakness"):
        reasons["회전근개 관련 통증"].append("외전/외회전 약화")
    if data.get("active_rom_limited") and not data.get("passive_rom_limited"):
        reasons["회전근개 관련 통증"].append("능동 ROM 제한, 수동 ROM 비교적 보존")

    # 충돌/점액낭염
    if data.get("overhead_pain"):
        reasons["견봉하 충돌/점액낭염"].append("overhead pain")
    if data.get("painful_arc"):
        reasons["견봉하 충돌/점액낭염"].append("painful arc")
    if data.get("hawkins"):
        reasons["견봉하 충돌/점액낭염"].append("Hawkins 양성")
    if data.get("neer"):
        reasons["견봉하 충돌/점액낭염"].append("Neer 양성")
    if data.get("repetitive_use"):
        reasons["견봉하 충돌/점액낭염"].append("반복 사용 병력")

    # 유착성 관절낭염
    if 40 <= age <= 65:
        reasons["유착성 관절낭염"].append("40~65세")
    if data.get("diabetes") or data.get("thyroid_disease"):
        reasons["유착성 관절낭염"].append("당뇨/갑상선 질환")
    if gradual_onset(data):
        reasons["유착성 관절낭염"].append("점진적 발생")
    if data.get("night_pain"):
        reasons["유착성 관절낭염"].append("야간통")
    if data.get("active_rom_limited") and data.get("passive_rom_limited"):
        reasons["유착성 관절낭염"].append("능동/수동 ROM 모두 제한")
    if data.get("external_rotation_limited"):
        reasons["유착성 관절낭염"].append("외회전 제한")
    if data.get("difficulty_reaching_back"):
        reasons["유착성 관절낭염"].append("등 뒤로 손 넣기 어려움")

    # 완전층 파열
    if age >= 50:
        reasons["완전층 회전근개 파열 의심"].append("50세 이상")
    if data.get("trauma"):
        reasons["완전층 회전근개 파열 의심"].append("외상 후 발생")
    if data.get("progressive_weakness") or sudden_weakness(data):
        reasons["완전층 회전근개 파열 의심"].append("근력저하")
    if data.get("cannot_raise_arm"):
        reasons["완전층 회전근개 파열 의심"].append("팔 거상 어려움")
    if data.get("drop_arm"):
        reasons["완전층 회전근개 파열 의심"].append("Drop arm 양성")
    if data.get("er_lag"):
        reasons["완전층 회전근개 파열 의심"].append("ER lag sign 양성")

    # AC joint
    if data.get("ac_tenderness"):
        reasons["AC joint 병변"].append("AC joint 국소 압통")
    if data.get("cross_body"):
        reasons["AC joint 병변"].append("cross-body adduction pain")
    if data.get("superior_pain"):
        reasons["AC joint 병변"].append("상부 국소 통증")

    # OA
    if age >= 60:
        reasons["견관절 골관절염"].append("고령")
    if duration_is_chronic(data.get("duration")):
        reasons["견관절 골관절염"].append("만성 통증")
    if data.get("stiffness"):
        reasons["견관절 골관절염"].append("강직감")
    if data.get("active_rom_limited") and data.get("passive_rom_limited"):
        reasons["견관절 골관절염"].append("능동/수동 ROM 모두 제한")
    if data.get("crepitus"):
        reasons["견관절 골관절염"].append("crepitus")

    # 경추성
    if data.get("neck_pain"):
        reasons["경추성 방사통/신경근병증"].append("목 통증 동반")
    if data.get("radiating_pain"):
        reasons["경추성 방사통/신경근병증"].append("팔로 방사통")
    if data.get("numbness"):
        reasons["경추성 방사통/신경근병증"].append("저림/감각이상")
    if data.get("pain_with_neck_motion"):
        reasons["경추성 방사통/신경근병증"].append("목 움직임으로 증상 유발")
    if data.get("spurling"):
        reasons["경추성 방사통/신경근병증"].append("Spurling 양성")
    if data.get("neuro_deficit"):
        reasons["경추성 방사통/신경근병증"].append("신경학적 진찰 이상")

    # 석회성 건염
    if 30 <= age <= 60:
        reasons["석회성 건염"].append("중년 연령대")
    if data.get("acute_severe_pain"):
        reasons["석회성 건염"].append("급성 심한 통증")
    if data.get("night_pain"):
        reasons["석회성 건염"].append("야간통")
    if data.get("lateral_pain"):
        reasons["석회성 건염"].append("외측 통증")
    if data.get("xray_calcification"):
        reasons["석회성 건염"].append("X-ray 석회화 소견")

    return reasons


# =========================================================
# 점수 계산
# =========================================================
def calculate_scores(data: Dict) -> Dict[str, int]:
    s = init_scores()
    age = data.get("age", 0)

    # 1. 회전근개 관련 통증
    if age >= 40:
        s["회전근개 관련 통증"] += 1
    if data.get("overhead_pain"):
        s["회전근개 관련 통증"] += 2
    if data.get("lateral_pain"):
        s["회전근개 관련 통증"] += 2
    if data.get("night_pain"):
        s["회전근개 관련 통증"] += 1
    if data.get("painful_arc"):
        s["회전근개 관련 통증"] += 2
    if data.get("abduction_weakness") or data.get("external_rotation_weakness"):
        s["회전근개 관련 통증"] += 2
    if data.get("jobe"):
        s["회전근개 관련 통증"] += 2
    if data.get("active_rom_limited") and not data.get("passive_rom_limited"):
        s["회전근개 관련 통증"] += 2
    if data.get("passive_rom_limited"):
        s["회전근개 관련 통증"] -= 2
    if data.get("numbness") or data.get("radiating_pain"):
        s["회전근개 관련 통증"] -= 2

    # 2. 견봉하 충돌/점액낭염
    if data.get("overhead_pain"):
        s["견봉하 충돌/점액낭염"] += 2
    if data.get("painful_arc"):
        s["견봉하 충돌/점액낭염"] += 2
    if data.get("hawkins"):
        s["견봉하 충돌/점액낭염"] += 2
    if data.get("neer"):
        s["견봉하 충돌/점액낭염"] += 2
    if data.get("lateral_pain"):
        s["견봉하 충돌/점액낭염"] += 1
    if data.get("repetitive_use"):
        s["견봉하 충돌/점액낭염"] += 1
    if data.get("passive_rom_limited"):
        s["견봉하 충돌/점액낭염"] -= 2

    # 3. 유착성 관절낭염
    if 40 <= age <= 65:
        s["유착성 관절낭염"] += 1
    if data.get("diabetes") or data.get("thyroid_disease"):
        s["유착성 관절낭염"] += 2
    if gradual_onset(data):
        s["유착성 관절낭염"] += 1
    if data.get("night_pain"):
        s["유착성 관절낭염"] += 1
    if data.get("active_rom_limited") and data.get("passive_rom_limited"):
        s["유착성 관절낭염"] += 4
    if data.get("external_rotation_limited"):
        s["유착성 관절낭염"] += 3
    if data.get("difficulty_reaching_back"):
        s["유착성 관절낭염"] += 2
    if data.get("trauma"):
        s["유착성 관절낭염"] -= 1
    if data.get("radiating_pain") or data.get("numbness"):
        s["유착성 관절낭염"] -= 2

    # 4. 완전층 회전근개 파열 의심
    if age >= 50:
        s["완전층 회전근개 파열 의심"] += 1
    if data.get("trauma"):
        s["완전층 회전근개 파열 의심"] += 2
    if data.get("progressive_weakness") or sudden_weakness(data):
        s["완전층 회전근개 파열 의심"] += 3
    if data.get("cannot_raise_arm"):
        s["완전층 회전근개 파열 의심"] += 3
    if data.get("drop_arm"):
        s["완전층 회전근개 파열 의심"] += 3
    if data.get("er_lag"):
        s["완전층 회전근개 파열 의심"] += 3
    if data.get("active_rom_limited") and not data.get("passive_rom_limited"):
        s["완전층 회전근개 파열 의심"] += 2
    if data.get("passive_rom_limited"):
        s["완전층 회전근개 파열 의심"] -= 2
    if data.get("neck_pain") or data.get("numbness"):
        s["완전층 회전근개 파열 의심"] -= 2

    # 5. AC joint 병변
    if data.get("ac_tenderness"):
        s["AC joint 병변"] += 3
    if data.get("cross_body"):
        s["AC joint 병변"] += 3
    if data.get("superior_pain"):
        s["AC joint 병변"] += 2
    if data.get("active_rom_limited") and data.get("passive_rom_limited"):
        s["AC joint 병변"] -= 1
    if data.get("numbness"):
        s["AC joint 병변"] -= 2

    # 6. 견관절 골관절염
    if age >= 60:
        s["견관절 골관절염"] += 2
    if duration_is_chronic(data.get("duration")):
        s["견관절 골관절염"] += 1
    if data.get("stiffness"):
        s["견관절 골관절염"] += 1
    if data.get("active_rom_limited") and data.get("passive_rom_limited"):
        s["견관절 골관절염"] += 2
    if data.get("crepitus"):
        s["견관절 골관절염"] += 2
    if data.get("radiating_pain") or data.get("numbness"):
        s["견관절 골관절염"] -= 2
    if data.get("acute_severe_pain"):
        s["견관절 골관절염"] -= 1

    # 7. 경추성 방사통/신경근병증
    if data.get("neck_pain"):
        s["경추성 방사통/신경근병증"] += 2
    if data.get("radiating_pain"):
        s["경추성 방사통/신경근병증"] += 3
    if data.get("numbness"):
        s["경추성 방사통/신경근병증"] += 3
    if data.get("pain_with_neck_motion"):
        s["경추성 방사통/신경근병증"] += 2
    if data.get("spurling"):
        s["경추성 방사통/신경근병증"] += 3
    if data.get("neuro_deficit"):
        s["경추성 방사통/신경근병증"] += 3
    if data.get("painful_arc"):
        s["경추성 방사통/신경근병증"] -= 2
    if data.get("ac_tenderness"):
        s["경추성 방사통/신경근병증"] -= 1

    # 8. 석회성 건염
    if 30 <= age <= 60:
        s["석회성 건염"] += 1
    if data.get("acute_severe_pain"):
        s["석회성 건염"] += 2
    if data.get("night_pain"):
        s["석회성 건염"] += 1
    if data.get("lateral_pain"):
        s["석회성 건염"] += 1
    if data.get("active_rom_limited"):
        s["석회성 건염"] += 1
    if data.get("xray_calcification"):
        s["석회성 건염"] += 4
    if data.get("numbness"):
        s["석회성 건염"] -= 2

    return s


# =========================================================
# 추천 검사
# =========================================================
def recommend_tests(data: Dict, ranked: List[str], red_flags: List[str]) -> Dict[str, List[str]]:
    essential = []
    optional = []
    physical = []

    if red_flags:
        essential.append("레드플래그 우선 평가: 응급 또는 전문의 진료 고려")

        if data.get("trauma"):
            essential.append("어깨 단순 X-ray (AP, axillary, scapular Y)")

        if data.get("fever") or data.get("warmth_redness") or data.get("recent_infection") or data.get("immunocompromised"):
            essential.extend(["CBC", "ESR", "CRP"])

        if data.get("progressive_weakness") or data.get("neuro_deficit"):
            essential.append("신경학적 정밀평가 ± 경추 영상 ± EMG/NCS")

        if data.get("cancer_history") and (data.get("night_pain") or data.get("rest_pain") or data.get("weight_loss")):
            essential.append("종양성 병변 배제 위한 전문의 평가 및 적절한 영상검사 고려")

        return {
            "physical": list(dict.fromkeys(physical)),
            "essential": list(dict.fromkeys(essential)),
            "optional": list(dict.fromkeys(optional)),
        }

    top3 = ranked[:3]

    # 이학적 검사 추천
    if "회전근개 관련 통증" in top3 or "견봉하 충돌/점액낭염" in top3:
        physical += ["Hawkins-Kennedy", "Neer", "Jobe", "painful arc", "외회전 근력평가"]

    if "유착성 관절낭염" in top3:
        physical += ["능동/수동 ROM 비교", "수동 외회전 범위 측정", "capsular pattern 확인"]

    if "완전층 회전근개 파열 의심" in top3:
        physical += ["Drop arm", "External rotation lag sign", "능동/수동 ROM 비교"]

    if "AC joint 병변" in top3:
        physical += ["AC joint 촉진", "Cross-body adduction"]

    if "경추성 방사통/신경근병증" in top3:
        physical += ["Spurling", "경추 ROM", "감각/근력/반사 검사"]

    # 필수 검사 추천
    if data.get("trauma"):
        essential.append("어깨 단순 X-ray (AP, axillary, scapular Y)")

    if data.get("passive_rom_limited") or duration_is_chronic(data.get("duration")):
        essential.append("어깨 단순 X-ray (구조적 병변/관절염/석회화 배제 목적)")

    if "유착성 관절낭염" in top3:
        essential.append("단순 X-ray 우선 고려")

    if "완전층 회전근개 파열 의심" in top3:
        essential.append("초음파 또는 MRI (완전층 파열 여부 확인 목적)")

    if "경추성 방사통/신경근병증" in top3 and (
        data.get("numbness") or data.get("neuro_deficit") or data.get("progressive_weakness")
    ):
        essential.append("경추 평가 고려 ± EMG/NCS")

    if data.get("fever") or data.get("weight_loss") or data.get("warmth_redness"):
        essential.extend(["CBC", "ESR", "CRP"])

    # 선택 검사 추천
    if "회전근개 관련 통증" in top3 or "견봉하 충돌/점액낭염" in top3 or "석회성 건염" in top3:
        optional.append("어깨 초음파 고려")

    if "견봉하 충돌/점액낭염" in top3 and not data.get("trauma"):
        optional.append("보존적 치료 반응 없으면 초음파 또는 MRI 고려")

    if "견관절 골관절염" in top3:
        optional.append("필요 시 추가 관절면 평가 영상 고려")

    return {
        "physical": list(dict.fromkeys(physical)),
        "essential": list(dict.fromkeys(essential)),
        "optional": list(dict.fromkeys(optional)),
    }


# =========================================================
# 요약 리포트
# =========================================================
def generate_summary_text(
    data: Dict,
    red_flags: List[str],
    ranked_items: List[Tuple[str, int, float]],
    reasons: Dict[str, List[str]],
    tests: Dict[str, List[str]],
) -> str:
    lines = []
    lines.append("=== 어깨 통증 평가 요약 ===")
    lines.append(f"나이: {data.get('age')}세 / 성별: {data.get('sex')} / 증상측: {data.get('affected_side')}")
    lines.append(f"증상 기간: {data.get('duration')}")
    lines.append("")

    lines.append("[주요 입력 소견]")
    key_findings = []
    for label, key in [
        ("외상", "trauma"),
        ("야간통", "night_pain"),
        ("휴식통", "rest_pain"),
        ("목 통증", "neck_pain"),
        ("방사통", "radiating_pain"),
        ("저림", "numbness"),
        ("능동 ROM 제한", "active_rom_limited"),
        ("수동 ROM 제한", "passive_rom_limited"),
        ("외회전 제한", "external_rotation_limited"),
        ("painful arc", "painful_arc"),
        ("AC joint 압통", "ac_tenderness"),
        ("열감/홍반", "warmth_redness"),
    ]:
        if data.get(key):
            key_findings.append(label)

    lines.append(", ".join(key_findings) if key_findings else "특이 소견 선택 없음")
    lines.append("")

    lines.append("[레드플래그]")
    if red_flags:
        for f in red_flags:
            lines.append(f"- {f}")
    else:
        lines.append("- 뚜렷한 레드플래그 없음")
    lines.append("")

    lines.append("[가능성 높은 감별진단 Top 5]")
    for idx, (disease, score, prob) in enumerate(ranked_items[:5], 1):
        reason_text = ", ".join(reasons.get(disease, [])[:5]) if reasons.get(disease) else "주요 근거 제한적"
        lines.append(f"{idx}. {disease} / 점수 {score} / 예측비율 {prob}% / 근거: {reason_text}")
    lines.append("")

    lines.append("[권장 이학적 검사]")
    if tests["physical"]:
        for t in tests["physical"]:
            lines.append(f"- {t}")
    else:
        lines.append("- 추가 이학적 검사 권고 없음")
    lines.append("")

    lines.append("[꼭 필요한 추가 검사]")
    if tests["essential"]:
        for t in tests["essential"]:
            lines.append(f"- {t}")
    else:
        lines.append("- 현 단계에서 필수 추가 검사 없음")
    lines.append("")

    lines.append("[고려 가능한 검사]")
    if tests["optional"]:
        for t in tests["optional"]:
            lines.append(f"- {t}")
    else:
        lines.append("- 선택적 검사 없음")
    lines.append("")

    lines.append("[주의]")
    lines.append("본 결과는 확정진단이 아니라 감별진단 우선순위 및 추가평가 제안입니다.")

    return "\n".join(lines)


# =========================================================
# 단계 이동
# =========================================================
def next_step():
    st.session_state.step += 1


def prev_step():
    st.session_state.step -= 1
    if st.session_state.step < 1:
        st.session_state.step = 1


def reset_all():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    init_session()

# =========================================================
# UI 렌더링
# =========================================================
def render_step_1():
    st.subheader("Step 1. 기본 정보")
    data = st.session_state.data

    col1, col2 = st.columns(2)
    with col1:
        data["age"] = st.number_input("나이", min_value=0, max_value=120, value=int(data["age"]))
        data["sex"] = st.selectbox("성별", ["여성", "남성"], index=0 if data["sex"] == "여성" else 1)
    with col2:
        side_options = ["우측", "좌측", "양측"]
        data["affected_side"] = st.selectbox("증상측", side_options, index=side_options.index(data["affected_side"]))
        duration_options = ["<2주", "2~6주", "6주~3개월", ">3개월"]
        data["duration"] = st.selectbox("증상 기간", duration_options, index=duration_options.index(data["duration"]))

    st.markdown("### 위험인자 / 과거력")
    c1, c2, c3 = st.columns(3)
    with c1:
        data["diabetes"] = st.checkbox("당뇨", value=data["diabetes"])
        data["thyroid_disease"] = st.checkbox("갑상선 질환", value=data["thyroid_disease"])
    with c2:
        data["cancer_history"] = st.checkbox("암 병력", value=data["cancer_history"])
        data["immunocompromised"] = st.checkbox("면역저하", value=data["immunocompromised"])
    with c3:
        data["recent_infection"] = st.checkbox("최근 감염", value=data["recent_infection"])
        data["steroid_use"] = st.checkbox("스테로이드 사용", value=data["steroid_use"])

    st.session_state.data = data

    colb1, colb2 = st.columns([1, 1])
    with colb1:
        if st.button("다음", use_container_width=True):
            next_step()
    with colb2:
        if st.button("초기화", use_container_width=True):
            reset_all()


def render_step_2():
    st.subheader("Step 2. 레드플래그 / 병력")
    data = st.session_state.data

    c1, c2, c3 = st.columns(3)
    with c1:
        data["trauma"] = st.checkbox("최근 외상 후 발생", value=data["trauma"])
        data["fever"] = st.checkbox("발열/오한 있음", value=data["fever"])
        data["weight_loss"] = st.checkbox("체중감소/전신증상", value=data["weight_loss"])
    with c2:
        data["night_pain"] = st.checkbox("야간통", value=data["night_pain"])
        data["rest_pain"] = st.checkbox("휴식 시 통증", value=data["rest_pain"])
        data["warmth_redness"] = st.checkbox("국소 열감/홍반", value=data["warmth_redness"])
    with c3:
        data["progressive_weakness"] = st.checkbox("진행성 근력저하", value=data["progressive_weakness"])
        data["acute_severe_pain"] = st.checkbox("급성의 매우 심한 통증", value=data["acute_severe_pain"])
        data["repetitive_use"] = st.checkbox("반복 사용/과사용 병력", value=data["repetitive_use"])

    st.session_state.data = data

    colb1, colb2 = st.columns([1, 1])
    with colb1:
        if st.button("이전", use_container_width=True):
            prev_step()
    with colb2:
        if st.button("다음 ", use_container_width=True):
            next_step()


def render_step_3():
    st.subheader("Step 3. 통증 위치 / 양상")
    data = st.session_state.data

    c1, c2, c3 = st.columns(3)
    with c1:
        data["lateral_pain"] = st.checkbox("외측 어깨 통증", value=data["lateral_pain"])
        data["anterior_pain"] = st.checkbox("전방 통증", value=data["anterior_pain"])
        data["superior_pain"] = st.checkbox("상부(AC joint 부위) 통증", value=data["superior_pain"])
    with c2:
        data["posterior_pain"] = st.checkbox("후방 통증", value=data["posterior_pain"])
        data["overhead_pain"] = st.checkbox("머리 위 동작에서 악화", value=data["overhead_pain"])
        data["sleep_disturbance"] = st.checkbox("수면 방해", value=data["sleep_disturbance"])
    with c3:
        data["neck_pain"] = st.checkbox("목 통증 동반", value=data["neck_pain"])
        data["radiating_pain"] = st.checkbox("팔로 방사통", value=data["radiating_pain"])
        data["numbness"] = st.checkbox("저림/감각이상", value=data["numbness"])

    st.session_state.data = data

    colb1, colb2 = st.columns([1, 1])
    with colb1:
        if st.button("이전 ", use_container_width=True):
            prev_step()
    with colb2:
        if st.button("다음  ", use_container_width=True):
            next_step()


def render_step_4():
    st.subheader("Step 4. 기능 / ROM")
    data = st.session_state.data

    c1, c2 = st.columns(2)
    with c1:
        data["cannot_raise_arm"] = st.checkbox("팔을 잘 못 들어올림", value=data["cannot_raise_arm"])
        data["difficulty_reaching_back"] = st.checkbox("등 뒤로 손 넣기 어려움", value=data["difficulty_reaching_back"])
        data["active_rom_limited"] = st.checkbox("능동 ROM 제한", value=data["active_rom_limited"])
        data["passive_rom_limited"] = st.checkbox("수동 ROM 제한", value=data["passive_rom_limited"])
    with c2:
        data["external_rotation_limited"] = st.checkbox("외회전 제한", value=data["external_rotation_limited"])
        data["stiffness"] = st.checkbox("강직감", value=data["stiffness"])
        data["severe_loss_of_motion"] = st.checkbox("거의 움직일 수 없음", value=data["severe_loss_of_motion"])

    st.session_state.data = data

    colb1, colb2 = st.columns([1, 1])
    with colb1:
        if st.button("이전  ", use_container_width=True):
            prev_step()
    with colb2:
        if st.button("다음   ", use_container_width=True):
            next_step()


def render_step_5():
    st.subheader("Step 5. 기본 진찰")
    data = st.session_state.data

    c1, c2, c3 = st.columns(3)
    with c1:
        data["painful_arc"] = st.checkbox("Painful arc", value=data["painful_arc"])
        data["abduction_weakness"] = st.checkbox("외전 약화", value=data["abduction_weakness"])
    with c2:
        data["external_rotation_weakness"] = st.checkbox("외회전 약화", value=data["external_rotation_weakness"])
        data["ac_tenderness"] = st.checkbox("AC joint 압통", value=data["ac_tenderness"])
    with c3:
        data["crepitus"] = st.checkbox("Crepitus", value=data["crepitus"])
        data["pain_with_neck_motion"] = st.checkbox("목 움직임으로 통증 유발", value=data["pain_with_neck_motion"])
        data["neuro_deficit"] = st.checkbox("객관적 신경학적 이상", value=data["neuro_deficit"])

    st.session_state.data = data

    st.info("다음 단계에서는 현재 소견을 바탕으로 의미 있는 선택 이학적 검사를 입력합니다.")

    colb1, colb2 = st.columns([1, 1])
    with colb1:
        if st.button("이전   ", use_container_width=True):
            prev_step()
    with colb2:
        if st.button("다음    ", use_container_width=True):
            next_step()


def render_step_6():
    st.subheader("Step 6. 선택 이학적 검사")
    data = st.session_state.data

    st.markdown("현재 입력에 따라 필요한 검사만 선택적으로 표시합니다.")

    show_rotator = data.get("overhead_pain") or data.get("lateral_pain") or data.get("painful_arc")
    show_adhesive = data.get("active_rom_limited") and data.get("passive_rom_limited")
    show_fulltear = data.get("trauma") or data.get("cannot_raise_arm") or data.get("progressive_weakness")
    show_ac = data.get("superior_pain") or data.get("ac_tenderness")
    show_cervical = data.get("neck_pain") or data.get("radiating_pain") or data.get("numbness") or data.get("pain_with_neck_motion")

    c1, c2, c3 = st.columns(3)

    with c1:
        if show_rotator:
            st.markdown("#### 회전근개/충돌 관련")
            data["hawkins"] = st.checkbox("Hawkins-Kennedy 양성", value=data["hawkins"])
            data["neer"] = st.checkbox("Neer 양성", value=data["neer"])
            data["jobe"] = st.checkbox("Jobe 양성", value=data["jobe"])

    with c2:
        if show_fulltear:
            st.markdown("#### 파열 관련")
            data["drop_arm"] = st.checkbox("Drop arm 양성", value=data["drop_arm"])
            data["er_lag"] = st.checkbox("ER lag sign 양성", value=data["er_lag"])
        if show_ac:
            st.markdown("#### AC joint 관련")
            data["cross_body"] = st.checkbox("Cross-body adduction pain 양성", value=data["cross_body"])

    with c3:
        if show_cervical:
            st.markdown("#### 경추성 관련")
            data["spurling"] = st.checkbox("Spurling 양성", value=data["spurling"])

        st.markdown("#### 기존 영상")
        data["xray_done"] = st.checkbox("기존 X-ray 시행됨", value=data["xray_done"])
        if data["xray_done"]:
            data["xray_calcification"] = st.checkbox("X-ray 석회화 소견 있음", value=data["xray_calcification"])
        else:
            data["xray_calcification"] = False

    if not any([show_rotator, show_adhesive, show_fulltear, show_ac, show_cervical]):
        st.write("현재 입력 기준으로 추가 선택 검사가 필수적으로 추천되지는 않습니다.")

    st.session_state.data = data

    colb1, colb2 = st.columns([1, 1])
    with colb1:
        if st.button("이전    ", use_container_width=True):
            prev_step()
    with colb2:
        if st.button("결과 보기", use_container_width=True):
            next_step()


def render_result():
    st.subheader("Step 7. 결과")
    data = st.session_state.data

    red_flags = check_red_flags(data)
    scores = calculate_scores(data)
    probs = normalize_probabilities(scores)
    ranked_items = sort_rank(scores, probs)
    ranked_names = [x[0] for x in ranked_items]
    reasons = build_reason_map(data)
    tests = recommend_tests(data, ranked_names, red_flags)
    summary = generate_summary_text(data, red_flags, ranked_items, reasons, tests)

    if red_flags:
        st.error("레드플래그가 감지되었습니다.")
        for rf in red_flags:
            st.write(f"- {rf}")
    else:
        st.success("뚜렷한 레드플래그는 감지되지 않았습니다.")

    st.markdown("### 가능성 높은 감별진단")
    for idx, (disease, score, prob) in enumerate(ranked_items[:5], 1):
        with st.expander(f"{idx}. {disease} — 예측비율 {prob}% / 점수 {score}", expanded=(idx <= 3)):
            reason_list = reasons.get(disease, [])
            if reason_list:
                st.write("근거:")
                for r in reason_list[:6]:
                    st.write(f"- {r}")
            else:
                st.write("선택된 입력 기준으로 뚜렷한 근거 문구가 제한적입니다.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 권장 이학적 검사")
        if tests["physical"]:
            for item in tests["physical"]:
                st.write(f"- {item}")
        else:
            st.write("- 추가 이학적 검사 권고 없음")

        st.markdown("### 꼭 필요한 추가 검사")
        if tests["essential"]:
            for item in tests["essential"]:
                st.write(f"- {item}")
        else:
            st.write("- 현 단계에서 필수 추가 검사 없음")

    with col2:
        st.markdown("### 고려 가능한 검사")
        if tests["optional"]:
            for item in tests["optional"]:
                st.write(f"- {item}")
        else:
            st.write("- 선택적 검사 없음")

        st.markdown("### 결과 요약")
        st.code(summary, language="text")

    st.download_button(
        label="요약 텍스트 다운로드",
        data=summary,
        file_name="shoulder_pain_summary.txt",
        mime="text/plain"
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("이전 단계로", use_container_width=True):
            prev_step()
    with c2:
        if st.button("처음부터 다시", use_container_width=True):
            reset_all()


# =========================================================
# 메인
# =========================================================
def main():
    init_session()

    st.title("어깨 통증 평가 알고리즘 MVP")
    st.caption("임상 치료사용 클릭형 의사결정지원 프로토타입")

    with st.expander("사용 안내 / 주의", expanded=False):
        st.write(DISCLAIMER)

    step = st.session_state.step
    progress = min(max((step - 1) / 6, 0.0), 1.0)
    st.progress(progress)

    if step == 1:
        render_step_1()
    elif step == 2:
        render_step_2()
    elif step == 3:
        render_step_3()
    elif step == 4:
        render_step_4()
    elif step == 5:
        render_step_5()
    elif step == 6:
        render_step_6()
    else:
        render_result()


if __name__ == "__main__":
    main()            
import json
from datetime import datetime

import streamlit as st
from google import genai
from google.genai import types
from supabase import create_client


# ---------------------------------------------------------
# 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="글지기 | 나만의 AI 글쓰기 멘토",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

MODEL_NAME = "gemini-3.5-flash-lite"
GEULJIGI_SYSTEM_PROMPT = """
너는 '글지기'라는 이름의 한국어 AI 글쓰기 멘토다.
사용자의 생각과 의도, 고유한 문체를 존중하면서 글의 구조·논리·표현·문법을 개선하도록 돕는다.
완성된 글을 무조건 대신 써주기보다 사용자가 스스로 더 좋은 글을 쓸 수 있도록 구체적으로 코칭한다.
사용자가 제공하지 않은 사실이나 출처를 만들어내지 않는다.
피드백은 친절하고 명확한 한국어로 작성하며 불필요하게 장황하게 설명하지 않는다.
사용자의 기존 문체 정보와 이번 요청의 조건이 다르면 이번 요청의 조건을 우선한다.
""".strip()


# ---------------------------------------------------------
# 디자인
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');

    :root {
        --ink: #352d2a;
        --ink-soft: #51443f;
        --muted: #85766f;
        --rose: #a96868;
        --rose-dark: #875252;
        --rose-pale: #f2e5e1;
        --cream: #faf7f3;
        --sidebar: #f3ece6;
        --paper: #fffefd;
        --line: #e9ded7;
        --shadow: 0 8px 26px rgba(69, 48, 39, .045);
    }

    html, body, [class*="css"] {
        font-family: 'DM Sans', 'Noto Sans KR', sans-serif;
    }
    .stApp {
        background: var(--cream);
        color: var(--ink);
    }
    [data-testid="stHeader"] {
        background: rgba(250, 247, 243, .94);
    }
    .block-container {
        max-width: 1240px;
        padding-top: 2.4rem;
        padding-bottom: 4rem;
    }
    h1, h2, h3, h4 {
        color: var(--ink) !important;
        letter-spacing: -.045em;
        font-weight: 800 !important;
    }
    p, label, .stMarkdown, [data-testid="stCaptionContainer"] {
        color: var(--ink-soft);
    }
    a {
        color: var(--rose-dark) !important;
    }

    /* 사이드바 */
    [data-testid="stSidebar"] {
        background: var(--sidebar);
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.8rem;
    }
    [data-testid="stSidebar"] .block-container {
        padding: 1.8rem 1.15rem 2rem;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] > label {
        display: none;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {
        gap: .35rem;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label {
        border-radius: 12px;
        padding: .58rem .72rem;
        transition: background .15s ease;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:hover {
        background: rgba(169, 104, 104, .09);
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label p {
        color: var(--ink-soft) !important;
        font-weight: 600;
    }

    /* 제목과 브랜드 */
    .brand-mark {
        color: var(--rose-dark);
        font-size: .74rem;
        font-weight: 800;
        letter-spacing: .23em;
    }
    .hero-title {
        font-size: clamp(2.15rem, 4.5vw, 3.65rem);
        line-height: 1.16;
        font-weight: 800;
        letter-spacing: -.07em;
        color: var(--ink);
        margin: .45rem 0 .75rem;
    }
    .hero-sub {
        color: var(--muted);
        font-size: 1.02rem;
        line-height: 1.85;
        max-width: 760px;
    }
    .eyebrow {
        color: var(--rose-dark);
        font-size: .73rem;
        font-weight: 800;
        letter-spacing: .2em;
        text-transform: uppercase;
    }
    .section-title {
        font-size: 1.45rem;
        font-weight: 800;
        letter-spacing: -.045em;
        color: var(--ink);
        margin-bottom: .35rem;
    }

    /* 카드 */
    .soft-card, .stat-card {
        background: var(--paper);
        border: 1px solid var(--line);
        border-radius: 20px;
        box-shadow: var(--shadow);
    }
    .soft-card {
        padding: 1.35rem 1.45rem;
    }
    .stat-card {
        padding: 1.15rem 1.3rem;
        min-height: 116px;
    }
    .stat-label {
        color: var(--muted);
        font-size: .86rem;
        font-weight: 500;
    }
    .stat-value {
        color: var(--ink);
        font-size: 1.9rem;
        font-weight: 800;
        margin-top: .3rem;
        letter-spacing: -.04em;
    }
    .small-muted {
        color: var(--muted);
        font-size: .88rem;
        line-height: 1.7;
    }
    .pill {
        display: inline-block;
        padding: .38rem .78rem;
        border-radius: 999px;
        background: var(--rose-pale);
        color: var(--rose-dark);
        font-size: .78rem;
        font-weight: 700;
    }

    /* 버튼 */
    .stButton > button, .stFormSubmitButton > button {
        border-radius: 13px;
        border: 1px solid var(--rose);
        background: var(--rose);
        color: #fff !important;
        font-weight: 700;
        min-height: 2.85rem;
        transition: background .16s ease, border-color .16s ease, transform .16s ease;
    }
    .stButton > button:hover, .stFormSubmitButton > button:hover {
        background: var(--rose-dark);
        border-color: var(--rose-dark);
        color: #fff !important;
        transform: translateY(-1px);
    }
    .stButton > button:focus, .stFormSubmitButton > button:focus {
        box-shadow: 0 0 0 .18rem #ead2ce;
    }

    /* 입력창: 배경과 글자색을 명시해 가독성 유지 */
    .stTextInput input, .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"] {
        color: var(--ink) !important;
        background: #fff !important;
        border: 1px solid #dfd1c9 !important;
        border-radius: 12px !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #a49690 !important;
        opacity: 1;
    }
    .stTextInput input, .stTextArea textarea {
        caret-color: var(--rose-dark) !important;
    }
    .stTextArea textarea {
        line-height: 1.75;
    }
    [data-baseweb="select"] * {
        color: var(--ink) !important;
    }
    [data-testid="stForm"] {
        border: 0;
    }

    /* Streamlit 기본 컨테이너와 피드백 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--paper);
        border: 1px solid var(--line);
        border-radius: 20px;
        box-shadow: var(--shadow);
    }
    div[data-testid="stAlert"] {
        border-radius: 14px;
    }
    [data-testid="stExpander"] {
        background: var(--paper);
        border: 1px solid var(--line);
        border-radius: 14px;
    }
    [data-testid="stMetric"] {
        background: var(--paper);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 1rem;
    }
    hr {
        border-color: var(--line);
    }
    footer {
        visibility: hidden;
    }

    /* 모바일·좁은 화면 */
    @media (max-width: 760px) {
        .block-container {
            padding: 1.35rem 1rem 2.5rem;
        }
        .hero-title {
            font-size: 2.15rem;
        }
        .hero-sub {
            font-size: .94rem;
        }
        .stat-card {
            min-height: 96px;
            padding: .9rem;
        }
        .stat-value {
            font-size: 1.55rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# 연결 설정
# ---------------------------------------------------------
@st.cache_resource
def get_supabase_client(url: str, key: str):
    return create_client(url, key)


@st.cache_resource
def get_gemini_client(api_key: str):
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=45_000),
    )


try:
    supabase = get_supabase_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )
    gemini = get_gemini_client(st.secrets["GEMINI_API_KEY"])
except Exception as exc:
    st.error("연결 설정을 확인해 주세요. 기존 secrets.toml의 키 이름이 맞는지 확인해야 합니다.")
    st.code(str(exc))
    st.stop()


def ask_geuljigi(prompt: str, max_output_tokens: int = 1100) -> str:
    """Gemini에 짧고 명확한 글쓰기 요청을 보내고 텍스트 응답을 반환한다."""
    response = gemini.interactions.create(
        model=MODEL_NAME,
        system_instruction=GEULJIGI_SYSTEM_PROMPT,
        input=prompt,
        generation_config={"max_output_tokens": max_output_tokens, "thinking_level": "low"},
    )
    answer = getattr(response, "output_text", None)
    if not answer:
        raise RuntimeError("AI가 빈 답변을 반환했습니다. 잠시 후 다시 시도해 주세요.")
    return answer.strip()


# ---------------------------------------------------------
# Supabase 데이터 함수
# ---------------------------------------------------------
def get_style_profile(user_id: str):
    result = (
        supabase.table("style_profiles")
        .select("style_data")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0].get("style_data")
    return None


def save_style_profile(user_id: str, profile: dict):
    existing = (
        supabase.table("style_profiles")
        .select("user_id")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if existing.data:
        (
            supabase.table("style_profiles")
            .update({"style_data": profile})
            .eq("user_id", user_id)
            .execute()
        )
    else:
        supabase.table("style_profiles").insert(
            {"user_id": user_id, "style_data": profile}
        ).execute()


def save_writing_record(user_id: str, kind: str, situation: str, settings: dict, draft: str, feedback: str):
    payload = {
        "user_id": user_id,
        "kind": kind,
        "situation": situation,
        "settings": settings,
        "draft": draft,
        "feedback": feedback,
    }
    supabase.table("writing_records").insert(payload).execute()


def get_writing_records(user_id: str, limit: int = 50):
    result = (
        supabase.table("writing_records")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []


def style_description(profile) -> str:
    if not profile:
        return "아직 저장된 글쓰기 스타일이 없습니다."
    if isinstance(profile, dict):
        return str(profile.get("description", profile))
    return str(profile)


def show_ai_error(exc: Exception):
    message = str(exc)
    if "503" in message or "UNAVAILABLE" in message or "high demand" in message.lower():
        st.error("Gemini 서버 요청이 몰려 응답하지 못했습니다. 잠시 후 다시 시도해 주세요.")
    elif "429" in message or "RESOURCE_EXHAUSTED" in message:
        st.error("AI 요청 한도에 도달했습니다. 잠시 기다린 뒤 다시 시도해 주세요.")
    elif "timeout" in message.lower() or "timed out" in message.lower():
        st.error("AI 응답 시간이 초과되었습니다. 글을 조금 짧게 나누어 다시 시도해 주세요.")
    else:
        st.error(f"AI 처리 중 문제가 발생했습니다: {message[:500]}")


# ---------------------------------------------------------
# 세션 상태 및 인증
# ---------------------------------------------------------
for key, default in {
    "logged_in": False,
    "user_email": "",
    "user_id": None,
    "page": "홈",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def render_auth():
    left, center, right = st.columns([1, 1.35, 1])
    with center:
        st.write("")
        st.markdown('<div class="brand-mark">YOUR PERSONAL WRITING MENTOR</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-title">글지기</div>', unsafe_allow_html=True)
        st.markdown('<p class="hero-sub">나만의 문체를 찾아가는 AI 글쓰기 멘토<br>생각은 그대로, 글은 더 자연스럽게.</p>', unsafe_allow_html=True)
        st.write("")
        with st.container(border=True):
            login_tab, signup_tab = st.tabs(["로그인", "회원가입"])
            with login_tab:
                with st.form("login_form"):
                    email = st.text_input("이메일", placeholder="name@example.com")
                    password = st.text_input("비밀번호", type="password")
                    submitted = st.form_submit_button("로그인", use_container_width=True)
                if submitted:
                    try:
                        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.logged_in = True
                        st.session_state.user_email = response.user.email or email
                        st.session_state.user_id = response.user.id
                        st.session_state.page = "홈"
                        st.rerun()
                    except Exception:
                        st.error("로그인에 실패했습니다. 이메일과 비밀번호를 확인해 주세요.")
            with signup_tab:
                with st.form("signup_form"):
                    new_email = st.text_input("이메일 주소", key="signup_email", placeholder="name@example.com")
                    new_password = st.text_input("비밀번호", type="password", key="signup_password")
                    confirm = st.text_input("비밀번호 확인", type="password", key="signup_confirm")
                    signed_up = st.form_submit_button("회원가입", use_container_width=True)
                if signed_up:
                    if not new_email or not new_password:
                        st.warning("이메일과 비밀번호를 입력해 주세요.")
                    elif new_password != confirm:
                        st.warning("비밀번호가 서로 다릅니다.")
                    elif len(new_password) < 6:
                        st.warning("비밀번호는 6자 이상 입력해 주세요.")
                    else:
                        try:
                            supabase.auth.sign_up({"email": new_email, "password": new_password})
                            st.success("회원가입 신청이 완료되었습니다. 이메일 인증 설정이 켜져 있다면 인증 후 로그인해 주세요.")
                        except Exception as exc:
                            st.error(f"회원가입에 실패했습니다: {str(exc)[:300]}")
        st.caption("계정과 글쓰기 기록은 사용자별로 관리됩니다.")


if not st.session_state.logged_in or not st.session_state.user_id:
    render_auth()
    st.stop()


# ---------------------------------------------------------
# 공통 레이아웃 / 사이드바
# ---------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="brand-mark">GEULJIGI</div>', unsafe_allow_html=True)
    st.markdown("## ✍️ 글지기")
    st.caption("나만의 AI 글쓰기 멘토")
    st.divider()
    page = st.radio(
        "메뉴",
        ["홈", "글쓰기 지원", "글쓰기 코칭", "내 글쓰기 기록", "내 문체"],
        key="page",
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("로그인 계정")
    st.write(st.session_state.user_email)
    if st.button("로그아웃", use_container_width=True):
        try:
            supabase.auth.sign_out()
        finally:
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state.user_id = None
            st.rerun()
    st.markdown("<div class='small-muted'>당신의 생각이 더 좋은 글이 되는 곳.</div>", unsafe_allow_html=True)

user_id = st.session_state.user_id


def render_header(kicker: str, title: str, subtitle: str):
    st.markdown(f'<div class="eyebrow">{kicker}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hero-title" style="font-size:2.65rem">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<p class="hero-sub">{subtitle}</p>', unsafe_allow_html=True)
    st.write("")


# ---------------------------------------------------------
# 홈
# ---------------------------------------------------------
if page == "홈":
    render_header("YOUR PERSONAL WRITING MENTOR", "나의 생각이 더 좋은 글이 되도록.", "글지기는 글을 대신 쓰기보다, 당신의 생각과 문체를 살려 더 자연스럽고 논리적인 글을 완성하도록 돕습니다.")
    try:
        records = get_writing_records(user_id, limit=50)
        profile = get_style_profile(user_id)
    except Exception as exc:
        records, profile = [], None
        st.warning(f"기록을 불러오지 못했습니다. Supabase 테이블 설정을 확인해 주세요. ({str(exc)[:180]})")

    a, b, c = st.columns(3)
    with a:
        st.markdown(f'<div class="stat-card"><div class="stat-label">저장된 글쓰기 기록</div><div class="stat-value">{len(records)}개</div></div>', unsafe_allow_html=True)
    with b:
        st.markdown(f'<div class="stat-card"><div class="stat-label">나의 문체 분석</div><div class="stat-value">{"완료" if profile else "시작 전"}</div></div>', unsafe_allow_html=True)
    with c:
        st.markdown('<div class="stat-card"><div class="stat-label">오늘의 글쓰기</div><div class="stat-value">한 걸음씩</div></div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 글쓰기 지원
# ---------------------------------------------------------
elif page == "글쓰기 지원":
    render_header("WRITING PLANNER", "글쓰기 방향 설계", "주제와 핵심 내용을 바탕으로 글의 구조를 먼저 잡아 보세요.")
    with st.container(border=True):
        situation = st.text_input("어떤 글을 작성하나요?", placeholder="예: 대학교 수업 과제 보고서")
        col1, col2 = st.columns(2)
        with col1:
            purpose = st.selectbox("글의 목적", ["정보 전달", "설득", "설명", "요청", "감정 표현", "비판적 분석"])
            audience = st.selectbox("예상 독자", ["교수님", "친구", "가족", "일반 독자", "학술 연구자"])
            tone = st.selectbox("어투", ["격식체", "정중한 높임말", "자연스러운 대화체", "친근한 반말"])
        with col2:
            length = st.selectbox("분량", ["간결하게", "보통", "자세하게"])
            structure = st.selectbox("문장 구성", ["단순하고 명확하게", "논리적으로 연결되게", "설명과 근거 중심으로", "자연스럽고 유연하게"])
            mood = st.selectbox("글의 분위기", ["객관적이고 전문적으로", "정중하고 공손하게", "부드럽고 친근하게", "진솔하고 감정적으로"])
        main_points = st.text_area("전달하고 싶은 주요 내용", placeholder="핵심 주장, 반드시 포함할 내용, 알고 있는 사실 등을 적어 주세요.", height=150)
        extra = st.text_area("추가 요청 사항 (선택)", placeholder="예: 서론을 짧게 하고 본론에서 근거를 충분히 다뤄 줘.", height=90)
        make_plan = st.button("글쓰기 방향 설계하기", key="make_plan", use_container_width=True)

    if make_plan:
        if not situation.strip() or not main_points.strip():
            st.warning("글쓰기 상황과 주요 내용을 입력해 주세요.")
        else:
            try:
                with st.spinner("글지기가 글의 구조를 설계하고 있어요..."):
                    profile = get_style_profile(user_id)
                    prompt = f"""
다음 조건에 맞춰 대학생이 직접 글을 작성할 수 있도록 글쓰기 설계안을 만들어 주세요.
[상황] {situation}
[목적] {purpose} / [독자] {audience}
[어투] {tone} / [분량] {length} / [문장 구성] {structure} / [분위기] {mood}
[핵심 내용]
{main_points}
[추가 요청]
{extra or '없음'}
[사용자 문체]
{style_description(profile)}

다음 순서로 간결하고 구체적으로 답해 주세요.
1. 글의 핵심 주제와 목적
2. 추천 제목 2개
3. 서론·본론·결론의 구성과 각 부분에 들어갈 내용
4. 사용자가 추가로 조사하거나 확인해야 할 정보
5. 글을 쓸 때 주의할 점
사용자가 제공하지 않은 사실을 만들어내지 말고, 완성된 보고서 전체를 대신 쓰지 마세요.
"""
                    answer = ask_geuljigi(prompt, max_output_tokens=1000)
                st.markdown("### 글지기의 글쓰기 설계안")
                st.markdown(answer)
                try:
                    save_writing_record(user_id, "support", situation, {"purpose": purpose, "audience": audience, "tone": tone, "length": length, "structure": structure, "mood": mood}, main_points, answer)
                    st.success("설계안이 생성되었고 내 글쓰기 기록에 저장되었습니다.")
                except Exception as save_exc:
                    st.warning(f"설계안은 생성됐지만 기록 저장에 실패했습니다: {str(save_exc)[:250]}")
            except Exception as exc:
                show_ai_error(exc)


# ---------------------------------------------------------
# 글쓰기 코칭
# ---------------------------------------------------------
elif page == "글쓰기 코칭":
    render_header("WRITING COACH", "나의 글 첨삭받기", "내가 쓴 글을 붙여 넣으면 글지기가 부족한 부분과 개선 방향을 짚어 드립니다.")
    profile = None
    try:
        profile = get_style_profile(user_id)
    except Exception:
        pass
    if profile:
        st.markdown('<span class="pill">저장된 나의 문체가 코칭에 반영됩니다</span>', unsafe_allow_html=True)
    else:
        st.info("아직 저장된 문체가 없습니다. 먼저 '내 문체' 메뉴에서 분석하면 개인화된 첨삭을 받을 수 있어요.")

    with st.container(border=True):
        situation = st.text_input("글의 종류 또는 상황", placeholder="예: 언어학 수업 보고서", key="coach_situation")
        draft = st.text_area("첨삭받을 글", placeholder="직접 작성한 글을 여기에 붙여넣어 주세요.", height=260, key="coach_draft")
        c1, c2 = st.columns([1, 1])
        with c1:
            coach = st.button("글쓰기 코칭 받기", key="coach_submit", use_container_width=True)
        with c2:
            analyze = st.button("이 글로 내 문체 분석하기", key="coach_analyze", use_container_width=True)

    if analyze:
        if len(draft.strip()) < 40:
            st.warning("문체를 분석하려면 40자 이상의 글을 입력해 주세요.")
        else:
            try:
                with st.spinner("글지기가 문체의 특징을 분석하고 있어요..."):
                    analysis = ask_geuljigi(
                        f"다음 글의 실제 표현을 근거로 문체를 분석해 주세요. 문장 길이, 문장 구조, 어휘, 어투, 문단 연결 특징을 5~7개 항목으로 간결하게 정리하고, 근거 없는 성격 추측은 하지 마세요.\n\n[글]\n{draft}",
                        max_output_tokens=650,
                    )
                    save_style_profile(user_id, {"description": analysis})
                st.success("나의 글쓰기 스타일을 저장했습니다.")
                st.markdown("### 분석된 나의 문체")
                st.markdown(analysis)
            except Exception as exc:
                show_ai_error(exc)

    if coach:
        if not draft.strip():
            st.warning("첨삭받을 글을 먼저 입력해 주세요.")
        else:
            try:
                with st.spinner("글지기가 글을 읽고 개선점을 찾고 있어요..."):
                    current_profile = get_style_profile(user_id)
                    prompt = f"""
다음 글을 대학생이 이해하기 쉽게 간결하고 구체적으로 첨삭해 주세요.
[글의 종류/상황] {situation or '미입력'}
[사용자의 글쓰기 스타일]
{style_description(current_profile)}
[첨삭할 글]
{draft}

아래 항목을 순서대로 작성해 주세요.
1. 부족한 부분: 중요한 문제 최대 3가지
2. 부족한 이유: 독자가 이해하기 어려운 이유
3. 개선 방향: 구체적으로 어떻게 고칠지
4. 수정 예시: 원래 의미와 사용자의 문체를 살린 수정 문장 또는 문단
5. 전체 평가: 2~3문장
글 전체를 불필요하게 바꾸지 말고, 실제로 개선이 필요한 부분만 짚어 주세요.
"""
                    feedback = ask_geuljigi(prompt, max_output_tokens=1100)
                st.markdown("### 글지기의 첨삭 결과")
                st.markdown(feedback)
                try:
                    save_writing_record(user_id, "coaching", situation, {"personalized": bool(current_profile)}, draft, feedback)
                    st.success("첨삭 결과가 내 글쓰기 기록에 저장되었습니다.")
                except Exception as save_exc:
                    st.warning(f"첨삭은 완료됐지만 기록 저장에 실패했습니다: {str(save_exc)[:250]}")
            except Exception as exc:
                show_ai_error(exc)


# ---------------------------------------------------------
# 내 문체
# ---------------------------------------------------------
elif page == "내 문체":
    render_header("MY WRITING STYLE", "나만의 문체 만들기", "평소 직접 쓴 글을 분석해 두면 글지기가 다음 요청부터 그 특징을 반영합니다.")
    try:
        profile = get_style_profile(user_id)
    except Exception as exc:
        profile = None
        st.error(f"문체 정보를 불러오지 못했습니다: {str(exc)[:250]}")

    with st.container(border=True):
        st.markdown("### 저장된 문체 정보")
        if profile:
            st.markdown(style_description(profile))
        else:
            st.caption("아직 분석된 문체 정보가 없습니다.")
        st.divider()
        sample = st.text_area("평소 내가 작성한 글을 입력해 주세요", placeholder="직접 작성한 글을 5~10문장 정도 붙여 넣어 주세요. 보고서, 과제, 일기 등 본인의 문체가 잘 드러나는 글이면 좋아요.", height=230, key="style_sample")
        if st.button("내 글쓰기 스타일 분석하고 저장하기", key="style_save", use_container_width=True):
            if len(sample.strip()) < 40:
                st.warning("조금 더 정확한 분석을 위해 40자 이상의 글을 입력해 주세요.")
            else:
                try:
                    with st.spinner("글지기가 나만의 문체를 분석하고 있어요..."):
                        analysis = ask_geuljigi(
                            f"다음 글에서 확인되는 글쓰기 스타일만 분석해 주세요. 문장 길이와 구조, 어휘와 표현, 어투, 문단 연결, 전체적인 특징을 구체적인 항목으로 정리해 주세요. 글에 없는 성격이나 개인 정보를 추측하지 마세요. 다음 글쓰기 요청에 반영할 수 있도록 5~7개 항목으로 간결하게 작성해 주세요.\n\n[사용자의 글]\n{sample}",
                            max_output_tokens=650,
                        )
                        save_style_profile(user_id, {"description": analysis})
                    st.success("문체 분석 결과를 저장했습니다. 다음 글쓰기 요청부터 반영됩니다.")
                    st.markdown("### 분석 결과")
                    st.markdown(analysis)
                except Exception as exc:
                    show_ai_error(exc)


# ---------------------------------------------------------
# 내 글쓰기 기록
# ---------------------------------------------------------
elif page == "내 글쓰기 기록":
    render_header("MY WRITING ARCHIVE", "내 글쓰기 기록", "이전에 작성하고 첨삭받은 글과 글쓰기 설계안을 다시 확인할 수 있습니다.")
    try:
        records = get_writing_records(user_id, limit=100)
        if not records:
            st.info("아직 저장된 글쓰기 기록이 없습니다. 글쓰기 지원이나 코칭을 이용하면 기록이 자동으로 저장됩니다.")
        else:
            st.caption(f"최근 기록 {len(records)}개")
            for index, record in enumerate(records):
                kind = record.get("kind", "writing")
                kind_label = "글쓰기 코칭" if kind == "coaching" else "글쓰기 지원"
                created = record.get("created_at", "")
                situation = record.get("situation") or "상황 미입력"
                draft_text = record.get("draft") or ""
                preview = draft_text.replace("\n", " ")[:65]
                title = f"{kind_label} · {situation}"
                with st.expander(f"{title}  |  {created[:16] if created else '날짜 정보 없음'}", expanded=(index == 0)):
                    st.markdown("**작성한 내용 / 핵심 내용**")
                    st.write(draft_text)
                    feedback = record.get("feedback") or ""
                    if feedback:
                        st.markdown("**글지기의 결과**")
                        st.markdown(feedback)
                    settings = record.get("settings")
                    if settings:
                        with st.expander("당시 설정 보기"):
                            st.json(settings)
    except Exception as exc:
        st.error("글쓰기 기록을 불러오지 못했습니다. writing_records 테이블과 접근 정책을 확인해 주세요.")
        st.code(str(exc)[:500])


# ---------------------------------------------------------
# 하단
# ---------------------------------------------------------
st.divider()
st.markdown(
    '<div style="text-align:center; padding:1rem 0 0.5rem;">'
    '<div class="brand-mark">GEULJIGI · YOUR PERSONAL WRITING MENTOR</div>'
    '<div class="small-muted" style="margin-top:.45rem">나의 생각이 더 좋은 글이 되는 곳.</div>'
    '</div>',
    unsafe_allow_html=True,
)

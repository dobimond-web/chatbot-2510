# streamlit_app.py
import json
import streamlit as st
from openai import OpenAI
from datetime import datetime

st.set_page_config(page_title="나의챗봇", page_icon="💬")

# =========================
# 헤더 & 안내
# =========================
st.title("💬 나의챗봇")
st.write(
    "이 앱은 OpenAI의 모델을 사용해 답변을 생성하는 간단한 챗봇입니다. "
    "이 앱을 사용하려면 OpenAI API 키가 필요하며, "
    "[여기에서 발급받을 수 있습니다](https://platform.openai.com/account/api-keys). "
    "직접 만들어보고 싶다면 "
    "[튜토리얼을 참고하세요](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)."
)

# =========================
# 사이드바: 설정 영역
# =========================
with st.sidebar:
    st.subheader("⚙️ 설정", divider="rainbow")

    # secrets.toml에 OPENAI_API_KEY가 있으면 자동으로 불러옴
    default_key = st.secrets.get("OPENAI_API_KEY", "")
    openai_api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=default_key if default_key else "",
        help="secrets.toml에 OPENAI_API_KEY를 저장해두면 자동으로 로드됩니다.",
    )

    model = st.selectbox(
        "모델 선택",
        # 필요에 따라 옵션을 조정하세요.
        ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"],
        index=0,
        help="가성비는 gpt-4o-mini, 품질은 gpt-4o/4.1 권장"
    )

    temperature = st.slider("창의성(temperature)", 0.0, 2.0, 0.7, 0.1)
    max_tokens = st.slider("최대 응답 토큰", 64, 4096, 512, 64)

    system_prompt = st.text_area(
        "시스템 프롬프트(선택)",
        value="You are a helpful, concise assistant. Reply in the user's language.",
        help="모델의 말투/역할/가이드라인을 정의합니다."
    )

    col_a, col_b = st.columns(2)
    with col_a:
        new_chat = st.button("🧹 새 대화", use_container_width=True)
    with col_b:
        show_meta = st.toggle("메타 표시", value=False)

# =========================
# 키 미입력 시 안내
# =========================
if not openai_api_key:
    st.info("🔑 좌측 사이드바에서 OpenAI API 키를 입력해주세요.", icon="🗝️")
    st.stop()

# =========================
# 세션 스테이트 초기화/관리
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if new_chat:
    st.session_state.messages = []
    st.rerun()

# =========================
# OpenAI 클라이언트
# =========================
client = OpenAI(api_key=openai_api_key)

# =========================
# 기존 대화 렌더링
# =========================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# =========================
# 다운로드(대화 내보내기)
# =============

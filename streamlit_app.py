import json
import streamlit as st
from openai import OpenAI
from datetime import datetime

st.set_page_config(page_title="나의챗봇", page_icon="💬")

st.title("💬 나의챗봇")
st.write(
    "이 앱은 OpenAI의 모델을 사용해 답변을 생성하는 간단한 챗봇입니다. "
    "이 앱을 사용하려면 OpenAI API 키가 필요하며, "
    "[여기에서 발급받을 수 있습니다](https://platform.openai.com/account/api-keys). "
    "직접 만들어보고 싶다면 "
    "[튜토리얼을 참고하세요](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)."
)

with st.sidebar:
    st.subheader("⚙️ 설정", divider="rainbow")
    default_key = st.secrets.get("OPENAI_API_KEY", "")
    openai_api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=default_key if default_key else "",
    )
    model = st.selectbox("모델 선택", ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"], index=0)
    temperature = st.slider("창의성(temperature)", 0.0, 2.0, 0.7, 0.1)
    max_tokens = st.slider("최대 응답 토큰", 64, 4096, 512, 64)
    system_prompt = st.text_area("시스템 프롬프트(선택)", "You are a helpful, concise assistant. Reply in the user's language.")
    new_chat = st.button("🧹 새 대화")

# 세션 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if new_chat:
    st.session_state.messages = []
    st.rerun()

# 기존 대화 렌더
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# 채팅 입력창은 항상 보이게
if user_input := st.chat_input("메시지를 입력하세요..."):
    # 키 없으면 모델 호출 안 하고 경고만
    if not openai_api_key:
        st.warning("🔑 OpenAI API 키를 먼저 입력해주세요.")
    else:
        # 사용자 메시지 표시/저장
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # OpenAI 클라이언트 생성
        client = OpenAI(api_key=openai_api_key)

        # 메시지 구성
        msgs = []
        if system_prompt.strip():
            msgs.append({"role": "system", "content": system_prompt.strip()})
        msgs.extend(st.session_state.messages)

        # 응답 스트리밍
        with st.chat_message("assistant"):
            try:
                stream = client.chat.completions.create(
                    model=model,
                    messages=[{"role": m["role"], "content": m["content"]} for m in msgs],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )
                assistant_text = st.write_stream(stream)
            except Exception as e:
                st.error(f"❗요청 중 오류가 발생했어요: {e}")
                assistant_text = ""

        st.session_state.messages.append({"role": "assistant", "content": assistant_text})

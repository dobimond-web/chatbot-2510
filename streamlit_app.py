# streamlit_app.py
import json
import re
from datetime import datetime
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="AI 튜터봇", page_icon="🎓")

# =========================
# 유틸
# =========================
def build_system_prompt(subject, level, mode, target_lang, tone):
    """
    학습/튜터 역할 프롬프트 생성.
    """
    level_map = {
        "초급": "Beginner",
        "중급": "Intermediate",
        "고급": "Advanced",
    }
    mode_desc = {
        "설명 모드": "Explain concepts step-by-step with clear examples and checks for understanding.",
        "교정 모드": "Detect mistakes, correct them, and explain why. Provide improved versions and tips.",
        "소크라테스 모드": "Ask guiding questions before giving answers. Encourage learner to think.",
        "퀴즈 모드": "Generate short multiple-choice quizzes with one correct answer and concise explanation.",
    }
    target_lang_note = f"Always reply in {target_lang}."
    if target_lang == "한국어":
        target_lang_note = "항상 한국어로 답변하세요."

    tone_note = {
        "따뜻하고 친절하게": "Warm, empathetic, and encouraging tone.",
        "간결하고 직설적으로": "Concise and direct tone.",
        "꼼꼼하고 자세하게": "Thorough and detailed tone.",
    }[tone]

    sys = f"""
You are an expert {subject} tutor. Your learner level: {level_map.get(level, 'Intermediate')}.
Primary mode: {mode}. {mode_desc.get(mode, '')}
{tone_note}
{target_lang_note}
Use markdown. Use short paragraphs and numbered steps when helpful.
If the learner's request is ambiguous, briefly ask a single clarifying question.
    """.strip()
    return sys


def call_chat(client, model, messages, temperature=0.7, max_tokens=512, stream=True):
    return client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=stream,
    )


def parse_quiz_json(txt: str):
    """
    모델이 반환한 텍스트에서 JSON을 찾아 파싱.
    기대 형식:
    {
      "question": "...",
      "choices": ["A) ...","B) ...","C) ...","D) ..."],
      "answer": "B",
      "explanation": "..."
    }
    """
    # 코드블록 안 JSON 추출
    codeblock = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", txt, flags=re.S)
    raw = codeblock.group(1) if codeblock else txt

    # 가장 큰 중괄호 블록 추출
    braces = re.search(r"\{.*\}", raw, flags=re.S)
    raw_json = braces.group(0) if braces else raw

    # 작은 따옴표를 큰 따옴표로 교체(가벼운 복구)
    try_candidates = [raw_json, raw_json.replace("'", '"')]
    for cand in try_candidates:
        try:
            data = json.loads(cand)
            return {
                "question": data.get("question", "").strip(),
                "choices": data.get("choices", []),
                "answer": str(data.get("answer", "")).strip().upper(),
                "explanation": data.get("explanation", "").strip(),
            }
        except Exception:
            continue
    return None


def request_quiz_item(client, model, subject, level, target_lang, tone):
    """
    퀴즈 아이템 1개 생성 요청.
    """
    sys = build_system_prompt(subject, level, "퀴즈 모드", target_lang, tone)
    user = (
        "다음 형식의 JSON으로 객관식 퀴즈를 1문제 생성해 주세요.\n\n"
        "요구사항:\n"
        "- 난이도는 학습자 레벨에 맞추세요.\n"
        "- 선택지는 4개(A,B,C,D)로 만들고, 정답은 answer에 A/B/C/D 중 하나로 표기.\n"
        "- explanation에는 간단하고 핵심적인 해설을 제공.\n\n"
        "출력 형식(반드시 아래 JSON 스키마만 출력하세요):\n"
        "{\n"
        '  "question": "문제 내용",\n'
        '  "choices": ["A) ...","B) ...","C) ...","D) ..."],\n'
        '  "answer": "B",\n'
        '  "explanation": "핵심 해설"\n'
        "}"
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": user},
        ],
        temperature=0.7,
        max_tokens=512,
        stream=False,
    )
    content = resp.choices[0].message.content
    return parse_quiz_json(content or "")


# =========================
# 헤더 & 안내
# =========================
st.title("🎓 AI 튜터봇")
st.caption("레벨·과목·모드에 따라 설명/교정/소크라테스식 질의/퀴즈를 제공하는 학습용 챗봇")

# =========================
# 사이드바: 설정
# =========================
with st.sidebar:
    st.subheader("⚙️ 설정", divider="rainbow")

    default_key = st.secrets.get("OPENAI_API_KEY", "")
    openai_api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=default_key if default_key else "",
        help="secrets.toml에 OPENAI_API_KEY를 저장하면 자동 로드됩니다.",
    )

    model = st.selectbox(
        "모델 선택",
        ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"],
        index=0,
        help="가성비는 gpt-4o-mini, 품질은 gpt-4o/4.1 권장"
    )

    subject = st.selectbox("과목", ["영어", "한국어 작문", "수학(개념 설명)", "코딩(Python)", "역사", "과학"], index=0)
    level = st.radio("학습자 레벨", ["초급", "중급", "고급"], horizontal=True)
    mode = st.selectbox("튜터 모드", ["설명 모드", "교정 모드", "소크라테스 모드", "퀴즈 모드"], index=0)
    target_lang = st.radio("답변 언어", ["한국어", "English"], horizontal=True)
    tone = st.selectbox("말투", ["따뜻하고 친절하게", "간결하고 직설적으로", "꼼꼼하고 자세하게"], index=0)

    temperature = st.slider("창의성(temperature)", 0.0, 2.0, 0.7, 0.1)
    max_tokens = st.slider("최대 응답 토큰", 64, 4096, 700, 64)

    col1, col2 = st.columns(2)
    with col1:
        new_chat = st.button("🧹 새 대화", use_container_width=True)
    with col2:
        show_meta = st.toggle("메타 표시", value=False)

# =========================
# 세션 상태
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "quiz" not in st.session_state:
    st.session_state.quiz = {
        "current": None,  # {"question":..., "choices":[], "answer":"B", "explanation":"..."}
        "score": 0,
        "total": 0,
        "last_result": None,  # ("정답"/"오답", 정답문자)
    }

if new_chat:
    st.session_state.messages = []
    st.session_state.quiz = {"current": None, "score": 0, "total": 0, "last_result": None}
    st.rerun()

# =========================
# 키 체크
# =========================
if not openai_api_key:
    st.info("🔑 좌측에서 OpenAI API 키를 입력해주세요.", icon="🗝️")

# =========================
# 기존 대화 렌더
# =========================
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# =========================
# 클라이언트
# =========================
client = OpenAI(api_key=openai_api_key) if openai_api_key else None

# =========================
# 퀴즈 모드 UI
# =========================
def render_quiz_ui():
    qstate = st.session_state.quiz
    if client is None:
        st.warning("🔑 퀴즈를 생성하려면 OpenAI API 키가 필요합니다.")
        return

    # 현재 문제가 없으면 생성
    if qstate["current"] is None:
        with st.spinner("퀴즈를 만드는 중..."):
            item = request_quiz_item(client, model, subject, level, target_lang, tone)
        if not item:
            st.error("퀴즈 생성에 실패했어요. 한 번 더 시도해 주세요.")
            return
        qstate["current"] = item

    item = qstate["current"]
    st.markdown(f"**문제:** {item['question']}")
    choice_labels = item.get("choices", [])
    if not choice_labels or len(choice_labels) < 4:
        st.error("퀴즈 형식이 올바르지 않습니다. 새 문제를 만들어 보세요.")
        if st.button("🔁 새 문제 만들기"):
            qstate["current"] = None
            st.rerun()
        return

    # 사용자의 선택
    selected = st.radio("정답을 고르세요:", choice_labels, index=None, key=f"quiz_select_{qstate['total']}")
    col_a, col_b = st.columns([1, 1])
    with col_a:
        submit = st.button("제출", use_container_width=True)
    with col_b:
        skip = st.button("다음 문제", use_container_width=True)

    if submit and selected:
        # 선택된 라벨에서 "A) " 등 접두 추출
        letter = selected.split(")")[0].strip().upper()[:1]
        correct = item["answer"].upper()
        qstate["total"] += 1
        if letter == correct:
            qstate["score"] += 1
            qstate["last_result"] = ("정답", correct)
            st.success(f"✅ 정답이에요! ({correct})")
        else:
            qstate["last_result"] = ("오답", correct)
            st.error(f"❌ 아쉬워요! 정답은 {correct} 입니다.")
        if item.get("explanation"):
            st.info(f"해설: {item['explanation']}")

        st.progress(qstate["score"] / max(qstate["total"], 1))
        st.caption(f"점수: {qstate['score']} / {qstate['total']}")

    if skip:
        qstate["current"] = None
        st.rerun()

# =========================
# 입력 처리
# =========================
if mode == "퀴즈 모드":
    render_quiz_ui()
else:
    # 일반 대화 입력창
    user_msg = st.chat_input("학습 질문을 입력하세요… (예: 현재완료 시제 설명해줘 / 문장 교정해줘)")
    if user_msg:
        # 사용자 메시지 저장/표시
        st.session_state.messages.append({"role": "user", "content": user_msg})
        with st.chat_message("user"):
            st.markdown(user_msg)

        # 시스템 프롬프트 + 히스토리
        sys_prompt = build_system_prompt(subject, level, mode, target_lang, tone)
        payload = [{"role": "system", "content": sys_prompt}]
        payload.extend(st.session_state.messages)

        with st.chat_message("assistant"):
            try:
                if client is None:
                    st.warning("🔑 OpenAI API 키를 먼저 입력해주세요.")
                    assistant_text = ""
                else:
                    stream = call_chat(
                        client=client,
                        model=model,
                        messages=payload,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stream=True,
                    )
                    assistant_text = st.write_stream(stream)
            except Exception as e:
                st.error(f"❗요청 중 오류가 발생했어요: {e}")
                assistant_text = ""

        st.session_state.messages.append({"role": "assistant", "content": assistant_text})

# =========================
# 메타데이터
# =========================
if show_meta:
    with st.expander("🔎 대화 설정 / 메타"):
        st.markdown(
            f"- **Model:** `{model}`\n"
            f"- **Subject:** `{subject}` · **Level:** `{level}` · **Mode:** `{mode}`\n"
            f"- **Language:** `{target_lang}` · **Tone:** `{tone}`\n"
            f"- **Temperature:** `{temperature}` · **Max tokens:** `{max_tokens}`\n"
            f"- **Messages:** `{len(st.session_state.messages)}`\n"
            f"- **Quiz Score:** `{st.session_state.quiz.get('score',0)}` / `{st.session_state.quiz.get('total',0)}`"
        )

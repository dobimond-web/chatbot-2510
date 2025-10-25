# streamlit_app.py
import json
from datetime import datetime
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="BX All-in-One Toolkit", page_icon="🧰", layout="wide")

# =========================
# 헤더
# =========================
st.title("🧰 BX All-in-One Toolkit")
st.caption("기업 정보를 바탕으로 BX 전 과정을 자동 기획 · 산출하는 브랜드 디자이너 도구")

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
        help="secrets.toml에 OPENAI_API_KEY 저장 시 자동 로드"
    )
    model = st.selectbox(
        "모델",
        ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"],
        index=0
    )
    temperature = st.slider("창의성(temperature)", 0.0, 2.0, 0.8, 0.1)
    max_tokens = st.slider("최대 토큰", 256, 4096, 1600, 64)

# =========================
# 입력 폼
# =========================
st.markdown("### 🧾 기본 정보 입력")
with st.form("brief_form"):
    col1, col2 = st.columns([1,1])
    with col1:
        company = st.text_input("기업명*", placeholder="예: 더바운스랩")
        industry = st.text_input("산업/카테고리", placeholder="예: 헬스케어 SaaS, 전통식품, 핀테크")
        region = st.text_input("시장/지역", placeholder="예: 한국, 동남아, 북미")
        competitors = st.text_area("경쟁사/레퍼런스", placeholder="경쟁사 또는 벤치마크 브랜드 리스트")
    with col2:
        target = st.text_area("타깃/세그먼트", placeholder="1차·2차 타깃, 페르소나 특징")
        request = st.text_area("요청사항(브리프)*", placeholder="요청 배경, 해결 과제, 성과 목표 등")
        constraints = st.text_area("제약/가드레일", placeholder="법규, 예산/일정 제한, 금지 요소 등")
    col3, col4, col5 = st.columns([1,1,1])
    with col3:
        mode = st.selectbox("프로젝트 유형", ["신규 브랜딩", "리브랜딩", "서비스 확장/하위브랜드"])
    with col4:
        tone = st.selectbox("브랜드 톤&매너", ["따뜻/친근", "기술/전문", "대담/혁신", "미니멀/정제"])
    with col5:
        depth = st.selectbox("디테일 수준", ["요약형", "표준형", "상세형"], index=1)

    submitted = st.form_submit_button("🚀 BX 자료 생성")

# =========================
# 유효성 체크
# =========================
if submitted and (not company or not request):
    st.warning("기업명과 요청사항(브리프)은 필수입니다.")
    submitted = False

# =========================
# OpenAI 클라이언트
# =========================
client = OpenAI(api_key=openai_api_key) if openai_api_key else None

# =========================
# 시스템 프롬프트 구성
# =========================
def build_system_prompt():
    return (
        "You are a senior brand strategist and BX architect. "
        "Produce rigorous, production-ready brand strategy & experience documentation in Korean. "
        "Use clear sectioning, bullets, and tables where helpful. Always provide practical examples."
    )

# =========================
# 사용자 프롬프트 구성
# =========================
def build_user_prompt():
    richness = {"요약형": "succinct with key bullets",
                "표준형": "balanced detail with examples",
                "상세형": "deep detail with frameworks, matrices and examples"}[depth]

    return f"""
다음 기업에 대해 BX 전 과정 문서를 만들어주세요. 산출물은 **한국어**로 작성하고 Markdown으로 구조화합니다.

[기업/시장 정보]
- 기업명: {company}
- 산업/카테고리: {industry or 'N/A'}
- 시장/지역: {region or 'N/A'}
- 경쟁/레퍼런스: {competitors or 'N/A'}
- 타깃/세그먼트: {target or 'N/A'}
- 프로젝트 유형: {mode}
- 요청사항/브리프: {request}
- 제약/가드레일: {constraints or 'N/A'}
- 톤&매너: {tone}
- 상세 수준: {depth} → {richness}

[필수 섹션]
1) 🔎 회사/시장/경쟁 분석  
   - 기업/제품 스냅샷, 고객/문제, 카테고리 정의, 트렌드/리스크  
   - 3C/4P 간단 정리, 경쟁 포지셔닝 맵(텍스트)  

2) 🎯 브랜드 전략(Brand Core)  
   - 미션/비전/가치(핵심행동 포함), 브랜드 개성/아키타입, 키워드/금지어  
   - 포지셔닝 스테이트먼트(For–Who–Unlike–We), 가치제안(Functional/Emotional)  

3) 🗣 메시징 시스템  
   - 메시지 피라미드(메인·세컨더리·증거), 톤 가이드(Do/Don't), 한 줄 슬로건 3안  
   - 엘리베이터 피치(30초/90초 버전)  

4) 🎨 아이덴티티 방향(디자인 가이드 초안)  
   - 무드보드 방향 2~3안(키워드/형용사, 레퍼런스 키워드)  
   - 로고 컨셉 가이드(형태/의미/확장성), 컬러 팔레트 제안(주/보조/경고/중립, 대비 비율)  
   - 타이포그래피(헤드/바디/코드, 한글·영문 페어링), 아이콘·일러스트·모션 원칙  
   - 접근성 체크(명도 대비·색맹 대응·폰트 크기/줄간격)  

5) 🧩 어플리케이션 적용 계획 (우선순위/난이도/효과 점수)  
   - 디지털: 웹/앱, 온보딩, 대시보드, 이메일, 랜딩, 마케팅 페이지  
   - 오프라인: 패키지, 리테일/사인, 행사·키트, 굿즈  
   - 커뮤니케이션: 소셜템플릿, 광고·배너, PR 키트, 세일즈덱, 문서템플릿  
   - 각 항목에 핵심 규칙(여백/그리드/모션/톤)과 예시 카피 1줄씩  

6) 🛤 브랜드 경험 여정 & 터치포인트 매트릭스  
   - 인지→고려→구매→온보딩→활용→유지·옹호 단계별 과업/감정/키콘텐츠/KPI  
   - 팀/채널/도구 책임 매핑(RACI 느낌으로 텍스트 표기)  

7) 🚀 론치/운영 플랜 & KPI  
   - 30/60/90일 플랜, 콘텐츠 캘린더 예시(주간), 캠페인 아이디어 3개  
   - 핵심 KPI·진단 질문, 리스크/대응, 실험 가설·측정(ICE 점수)  

8) 📦 산출물 체크리스트  
   - 브랜드 북(전략/디자인), 로고/컬러/폰트/아이콘, 모션/사진 가이드, 소셜/배너 키트  
   - 프리젠테이션 템플릿, 영수증/인보이스/문서 템플릿, 웹·앱 UI 키트(토큰 표기)  
   - 파일 구조/버전 관리 원칙(Git/Drive), 승인/거버넌스 프로세스  

9) 🔗 참고 사례/가이드 제안(텍스트 링크 목록)  
   - 유사 카테고리/톤의 **브랜드 사례** 5~8개(국내/해외 혼합 가능)  
   - **디자인 시스템/가이드** 3~5개(왜 참고하면 좋은지 한 줄 코멘트)

모든 항목은 실행 가능한 실무 수준으로 작성하고, 불확실한 가정은 합리적으로 명시하세요.
"""

# =========================
# 생성 실행
# =========================
if submitted:
    if not client:
        st.warning("🔑 OpenAI API 키를 입력해주세요.")
    else:
        with st.spinner("BX 자료 생성 중…"):
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": build_system_prompt()},
                    {"role": "user", "content": build_user_prompt()},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
        content = resp.choices[0].message.content
        st.success("완료! 아래 결과를 검토하세요.")
        st.markdown(content)

        # 다운로드
        colA, colB = st.columns(2)
        with colA:
            st.download_button(
                "💾 TXT로 저장",
                data=content,
                file_name=f"{company}_BX_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with colB:
            st.download_button(
                "💾 JSON로 저장",
                data=json.dumps({
                    "company": company, "industry": industry, "region": region,
                    "competitors": competitors, "target": target, "mode": mode,
                    "tone": tone, "depth": depth, "constraints": constraints,
                    "content": content
                }, ensure_ascii=False, indent=2),
                file_name=f"{company}_BX_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )

# =========================
# 참고할 만한 사례/가이드(큐레이션)
# – 아래 섹션은 고정 링크 큐레이션(모델 결과와 별개로 항상 표시)
# =========================
st.markdown("### 🔗 참고할 만한 사례/가이드 (큐레이션)")

refs_col1, refs_col2, refs_col3 = st.columns(3)
with refs_col1:
    st.markdown("- **Behance | Branding Case Studies** – 다양한 브랜드 케이스 스터디 모음")
    st.markdown("  - https://www.behance.net/search/projects/branding%20case%20study")
    st.markdown("- **Awwwards** – 트렌디한 웹/브랜딩 사이트")
    st.markdown("  - https://www.awwwards.com/websites/")

with refs_col2:
    st.markdown("- **Brand New (UnderConsideration)** – 리브랜딩 사례 리뷰")
    st.markdown("  - https://www.underconsideration.com/brandnew/archives/complete")
    st.markdown("- **BP&O** – 브랜딩/패키징 리뷰 & 인사이트")
    st.markdown("  - https://bpando.org/")

with refs_col3:
    st.markdown("- **Atlassian Design System** – 로고/토큰/콘텐츠 가이드")
    st.markdown("  - https://atlassian.design/")
    st.markdown("- **IBM Design Language** – 대규모 브랜드·이벤트 가이드")
    st.markdown("  - https://www.ibm.com/design/language/")
    st.markdown("- **Material Design 3** – 구글 디자인 시스템")
    st.markdown("  - https://m3.material.io/")
    st.markdown("- **Apple HIG – Branding**")
    st.markdown("  - https://developer.apple.com/design/human-interface-guidelines/branding")

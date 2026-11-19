# 글지기 — AI 글쓰기 멘토

Streamlit + Supabase + Gemini 기반의 개인화 글쓰기 멘토 웹앱입니다.

## 포함 기능
- 이메일 회원가입 / 로그인 / 로그아웃 (Supabase Auth)
- 글쓰기 상황과 조건을 반영한 글쓰기 설계
- 직접 작성한 글의 AI 코칭
- 사용자별 글쓰기 스타일 분석 및 저장
- 이전 글쓰기 설계안과 첨삭 결과 자동 저장 / 다시 보기
- 개인별 데이터 조회 (Supabase RLS 정책 전제)

## 1. 기존 프로젝트에서 가져올 것
기존 `.streamlit/secrets.toml` 파일은 덮어쓰거나 공유하지 마세요. 이 프로젝트의 `.streamlit/secrets.toml.example`을 참고해 다음 세 키가 설정되어 있는지 확인하세요.

```toml
SUPABASE_URL = "기존 Supabase 프로젝트 URL"
SUPABASE_KEY = "기존 Supabase 키"
GEMINI_API_KEY = "기존 Gemini API 키"
```

기존 Supabase 프로젝트와 로그인 계정을 그대로 사용하도록 설계했습니다.

## 2. 설치 및 실행

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## 3. Supabase 데이터 테이블
앱은 `style_profiles`와 `writing_records` 테이블을 사용합니다. 이미 기존 프로젝트에서 같은 이름과 컬럼으로 사용 중이라면 SQL을 실행할 필요가 없습니다. 테이블이 없다면 Supabase SQL Editor에서 `supabase_schema.sql`을 검토한 후 실행하세요.

- `style_profiles`: `user_id`, `style_data`
- `writing_records`: `user_id`, `kind`, `situation`, `settings`, `draft`, `feedback`, `created_at`

RLS(Row Level Security) 정책은 로그인한 사용자가 본인 데이터만 조회/추가/수정하도록 제한합니다.

## 4. Gemini 모델
기본 모델은 빠른 텍스트 작업을 위한 `gemini-3.5-flash-lite`입니다. 모델 이용 가능 여부와 API 한도는 Google AI Studio 프로젝트 설정에 따라 달라질 수 있습니다.

## 5. 배포
GitHub에 올릴 때 `.streamlit/secrets.toml`은 절대 업로드하지 마세요. Streamlit Community Cloud의 App settings → Secrets에 위 세 키를 등록하세요.

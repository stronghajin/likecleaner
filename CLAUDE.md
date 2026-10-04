# LikeCleaner — 작업 규칙

YouTube "좋아요 한 동영상"과 재생목록을 한 화면에서 보고 일괄 정리하는 웹 툴.
기획서 원본은 `docs/SPEC.md`, 기획서의 애매한 부분과 이후 변경에 대한 확정 사항은 `docs/DECISIONS.md`에 있다.

## 문서 우선순위

- `docs/DECISIONS.md`가 `docs/SPEC.md`보다 우선한다. 둘의 내용이 다르면 DECISIONS.md를 따른다.
- 그 밖의 경우는 SPEC.md가 판단의 기준이다.

## 사용자에 대해

- 사용자는 비개발자다. 설명은 쉬운 한국어로, 전문 용어는 꼭 필요할 때만 짧게 풀어서 쓴다.

## 개발 단계

- **Phase 1 (완료):** 프론트엔드와 mock 데이터로 모든 화면과 작업 흐름을 완성했다. 정리는 `docs/PHASE1_NOTES.md`.
- **Phase 2 (현재):** 백엔드(Python FastAPI + SQLite), Google OAuth, YouTube Data API를 붙인다. 단계별 계획은 `docs/PHASE2_PLAN.md`.
  - 순서: P2-1 기본 구조와 DB → P2-2 PoC → P2-3 로그인과 승인 → P2-4 조회 API → P2-5 작업 처리 → P2-6 프론트 교체 → P2-7 운영 마무리
  - 화면 동작은 Phase 1 결과를 기준으로 하고, 바꿔야 하면 먼저 묻는다.

## 폴더 구조

```
frontend/   # Phase 1 — React 앱
  src/services/   # 데이터 계층 (유일한 데이터 통로)
  src/pages/      # 화면 단위
  src/components/ # 공통 부품
  src/state/      # 로그인 상태, 할당량 등 여러 화면이 함께 쓰는 상태
backend/    # Phase 2 — FastAPI (구조는 아래 "백엔드 구조 원칙")
docs/       # 기획서
```

## 기술 스택

- frontend: React + Vite + TypeScript + Tailwind CSS + React Router
- backend: Python + uv, FastAPI, SQLAlchemy(async) + aiosqlite, alembic, httpx, aiosmtplib (DECISIONS.md 36–38)
  - 승인된 라이브러리 목록은 DECISIONS.md 37번. 테스트는 pytest + pytest-asyncio + respx
- 새 라이브러리를 추가해야 할 때는 이유를 먼저 설명하고 동의를 받는다.

## 비밀값

- `backend/.env`(Google 클라이언트 비밀번호, Gmail 앱 비밀번호, 토큰 암호화 키 등)와 DB 파일은 절대 git에 올리지 않는다. 예시는 `.env.example`에만 둔다.
- 사용자에게 비밀값을 대화창에 붙여 넣으라고 하지 않는다. `.env` 파일에 직접 넣도록 안내한다.
- 비밀값을 로그나 오류 메시지에 출력하지 않는다.

## 데이터 계층 (가장 중요한 구조 규칙)

- 모든 데이터 접근은 `frontend/src/services/` 폴더 하나를 통해서만 한다.
- 화면 컴포넌트는 데이터가 mock인지 실제 API인지 몰라야 한다.
  - 컴포넌트에서 mock 데이터 파일을 직접 import하지 않는다.
  - 컴포넌트에서 `fetch` 등 네트워크 호출을 직접 하지 않는다.
- services의 함수는 실제 API처럼 비동기(Promise)로 동작하고, 약간의 지연과 오류도 흉내 낼 수 있게 만든다.
- 데이터 타입(영상, 재생목록, 작업, 할당량 등)은 한 곳에 정의하고, 기획서 9장 테이블 구조와 맞춘다.
- Phase 2에서는 services 내부 구현만 실제 API 호출로 교체하고, 화면 코드는 바꾸지 않는 것이 목표다.
- mock 구현은 지우지 않는다. 개발 중에만 설정 하나로 mock / 실제 API를 바꿀 수 있고, DEV 패널은 mock 모드에서만 보인다. 운영 결과물에는 mock과 DEV 패널이 들어가지 않는다(DECISIONS.md 47).

## 백엔드 구조 원칙 (Phase 2에서 적용)

### 폴더

```
backend/app/
  api/           # 라우터
  services/      # 비즈니스 로직
  repositories/  # DB 접근
  clients/       # 외부 API (YouTube, Google OAuth, 메일 등)
  schemas/       # Pydantic 스키마
  models/        # SQLAlchemy 모델
  workers/       # 백그라운드 작업
  core/          # 설정 등 공통 기반
```

### 계층 규칙

- 호출 방향은 `api → services → repositories / clients` 한 방향만이다. 계층 건너뛰기 금지.
- api는 DB나 외부 API를 직접 호출하지 않는다.
- repositories와 clients에는 비즈니스 판단을 넣지 않는다.
- 계층 간 데이터는 반드시 Pydantic 스키마 객체로 전달한다. dict, ORM 객체, 외부 API 원본 JSON을 계층 밖으로 넘기지 않는다.
- 응답 스키마는 `frontend/src/services/types.ts`의 타입과 같은 구조로 맞춘다.

### 비동기 규칙

- 모든 계층 함수는 `async def`로 작성한다.
  - DB: SQLAlchemy `AsyncSession` + `aiosqlite`
  - 외부 API: `httpx.AsyncClient` (`google-api-python-client` 사용 금지)
  - 메일: `aiosmtplib`
- `time.sleep`, `requests` 같은 블로킹 코드는 금지한다.
- 일괄 작업 항목은 할당량과 속도 제한 때문에 순차 처리를 유지한다.

## UI와 디자인

- 화면에 보이는 모든 문구는 **영어**. 기획서에 정확한 문구가 있으면 그대로 쓴다.
- 데스크톱 전용. 모바일/반응형 대응은 하지 않는다.
- 색상은 기획서 11장의 Black Mode 색상**만** 사용한다. Tailwind 설정에 아래 이름으로 등록해 쓰고, 다른 색(Tailwind 기본 팔레트 포함)은 쓰지 않는다.

| 이름 | 값 | 용도 |
|---|---|---|
| `bg` | `#0A0A0A` | 배경 |
| `panel` | `#161616` | 카드, 패널 |
| `border` | `#2A2A2A` | 테두리 |
| `text` | `#F5F5F5` | 기본 텍스트 |
| `muted` | `#A1A1A1` | 보조 텍스트 |
| `accent` | `#FFFFFF` 배경 + `#0A0A0A` 텍스트 | 주요 버튼, 선택 상태 |
| `danger` | `#EF4444` | 경고, 오류, 할당량 부족, 파괴적 액션 최종 버튼 |
| `success` | `#22C55E` | 성공 |

- 라이트 모드는 만들지 않는다.
- 마우스 효과(DECISIONS.md 16번): 클릭할 수 있는 요소와 목록 행에는 반드시 호버 효과를 준다. 호버 색은 위 색상에 투명도만 조절해서 만든다(예: `hover:bg-text/5`, `hover:bg-accent/85`). 커서 글로우(`components/CursorGlow.tsx`)와 아이콘 꼬리(`components/CursorTrail.tsx`)는 앱 최상단에 한 번만 넣어 전체에 적용한다.
- 정보 밀도가 높은 데스크톱용 리스트 UI를 기준으로 한다.
- 화면 배치(DECISIONS.md 17): 왼쪽 사이드바(로고, `Liked Videos` / `Playlists`) + 상단 바(할당량, 프로필, `Sign out`). 공통 틀은 `components/AppLayout.tsx`.
- 모양(DECISIONS.md 19): 박스와 패널은 각진 모서리. 버튼과 입력칸만 `rounded-sm`. 버튼은 `components/Button.tsx`를 쓴다.
- 통계/항목 라벨(DECISIONS.md 20): `font-bold text-accent`(흰색 볼드).
- 로고 글꼴 Clash Display(`font-logo`)는 로고에만 쓴다(DECISIONS.md 18).

## 범위 관리

- 기획서에 없는 기능은 임의로 추가하지 않는다. 필요해 보이면 먼저 물어본다.
- 기획서 12장 "MVP 제외 범위"의 기능은 만들지 않는다.
- 기획서가 애매하거나 충돌하면 추측하지 말고 질문한다.

## Git

- 커밋할 때마다 GitHub(`origin`)에 push까지 한다.

## 작업 보고 방식

작업이 끝날 때마다 아래 두 가지를 알려준다.

1. **무엇을 바꿨는지** — 쉬운 말로 3줄 요약
2. **브라우저에서 확인할 것** — 실행 방법과 함께, 직접 눌러보고 확인할 수 있는 체크리스트

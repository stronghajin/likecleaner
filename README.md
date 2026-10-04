# LikeCleaner

YouTube "좋아요 한 동영상"과 재생목록을 한 화면에서 보고 한꺼번에 정리하는 웹 툴입니다.
지금은 **Phase 1**(가짜 데이터로 동작하는 화면) 단계입니다. 실제 YouTube 계정에는 아무 영향이 없습니다.

## 앱 실행하기

### 처음 한 번만: 준비물

- **Node.js**가 설치되어 있어야 합니다. 설치 여부는 아래 2단계에서 `node -v`를 입력해 확인할 수 있습니다. 버전 숫자(예: `v24.21.0`)가 나오면 설치된 것입니다. 설치되어 있지 않으면 https://nodejs.org 에서 **LTS** 버전을 받아 설치하세요.

### 1. 터미널 열기

둘 중 편한 방법을 쓰세요.

- **VS Code에서 (추천):** VS Code로 `likecleaner` 폴더를 연 상태에서, 위쪽 메뉴의 **Terminal → New Terminal**을 누릅니다. 단축키는 `Ctrl` + `` ` ``(숫자 1 왼쪽 키)입니다. 화면 아래쪽에 터미널이 열립니다.
- **Mac의 터미널 앱:** `Cmd` + `Space`를 누르고 `Terminal`을 입력한 뒤 `Enter`를 누릅니다.

### 2. 앱이 있는 폴더로 이동

터미널에 아래 한 줄을 그대로 입력하고 `Enter`를 누르세요.

```
cd ~/Desktop/likecleaner/frontend
```

> VS Code 터미널은 보통 이미 `likecleaner` 폴더에서 열리므로 `cd frontend`만 입력해도 됩니다.

### 3. (처음 한 번만) 필요한 파일 설치

```
npm install
```

1~2분 정도 걸릴 수 있습니다. 다시 설치할 필요는 없습니다. 다만 GitHub에서 새로 받은 직후나, 앱이 실행되지 않고 오류가 날 때는 한 번 더 해 주세요.

### 4. 앱 실행

```
npm run dev
```

잠시 뒤 터미널에 아래와 비슷한 줄이 나오면 실행된 것입니다.

```
➜  Local:   http://localhost:5173/
```

### 5. 브라우저에서 열기

Chrome 같은 브라우저 주소창에 아래 주소를 입력하세요.

```
http://localhost:5173
```

> 터미널의 주소를 `Cmd`를 누른 채 클릭해도 열립니다.

### 6. 종료하기

- 앱을 실행한 터미널을 클릭한 뒤 `Ctrl` + `C`를 누르면 종료됩니다. 터미널에 다시 명령어를 입력할 수 있는 상태가 되면 꺼진 것입니다.
- 터미널 창이나 VS Code를 닫아도 종료됩니다.
- 다시 켤 때는 2번(폴더 이동)과 4번(`npm run dev`)만 하면 됩니다.

## 백엔드 서버 실행하기 (Phase 2 개발 중)

Phase 2 작업이 끝나기 전까지 화면은 계속 가짜 데이터로 동작합니다. 백엔드는 따로 켜서 확인합니다.
파이썬 버전과 가상환경, 패키지 설치는 **uv**라는 도구가 한꺼번에 맡습니다(DECISIONS.md 36). 그래서 `pip`이나 `venv` 명령은 쓰지 않습니다.

### 1. 터미널 열기

**새 터미널**을 엽니다. 화면(`npm run dev`)을 켜 둔 터미널과는 다른 터미널이어야 합니다. VS Code에서는 터미널 오른쪽 위의 `+`를 누르면 됩니다.

### 2. uv 확인 (처음 한 번)

```
uv --version
```

`uv 0.x.x`처럼 버전이 나오면 됩니다. `command not found`가 나오면 `docs/PHASE2_PLAN.md`의 "A. uv 설치"를 먼저 하세요.

### 3. 백엔드 폴더로 이동

```
cd ~/Desktop/likecleaner/backend
```

### 4. Python 확인 (처음 한 번)

```
uv run python --version
```

`Python 3.13.x`가 나오면 됩니다. 컴퓨터에 원래 있던 파이썬(3.9)과는 별개로, uv가 이 프로젝트용 파이썬을 받아 둡니다. 처음에는 내려받느라 조금 걸릴 수 있습니다.

### 5. 가상환경 만들기 + 패키지 설치

처음 한 번, 그리고 GitHub에서 새로 받았거나 패키지 목록이 바뀌었을 때만 실행합니다.

```
uv sync
```

이 명령 하나로 두 가지가 됩니다.
- `backend/.venv` 폴더(이 프로젝트 전용 가상환경)를 만든다
- `pyproject.toml`에 적힌 패키지(FastAPI 등)를 설치한다

마지막 줄에 `Installed … packages`, `Audited … packages`, `Checked … packages` 중 하나가 나오면 끝입니다(이미 설치되어 있으면 Checked/Audited).

### 6. 설정 파일 확인 (처음 한 번)

`backend/.env` 파일이 있어야 합니다. 이 컴퓨터에는 이미 만들어 두었습니다. 다른 컴퓨터라면 `backend/.env.example`을 복사해 `.env`로 이름을 바꾸고, 각 줄 위의 설명대로 값을 채우세요. 이 파일은 GitHub에 올라가지 않으며, 내용을 다른 곳에 붙여 넣지 마세요.

### 7. 서버 켜기

```
uv run uvicorn app.main:app --reload --port 8000
```

`Application startup complete.`가 나오면 켜진 것입니다. 서버가 켜질 때 DB 파일(`backend/data/likecleaner.db`)과 테이블이 자동으로 만들어집니다.

### 8. 브라우저에서 확인

- http://localhost:8000/api/health → `{"status":"ok","database":"ok"}`
- http://localhost:8000/docs → API 목록 화면. 여기서 직접 시험해 볼 수 있습니다.
  1. `GET /api/health` 줄을 클릭해 펼칩니다.
  2. 오른쪽의 **Try it out** → 파란 **Execute** 버튼을 누릅니다.
  3. 아래 **Responses**에 `Code 200`과 `{"status": "ok", "database": "ok"}`가 나오면 정상입니다.

### 9. 끄기

서버를 켠 터미널에서 `Ctrl` + `C`를 누릅니다.

### 자주 생기는 문제

| 증상 | 해결 |
|---|---|
| `uv: command not found` | 2번 단계를 보세요. 설치 직후라면 터미널을 닫았다 다시 여세요 |
| `address already in use` | 서버가 이미 다른 터미널에서 켜져 있습니다. 그 터미널에서 `Ctrl` + `C`로 끄고 다시 켜세요 |
| `ValidationError` 또는 `.env` 관련 오류 | `backend/.env`의 값 형식이 틀렸습니다. `.env.example`의 설명과 비교해 보세요. 숫자 칸(`DAILY_QUOTA`)에 글자가 들어가지 않았는지 확인하세요 |
| `ModuleNotFoundError` | 5번(`uv sync`)을 다시 실행하세요 |

## 사용자 관리하기 (누가 LikeCleaner를 쓸 수 있는지)

LikeCleaner는 admin이 **미리 등록한 이메일만** 쓸 수 있습니다(DECISIONS 56). 등록되지 않았거나 막힌(disabled) 이메일로 로그인하면 "Access Denied" 화면이 나옵니다. 등록은 터미널에서 명령으로 합니다. 서버가 켜져 있든 꺼져 있든 상관없습니다.

먼저 새 터미널을 열고 백엔드 폴더로 이동합니다.

```
cd ~/Desktop/likecleaner/backend
```

| 하고 싶은 일 | 명령 |
|---|---|
| 이메일 등록 (바로 사용 가능) | `uv run python -m scripts.users add someone@gmail.com` |
| 사용 막기 | `uv run python -m scripts.users disable someone@gmail.com` |
| 다시 허용하기 | `uv run python -m scripts.users enable someone@gmail.com` |
| 등록된 사람 목록 보기 | `uv run python -m scripts.users list` |

- `someone@gmail.com` 자리에 실제 이메일을 넣으세요. 대문자와 소문자는 구분하지 않습니다.
- 막으면 그 사람이 로그인해 있어도 다음 화면 이동 때 바로 Access Denied가 됩니다.

성공하면 이런 글이 나옵니다.

```
Added someone@gmail.com (active). They can sign in now.
```

`list`는 한 사람당 한 줄로 이렇게 보여줍니다. 순서대로 이메일, 상태(`active` 사용 가능 / `disabled` 막힘), 로그인한 적이 있는지, YouTube 권한이 저장됐는지, 등록한 날짜입니다.

```
someone@gmail.com                        active    signed in before  YouTube connected      added 2026-10-04 19:10 KST
```

| 이런 글이 나오면 | 뜻 |
|---|---|
| `Error: someone@gmail.com is already registered.` | 이미 등록된 이메일입니다. `list`로 상태를 확인하세요 |
| `Error: someone@gmail.com is not registered.` | 등록된 적 없는 이메일입니다. 먼저 `add` 하세요 |
| `Error: '...' is not an email address.` | 이메일 형식이 아닙니다. 오타를 확인하세요 |

> 개발 중(테스트 상태, DECISIONS 51)에는 Google Cloud의 **대상 → 테스트 사용자**에도 그 이메일이 있어야 Google 로그인이 됩니다.

## 실제 로그인으로 실행하기 (Phase 2 개발 중)

`npm run dev`는 가짜 데이터(mock)로 돌아갑니다. 진짜 Google 로그인으로 보려면 **터미널 두 개**를 씁니다.

1. 첫 번째 터미널: 위 "백엔드 서버 실행하기"의 7번처럼 백엔드를 켭니다.
   ```
   cd ~/Desktop/likecleaner/backend
   uv run uvicorn app.main:app --reload --port 8000
   ```
2. 두 번째 터미널(VS Code 터미널 오른쪽 위 `+`): 화면을 실제 모드로 켭니다.
   ```
   cd ~/Desktop/likecleaner/frontend
   npm run dev:real
   ```
3. 브라우저에서 http://localhost:5173 을 엽니다. 실제 모드에서는 오른쪽 아래 **DEV** 버튼이 보이지 않습니다.

- 지금(P2-4)은 로그인과 **조회**(좋아요 목록, 재생목록, 할당량)까지 실제로 연결돼 있습니다. 좋아요 취소, 이동, 제거 같은 작업은 다음 단계(P2-5) 전까지 `not connected to the server yet` 오류로 나옵니다.
- 실제 모드에서 목록을 불러오면 YouTube 할당량을 씁니다. 좋아요 목록 전체(약 4,900개)는 1분 남짓 걸리고 약 200 units가 듭니다. 새로고침해도 서버가 기억하고 있으면 0 units입니다. `Resync`를 누를 때마다 다시 씁니다(DECISIONS 59).
- 반드시 **5173 주소**로 들어가세요. Google 로그인이 이 주소로 돌아오도록 등록돼 있습니다.
- 끌 때는 두 터미널에서 각각 `Ctrl` + `C`를 누릅니다.

## 앱 안에서 테스트하기

- `npm run dev`(mock 모드)에서는 화면 오른쪽 아래의 **DEV** 버튼으로 개발용 패널을 열 수 있습니다. 사용자 상태, 오류 상황, 남은 할당량을 바꿔 가며 테스트할 수 있습니다.
- 클릭해 볼 시나리오 10개는 [docs/TEST_SCENARIOS.md](docs/TEST_SCENARIOS.md)에 있습니다.
- 처음 상태로 되돌리려면 DEV 패널의 **Reset mock data**를 누르세요.

## 자주 생기는 문제

| 증상 | 해결 |
|---|---|
| `command not found: npm` | Node.js가 설치되지 않았습니다. "처음 한 번만: 준비물"을 보세요 |
| `Port 5173 is in use` 또는 다른 주소(5174 등)로 열림 | 이미 앱이 다른 터미널에서 실행 중입니다. 그 터미널에서 `Ctrl` + `C`로 끄거나, 터미널에 나온 새 주소로 들어가세요 |
| 브라우저에 "사이트에 연결할 수 없음" | 앱이 꺼져 있습니다. 4번(`npm run dev`)을 다시 실행하세요 |
| 화면이 이상하게 멈춤 | 브라우저 새로고침(`Cmd` + `R`). 그래도 안 되면 DEV 패널의 Reset mock data |

## 문서

| 파일 | 내용 |
|---|---|
| [docs/SPEC.md](docs/SPEC.md) | 기획서 원본 |
| [docs/DECISIONS.md](docs/DECISIONS.md) | 기획서 이후 확정한 결정 (SPEC.md보다 우선) |
| [docs/PHASE1_NOTES.md](docs/PHASE1_NOTES.md) | Phase 1 화면 흐름, 기획서와 달라진 점, 완료 기준 점검, Phase 2 주의 사항 |
| [docs/TEST_SCENARIOS.md](docs/TEST_SCENARIOS.md) | 직접 클릭해 볼 테스트 시나리오 10개 |
| [docs/PHASE2_PLAN.md](docs/PHASE2_PLAN.md) | Phase 2(백엔드, 실제 로그인/YouTube) 작업 계획과 직접 할 일 |
| [CLAUDE.md](CLAUDE.md) | 개발 작업 규칙 |

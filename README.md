# LikeCleaner

YouTube "좋아요 한 동영상"과 재생목록을 한 화면에서 보고 한꺼번에 정리하는 웹 툴입니다.
지금은 **Phase 2**(실제 Google 로그인과 YouTube 연결) 단계입니다. 운영 주소는 https://likecleaner.kknaks.cloud 입니다(2026-10-05 배포). 배포, 친구 등록, 백업은 [docs/DEPLOY_PLAN.md](docs/DEPLOY_PLAN.md)를 보세요. 아래는 이 컴퓨터에서 개발할 때 실행하는 방법입니다.

> ⚠️ **실제 모드에서 누르는 작업(좋아요 취소, 이동, 재생목록에서 제거)은 진짜 YouTube 계정을 바꿉니다.** 연습은 가짜 데이터 모드에서 하세요.

## 두 가지 실행 방법

| | 실제 모드 | 가짜 데이터 모드 (mock) |
|---|---|---|
| 무엇이 보이나 | 내 진짜 좋아요와 재생목록 | 만들어 둔 가짜 계정 |
| 켜는 것 | 백엔드 + 화면, **터미널 2개** | 화면만, 터미널 1개 |
| 화면 명령 | `npm run dev:real` | `npm run dev` |
| YouTube 할당량 | 씀 (목록 불러오기, 작업) | 안 씀 |
| 오른쪽 아래 DEV 버튼 | 없음 | 있음 (오류 상황 흉내 등) |

어느 쪽이든 브라우저 주소는 **http://localhost:5173** 하나입니다. 실제 모드에서는 화면이 `/api`로 시작하는 요청을 백엔드(8000번)로 넘겨줍니다.
두 모드를 바꾸는 설정은 `frontend/.env.real`의 `VITE_API_MODE=real` 하나이고, `npm run dev:real`이 이 설정을 씁니다(DECISIONS 47). 인터넷에 올릴 운영용 결과물(`npm run build`)에는 가짜 데이터와 DEV 패널이 아예 들어가지 않습니다(DECISIONS 64).

## 처음 한 번만: 준비

### 1. 터미널 열기

- **VS Code에서 (추천):** VS Code로 `likecleaner` 폴더를 연 상태에서 위쪽 메뉴의 **Terminal → New Terminal**을 누릅니다. 단축키는 `Ctrl` + `` ` ``(숫자 1 왼쪽 키)입니다. 터미널을 하나 더 열 때는 터미널 오른쪽 위의 `+`를 누릅니다.
- **Mac의 터미널 앱:** `Cmd` + `Space`를 누르고 `Terminal`을 입력한 뒤 `Enter`를 누릅니다.

### 2. 도구 확인

아래 두 줄을 하나씩 입력해 보세요. 버전 숫자가 나오면 설치된 것입니다.

```
node -v
uv --version
```

- `node`가 없으면 https://nodejs.org 에서 **LTS** 버전을 받아 설치합니다.
- `uv`가 없으면 `docs/PHASE2_PLAN.md`의 "A. uv 설치"를 따라 합니다. uv는 파이썬 버전, 가상환경, 패키지 설치를 한꺼번에 맡는 도구입니다(DECISIONS 36). 그래서 `pip`이나 `venv` 명령은 쓰지 않습니다.
- 설치한 직후라면 터미널을 닫았다가 다시 여세요.

### 3. 화면 쪽 설치

```
cd ~/Desktop/likecleaner/frontend
npm install
```

1~2분 걸릴 수 있습니다.

### 4. 백엔드 쪽 설치

```
cd ~/Desktop/likecleaner/backend
uv sync
```

`backend/.venv`(이 프로젝트 전용 파이썬 환경)를 만들고 필요한 패키지를 설치합니다. 처음에는 파이썬을 내려받느라 조금 걸릴 수 있습니다. 마지막 줄에 `Installed …`, `Audited …`, `Checked …` 중 하나가 나오면 끝입니다.

> 3, 4번은 GitHub에서 새로 받은 직후나 실행이 안 되고 오류가 날 때 한 번 더 해 주세요.

### 5. 설정 파일 확인

`backend/.env` 파일이 있어야 합니다. 이 컴퓨터에는 이미 있습니다. 다른 컴퓨터라면 `backend/.env.example`을 복사해 이름을 `.env`로 바꾸고, 각 줄 위의 설명대로 값을 채웁니다.
- 이 파일에는 비밀값이 들어 있습니다. GitHub에 올라가지 않으며, 내용을 대화창 같은 다른 곳에 붙여 넣지 마세요.
- 개인정보처리방침에 보이는 연락처 이메일은 이 파일의 `ADMIN_EMAIL`입니다(비우면 `hajin300@gmail.com`).

## 실제 모드로 켜기 (터미널 2개)

### 터미널 ①: 백엔드

```
cd ~/Desktop/likecleaner/backend
uv run uvicorn app.main:app --reload --port 8000
```

`Application startup complete.`가 나오면 켜진 것입니다. DB 파일(`backend/data/likecleaner.db`)과 테이블은 서버가 켜질 때 자동으로 준비됩니다. **이 터미널은 켜 둔 채로** 둡니다.

### 터미널 ②: 화면

터미널 오른쪽 위 `+`로 새 터미널을 열고:

```
cd ~/Desktop/likecleaner/frontend
npm run dev:real
```

`➜  Local:   http://localhost:5173/`이 나오면 됩니다.

### 브라우저

http://localhost:5173 을 열고 `Sign in with Google`을 누릅니다.
- 반드시 **5173 주소**로 들어가세요. Google 로그인이 이 주소로 돌아오도록 등록돼 있습니다.
- 로그인한 이메일이 등록돼 있어야 합니다(아래 "사용자 관리하기").

### 할당량 주의

YouTube는 하루에 쓸 수 있는 양(10,000 units, 미국 태평양 시간 자정에 초기화)이 정해져 있고, 이 앱을 쓰는 모두가 나눠 씁니다. 화면 위쪽에 오늘 남은 양이 보입니다.

| 하는 일 | 대략 |
|---|---|
| 로그인 후 좋아요 처음 불러오기 / Liked Videos `Resync` | 약 200 units (좋아요 약 5,000개 기준, 1분 남짓) |
| 새로고침 (서버가 목록을 기억하는 동안) | 0 |
| 재생목록 열기 / 재생목록 `Resync` | 50개당 약 2 units |
| 좋아요 취소, 재생목록에서 제거 | 영상 1개당 50 |
| 재생목록으로 이동 / 이동 + 좋아요 취소 | 영상 1개당 50 / 100 (+ 중복 확인 몇 units) |

- `Resync` 버튼에 마우스를 올리면 예상 소모량이 보입니다. 모자라면 버튼이 꺼집니다.
- **백엔드를 껐다 켜면** 서버가 기억하던 좋아요 목록이 사라져 다음 화면에서 약 200 units를 다시 씁니다. 작업이 도는 중에 끄면 그 작업은 중단 처리되고, 진행 패널의 `Retry Failed`로 이어서 할 수 있습니다(DECISIONS 63).

### 끄기

두 터미널에서 각각 `Ctrl` + `C`를 누릅니다. 다시 켤 때는 위 "터미널 ①", "터미널 ②"만 하면 됩니다.

## 가짜 데이터 모드로 켜기 (터미널 1개)

```
cd ~/Desktop/likecleaner/frontend
npm run dev
```

http://localhost:5173 을 엽니다. 백엔드는 켜지 않아도 됩니다.
- 화면 오른쪽 아래 **DEV** 버튼으로 개발용 패널을 열어 사용자 상태, 오류 상황(실패, 할당량 초과, 429), 남은 할당량을 바꿔 볼 수 있습니다.
- 처음 상태로 되돌리려면 DEV 패널의 **Reset mock data**를 누릅니다.
- 직접 해 볼 시나리오는 [docs/TEST_SCENARIOS.md](docs/TEST_SCENARIOS.md) 1부에 있습니다.

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

## 서버 상태 확인 (문제가 생겼을 때)

백엔드가 켜져 있을 때:
- http://localhost:8000/api/health → `{"status":"ok","database":"ok"}`이면 서버와 DB가 정상입니다.
- http://localhost:8000/docs → API 목록 화면입니다. 줄을 펼쳐 **Try it out → Execute**로 직접 시험할 수 있습니다.

## 자주 생기는 문제

| 증상 | 해결 |
|---|---|
| `command not found: npm` / `uv: command not found` | "처음 한 번만: 준비"의 2번을 보세요. 설치 직후라면 터미널을 닫았다 다시 여세요 |
| `Port 5173 is in use` 또는 다른 주소(5174 등)로 열림 | 화면이 이미 다른 터미널에서 켜져 있습니다. 그 터미널에서 `Ctrl` + `C`로 끄고 다시 켜세요 |
| `address already in use` (백엔드) | 백엔드가 이미 다른 터미널에서 켜져 있습니다. 그 터미널에서 `Ctrl` + `C`로 끄고 다시 켜세요 |
| 실제 모드 화면에 `The server is not responding.` | 백엔드(터미널 ①)가 꺼져 있습니다. 다시 켜세요 |
| 브라우저에 "사이트에 연결할 수 없음" | 화면(터미널 ②)이 꺼져 있습니다 |
| 로그인 화면에 `Your session has ended. Please sign in again.` | 로그인 기간(7일)이 지났거나 Google 쪽 권한이 끊겼습니다. 다시 로그인하세요. 개발 중(테스트 상태)에는 Google 권한이 7일마다 끊깁니다(DECISIONS 51) |
| `ValidationError` 또는 `.env` 관련 오류 | `backend/.env`의 값 형식이 틀렸습니다. `.env.example`의 설명과 비교해 보세요 |
| `ModuleNotFoundError` | 백엔드 폴더에서 `uv sync`를 다시 실행하세요 |
| 가짜 데이터 모드 화면이 이상하게 멈춤 | 브라우저 새로고침(`Cmd` + `R`). 그래도 안 되면 DEV 패널의 Reset mock data |

## 문서

| 파일 | 내용 |
|---|---|
| [docs/SPEC.md](docs/SPEC.md) | 기획서 원본 |
| [docs/DECISIONS.md](docs/DECISIONS.md) | 기획서 이후 확정한 결정 (SPEC.md보다 우선) |
| [docs/PHASE1_NOTES.md](docs/PHASE1_NOTES.md) | Phase 1 화면 흐름, 기획서와 달라진 점, 완료 기준 점검, Phase 2 주의 사항 |
| [docs/PHASE2_NOTES.md](docs/PHASE2_NOTES.md) | Phase 2에서 기획서와 달라진 점, 완료 기준 다시 점검, 남은 과제 |
| [docs/TEST_SCENARIOS.md](docs/TEST_SCENARIOS.md) | 직접 해 볼 테스트 시나리오 (1부: 가짜 데이터, 2부: 실제 계정과 예상 할당량) |
| [docs/PHASE2_PLAN.md](docs/PHASE2_PLAN.md) | Phase 2(백엔드, 실제 로그인/YouTube) 작업 계획과 직접 할 일 |
| [docs/POC_RESULTS.md](docs/POC_RESULTS.md) | 실제 YouTube로 미리 확인한 결과 |
| [docs/DEPLOY_PLAN.md](docs/DEPLOY_PLAN.md) | 배포 계획: 확정한 구성(Vercel + 홈서버), 자동 배포 흐름, 백업, 친구 사용 시 할당량, 할 일, 공유 체크리스트, 남은 질문 |
| [CLAUDE.md](CLAUDE.md) | 개발 작업 규칙 |

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

**처음 한 번만:** uv가 설치되어 있어야 합니다. 터미널에 `uv --version`을 입력했을 때 버전 숫자가 나오면 됩니다. 안 나오면 `docs/PHASE2_PLAN.md`의 "A. uv 설치"를 따라 하세요.

1. **새 터미널**을 엽니다. 화면(`npm run dev`)을 켜 둔 터미널과는 다른 터미널이어야 합니다. VS Code에서는 터미널 오른쪽 위의 `+`를 누르면 됩니다.
2. 백엔드 폴더로 이동합니다.
   ```
   cd ~/Desktop/likecleaner/backend
   ```
3. 서버를 켭니다. 처음에는 필요한 파일을 받느라 조금 걸립니다.
   ```
   uv run uvicorn app.main:app --reload --port 8000
   ```
   `Application startup complete.`가 나오면 켜진 것입니다.
4. 브라우저에서 확인합니다.
   - http://localhost:8000/api/health → `{"status":"ok","database":"ok"}`
   - http://localhost:8000/docs → API 목록 화면
5. 끄기: 그 터미널에서 `Ctrl` + `C`

> 비밀 설정값은 `backend/.env`에 있습니다. 이 파일은 GitHub에 올라가지 않으며, 내용을 다른 곳에 붙여 넣지 마세요.

## 앱 안에서 테스트하기

- 화면 오른쪽 아래의 **DEV** 버튼으로 개발용 패널을 열 수 있습니다. 승인 상태, 오류 상황, 남은 할당량을 바꿔 가며 테스트할 수 있습니다.
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

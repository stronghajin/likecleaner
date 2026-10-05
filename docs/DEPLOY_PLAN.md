# 배포 계획 (DEPLOY_PLAN)

목표: 나와 친구 몇 명이 인터넷에서 LikeCleaner를 쓸 수 있게 하기.
작성: 2026-10-05, 갱신: 2026-10-06 (첫 배포와 실제 계정 테스트 완료).
**2026-10-05 첫 배포를 마쳤습니다.** 화면 https://likecleaner.kknaks.cloud , 백엔드 https://likecleaner-api.kknaks.cloud . 레포 주인 계정으로 로그인과 정리 작업까지 확인했습니다. 친구 공유 전에 할 일(6장 7·8·11번)과 7장의 질문이 남아 있습니다.

| 파일 | 무엇 |
|---|---|
| `backend/Dockerfile`, `backend/.dockerignore` | 백엔드 도커 이미지 |
| `deploy/docker-compose.prod.yml` | 홈서버에서 컨테이너 실행 설정(포트 48200, `data/`·`backups/` 연결) |
| `.github/workflows/deploy-backend.yml` | 백엔드 자동 배포 |
| `.github/workflows/manage-users.yml` | 사용자 등록 버튼 |
| `backend/scripts/backup.py` | DB 백업(14일 보관) |
| `frontend/vercel.json` | Vercel의 `/api` 넘김, 화면 주소 처리 |
| `backend/.env.prod` | 운영 설정 원본(git에 올라가지 않음, 직접 작성) |

- 최초 배포는 kknaks가 완성하고, 그 뒤 관리(새 버전 올리기, 친구 등록)는 이 레포 주인이 GitHub 화면에서 합니다.
- 비용과 정책 중 확실하지 않은 것은 **(확인 필요)**로 표시했습니다.
- 관련 문서: 남은 과제는 `PHASE2_NOTES.md` 4장, Google 설정 기록은 `PHASE2_PLAN.md` B·F, 실제 계정 테스트는 `TEST_SCENARIOS.md` 2부.

## 1. 확정한 구성 (DECISIONS 65)

```
브라우저 ──https──▶ likecleaner.kknaks.cloud        화면 (Vercel)
                         │  /api/* 요청은 Vercel이 그대로 넘겨줌
                         ▼
                   likecleaner-api.kknaks.cloud    백엔드 (kknaks 홈서버)
                         │  Nginx Proxy Manager(HTTPS) → 서버 48200번 포트
                         ▼
                   docker 컨테이너 1개 (uvicorn worker 1개)
                         │
                   /home/kknaks/likecleaner/data/likecleaner.db   SQLite (서버 디스크에 영구 보관)
```

| 항목 | 결정 |
|---|---|
| 화면 | Vercel. 레포 주인 계정으로 이 레포를 연결. `main`에 push하면 화면이 자동으로 새로 올라감 |
| 백엔드 | kknaks 홈서버의 docker 컨테이너 1개. 서버 포트 `48200` → 컨테이너 `8000` |
| DB | SQLite 그대로. 서버 폴더 `/home/kknaks/likecleaner/data`를 컨테이너의 `/app/data`에 연결(bind mount)해서, 컨테이너를 새로 만들어도 DB 파일이 남음 |
| 주소 | 화면 `https://likecleaner.kknaks.cloud`, 백엔드 `https://likecleaner-api.kknaks.cloud` |
| 주소 하나처럼 쓰기 | 브라우저는 화면 주소만 씀. 화면 주소의 `/api/*`를 Vercel이 백엔드 주소로 넘겨줌(rewrite). 그래서 로그인 쿠키와 Google 로그인 돌아오는 주소가 모두 화면 주소 하나로 동작하고, CORS 설정이 필요 없음 |
| 백엔드 배포 | GitHub Actions. `main`에 백엔드 관련 파일이 바뀌어 push되면 자동 배포. 수동 실행(이전 버전으로 되돌리기)도 가능 |
| 도커 이미지 | GitHub Actions에서 만들어 GitHub 이미지 저장소(GHCR, `ghcr.io/stronghajin/likecleaner-api`)에 올림. 홈서버는 받아서 실행만 함 |
| 비밀값 | GitHub Secrets. 운영 설정 전체를 `ENV_PROD` 하나에 넣고, 배포할 때마다 서버의 `.env`로 씀 |

**왜 SQLite로 충분한가:** 이 앱은 좋아요 목록, 작업 진행 상황, 동시 실행 잠금이 서버 메모리에 있어서 원래 서버 1대·프로세스 1개로만 돌 수 있습니다(DECISIONS 58, 63). 여러 서버가 DB 하나를 나눠 쓰는 일이 없고, DB에 쓰는 것도 사용자·토큰·작업 기록·할당량 기록뿐이라 양이 적습니다. 할당량(하루 10,000 units) 때문에 하루 작업 수 자체가 작습니다. API와 백그라운드 작업이 동시에 읽고 쓰는 부분은 이미 WAL 모드로 되어 있습니다(`backend/app/core/db.py`).

## 2. 이 구성이 지키는 배포 조건

| 조건 | 왜 | 어떻게 |
|---|---|---|
| 서버 프로세스는 딱 하나 | 메모리 상태(좋아요 목록, 작업, 잠금)가 프로세스마다 따로 생기면 안 됨(DECISIONS 58, 63) | 컨테이너 1개, uvicorn worker 1개로 고정 |
| 항상 켜져 있음 | 작업은 몇 분씩 서버 안에서 돌고, 30일 삭제도 서버 안에서 매일 돎 | 홈서버 컨테이너, 꺼지면 자동으로 다시 켜짐(`restart: unless-stopped`) |
| DB 파일은 영구 보관 | 등록된 사용자, 암호화된 refresh token, 작업·할당량 기록 | bind mount(`/home/kknaks/likecleaner/data`). 배포해도 그대로 |
| 백업 | DB가 없어지면 모두 다시 등록·로그인, 오늘 쓴 할당량 기록도 사라짐 | 4장 |
| HTTPS | Google 로그인은 운영 주소에 https 필요. `APP_BASE_URL`이 `https://`이면 쿠키에 Secure가 붙음(DECISIONS 57) | 화면은 Vercel 인증서, 백엔드는 Nginx Proxy Manager의 Let's Encrypt 인증서 |
| 화면 주소 하나 | 로그인 쿠키(`SameSite=Lax`)와 Google 리디렉션이 한 주소에서 동작해야 함 | Vercel rewrite(1장). 개발 중 Vite 프록시와 같은 구조 |
| 비밀값은 git에 안 올림 | CLAUDE.md "비밀값" | GitHub Secrets. 운영용 키는 새로 만들고 DB도 새로 시작(사용자는 다시 등록) |
| 화면 수정은 백엔드를 건드리지 않음 | 백엔드가 재시작되면 메모리가 비어 할당량을 다시 씀(5장) | 화면은 Vercel, 백엔드 자동 배포는 백엔드 관련 파일이 바뀔 때만 |

## 3. 자동 배포 흐름 (GitHub Actions)

### 백엔드 배포 (`deploy-backend`)

- **언제:** `main`에 push됐는데 `backend/` 또는 배포 설정 파일이 바뀐 경우. 화면(`frontend/`)이나 문서만 바뀐 push에는 돌지 않음
- **수동 실행:** GitHub → Actions → 실행. 이전 버전 번호(커밋 SHA)를 넣으면 그 버전으로 되돌림

```
1. 도커 이미지 만들기 (GitHub 서버에서, linux/amd64)
2. GHCR에 올리기: likecleaner-api:<커밋 SHA>, likecleaner-api:latest
3. 홈서버에 SSH로 접속
4. Secret ENV_PROD 내용을 /home/kknaks/likecleaner/.env 로 쓰기
5. 배포 설정 파일(`deploy/docker-compose.prod.yml`) 받기
6. 새 이미지 받아서 컨테이너 교체 (DB 구조는 서버가 켜질 때 자동으로 맞춤, DECISIONS 50)
7. `/api/health`가 60초 안에 응답하는지 확인. 응답이 없으면 실패로 표시하고 서버 로그를 보여줌
```

만들기(1~2)가 실패하면 3번 이후로 가지 않으므로, 지금 돌고 있는 서버는 그대로입니다.

### 사용자 관리 (`manage-users`)

- GitHub → Actions → 실행에서 동작(`add` / `disable` / `enable` / `list`)과 이메일을 넣고 누름
- 서버 컨테이너 안에서 `python -m scripts.users ...`를 실행하고 결과를 실행 기록에 보여줌
- 터미널이나 서버 접속 없이 친구를 등록할 수 있음

### 필요한 GitHub Secrets

| 이름 | 내용 | 누가 넣나 |
|---|---|---|
| `ENV_PROD` | 운영 설정 전체(아래 표). `backend/.env.prod` 파일 내용을 통째로 붙여 넣음 | kknaks |
| `PROD_SSH_HOST` | 홈서버 주소 | kknaks |
| `PROD_SSH_USER` | 홈서버 SSH 사용자 | kknaks |
| `PROD_SSH_KEY` | 홈서버 SSH 키 | kknaks |

`ENV_PROD`에 들어가는 값 (`backend/.env.example` 기준, `backend/.env.prod`에 작성):

| 이름 | 운영 값 |
|---|---|
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Google Cloud 클라이언트 값 |
| `ADMIN_EMAIL` | 개인정보처리방침 연락처(7장 질문 2) |
| `TOKEN_ENCRYPTION_KEY` | 운영용으로 새로 만듦 |
| `SESSION_SECRET` | 운영용으로 새로 만듦 |
| `DAILY_QUOTA` | `10000` |
| `DATABASE_URL` | `sqlite+aiosqlite:////app/data/likecleaner.db` (컨테이너 안 경로 = 서버의 `data/` 폴더) |
| `APP_BASE_URL` | `https://likecleaner.kknaks.cloud` (화면 주소. Google 리디렉션도 이 주소로 옴) |

`SMTP_*`는 쓰지 않으므로 넣지 않습니다(DECISIONS 56).

> ⚠️ **`TOKEN_ENCRYPTION_KEY`는 한 번 쓰기 시작하면 바꾸지 않습니다.** 바뀌면 저장된 refresh token을 못 읽어 모두 다시 로그인해야 합니다. GitHub Secret은 저장한 뒤 다시 볼 수 없으므로, `backend/.env.prod` 원본(git에 올라가지 않음)을 안전한 곳에 따로 보관하고 Secret을 고칠 때는 원본을 통째로 다시 붙여 넣습니다. `SESSION_SECRET`이 바뀌면 모두 로그아웃될 뿐입니다.

### Vercel 설정

- 레포 연결 시 Root Directory는 `frontend`, 빌드 명령은 `npm run build`, 결과 폴더는 `dist`
- `frontend/vercel.json`:
  - `/api/*` → `https://likecleaner-api.kknaks.cloud/api/*`로 넘김
  - 그 밖의 주소(`/privacy`, `/denied` 등)는 `index.html`로 보냄(화면 안에서 주소를 처리하므로)
- 좋아요 불러오기와 작업은 시작 요청 후 진행 상황을 따로 묻는 방식이라(DECISIONS 48, 59), Vercel이 넘겨주는 요청이 오래 걸리는 경우는 없음

## 4. 백업

- **방식:** SQLite 공식 백업 방식(`.backup`)으로 사본을 만든다. WAL 모드라서 DB 파일을 그냥 복사하면 깨진 사본이 될 수 있다. 명령은 `docker exec likecleaner-api python -m scripts.backup`(`backend/scripts/backup.py`)
- **주기:** 홈서버 cron에 하루 1번 위 명령을 등록, `/home/kknaks/likecleaner/backups/`에 날짜별로 보관하고 14일 지난 것은 지움. 운영 DB(`data/likecleaner.db`)는 계속 유지되고, 지우는 것은 백업 사본뿐
- **왜 14일인가:** 개인정보처리방침에서 작업·할당량 기록은 30일, "YouTube API 데이터는 30일 넘게 보관하지 않음", 계정 삭제 시 토큰과 작업 기록을 지운다고 약속했다. 백업 사본에도 같은 데이터가 들어 있으므로 30일보다 짧게 둔다
- **복구 방법:** 홈서버 `/home/kknaks/likecleaner`에서 `docker compose --env-file .env -f docker-compose.prod.yml stop` → `data/likecleaner.db`를 백업 파일로 바꾸고 `data/likecleaner.db-wal`, `data/likecleaner.db-shm`을 지움 → `... up -d`
- **복구 연습:** 첫 배포 뒤 1번. 위 방법으로 바꿔 넣고 로그인이 되는지 확인
- 좋아요 목록 자체는 DB에 없으므로(DECISIONS 58) 잃는 것은 등록 사용자, 토큰, 작업·할당량 기록

## 5. 친구가 쓸 때 하루 할당량 (프로젝트 전체 10,000 units/일, 태평양 시간 자정 초기화)

가정 (좋아요가 많은 사용자 기준, 좋아요가 적으면 불러오기 비용은 훨씬 작음: 1,000개면 약 42 units):
- 좋아요 불러오기 = 약 200 (로그인 후 서버 메모리가 비어 있을 때: 처음, 로그아웃 후, **서버 재시작 후**, 7일 뒤)
- `Resync` 1번 = 약 200
- 작업 = 항목당 50 (이동+좋아요 취소는 100)

| 사용 패턴 (1인 하루) | 1인 units | 5명 | 10명 |
|---|---|---|---|
| 가볍게: 불러오기 1 + 10개 정리 | 200 + 500 = 700 | 3,500 (35%) | 7,000 (70%) |
| 보통: 불러오기 1 + Resync 1 + 20개 정리 | 400 + 1,000 = 1,400 | 7,000 (70%) | **14,000 (초과)** |
| 몰아서: 불러오기 1 + 100개 좋아요 취소 | 200 + 5,000 = 5,200 | **26,000 (초과)** | **52,000 (초과)** |
| 이동+좋아요 취소 100개 | 200 + 10,000 | 1명이 하루 한도를 다 씀 | |

- 정리 작업 자체가 대부분을 씀. 100개 일괄 작업 1번(5,000~10,000)이면 그날 다른 사람은 거의 못 씀.
- 할당량이 바닥나면 그날은 모두 작업 중단, 다음날 태평양 자정(한국 오후 4~5시)에 초기화.

**백엔드 자동 배포와 할당량:** 백엔드가 새로 배포될 때마다 서버 메모리가 비워집니다. 그래서 사용자마다 다음 접속 때 좋아요를 다시 불러오고(약 200 units), 진행 중이던 작업은 중단 처리됩니다(`Retry Failed`로 이어서 하기, DECISIONS 63). 백엔드 변경은 **사람들이 안 쓰는 시간에 `main`에 올리는 것**을 권합니다. 화면만 바꾸는 것은 상관없습니다.

**줄이는 방법 (7장 질문 3에서 결정)**

| 방법 | 절약 | 단점 / 바뀌는 것 |
|---|---|---|
| ① 로그아웃해도 좋아요 목록을 서버 메모리에 유지(최대 7일 또는 서버 재시작까지) | 다시 로그인할 때마다 약 200 | 개인정보처리방침 문구 수정 필요("로그아웃하면 지움" → "최대 7일 메모리"). DB에는 여전히 저장 안 함 |
| ② 1인 하루 사용 한도(예: 2,000 units) | 한 사람이 전체를 다 쓰는 것 방지 | 새 기능(기획서에 없음). 한도 안내 문구 필요 |
| ③ 친구에게 "하루 50개 정도씩" 사용 안내 | 코드 변경 없음 | 지켜 줄지는 사람에 달림 |
| ④ Google에 할당량 증가 신청 | 한도 자체를 늘림 | 신청서·심사 필요, 승인 보장 없음 **(확인 필요)** |
| ⑤ 백엔드 변경은 밤에 `main`에 올리기 | 재시작마다 사용자당 약 200 | 운영 습관 |

추천 조합: ① + ③ + ⑤. ②는 친구가 늘면 검토.

## 6. 할 일 (순서)

| # | 할 일 | 누가 |
|---|---|---|
| 1 | 배포용 코드: Dockerfile, `deploy/docker-compose.prod.yml`, GitHub Actions 2개(백엔드 배포, 사용자 관리), `frontend/vercel.json`, 백업 스크립트 → 커밋 | ✅ 2026-10-05 |
| 2 | 홈서버: 도메인 연결(`likecleaner`, `likecleaner-api`), Nginx Proxy Manager에 `likecleaner-api.kknaks.cloud` → 48200 + 인증서, 백업 cron(`docker exec likecleaner-api python -m scripts.backup`). 폴더 `/home/kknaks/likecleaner`는 첫 배포가 만듦 | ✅ 2026-10-05 |
| 3 | `backend/.env.prod` 작성(운영용 키 새로 생성) → GitHub Secrets에 `ENV_PROD`, `PROD_SSH_*` 넣기 | ✅ 2026-10-05 |
| 4 | 첫 백엔드 배포 → `https://likecleaner-api.kknaks.cloud/api/health`가 ok | ✅ 2026-10-05 |
| 5 | Vercel 가입, 이 레포 연결(Root Directory `frontend`), 도메인 `likecleaner.kknaks.cloud` 추가. Vercel이 요구한 CNAME과 `_vercel` TXT를 dnszi에 등록 | ✅ 2026-10-05 |
| 6 | Google Cloud: 클라이언트 `likecleaner-local` 편집(또는 운영용 새 클라이언트) → 승인된 리디렉션 URI에 `https://likecleaner.kknaks.cloud/api/auth/google/callback` 추가 | ✅ 2026-10-05 |
| 7 | Google Cloud: 브랜딩 — 홈페이지 `https://likecleaner.kknaks.cloud`, 개인정보처리방침 `https://likecleaner.kknaks.cloud/privacy`, 승인된 도메인 `kknaks.cloud`. 로고는 올리지 않음(DECISIONS 51). 도메인 소유 확인(Search Console)이 요구되면 kknaks가 함 **(확인 필요)** | 레포 주인 + kknaks |
| 8 | Google Cloud: 대상 → **앱 게시**(In production). `youtube` 범위는 민감한 범위라 검증 없이는 "Google에서 확인하지 않은 앱" 화면이 나옴(7장 질문 4). 검증 안 된 앱의 사용자 수 상한(약 100명) **(확인 필요)**. 게시 후 테스트 사용자 제한과 7일 토큰 만료가 없어지는지 확인(SPEC 14장 PoC 2번) | 레포 주인 |
| 9 | Actions `manage-users`로 내 이메일 등록 → 운영 주소로 로그인 → `TEST_SCENARIOS.md` 2부 일부(R1, R2, R6, R7 + 작업 2~3개) | ✅ 2026-10-05 (로그인, YouTube 연결, 좋아요·재생목록 조회, 작업 8번과 Retry 1번, 서버 오류 없음) |
| 10 | 백업 확인: 다음날 백업 파일이 생겼는지, 복구 연습 1번 | 백업은 2026-10-06 04:00에 자동으로 생김. 복구 연습은 남음 |
| 11 | 친구 공유 — 8장 체크리스트 | 레포 주인 |

## 7. 아직 정할 것 (질문)

1. **친구 수**: 처음에 몇 명인가요? (5명 이하면 할당량이 대체로 버팀)
2. **연락처 이메일 공개**: 개인정보처리방침에 `hajin300@gmail.com`이 공개돼도 되나요, 아니면 별도 이메일을 만들까요?
3. **할당량 절약**: ① "로그아웃해도 목록 유지"를 할까요? ② 1인 하루 한도를 둘까요(둔다면 몇 units)?
4. **"확인되지 않은 앱" 경고**: 경고 화면을 감수하고 검증 없이 갈까요? (검증은 몇 주 걸리고 요구 사항이 많아 MVP에서는 제외, 기획서 3-1)

## 8. 친구에게 공유하기 전 체크리스트

**내가 할 일**
- [ ] 친구의 Google 계정 이메일(로그인할 그 계정)을 받아 GitHub → Actions → `manage-users` → `add` + 친구 이메일
- [ ] 같은 곳에서 `list`로 `active` 확인
- [ ] 개인정보처리방침의 연락처 이메일이 공개돼도 괜찮은지 확인(`ADMIN_EMAIL`)
- [ ] 오늘 남은 할당량 확인(내가 많이 쓴 날은 피하기)

**친구에게 보낼 안내문 (초안, 한국어)**
> LikeCleaner 주소: https://likecleaner.kknaks.cloud
> 1. `Sign in with Google`을 누르고, 알려 준 그 Google 계정으로 로그인해.
> 2. **"Google에서 확인하지 않은 앱"** 화면이 나오면 왼쪽 아래 **고급(Advanced)** → **LikeCleaner(으)로 이동(안전하지 않음)**을 눌러. 내가 만든 개인 앱이라 Google 심사를 받지 않아서 나오는 화면이야.
> 3. YouTube 권한 화면에서 체크하고 **계속**. 좋아요와 재생목록을 읽고 바꾸는 데만 써.
> 4. 처음 들어가면 좋아요 목록을 불러오는 데 1분 정도 걸려.
> 5. ⚠️ 좋아요 취소, 이동, 재생목록 제거는 **진짜 YouTube 계정을 바꿔**. 처음엔 2~3개로 해 봐.
> 6. YouTube 하루 사용량을 모두가 나눠 써. **하루 50개 정도씩** 정리해 주고, 할당량 부족이 뜨면 다음날 오후 4~5시 이후에 다시 해 줘.
> 7. 그만 쓰고 싶으면 https://myaccount.google.com/permissions 에서 LikeCleaner 권한을 지우고, 기록 삭제는 나한테 말해 줘.

## 9. 처음 비교했던 방법 (기록)

처음 계획에서는 아래 셋을 비교하고 Fly.io를 추천했습니다. kknaks 홈서버(이미 docker, Nginx Proxy Manager, `kknaks.cloud` 도메인을 운영 중)를 쓸 수 있게 되어 1장 구성으로 바꿨습니다.

| | A. Fly.io | B. 작은 VPS | C. 내 맥 + 터널 |
|---|---|---|---|
| 요약 | 컨테이너 호스팅, 업체가 서버 관리 | 리눅스 서버를 빌려 직접 관리 | 개발용 맥을 터널로 인터넷에 연결 |
| 월 비용(대략) | $3~6 | $4~7 | $0 + 도메인 |
| 안 고른 이유 | 비용과 도메인이 따로 필요. 홈서버로 비용 0, 도메인 이미 있음 | 서버 보안·관리를 직접 해야 함 | 맥이 꺼지거나 잠자면 서비스 중단, 개발과 운영이 섞임 |

홈서버의 위험: 정전이나 집 인터넷 장애 때 서비스가 멈춤. 친구 몇 명이 쓰는 규모라 감수합니다.

## 10. 첫 배포 때 겪은 것 (2026-10-05)

- **dnszi 반영 지연:** dnszi 화면에 레코드를 저장해도 네임서버에 나오기까지 몇 분 걸렸다(영역 번호 SOA serial이 바뀌어야 반영된 것). 반영 전에 주소를 열어 보면 그 "없음" 답을 KT DNS(168.126.63.1)가 **최대 2시간** 기억해서, 다른 DNS에서는 열리는데 내 컴퓨터에서만 `Can't reach`가 나왔다. 새 주소를 만들 때는 dnszi 반영을 확인한 뒤에 열어 보고, 이미 막혔으면 컴퓨터 DNS를 `8.8.8.8`로 바꾸고 캐시를 비운다(`sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder`).
- **Vercel 도메인 소유 확인:** `kknaks.cloud`가 다른 Vercel 계정에서도 쓰여서, 레포 주인 계정에 연결할 때 `_vercel` TXT 레코드를 요구했다.
- **백업 파일 이름:** 컨테이너 시계가 UTC라서 새벽 4시(KST) 백업이 전날 날짜로 저장됐다. `scripts/backup.py`가 한국 날짜로 이름을 짓도록 고쳤다.
- **로그의 404:** 백엔드 주소에 `/.env`, `/` 같은 자동 스캔 요청이 계속 들어온다. 없는 주소라 404로 끝나며 문제 없다.

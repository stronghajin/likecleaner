# Phase 2 작업 계획

백엔드(FastAPI + SQLite), Google OAuth, YouTube Data API를 붙여 실제로 동작하게 만드는 단계의 계획이다.
기준 문서는 `CLAUDE.md`, `docs/SPEC.md`, `docs/DECISIONS.md`(SPEC보다 우선), `docs/PHASE1_NOTES.md`다.

---

## 1. 단계별 계획

| 단계 | 하는 일 | 완료 기준 | 사용자가 할 일 |
|---|---|---|---|
| **P2-1 기본 구조와 DB** | `backend/` uv 프로젝트, 설정(`.env`) 읽기, 비동기 DB 연결, 테이블(기획서 9장 + DECISIONS 42), alembic 첫 이력, 공통 오류 응답 `{status, reason, message}`, `/api/health`, 테스트 틀 | 서버가 켜지고 `/api/health` 응답, DB 파일 생성, 테스트 통과 | A |
| **P2-2 PoC 검증** (완료, `POC_RESULTS.md`) | 기획서 14장 5가지를 실제 계정으로 확인. `clients` 계층(Google 로그인, YouTube, 메일)을 먼저 만들어 그것으로 검증. 결과는 `docs/POC_RESULTS.md`, 설계 변경은 DECISIONS.md에 기록 | 5가지 결과 기록. 특히 삭제/비공개 영상 판정 방법, `position=0` 오류 여부. 14장 2번은 테스트 상태로 확인하고, In production 확인은 P2-7(DECISIONS 51) | B, C, D, 브라우저 로그인 |
| **P2-3 로그인과 사용자 관리** | 2단계 Google 로그인(기본 정보 → `active`만 YouTube 권한, 처음 한 번, DECISIONS 56·57), 7일 세션 쿠키(44), `/api/me`, 로그아웃, refresh token 암호화 저장과 갱신, 권한 끊김 시 재동의(45), `active` 검사, 사용자 관리 명령(`scripts/users.py`), 화면은 로그인만 실제 연결(`npm run dev:real`) | 등록 안 됨 → Access Denied(내 이메일) → `add` → YouTube 권한 → 메인 화면 → `disable` → Access Denied → `enable` | E, 내 계정으로 확인 |
| **P2-4 조회 API** (완료) | `GET /api/likes`(끝 페이지까지, 최근 약 1,000개 DECISIONS 52 + 카테고리 이름, 서버 메모리 보관, DECISIONS 46), `/api/playlists`, `/api/playlists/{id}/items`(+ `videos.list`, DECISIONS 6), `/api/quota`(태평양 시간 하루). 실패 호출을 포함한 모든 호출의 units 기록 | 실제 계정의 좋아요와 재생목록 수가 YouTube와 같고, 할당량이 실제 호출량과 맞음 | 화면 숫자 비교 |
| **P2-5 작업 처리** (구현 완료, 실제 계정 확인 중. 작업 버튼의 화면 연결을 P2-6에서 앞당김) | `POST /api/jobs`(1인 1작업, 100개, 할당량 예상 검사, DECISIONS 30), 워커(사용자별 동시 진행, 항목은 순차, DECISIONS 41). 처리 규칙은 아래 참고 | 자동 테스트로 규칙 확인 + 실제 계정에서 2~3개 소량 실행 | 테스트 계정 확인 |
| **P2-6 프론트엔드 교체** | (작업 생성·Retry Failed·진행 조회, 조회 간격 1.5초, DECISIONS 55의 화면 갱신은 P2-5에서 먼저 함) services에 실제 API 구현 추가, 설정 하나로 mock / 실제 전환(DECISIONS 47), `signIn`을 Google 페이지 이동으로, Vite 프록시(DECISIONS 35), 로그인 만료 시 로그인 화면, 조회 간격 1.5초(48) | `TEST_SCENARIOS.md` 중 실제 계정으로 가능한 것이 그대로 동작 | 화면 확인 |
| **P2-7 운영 마무리** | 배포처 결정과 배포(HTTPS, DECISIONS 34), FastAPI가 화면 파일도 제공(35), 운영 주소로 Google 설정과 앱 게시(DECISIONS 51, 기획서 14장 2번 확인), 30일 데이터 매일 삭제 확인, DB 백업, 로그, PHASE1_NOTES 4장 "공개 배포 전" 확인 | 지인 계정이 실제 주소로 가입 → 승인 → 정리 작업 완료 | 호스팅 가입, F, 지인 테스트 |

P2-5 처리 규칙:
- 이미 있는 영상 건너뛰기(기획서 6-6)
- 맨 앞 추가 실패(`manualSortRequired`) 시 위치 없이 재추가
- 롤백과 `Rollback failed`
- 429는 2/4/8초 재시도(DECISIONS 28)
- quotaExceeded면 중단하고 남은 항목 `not_processed`
- `Retry Failed`
- 서버가 재시작되면 진행 중이던 작업은 중단 처리하고 `Retry Failed`로 이어서 하게 함(DECISIONS 63, "이어서 처리"를 대체)
- 30일 지난 데이터 매일 삭제

---

## 2. backend 폴더 구조

```
backend/
├─ pyproject.toml / uv.lock     # 라이브러리 목록 (uv)
├─ .env.example                 # 설정 예시 (git에 올림)
├─ .env                         # 실제 비밀값 (git에 올리지 않음)
├─ alembic.ini, alembic/versions/
├─ data/likecleaner.db          # SQLite (git에 올리지 않음)
├─ app/
│  ├─ main.py                   # 앱 시작점, 시작 시 워커 실행
│  ├─ core/        config.py · db.py · security.py · errors.py · time.py
│  ├─ api/         deps.py · auth.py · me.py · quota.py · likes.py · playlists.py · jobs.py · health.py
│  ├─ services/    auth_service · user_service · quota_service
│  │               likes_service · playlist_service · job_service · job_processor
│  ├─ repositories/ user_repository · token_repository · quota_repository · job_repository
│  ├─ clients/     google_oauth_client · youtube_client · mail_client   (httpx / aiosmtplib)
│  ├─ schemas/     common(camelCase 기본형, ErrorResponse) · user · quota · video · playlist · job · auth · youtube
│  ├─ models/      user · oauth_token · quota_usage · job
│  └─ workers/     job_worker · cleanup_worker   (services만 호출)
├─ scripts/
│  ├─ users.py                  # 사용자 관리 명령: add / disable / enable / list (DECISIONS 56)
│  └─ poc/                      # P2-2 검증 스크립트
└─ tests/                       # pytest + respx
```

- 호출 방향은 `api / workers → services → repositories / clients` 한 방향이다.
- DB 행(models)과 외부 API 원본 JSON은 각각 repositories와 clients 안에서 Pydantic 스키마로 바뀐 뒤에만 밖으로 나간다.

---

## 3. 예시 흐름: 좋아요 취소 3개

1. **브라우저:** `POST /api/jobs` `{"type":"remove_like","videoIds":[…]}`
2. **api/jobs.py:** 다음 순서로 처리한다.
   - JSON을 `CreateJobRequest`로 검사
   - 쿠키로 `CurrentUser` 확인
   - `job_service.create_job(CurrentUser, CreateJobRequest)` 호출
3. **services/job_service.py:** 작업을 시작해도 되는지 판단한다.
   - 진행 중 작업 확인: `job_repository.get_running` → `JobRecord | None`
   - 100개 이하인지, 할당량이 충분한지: `quota_service.units_left` → `QuotaStatus`
   - 제목은 서버 메모리의 좋아요 목록(`VideoResponse`)에서 가져옴
   - 저장: `job_repository.create(JobCreate)` → `JobRecord`
   - `JobResponse`로 바꿔 api에 반환
4. **repositories/job_repository.py:** DB 행을 저장한 뒤 `JobRecord`로 바꿔 돌려준다. ORM 객체는 밖으로 내보내지 않는다.
5. **api:** `JobResponse`를 camelCase JSON으로 응답한다.
6. **workers/job_worker.py → services/job_processor.py:** 항목마다 다음을 반복한다.
   - access token 준비: `auth_service.get_access_token` → `token_repository.get` → `StoredToken` → 복호화 → `google_oauth_client.refresh` → `AccessToken`
   - `youtube_client.rate_video(...)` → `YouTubeCallResult`(실패 시 `ApiErrorInfo`)
   - 사용량 기록: `quota_repository.record(QuotaUsageCreate)`
   - 결과에 따라 `job_repository.update_item(JobItemUpdate)` 또는 429 대기(`asyncio.sleep`) 또는 중단
7. **브라우저:** 1.5초마다 `GET /api/jobs/latest`로 `JobResponse`를 받아 진행 패널을 갱신한다.

---

## 4. 프론트 타입 ↔ 백엔드 스키마

백엔드는 `snake_case`로 쓰고, 응답 JSON은 자동으로 `camelCase`로 내보내 `frontend/src/services/types.ts`와 같은 모양을 만든다.

| `types.ts` | 백엔드 스키마 | 엔드포인트 | 출처 / 메모 |
|---|---|---|---|
| `User`, `UserStatus` | `UserResponse`, `UserStatus` | `GET /api/me` | `users` |
| `Quota` | `QuotaResponse` | `GET /api/quota` | `quota_usage` 합계, 태평양 시간 자정 리셋 |
| `Video` | `VideoResponse` | `GET /api/likes` | `videos.list` + `videoCategories.list`, DB 저장 안 함 |
| `Playlist` | `PlaylistResponse` | `GET /api/playlists` | `playlists.list` |
| `PlaylistItem`, `VideoAvailability` | `PlaylistItemResponse`, `VideoAvailability` | `GET /api/playlists/{id}/items` | `playlistItems.list` + `videos.list`, 판정은 PoC 3 |
| `JobType`, `JobStatus`, `JobItemStatus` | 같은 이름의 Literal | | 값은 DECISIONS 42 |
| `ApiErrorInfo` | `ErrorResponse` | 모든 오류 응답 | `{status, reason, message}` |
| `JobItem` | `JobItemResponse` | 작업 응답 안 | `job_items` |
| `Job`, `Job.rateLimit` | `JobResponse`, `RateLimitInfo` | `POST /api/jobs`, `POST /api/jobs/{id}/retry`, `GET /api/jobs/latest` | `jobs` + `job_items` |
| `CreateJobInput` | `CreateJobRequest` (요청, `type`으로 구분) | `POST /api/jobs` | |

---

## 5. 사용자가 직접 할 일

| 기호 | 할 일 | 언제 |
|---|---|---|
| A | uv 설치 | P2-1 전 |
| B | Google Cloud 설정 | P2-2 전 |
| C | 테스트용 YouTube 계정 준비 | P2-2 전 |
| D | Gmail 앱 비밀번호 발급 | P2-2 전 |
| E | 사용자 관리 명령 사용 | P2-3 |
| F | 운영 주소용 Google 설정 | P2-7 |

### A. uv 설치

1. Claude Code 입력칸에 입력: `! curl -LsSf https://astral.sh/uv/install.sh | sh`
2. VS Code 터미널을 닫았다 다시 연다.
3. `! uv --version` → 버전 숫자가 나오면 완료.

### B. Google Cloud 설정

메뉴 이름은 바뀔 수 있다. 다르게 보이면 캡처해서 보낸다.
1. https://console.cloud.google.com → `hajin300@gmail.com` 로그인
2. 프로젝트 선택 상자 → **새 프로젝트** → 이름 `likecleaner` → **만들기** → 그 프로젝트 선택
3. **API 및 서비스 → 라이브러리** → `YouTube Data API v3` → **사용**
4. **Google 인증 플랫폼**(예전 "OAuth 동의 화면") → **시작하기**
   - 앱 이름 `LikeCleaner`, 지원 이메일 `hajin300@gmail.com`
   - 대상 **외부(External)**
   - 연락처 이메일 입력 → 동의 → **만들기**
5. **데이터 액세스** → **범위 추가 또는 삭제**
   - `openid`, `userinfo.email`, `userinfo.profile`, `auth/youtube` 체크 → **업데이트** → **저장**
6. **대상(Audience)** → **테스트 사용자** → **Add users** → 테스트용 YouTube 계정(C)과 `hajin300@gmail.com` 추가 → **저장**
   - 게시 상태는 **테스트 중**으로 둔다. 게시는 P2-7에서 한다(DECISIONS 51).
   - 브랜딩에 로고를 올리지 않는다(올리면 앱 검증이 필요해진다).
7. **클라이언트** → **클라이언트 만들기** → **웹 애플리케이션**, 이름 `likecleaner-local`
   - 승인된 리디렉션 URI: `http://localhost:5173/api/auth/google/callback` → **만들기**
8. 클라이언트 ID와 보안 비밀번호를 `backend/.env`의 `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`에 **직접** 붙여 넣는다(대화창에 붙여 넣지 않음).

### C. 테스트용 YouTube 계정 (DECISIONS 43)

1. 테스트 계정은 기존 계정 `hajin300@gmail.com`을 쓴다(DECISIONS 43). 실제로 바꾸는 시험은 2~3개 소량으로만 한다.
2. YouTube에서 영상 10개 이상에 좋아요가 눌려 있는지 확인한다.
3. 재생목록 2개를 만든다: `LC Test 1`은 기본(수동 정렬), `LC Test 2`는 정렬을 "추가된 날짜" 등 자동 정렬로 바꾼다.
4. 한 재생목록에 같은 영상을 두 번 넣는다.

### D. Gmail 앱 비밀번호 (DECISIONS 40)

1. https://myaccount.google.com → **보안** → **2단계 인증** 켜기(꺼져 있다면)
2. https://myaccount.google.com/apppasswords
3. 앱 이름 `LikeCleaner` → **만들기**
4. 16자리 비밀번호를 `backend/.env`의 `SMTP_APP_PASSWORD`에 바로 붙여 넣는다(다시 볼 수 없음).

### E. 사용자 관리 (DECISIONS 56)

README의 "사용자 관리하기"를 따른다. 테스트 상태 동안에는 Google Cloud 테스트 사용자에도 같은 이메일을 넣는다(DECISIONS 51).

### F. 운영 주소용 Google 설정

P2-7에서 배포처를 정한 뒤 안내한다. 이때 브랜딩에 홈페이지와 개인정보처리방침 주소, 승인된 도메인을 넣고 **대상 → 앱 게시**로 프로덕션 단계(In production)로 바꾼다(기획서 3-1, DECISIONS 51).

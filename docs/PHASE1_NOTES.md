# Phase 1 정리 노트

Phase 1(프론트엔드 + mock 데이터)에서 만든 화면 흐름, 기획서와 달라진 점, Phase 2에서 주의할 점을 정리한다.
결정의 자세한 내용은 `DECISIONS.md`에 있고, 이 문서는 번호로만 연결한다. 두 문서가 다르면 DECISIONS.md를 따른다.

---

## 1. 화면별 UI 흐름

### 로그인 전후 (Landing / Pending Approval / Access Denied / Privacy Policy)

- `/`(Landing): 로고, 서비스 소개 한 줄, `Sign in with Google`, 정책 링크. 로그인하면 승인 상태에 따라 이동한다.
  - approved → `/liked`, pending → `/pending`, rejected → `/denied`
- 로그인 상태에서 다른 주소를 직접 입력하면 자기 상태에 맞는 화면으로 돌려보낸다. 없는 주소는 `/`로 보낸다.
- `/privacy`: 로그인 여부와 상관없이 열린다. 오른쪽 위 `Back`은 `/`로 가므로, 로그인한 사용자는 자기 화면으로 돌아간다.
- 모든 화면 아래쪽에 Privacy Policy, YouTube Terms of Service, Google Privacy Policy 링크가 있다.

### 공통 틀 (로그인 후)

- 왼쪽 사이드바: 로고와 메뉴 `Liked Videos` / `Playlists` (DECISIONS 17)
- 상단 바: 남은 할당량, 진행 바, 리셋까지 남은 시간 / 작업 진행 표시(작업이 있을 때) / 프로필, `Sign out`
- 할당량은 30초마다, 그리고 할당량을 쓰는 동작 직후에 새로 읽는다.

### Liked Videos

1. 로그인 직후 좋아요 목록 전체를 한 번 불러와 계속 보관한다. 메뉴를 오가도 다시 불러오지 않는다.
2. 위쪽부터 다음 순서로 놓인다.
   - 검색, 채널, 카테고리, 정렬, `Reset filters`
   - `Select all` / `Deselect all` / (채널 필터 중) `Select all from this channel`
   - 개수 표시, Rows per page, 페이지 번호, `Resync` (DECISIONS 23)
   - 목록
3. 체크박스나 줄을 클릭해 선택한다. 최대 100개까지 고를 수 있고(DECISIONS 1, 2), 선택하면 하단 액션 바가 나타난다.
   - 액션 바: `N selected` · `Remove Like` · `Move to Playlist` · `Clear selection` (DECISIONS 26)
4. `Remove Like` → 확인 창 → 작업 시작
5. `Move to Playlist` → 재생목록 선택 창 → 이동 방식 창(`Move and Remove Likes` / `Move Only` / `Cancel`) → 작업 시작
6. 모든 확인 창에는 다음이 들어 있다(DECISIONS 29).
   - 예상 units
   - 할당량이 모자랄 때의 빨간 경고와 `Keep first N only`
   - ✕로 뺄 수 있는 선택 목록
7. 작업을 시작하면 선택이 해제되고(DECISIONS 31), 진행 패널이 열린다.

### Playlists

1. 처음 들어오면 재생목록 목록을 불러온다. 왼쪽에서 재생목록 하나를 고르면 오른쪽에 그 영상들이 나온다.
2. 검색, 필터, 정렬은 없다(DECISIONS 5). 대신 선택 버튼, `Remove Duplicates`, `Remove Unavailable Videos`, 페이지 이동, `Resync`가 있다.
3. 자동 선택 버튼은 대상을 고르기만 하고 바로 지우지 않는다. 선택된 상태로 보여준 뒤 하단 바의 `Remove Selected` → 확인 창 → 작업 순서로 진행한다.
4. 자동 선택은 100개까지만 고르고, 넘는 경우 안내한다(DECISIONS 7). 다른 재생목록을 열면 선택이 해제된다(DECISIONS 32).

### 작업 진행 (모든 일괄 작업 공통)

- 오른쪽 아래 진행 패널(DECISIONS 11)에 다음이 나온다.
  - 진행률
  - Success / Failed / Skipped 개수와 not processed 개수
  - 실패 항목 목록(제목 + `Error 코드 · reason · 메시지`)
  - `Retry Failed (N)`
- 상단 바의 진행 표시를 눌러 패널을 열고 닫는다. 작업이 끝난 뒤에는 패널 밖을 클릭해도 닫힌다(DECISIONS 27).
- 작업 중에는 새 액션과 `Resync`를 막는다(SPEC 8-1, DECISIONS 13).
- 좋아요가 취소된 영상과 재생목록에서 제거된 항목은 진행 중에 바로 목록에서 빠진다.
- 429가 나면 "Rate limited. Retrying in N s..."를 보여주며 자동으로 다시 시도한다(DECISIONS 28).
- 작업을 멈추게 한 오류(quotaExceeded, 재시도 후에도 실패한 429)만 팝업으로 띄운다(DECISIONS 9).
- 새로고침하거나 탭을 다시 열면 가장 최근 작업을 보여준다(DECISIONS 12). 진행 중이면 이어서 진행한다.

### DEV 패널 (개발 중에만, Phase 2에서 제거)

모든 화면 오른쪽 아래의 `DEV` 버튼으로 연다(DECISIONS 14, 22, 25, 28). 다음을 바꿀 수 있다.
- 승인 상태
- 작업 실패 모드
- 다음 작업의 429
- 남은 할당량
- mock 데이터 초기화

---

## 2. SPEC.md와 달라진 점

| SPEC.md | Phase 1 구현 | DECISIONS |
|---|---|---|
| 5장: 공통 헤더에 탭(`Liked Videos` / `Playlists`) | 왼쪽 사이드바 메뉴 + 상단 바 | 17 |
| 6-3: 페이지네이션 옆 `Resync` (위치 미정) | 리스트 **위**에 배치 | 23 |
| 6-4: `Deselect all`은 현재 페이지만 | 그대로 두고, 전체 해제용 `Clear selection` 추가 | 26 |
| 6-2: 필터/정렬 (유지 여부 미정) | 메뉴를 오가도 유지, `Reset filters` 추가 | 24 |
| 6-1: 썸네일 120×90 | 화면에는 80×60으로 표시 | 33 |
| 4-3: 예상치는 최대치 기준 | Move 계열에 자동 정렬 재생목록 대비 +50 units | 30 |
| 4-4: 선택을 줄이면 다시 계산 | 확인 창 안에서 ✕ / `Keep first N only`로 줄이며 즉시 재계산 | 29 |
| 7-2: 같은 기준 적용 | Playlists에는 검색/필터/정렬 없음, 카테고리/길이 칸은 표시 | 5, 6 |
| 7-2: 자동 선택 (100개 초과 시 미정) | 앞 100개만 선택하고 안내 | 7 |
| 8-2: 진행 화면 (패널 또는 모달) | 오른쪽 아래 패널 + 상단 진행 표시 | 11, 27 |
| 8-2: `Retry Failed` 대상 | Failed + Not processed (Rollback failed 제외) | 10 |
| 8-3: API 오류(403, 429 등)마다 팝업 | 작업을 멈춘 오류만 팝업, 나머지는 실패 목록에 표시 | 9 |
| 8-3: 429 처리 (미정) | 2/4/8초 자동 재시도 3회 후 중단 | 28 |
| 8-1: 다시 접속 시 결과 확인 | 가장 최근 작업 하나만 표시 | 12 |
| 11장: 디자인 | 마우스 효과, 로고 글꼴, 각진 박스, 흰색 볼드 라벨 추가 | 16, 18, 19, 20 |
| (기획서에 없음) | 개발용 DEV 패널 | 14, 22, 25, 28 |
| (기획서에 없음) | 작업 시작 시 선택 해제, 재생목록 전환 시 선택 해제 | 31, 32 |

---

## 3. Acceptance Criteria 점검 (기획서 13장)

Phase 1(mock) 기준이다. "부분 충족"은 화면과 흐름은 완성됐지만 실제 서버나 YouTube로 검증해야 하는 항목이다.

| 기준 | 판정 | 이유 |
|---|---|---|
| 승인되지 않은 사용자는 Pending Approval 화면을 보고, admin은 메일로 요청 알림을 받는다 | 부분 충족 | Pending 화면과 이동은 완성. admin 메일 발송은 백엔드(Phase 2) |
| 승인된 사용자만 좋아요 목록과 재생목록을 볼 수 있다 | 부분 충족 | 화면 이동 차단과 mock 서버의 승인 확인은 완성. 실제 권한 검사는 Phase 2 백엔드 |
| 좋아요 영상 전체를 작은 썸네일 리스트로 볼 수 있다 | 충족 | 전체를 불러와 목록으로 표시. 썸네일은 mock 이미지(실제 이미지는 Phase 2) |
| 제목 검색, 채널, 카테고리로 좁히고 길이와 업로드 날짜로 정렬 | 충족 | |
| Resync로 최신 상태를 다시 불러온다 | 충족 | |
| 최대 100개를 골라 좋아요 취소 또는 재생목록 이동 | 충족 | |
| 이미 재생목록에 있는 영상은 중복으로 추가되지 않는다 | 충족 | mock에서 `Skipped` 처리 확인. 실제 API 동작은 Phase 2에서 재확인 |
| "이동 + 좋아요 취소"에서 한 단계만 성공한 상태로 남지 않는다 | 부분 충족 | 되돌리기(롤백)와 `Rollback failed` 표시는 mock에서 동작. 실제 YouTube API로 검증 필요 |
| 재생목록에서 중복, 삭제/비공개, 선택 영상을 제거할 수 있다 | 부분 충족 | 화면과 흐름 완성. 삭제/비공개 영상이 실제 응답에서 어떻게 오는지는 SPEC 14장 PoC 3번 확인 필요 |
| 오늘 남은 할당량과 실행 전 예상 소모량을 항상 볼 수 있다 | 충족 | |
| 할당량이 부족하면 실행할 수 없고, 몇 개까지 처리 가능한지 안내받는다 | 충족 | 경고 + 버튼 비활성화 + 확인 창 안에서 줄이기와 즉시 재계산(DECISIONS 29) |
| 작업 진행률, 성공/실패 개수를 보고, 실패 항목만 다시 실행 | 충족 | 429 자동 재시도와 중단 후 `Retry Failed` 포함(DECISIONS 28) |
| 탭을 닫았다 다시 열어도 작업 결과를 확인할 수 있다 | 부분 충족 | mock은 같은 브라우저 저장소로 흉내 냄. 다른 기기나 브라우저까지 이어지는 것은 Phase 2 서버 작업 처리 |

미충족 항목은 없다. "부분 충족" 6개는 모두 Phase 2(백엔드, 실제 API) 작업으로 완성된다.

---

## 4. Phase 2에서 주의할 점

### 데이터 계층 교체

- 교체 대상은 `frontend/src/services/index.ts`의 `api = mockApi` 한 곳이다. 각 함수가 바뀔 엔드포인트, YouTube API, units는 `frontend/src/services/api.ts`의 주석에 있다.
- 백엔드 응답은 `frontend/src/services/types.ts`와 같은 구조로 만든다(CLAUDE.md). 특히 다음 필드를 맞춘다.
  - `Job.rateLimit`(429 대기 중 표시용)
  - `Job.fatalError`
  - `JobItem.error`의 `{ status, reason, message }`
- `signIn()`은 mock에서는 `Promise<User>`지만, 실제로는 Google 로그인 페이지로 이동하는 방식이다. services 쪽 구현과 로그인 화면의 처리를 함께 바꿔야 한다.
- DEV 패널(`components/DevPanel.tsx`), `devTools`, `services/mock/` 폴더를 삭제한다. 브라우저에 남은 mock 저장값(`likecleaner.mock.*`)도 정리한다.

### 할당량

- 실패한 호출과 429 재시도 호출도 `quota_usage`에 기록한다(SPEC 4-1, DECISIONS 28).
- 하루 기준은 미국 태평양 시간 자정이다. 화면은 백엔드가 주는 `resetsAt`을 그대로 쓴다.
- 예상치 계산식(`services/quotaEstimate.ts`)과 백엔드의 실행 전 검사가 같은 결과를 내야 한다. Move 계열의 +50도 포함한다(DECISIONS 30).
- 재생목록 항목 조회에는 카테고리와 길이를 위한 `videos.list`가 추가로 든다(DECISIONS 6).

### 작업 처리

- 작업과 항목은 `jobs` / `job_items` 테이블에 저장하고, 백그라운드 워커가 한 항목씩 순서대로 처리한다(CLAUDE.md 비동기 규칙).
- 429 대기는 반드시 `asyncio.sleep`으로 한다. `time.sleep` 금지.
- 자동 정렬 재생목록의 `manualSortRequired`는 한 번 거절되면 그 재생목록에 대해 기억해 두고, 같은 작업 안에서 위치 지정을 다시 시도하지 않는다(DECISIONS 30).
- 진행 화면은 0.7초마다 최신 작업을 조회한다. 서버 부담을 보고 1~2초로 늘려도 화면은 그대로 동작한다.
- `Remove Duplicates`는 재생목록 위치(position)상 가장 앞의 하나를 남긴다. 화면이 받은 목록 순서가 실제 재생목록 순서와 같아야 한다.

### 먼저 검증할 것 (SPEC 14장 PoC)

- 좋아요 목록이 끝까지 조회되는지
- 검증 전 "In production" 상태에서 refresh token이 정상 발급되는지
- 삭제/비공개 영상이 응답에 어떻게 표시되는지 → `PlaylistItem.availability` 판정 방식이 여기에 달려 있다
- `position=0` 추가 시 자동 정렬 재생목록에서 오류가 나는지 → DECISIONS 30의 전제
- Gmail SMTP 발송이 되는지

### 공개 배포 전

- Clash Display 폰트 파일의 공개 저장소 배포 허용 여부를 Fontshare 라이선스에서 확인한다.
- 실제 Google 로그인 버튼은 Google 브랜딩 규정을 따라야 할 수 있다.
- Privacy Policy의 시행일과 연락처(admin 이메일)를 최종 확인한다.

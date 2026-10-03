# Phase 1 직접 테스트 시나리오

브라우저에서 직접 클릭하며 확인하는 시나리오 10개입니다. 앱 실행 방법은 맨 위 폴더의 `README.md`를 보세요.

## 시작 전에: DEV 패널 사용법

- 화면 오른쪽 아래의 작은 **DEV** 버튼을 누르면 패널이 열립니다. 패널 밖을 클릭하면 닫힙니다.
- 패널 항목:

| 항목 | 하는 일 |
|---|---|
| **Approval status** | 로그인했을 때의 승인 상태(Approved / Pending / Rejected). 로그인한 상태에서 바꾸면 바로 해당 화면으로 이동합니다 |
| **Job failures** | None(모두 성공) / Some items fail(일부 실패) / Quota runs out(작업 중간에 할당량 소진) |
| **Next action** | None / 429 (recovers after retry) / 429 (keeps failing). 다음에 시작하는 작업 하나에만 적용되고, 자동으로 None으로 돌아갑니다 |
| **Quota left** | 숫자를 입력하고 **Set**을 누르면 오늘 남은 할당량이 그 값이 됩니다 |
| **Reset mock data** | 가짜 데이터와 할당량을 처음 상태로 되돌리고 로그아웃합니다 |

- **모든 시나리오는 Reset mock data로 시작하세요.** 시작 상태는 이렇습니다.
  - 좋아요 영상 320개, 재생목록 7개
  - 남은 할당량 7,450. 로그인하면 좋아요 목록을 불러오느라 8이 줄어 7,442가 됩니다.

---

## 1. 로그인과 승인 상태

**DEV 설정:** Reset mock data → Approval status: **Pending**

| 순서 | 할 일 | 기대 결과 |
|---|---|---|
| 1 | `Sign in with Google` 클릭 | "Pending Approval" 화면과 "Your access request has been sent…" 문구 |
| 2 | 주소창에 `localhost:5173/liked` 입력 | 다시 Pending Approval 화면으로 돌아옴 |
| 3 | DEV → Approval status: **Rejected** | 바로 빨간 "Access Denied" 화면으로 바뀜 |
| 4 | DEV → **Approved** | Liked Videos 화면으로 이동하고 영상 목록이 보임 |
| 5 | 상단 `Sign out` 클릭 | 로그인 화면으로 돌아옴 |
| 6 | 아래쪽 `Privacy Policy` 클릭 → `Back` | 영어 개인정보처리방침이 보이고, Back으로 돌아옴 |

## 2. 좋아요 목록 둘러보기 (검색, 필터, 정렬, 유지)

**DEV 설정:** Reset mock data → 로그인

| 순서 | 할 일 | 기대 결과 |
|---|---|---|
| 1 | 검색창에 `jazz` 입력 | 9개만 보임, `Reset filters`가 켜짐 |
| 2 | 검색어 지우고 채널 드롭다운에서 **Tech Bench (13)** 선택 | 13개만 보임 |
| 3 | 정렬에서 **Duration: longest first** 선택 | 영상 길이가 긴 순서로 바뀜 |
| 4 | 왼쪽 `Playlists` 클릭 → 다시 `Liked Videos` 클릭 | 채널 필터와 정렬이 그대로 남아 있음 |
| 5 | `Reset filters` 클릭 | 320개 전체, "Recently liked" 정렬로 돌아오고 버튼이 흐려짐 |
| 6 | Rows per page를 **100**으로 바꾸고 페이지 4로 이동 | "301–320 of 320" 표시 |
| 7 | `Resync` 클릭 | 잠깐 "Resyncing…", 상단 할당량이 8 줄어듦 |

## 3. 선택 규칙 (100개 제한, 채널 선택, 전체 해제)

**DEV 설정:** Reset mock data → 로그인

| 순서 | 할 일 | 기대 결과 |
|---|---|---|
| 1 | 줄 아무 곳이나 클릭 | 체크되고 하단에 "1 selected" 바가 나타남 |
| 2 | Rows per page **50** → `Select all` → 페이지 2 → `Select all` | "100 selected" |
| 3 | 페이지 3 → `Select all` | 빨간 상자 "You can select up to 100 videos at a time.", 여전히 100 selected |
| 4 | 페이지 2에서 `Deselect all` | "50 selected" (현재 페이지만 해제) |
| 5 | 채널 필터 **Tech Bench** → `Select all from this channel` | 선택 개수가 늘어남(이미 선택된 영상은 중복으로 세지 않음) |
| 6 | 하단 바 `Clear selection` | 모든 페이지의 선택이 풀리고 바가 사라짐 |

## 4. 좋아요 취소 기본 흐름 + 새로고침

**DEV 설정:** Reset mock data → 로그인 (Job failures: None)

| 순서 | 할 일 | 기대 결과 |
|---|---|---|
| 1 | 영상 5개 선택 → `Remove Like` | "Remove likes from 5 videos?", "about 250 units", 선택 목록 5줄 |
| 2 | 빨간 `Remove Likes` 클릭 | 오른쪽 아래 진행 패널이 열리고 숫자가 올라감. 상단에 "Processing N / 5" |
| 3 | 진행 중에 `Resync` 확인 | 흐리게 비활성화됨 |
| 4 | 완료될 때까지 기다림 | "Completed", Success 5. 그 5개가 목록에서 사라지고 "Liked videos: 315", 할당량 250 감소 |
| 5 | 패널 밖 클릭 | 패널이 닫힘. 상단 "Last job: completed"를 누르면 다시 열림 |
| 6 | `Select all`(20개) → `Remove Like` → `Remove Likes` 후, 진행 중에 **브라우저 새로고침** | 새로고침 후에도 패널이 다시 열리고 이어서 진행되어 완료됨 |

## 5. 확인 창 안에서 선택 줄이기 (할당량 부족 재계산)

**DEV 설정:** Reset mock data → 로그인 → Quota left: **120** → Set

| 순서 | 할 일 | 기대 결과 |
|---|---|---|
| 1 | 영상 5개 선택 → `Remove Like` | "about 250 units", 빨간 "Not enough quota. You can process up to 2 items today.", `Keep first 2 only` 버튼, `Remove Likes` 비활성화 |
| 2 | 목록 첫 줄의 ✕ 클릭 | 제목이 "4 videos", "about 200 units"로 바뀜. 뒤쪽 목록에서도 그 영상의 체크가 풀림 |
| 3 | `Keep first 2 only` 클릭 | 2개만 남고 "about 100 units", 경고가 사라지고 `Remove Likes`가 켜짐. 하단 바도 "2 selected" |
| 4 | ✕로 2개 모두 빼기 | "No videos selected.", `Remove Likes` 비활성화 |
| 5 | `Cancel` → DEV에서 Quota left **262** → 4개 선택 → `Move to Playlist` → **Favorites Mix** → `Continue` | "Move and Remove Likes"에만 경고와 `Keep first 2 only`. "Move Only"는 켜져 있음 |
| 6 | `Keep first 2 only` 클릭 | 두 버튼 모두 켜지고, 두 예상치가 함께 줄어듦 |
| 7 | DEV → Quota left **0** → Set 후 영상 1개 → `Remove Like` | 경고만 있고 `Keep first` 버튼은 없음 |

## 6. 재생목록으로 이동 (중복 건너뛰기, 이동 + 좋아요 취소)

**DEV 설정:** Reset mock data → 로그인

| 순서 | 할 일 | 기대 결과 |
|---|---|---|
| 1 | 첫 페이지에서 영상 10개 선택 → `Move to Playlist` | 재생목록 7개와 각 영상 수가 보임 |
| 2 | **Favorites Mix** 선택 → `Continue` → `Move Only` | 완료 후 Skipped가 1 이상(이미 들어 있던 영상), 나머지는 Success |
| 3 | 확인 | "Liked videos" 숫자는 그대로(Move Only는 좋아요를 유지) |
| 4 | 영상 3개 선택 → `Move to Playlist` → **Study Music** → `Move and Remove Likes` | 완료 후 그 3개가 좋아요 목록에서 사라짐 |
| 5 | `Playlists` → Favorites Mix 열기 | 영상 수가 2번 단계의 Success 개수만큼 늘어나 있음 (85 → 85 + Success) |

## 7. 일부 실패와 Retry Failed

**DEV 설정:** Reset mock data → 로그인 → Job failures: **Some items fail**

| 순서 | 할 일 | 기대 결과 |
|---|---|---|
| 1 | `Select all`(20개) → `Move to Playlist` → **Watch Again** → `Move and Remove Likes` | 완료 후 Failed가 1 이상. "Failed items"에 제목과 "Error 404 · …" 또는 "Error 500 · …" |
| 2 | (드물게) 굵은 빨간 "Rollback failed. Check this video on YouTube yourself." | 되돌리기까지 실패한 영상. `Retry Failed` 대상에서 빠짐 |
| 3 | DEV → Job failures: **None** → 패널의 `Retry Failed (N)` | 새 작업으로 실패 항목만 다시 실행, 모두 Success |

## 8. 할당량 소진 (403 quotaExceeded)

**DEV 설정:** Reset mock data → 로그인 → Job failures: **Quota runs out**

| 순서 | 할 일 | 기대 결과 |
|---|---|---|
| 1 | `Select all`(20개) → `Remove Like` → `Remove Likes` | 절반쯤 처리 후 팝업 "Error 403 · quotaExceeded · …" |
| 2 | 팝업 `OK` | 패널에 "Stopped", "Processed 10 / 20", "10 not processed". 상단 할당량 0 |
| 3 | 패널 아래쪽 확인 | "Not enough quota. You can process up to 0 items today.", `Retry Failed (10)` 비활성화 |
| 4 | DEV → **Reset mock data** | 로그아웃되고 할당량이 7,450으로 돌아옴 |

## 9. 429 자동 재시도 (복구되는 경우 / 계속 실패하는 경우)

**DEV 설정:** Reset mock data → 로그인

**A. 복구되는 경우**

| 순서 | 할 일 | 기대 결과 |
|---|---|---|
| 1 | DEV → Next action: **429 (recovers after retry)** | 버튼이 흰색으로 선택됨 |
| 2 | 영상 5개 선택 → `Remove Like` → `Remove Likes` | 2개 처리 후 진행 패널에 빨간 "Rate limited. Retrying in 2 s..."와 줄어드는 숫자 |
| 3 | 계속 지켜보기 | 이어서 "Retrying in 4 s...", 그 뒤 진행이 재개되어 Success 5 |
| 4 | 작업이 끝나고 몇 초 뒤 상단 할당량 확인 | 시작 전보다 350 감소(정상 250 + 재시도 2회 100) |
| 5 | DEV 다시 열기 | Next action이 **None**으로 돌아가 있음 |

**B. 계속 실패하는 경우**

| 순서 | 할 일 | 기대 결과 |
|---|---|---|
| 1 | DEV → Next action: **429 (keeps failing)** | |
| 2 | 영상 6개 선택 → `Remove Like` → `Remove Likes` | 2개 처리 후 2 s → 4 s → 8 s 카운트다운(약 14초) |
| 3 | 기다리기 | 팝업 "Error 429 · rateLimitExceeded · Rate Limit Exceeded" |
| 4 | 팝업 `OK` | 패널에 "Stopped", Success 2, "4 not processed" |
| 5 | `Retry Failed (4)` | 남은 4개가 처리되어 Success 4 |

## 10. 재생목록 정리

**DEV 설정:** Reset mock data → 로그인 → 왼쪽 `Playlists`

| 순서 | 할 일 | 기대 결과 |
|---|---|---|
| 1 | **Watch Again** 클릭 | 60개 목록, "Deleted video" / "Private video" 줄은 회색 기울임 글씨 |
| 2 | `Remove Unavailable Videos` | "Selected 10 deleted or private videos…", 하단 "10 selected" (아직 지워지지 않음) |
| 3 | `Remove Selected` → 확인 창 → 빨간 `Remove` | "about 500 units", 완료 후 목록과 왼쪽 숫자가 50으로 줄어듦 |
| 4 | **Big Archive** 클릭 → `Remove Duplicates` | "Selected the first 100 of 130 duplicate videos…", "100 selected" |
| 5 | **Workout** 클릭 | 선택과 안내 문구가 사라짐(재생목록을 바꾸면 해제) |
| 6 | `Remove Duplicates` | "Selected 8 duplicate videos…" |
| 7 | **Study Music** → `Remove Duplicates` | "No duplicate videos found." |
| 8 | **New Playlist** 클릭 | "This playlist is empty." |

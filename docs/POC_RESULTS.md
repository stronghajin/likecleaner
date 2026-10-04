# P2-2 PoC 결과 (2026-10-04)

기획서 14장의 다섯 가지를 실제 계정(`hajin300@gmail.com`, DECISIONS 43)으로 확인한 결과다.
OAuth 앱은 "테스트 중" 상태였다(DECISIONS 51).

- 실행 방법(`backend/`에서):
  - `uv run python -m scripts.poc.login`
  - `uv run python -m scripts.poc.youtube_checks`
  - `uv run python -m scripts.poc.mail_check`
- 원본 결과는 `backend/data/poc/*.json`에 있다(git에 올리지 않음). 이 문서에는 개수와 응답 모양만 적고, 개인 영상 제목이나 ID는 적지 않는다.
- PoC 전체에서 쓴 할당량은 약 1,300 units다(하루 10,000 중).

---

## 1. 좋아요 목록을 끝까지 가져올 수 있는가 → ⚠️ 최근 약 1,000개까지만

`videos.list?myRating=like&maxResults=50`

| 항목 | 값 |
|---|---|
| 받은 영상 | **969개** (중복 없음), 20페이지에서 `nextPageToken`이 끝남 |
| 페이지별 개수 | 50개보다 적은 페이지가 많다(45~50개). 삭제/비공개 영상은 빠지는 것으로 보인다 |
| `pageInfo.totalResults` | 6,173. 실제로 받을 수 있는 개수와 다르다 |

비교를 위해 "좋아요 표시한 동영상" 재생목록(`LL`, `playlistItems.list`)도 확인했다.
- 4,919개를 끝까지 받았다. 그중 삭제 88개, 비공개 194개가 들어 있다.
- 비용은 목록 99 units에, 상세 정보 조회 약 99 units가 더 든다.
- YouTube 웹에서도 좋아요 목록이 5,000개까지만 보인다.

→ **결정(DECISIONS 52):** 기획서 방식(`myRating=like`)을 유지한다. 화면에는 최근 좋아요 약 1,000개만 보인다.

## 2. 테스트 상태에서 `youtube` 권한 로그인과 refresh token 발급 → ✅

| 단계 | 결과 |
|---|---|
| 1단계 (`openid email profile`) | 로그인 성공, refresh token **없음**(의도대로) |
| 2단계 (`youtube`, `access_type=offline`, `prompt=consent`, `include_granted_scopes=true`) | refresh token **발급**. 받은 권한에 1단계 권한도 함께 들어 있다(점진적 승인 정상) |
| refresh token으로 갱신 | 성공. 새 refresh token은 주지 않음(처음 받은 것을 계속 씀). 같은 계정 확인 |
| access token 유효 시간 | 3,599초(약 1시간) |

- 테스트 상태에서는 refresh token이 7일 뒤 만료된다.
- In production 상태에서 같은 동작을 하는지는 P2-7에서 확인한다(DECISIONS 51).

## 3. 삭제/비공개 영상은 `playlistItems.list`에서 어떻게 보이는가 → ✅

재생목록 22개, 항목 약 350개를 조회만 해서 확인했다.

| 종류 | 개수 | `snippet.title` | `status.privacyStatus` | `videoOwnerChannelTitle` | 썸네일 | `videoPublishedAt` |
|---|---|---|---|---|---|---|
| 비공개 | 12 | `Private video` | `private` | 없음 | 없음 | 없음 |
| 삭제 | 2 | `Deleted video` | `privacyStatusUnspecified` | 없음 | 없음 | 없음 |
| 일반 | 333 | 실제 제목 | `public` / `unlisted` | 있음 | 있음 | 있음 |

- 삭제/비공개 영상 14개의 ID로 `videos.list`를 부르면 **하나도 돌아오지 않는다**. 그래서 채널, 카테고리, 길이를 알 수 없다(`PlaylistItem`의 `null` 칸과 맞음).
- 제목은 실제 제목이면서 채널 이름이 없는 항목은 없었다.
- → 판정 규칙: DECISIONS 53

## 4. `position=0` 추가 시 자동 정렬 재생목록에서 오류가 나는가 → 오류 없음

`LC Test 1`(수동 정렬)과 `LC Test 2`(웹에서 정렬을 "추가된 날짜"로 바꿈)로 확인했다. 시험할 때마다 추가한 항목은 바로 지웠고, 두 재생목록이 시험 전과 같은 상태로 돌아온 것을 확인했다.

| 시험 | 결과 |
|---|---|
| `LC Test 1`에 `position=0` | 성공, 실제로 0번 자리 |
| `LC Test 2`에 `position=0` | **성공** (`manualSortRequired` 없음), 실제로 0번 자리 |
| `LC Test 2`에 `position=1` (중간) | **성공**, 실제로 1번 자리. 웹의 정렬 설정을 API 추가에서는 강제하지 않는다 |
| 같은 영상을 한 번 더 추가 (`LC Test 1`) | 성공. 같은 영상이 서로 다른 `playlistItemId`를 가진 두 항목(0번, 2번)으로 보인다 |

- YouTube 웹의 "저장" 창은 체크박스 방식이라 같은 영상을 두 번 넣을 수 없다. 그래서 중복은 API로 만들어 확인했다.
- **추가와 삭제는 몇 초 뒤에야 조회에 반영된다.** 추가 직후 바로 조회하면 이전 목록이 나왔고, 약 5초 뒤에는 반영됐다. → DECISIONS 55

## 5. Gmail SMTP 앱 비밀번호로 메일 발송 → ✅

`smtp.gmail.com:587`(STARTTLS)로 `hajin300@gmail.com`이 자기 자신에게 시험 메일(`[LikeCleaner] PoC test mail`) 1통을 보냈다.

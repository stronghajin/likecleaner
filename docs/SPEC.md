# LikeCleaner 서비스 기획서 v2

> 이 문서는 AI 코딩 도구(Claude 등)에 그대로 입력해 개발을 시작하기 위한 기획서입니다.
> 기획서는 한국어로 작성하고, **서비스 UI의 모든 문구는 영어**로 구현합니다.

---

## 1. 개요

| 항목 | 내용 |
|---|---|
| 서비스명 | LikeCleaner (가칭) |
| 목적 | YouTube "좋아요 한 동영상"과 재생목록을 한 화면에서 보고, 일괄로 좋아요 취소, 재생목록 이동, 재생목록 정리를 할 수 있는 웹 툴 |
| MVP 사용자 | 운영자(admin)와 지인. admin이 승인한 사용자만 사용 가능 |
| 지원 환경 | 데스크톱 웹 브라우저만 지원 (모바일 미지원) |
| UI 언어 | 영어만 지원 |
| 디자인 | Black Mode (다크 테마 단일) |
| 수익 모델 | MVP에는 없음. 추후 "3일 사용권" 형태 검토 중 (미확정) |

---

## 2. 기술 스택

| 영역 | 선택 |
|---|---|
| Frontend | React (Vite) + Tailwind CSS |
| Backend | Python FastAPI |
| DB | SQLite |
| 작업 처리 | 백엔드 내 백그라운드 작업 워커 (작업 큐는 DB 테이블로 관리) |
| 인증 | Google OAuth 2.0 (offline access로 refresh token 발급) |
| 메일 발송 | Gmail SMTP (앱 비밀번호 사용) |

환경 변수로 관리할 값: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `ADMIN_EMAIL=hajin300@gmail.com`, `SMTP_USER`, `SMTP_APP_PASSWORD`, `TOKEN_ENCRYPTION_KEY`, `DAILY_QUOTA=10000`

---

## 3. 로그인과 승인 흐름

### 3-1. OAuth 앱 운영 방식

* Google OAuth 앱은 **"In production" 상태, 앱 검증은 받지 않음**으로 운영합니다.
  * 로그인 시 "Google에서 확인하지 않은 앱" 경고 화면이 나오며, 사용자는 "고급 → 계속"을 눌러 진행합니다.
  * 검증 전 누적 사용자 100명 제한이 있습니다. MVP 규모에서는 문제 없습니다.
  * Testing 상태와 달리 refresh token이 7일 뒤 만료되지 않고, GCP 콘솔에 테스트 사용자를 따로 등록할 필요가 없습니다. **승인 관리는 서비스 DB 한 곳에서만** 합니다.

### 3-2. 2단계 로그인 (권한 분리)

1. **1단계 (기본 로그인):** `openid email profile` 스코프만 요청해 사용자 신원을 확인합니다.
2. DB에서 승인 상태를 확인합니다.
   * `approved` → 2단계로 진행
   * `pending` 또는 신규 → **Pending Approval 화면** 표시
   * `rejected` → 접근 불가 안내 화면 표시
3. **2단계 (YouTube 권한):** 승인된 사용자에게만 `https://www.googleapis.com/auth/youtube` 스코프를 추가 요청합니다(incremental authorization, `access_type=offline`).
4. 발급받은 refresh token은 암호화해서 DB에 저장합니다.

### 3-3. 승인 요청과 admin 알림

* 신규 사용자가 처음 1단계 로그인을 하면 `users` 테이블에 `pending` 상태로 추가합니다.
* 동시에 `ADMIN_EMAIL`로 알림 메일을 **1회만** 발송합니다.
  * 제목: `[LikeCleaner] New access request`
  * 본문: 요청자 이름, 이메일, 요청 시각(KST)
* admin은 DB를 직접 수정해 `approved` 또는 `rejected`로 바꿉니다. **admin 화면은 만들지 않습니다.**

### 3-4. 로그아웃

* 세션만 종료합니다. Google 토큰 폐기(revoke)는 하지 않습니다.

---

## 4. API 할당량(Quota) 관리

### 4-1. 기본 원칙

* YouTube Data API 할당량은 **GCP 프로젝트 전체가 공유하는 하루 10,000 units**입니다.
* 사용자별 배분 없이 **먼저 쓰는 사람이 쓰는 방식**입니다.
* YouTube API는 잔여 할당량을 조회하는 기능이 없으므로, **백엔드가 모든 API 호출의 소모 units를 직접 기록**합니다. 실패한 호출도 기록합니다.
* 하루 기준은 **미국 태평양 시간 자정**(한국 시간 오후 4시 또는 5시)에 초기화됩니다.

### 4-2. API별 소모 units

| API 호출 | 용도 | units |
|---|---|---|
| `videos.list` (myRating=like) | 좋아요 목록 조회 (50개/페이지) | 1 / 페이지 |
| `videoCategories.list` | 카테고리 이름 조회 | 1 |
| `playlists.list` (mine=true) | 내 재생목록 조회 | 1 / 페이지 |
| `playlistItems.list` | 재생목록 항목 조회, 중복 확인 | 1 / 페이지 |
| `videos.rate` (rating=none) | 좋아요 취소 | 50 |
| `playlistItems.insert` | 재생목록에 추가 | 50 |
| `playlistItems.delete` | 재생목록에서 제거, 롤백 | 50 |

### 4-3. 화면 표시

* 상단 헤더에 항상 **프로젝트 전체 잔여 할당량**을 표시합니다.
  * 예: `Quota left today: 7,450 / 10,000 units` + 진행 바
  * 리셋까지 남은 시간도 함께 표시: `Resets in 5h 12m`
* 액션 확인 팝업에 **예상 소모량**을 표시합니다.
  * 예: `This action will use about 2,500 units.`
  * 예상치는 최대치 기준으로 계산합니다(조회 호출 포함, 롤백 비용 제외).

### 4-4. 할당량 부족 시

* 예상 소모량이 잔여 할당량보다 크면:
  * 최종 실행 버튼을 **비활성화**합니다.
  * 빨간색 경고 문구를 표시합니다.
    * `Not enough quota. You can process up to N items today.`
  * 사용자가 선택 개수를 줄이면 다시 계산해서 버튼을 활성화합니다.

---

## 5. 화면 구성

| # | 화면 | 설명 |
|---|---|---|
| 1 | Landing / Login | 서비스 소개 한 줄, `Sign in with Google` 버튼, 개인정보처리방침 링크 |
| 2 | Pending Approval | `Your access request has been sent. You can use LikeCleaner once the admin approves it.` |
| 3 | Access Denied | `Your access request was not approved.` |
| 4 | Liked Videos (메인) | 좋아요 목록 조회, 필터/정렬, 일괄 액션 |
| 5 | Playlists | 재생목록 선택 후 항목 정리 |
| 6 | Job Progress | 작업 진행률과 결과 (패널 또는 모달) |
| 7 | Privacy Policy | 개인정보처리방침 (영어) |

공통 헤더: 로고, 탭(`Liked Videos` / `Playlists`), 할당량 표시, 프로필 이미지와 이름, `Sign out`

---

## 6. 기능 상세: Liked Videos (메인)

### 6-1. 목록 조회

* 로그인 직후 좋아요 목록 **전체**를 백엔드에서 불러옵니다(`videos.list`, `part=snippet,contentDetails`, 50개씩 반복 조회).
  * 전체를 불러와야 필터와 정렬이 전체 목록 기준으로 동작합니다.
  * 좋아요 1,000개 기준 약 20 units 소모.
* 불러온 목록은 **DB에 저장하지 않고** 서버 세션 메모리에만 둡니다.
* 리스트 보기 한 가지만 제공합니다. 각 행 구성:
  * 체크박스
  * 작은 썸네일 (120×90, `default` 해상도. 이미지 로딩은 할당량을 쓰지 않음)
  * 제목
  * 채널명
  * 카테고리
  * 영상 길이
  * 업로드 날짜

### 6-2. 필터와 정렬

| 구분 | 기능 |
|---|---|
| 검색 필터 | 제목 키워드 검색 |
| 채널 필터 | 채널 드롭다운으로 특정 채널 영상만 보기 |
| 카테고리 필터 | YouTube 카테고리(Music, Gaming 등)로 보기 |
| 정렬 | 영상 길이 (짧은 순/긴 순), 업로드 날짜 (최신순/오래된 순) |

필터와 정렬은 이미 불러온 목록 안에서 처리하므로 할당량을 쓰지 않습니다.

### 6-3. 페이지네이션과 재동기화

* 페이지 크기 선택: **20 / 50 / 100**
* 페이지네이션 옆에 **`Resync` 버튼**을 둡니다. 누르면 좋아요 목록을 다시 전체 조회합니다.
  * YouTube 앱에서 따로 바꾼 내용을 반영하기 위한 기능입니다.

### 6-4. 선택

* 개별 체크박스 선택
* `Select all` / `Deselect all`: **현재 페이지**의 항목 전체를 선택/해제
* 채널 단위 선택: 채널 필터를 적용한 상태에서 `Select all from this channel` 버튼 제공
* **한 번에 선택할 수 있는 최대 개수는 100개**입니다.
  * 100개를 넘기려 하면 추가 선택을 막고 안내합니다: `You can select up to 100 videos at a time.`
* 1개 이상 선택하면 하단 플로팅 액션 바가 나타납니다.
  * `N selected` · `Remove Like` · `Move to Playlist`

### 6-5. 액션 1: Remove Like (좋아요 취소)

1. `Remove Like` 클릭
2. 확인 모달
   * `Remove likes from N videos?`
   * 예상 소모량 표시 (N × 50 units)
   * 버튼: `Remove Likes` / `Cancel`
3. 확인 시 작업 생성 → 백엔드에서 `videos.rate(rating=none)` 순차 호출
4. 성공한 항목은 목록에서 제거

### 6-6. 액션 2: Move to Playlist (재생목록으로 이동)

1. `Move to Playlist` 클릭
2. 재생목록 선택 팝업 (`playlists.list`로 내 재생목록 표시, 한 개만 선택 가능)
   * 재생목록 새로 만들기는 제공하지 않습니다.
3. 이동 방식 확인 팝업
   * 문구: `Move N videos to "{playlist name}". Do you also want to remove their likes?`
   * 각 선택지별 예상 소모량 표시
   * 버튼:
     * `Move and Remove Likes`
     * `Move Only`
     * `Cancel`
4. 처리 규칙

| 상황 | Move Only | Move and Remove Likes |
|---|---|---|
| 대상 재생목록에 없는 영상 | 맨 앞에 추가 | 맨 앞에 추가 → 좋아요 취소 |
| 대상 재생목록에 이미 있는 영상 | 건너뜀 (`Skipped`) | 추가는 건너뛰고 **좋아요 취소만 실행** |

* **중복 확인:** 작업 시작 전 대상 재생목록 항목을 조회(`playlistItems.list`)해 이미 있는 영상 ID를 확인합니다.
* **맨 앞에 추가:** `position=0`으로 추가합니다. 재생목록이 수동 정렬이 아니어서 `manualSortRequired` 오류가 나면 위치 지정 없이 다시 추가합니다.

### 6-7. 이동 + 좋아요 취소의 롤백 처리

YouTube API는 트랜잭션을 지원하지 않으므로, 항목별로 아래 보상 처리를 해서 "부분 성공" 상태가 남지 않게 합니다.

1. 재생목록에 추가
2. 좋아요 취소
3. 2번이 실패하면 1번에서 추가한 항목을 `playlistItems.delete`로 삭제 → 해당 항목은 `Failed`
4. 3번의 삭제까지 실패하면 `Rollback failed`로 표시 (사용자가 직접 확인해야 하는 유일한 예외 상태)

---

## 7. 기능 상세: Playlists (재생목록 정리)

### 7-1. 재생목록 선택

* 내 재생목록 목록을 보여주고, 하나를 선택하면 항목 목록을 보여줍니다.
* 항목 행 구성은 좋아요 목록과 같습니다(체크박스, 썸네일, 제목, 채널명 등).
* 페이지네이션(20/50/100)과 `Resync` 버튼도 동일하게 제공합니다.

### 7-2. 정리 기능

| 기능 | 동작 |
|---|---|
| `Remove Duplicates` | 같은 영상이 여러 번 있으면 **가장 앞의 하나만 남기고** 나머지를 제거 대상으로 자동 선택 |
| `Remove Unavailable Videos` | 삭제된 영상, 비공개 영상(`Deleted video`, `Private video`)을 제거 대상으로 자동 선택 |
| `Remove Selected` | 사용자가 체크한 항목을 재생목록에서 제거 |

* 자동 선택 기능은 바로 삭제하지 않고 **선택 상태로 만들어 보여준 뒤** 사용자가 확인하게 합니다.
* 한 번에 최대 100개, 할당량 확인 규칙은 좋아요 화면과 같습니다.
* 확인 모달: `Remove N videos from "{playlist name}"?` + 예상 소모량 (N × 50 units)

---

## 8. 작업(Job) 처리

### 8-1. 처리 방식

* 모든 일괄 액션은 **백엔드 작업**으로 처리합니다.
  * 액션 확인 시 백엔드가 작업과 항목 목록을 DB에 저장하고, 백그라운드에서 순차 처리합니다.
  * **사용자가 탭을 닫아도 작업은 계속됩니다.** 다시 접속하면 진행 상황과 결과를 볼 수 있습니다.
  * access token이 만료되면 서버가 refresh token으로 자동 갱신합니다.
* 한 사용자는 동시에 하나의 작업만 실행할 수 있습니다. 실행 중에는 새 액션 버튼을 비활성화합니다.

### 8-2. 진행 화면

* 진행률 바 (`Processing 37 / 100`)
* 성공 / 실패 / 건너뜀 개수
* 실패 항목 목록 (영상 제목 + 오류 내용)
* `Retry Failed` 버튼: 실패한 항목만 모아 새 작업으로 다시 실행 (할당량 확인 규칙 동일 적용)

### 8-3. 오류 처리

* API 오류(403, 429 등)가 나면 **오류 팝업**을 띄웁니다.
  * 표시 내용: HTTP 상태 코드, 오류 사유(reason), 오류 메시지
  * 예: `Error 403 · quotaExceeded · The request cannot be completed because you have exceeded your quota.`
* 할당량 초과(`quotaExceeded`) 오류가 나면 남은 항목 처리를 중단하고, 남은 항목은 `Not processed`로 표시합니다.

---

## 9. 데이터 저장

좋아요 목록과 영상 정보는 저장하지 않습니다. 저장하는 데이터는 아래가 전부입니다.

| 테이블 | 주요 컬럼 | 보관 기간 |
|---|---|---|
| `users` | id, google_sub, email, name, picture_url, status(pending/approved/rejected), created_at, notified_at | 삭제 요청 시까지 |
| `oauth_tokens` | user_id, refresh_token(암호화), scopes, updated_at | 사용자 삭제 시까지 |
| `quota_usage` | date_pt, method, units, user_id, success, created_at | 30일 |
| `jobs` | id, user_id, type(remove_like/move/move_and_unlike/playlist_remove), target_playlist_id, status, created_at, finished_at | 30일 |
| `job_items` | job_id, video_id, video_title, status(success/failed/skipped/rollback_failed/not_processed), error_code, error_message | 30일 |

* 30일이 지난 데이터는 매일 1회 자동 삭제합니다.
* refresh token은 `TOKEN_ENCRYPTION_KEY`로 암호화해서 저장합니다.

---

## 10. 정책 준수 (Google API 사용자 데이터 정책, YouTube API 약관)

* 영어 개인정보처리방침 페이지를 제공합니다. 포함 내용:
  * 수집 항목 (이름, 이메일, 프로필 이미지, OAuth 토큰, 작업 기록)
  * 사용 목적 (사용자가 요청한 YouTube 정리 작업 수행에만 사용)
  * 보관 기간 (9번 표 기준)
  * 삭제 요청 방법 (admin 이메일로 요청)
* 로그인 화면과 푸터에 [YouTube Terms of Service](https://www.youtube.com/t/terms)와 [Google Privacy Policy](https://policies.google.com/privacy) 링크를 넣습니다.
* 가져온 데이터는 화면 표시와 사용자가 요청한 작업에만 사용하고, 분석, 광고, 제3자 제공에 쓰지 않습니다.
* 사용 통계(GA 등)는 수집하지 않습니다.
* YouTube API 데이터는 30일 넘게 저장하지 않습니다.
* 삭제 요청이 오면 admin이 DB에서 해당 사용자 데이터를 직접 삭제합니다.
* 추후 유료화할 경우 앱 검증과 정책 검토를 다시 해야 합니다.

---

## 11. 디자인 가이드 (Black Mode)

| 요소 | 값 |
|---|---|
| 배경 | `#0A0A0A` |
| 카드, 패널 | `#161616` |
| 테두리 | `#2A2A2A` |
| 기본 텍스트 | `#F5F5F5` |
| 보조 텍스트 | `#A1A1A1` |
| 강조 (주요 버튼, 선택 상태) | `#FFFFFF` 배경 + `#0A0A0A` 텍스트 |
| 경고, 오류, 할당량 부족 | `#EF4444` |
| 성공 | `#22C55E` |

* 라이트 모드는 제공하지 않습니다.
* 정보 밀도가 높은 데스크톱용 리스트 UI를 기준으로 합니다.
* 파괴적인 액션(좋아요 취소, 재생목록에서 제거)의 최종 버튼은 빨간색으로 표시합니다.

---

## 12. MVP 제외 범위

* 모바일 지원
* 그리드 보기
* 재생목록 새로 만들기
* 여러 재생목록에 동시 추가
* 재생목록 병합
* 좋아요 되돌리기 (Undo)
* CSV/JSON 백업
* admin 관리 화면
* 사용자별 할당량 배분
* 할당량 증설 신청
* "Watch Later" 관련 안내
* 다국어 지원
* 사용 통계 수집
* 유료 결제

---

## 13. Acceptance Criteria

**로그인과 승인**
* 승인되지 않은 사용자는 로그인 후 Pending Approval 화면을 보고, admin은 메일로 요청 알림을 받는다.
* 승인된 사용자만 좋아요 목록과 재생목록을 볼 수 있다.

**좋아요 목록**
* 사용자는 좋아요 한 영상 전체를 작은 썸네일이 있는 리스트로 볼 수 있다.
* 사용자는 제목 검색, 채널, 카테고리로 목록을 좁히고, 영상 길이와 업로드 날짜로 정렬할 수 있다.
* 사용자는 Resync로 최신 상태를 다시 불러올 수 있다.

**일괄 액션**
* 사용자는 최대 100개를 골라 좋아요를 취소하거나 재생목록으로 옮길 수 있다.
* 이미 재생목록에 있는 영상은 중복으로 추가되지 않는다.
* "이동 + 좋아요 취소"에서 한 단계만 성공한 상태로 남는 영상은 없다(롤백 실패 예외 제외).

**재생목록 정리**
* 사용자는 재생목록에서 중복 영상, 삭제/비공개 영상, 선택한 영상을 제거할 수 있다.

**할당량**
* 사용자는 항상 오늘 남은 할당량과, 실행 전 예상 소모량을 볼 수 있다.
* 할당량이 부족하면 실행할 수 없고, 몇 개까지 처리 가능한지 안내받는다.

**작업 처리**
* 사용자는 작업 진행률, 성공/실패 개수를 보고, 실패한 항목만 다시 실행할 수 있다.
* 탭을 닫았다 다시 열어도 작업 결과를 확인할 수 있다.

---

## 14. 개발 착수 시 먼저 검증할 항목 (PoC)

1. `videos.list?myRating=like`로 좋아요 목록이 **끝까지 모두** 조회되는지, 개수 상한이 있는지
2. 검증 전 "In production" 상태에서 `youtube` 스코프 로그인과 refresh token 발급이 정상 동작하는지
3. 삭제/비공개 영상이 `playlistItems.list` 응답에서 어떻게 표시되는지 (제목 값, `videoOwnerChannelTitle` 유무)
4. `position=0` 추가 시 자동 정렬 재생목록에서 오류가 나는지
5. Gmail SMTP 앱 비밀번호로 메일 발송이 되는지

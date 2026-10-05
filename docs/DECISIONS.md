# 기획 결정 사항

`SPEC.md`의 애매한 부분에 대해 확정한 내용 (2026-10-02). SPEC.md와 함께 기준으로 삼는다.

## 선택과 목록

1. 선택 상태는 페이지 이동이나 필터 변경 후에도 유지된다. 하단 액션 바에 전체 선택 개수를 표시한다.
2. `Select all from this channel`을 눌렀을 때 그 채널 영상이 100개를 넘으면, 앞에서부터 100개까지만 선택하고 안내 문구를 보여준다.
3. 정렬을 고르지 않았을 때 기본 순서는 최근에 좋아요 누른 순서(YouTube가 주는 순서)다.
4. `Move Only`로 옮긴 영상은 좋아요 목록에 그대로 남는다. 좋아요가 취소된 영상만 목록에서 빠진다.

## 재생목록 화면

5. 재생목록 화면에는 검색, 필터, 정렬을 넣지 않는다. 페이지 크기 선택(20/50/100)과 `Resync`만 둔다.
6. 재생목록 항목 행에도 카테고리와 영상 길이를 표시한다. Phase 2에서는 이 정보를 가져오는 `videos.list` 호출(50개당 1 unit)을 할당량 계산에 포함한다.
7. 중복 영상이 100개를 넘으면 `Remove Duplicates`는 앞에서부터 100개만 자동 선택하고, 나머지는 다음 실행에서 처리하라고 안내한다.

## 할당량

8. Move 확인 창에서 할당량이 모자란 선택지는 그 버튼만 비활성화하고, 버튼 옆에 빨간 안내 문구를 표시한다.

## 작업 처리

9. 작업을 멈추게 하는 오류(예: `quotaExceeded`)가 났을 때만 오류 팝업을 띄운다. 나머지 항목별 오류는 실패 목록에만 표시한다.
10. `Retry Failed`는 `Failed`와 `Not processed` 항목을 다시 실행한다. `Rollback failed` 항목은 사용자가 직접 확인해야 하므로 제외한다.
11. 작업 진행 화면은 오른쪽 아래 패널로 만든다. 헤더에 작은 진행 표시를 두고, 그것을 누르면 패널이 열린다. 다른 탭을 보는 중에도 진행 상황이 보인다.
12. 다시 접속했을 때는 가장 최근 작업 하나의 결과만 보여준다. 지난 작업 목록 화면은 만들지 않는다.
13. 작업이 진행되는 동안에는 `Resync` 버튼을 비활성화한다.

## Phase 1 전용

14. 개발용 패널을 둔다. 사용자 상태(approved/pending/rejected)를 고르는 스위치와 작업 실패나 할당량 초과를 흉내 내는 스위치가 들어간다. Phase 2에서 제거한다.
    - (수정) 로그인 화면이 아니라 모든 화면의 오른쪽 아래 작은 "DEV" 버튼으로 연다. 평소에는 닫혀 있다.
    - 로그인한 상태에서 사용자 상태를 바꾸면 그에 맞는 화면으로 즉시 이동한다.
    - 개발 중 화면(`npm run dev`)에서만 보이고, 실제 서비스용 결과물(build)에서는 자동으로 빠진다.
15. 로고는 "LikeCleaner" 글자로 만든다.

## 추가 결정 (기획서 외, 사용자 요청)

16. 마우스 애니메이션을 모든 화면에 적용한다.
    - 호버/누름 효과: 버튼, 목록 행, 탭 등에 마우스를 올리면 색이 0.15초 동안 부드럽게 바뀌고, 버튼을 누르면 살짝 작아졌다 돌아온다.
    - 커서 글로우: 커서 주변에 은은한 흰빛(지름 180px)이 부드럽게 따라다닌다. 커서 모양은 바꾸지 않는다.
    - 아이콘 꼬리: 흰색 테두리 아이콘 4개(좋아요, 구독 알림 종, 재생, 재생목록 추가)가 커서 뒤를 꼬리처럼 따라오고, 마우스가 멈추면 서서히 사라진다. 아이콘은 YouTube 원본이 아닌 직접 그린 것을 쓴다.
    - 운영체제의 "동작 줄이기" 설정을 켠 사용자에게는 두 효과를 모두 끈다.
17. 화면 배치는 기획서 5장의 "상단 탭" 대신 **왼쪽 사이드바**로 한다.
    - 사이드바: 로고 + 메뉴 `Liked Videos` / `Playlists`
    - 상단 바: 할당량(잔여량, 진행 바, 리셋까지 남은 시간), 프로필 사진과 이름, `Sign out`
18. 로고 글꼴은 Clash Display(Fontshare, 무료 상업 사용 가능)를 쓴다. 외부에서 불러오지 않고 폰트 파일을 프로젝트에 넣어 쓴다. 로고에만 쓰고, 나머지 글자는 기본 글꼴을 쓴다.
19. 박스와 패널은 모서리를 각지게(직사각형) 만들고, 콘텐츠 영역은 사이드바 오른쪽 전체 너비를 쓴다. 버튼과 입력칸은 아주 살짝만 둥글게 한다.
20. 통계 라벨(예: `Liked videos`, `Quota left today`)은 흰색 `#FFFFFF` + 볼드로 표시한다.
21. 화면 이동에는 React Router를 쓴다.
22. 개발용 패널에는 두 가지를 더 넣는다. "남은 할당량 직접 정하기"와 "mock 데이터 초기화"이며, Phase 2에서 함께 지운다.
23. Liked Videos 화면의 페이지 이동 줄(Rows per page, 페이지 번호, `Resync`)은 리스트 **위**에 둔다.
24. 검색어, 필터, 정렬, 페이지 위치는 다른 메뉴에 다녀와도 유지한다. 로그아웃하면 초기화된다.
    - `Reset filters` 버튼으로 검색어, 채널, 카테고리, 정렬을 처음 상태로 되돌린다. Rows per page는 유지한다. 바꾼 것이 없을 때는 버튼을 비활성화한다.
25. DEV 패널이 열린 상태에서 패널 밖을 클릭하면 닫힌다.
26. 하단 액션 바에 `Clear selection` 버튼을 둔다. 모든 페이지에 걸친 선택을 한 번에 해제한다. (`Deselect all`은 기획서대로 현재 페이지만 해제)
27. 작업이 끝난 뒤(완료 또는 중단)에는 진행 패널 밖을 클릭하면 패널이 닫힌다. 진행 중에는 닫히지 않는다. 상단 바의 진행 표시 버튼과 팝업 창 안의 클릭은 "바깥"으로 치지 않는다.
28. 작업 중 429 rateLimitExceeded 처리 (기획서 8-3 보완)
    - 429가 나면 2초, 4초, 8초 간격으로 최대 3번 자동 재시도한다. 재시도를 기다리는 동안 진행 패널에 "Rate limited. Retrying in N s..."를 표시한다.
    - 3번 모두 실패하면 작업을 멈추고 오류 팝업을 띄운다. 그 항목과 남은 항목은 `Not processed`로 표시하고, `Retry Failed`로 이어서 처리할 수 있다.
    - 재시도한 호출도 할당량 사용량에 기록한다.
    - DEV 패널에 "Next action" 옵션 두 가지를 둔다: "429 (recovers after retry)"와 "429 (keeps failing)". 옵션을 켜고 시작한 다음 작업 하나에만 적용되고, 작업이 시작되면 "None"으로 돌아간다.
29. 확인 창 안에서 선택 줄이기 (기획서 4-4 "선택 개수를 줄이면 다시 계산" 구현 방식)
    - 모든 액션 확인 창(Remove Like, Move to Playlist의 두 번째 창, Remove from playlist)에 선택한 영상의 제목 목록을 보여준다. 높이는 정해 두고 넘치면 스크롤한다.
    - 목록 순서: 좋아요 화면은 선택한 순서, 재생목록 화면은 재생목록 순서.
    - 각 줄의 ✕ 버튼으로 빼면 메인 목록의 선택도 함께 해제된다.
    - 할당량이 부족하면 빨간 경고 옆에 "Keep first N only" 버튼을 둔다. 누르면 목록 위에서부터 처리 가능한 N개만 남기고 나머지는 선택 해제한다. N이 0이면 버튼을 보이지 않는다.
    - 항목이 바뀔 때마다 예상 units, 경고 문구, 최종 버튼 상태를 즉시 다시 계산한다. 항목이 하나도 없으면 최종 버튼을 비활성화한다.

## 구현 중 정한 세부 사항 (보고 시 안내한 내용을 기록)

30. "Move" 계열 예상 소모량에는 자동 정렬 재생목록에서 생길 수 있는 "맨 앞에 추가" 실패 호출 1회분(50 units)을 더한다. 기획서 4-3의 "최대치 기준"을 지키기 위해서다. 한 번 거절된 재생목록은 이후 맨 앞 추가를 다시 시도하지 않는다.
31. 확인 창에서 작업을 시작하면 선택이 모두 해제된다.
32. Playlists 화면에서 다른 재생목록을 열면 선택이 해제된다. `Remove Duplicates` / `Remove Unavailable Videos`는 기존 선택을 지우고 찾은 항목으로 바꾼다.
33. 썸네일은 120×90 해상도 이미지를 쓰되, 목록을 촘촘하게 보여주기 위해 화면에는 80×60으로 표시한다.

## Phase 2 결정 (2026-10-03)

34. 배포처는 P2-7 전에 정한다. P2-1~P2-6은 이 컴퓨터에서 개발한다.
35. 운영할 때는 FastAPI가 빌드된 프론트엔드 파일도 함께 내보내, 화면과 API를 한 주소로 운영한다. 개발 중에는 Vite 프록시로 `/api`를 백엔드에 연결하므로, 브라우저 기준으로 주소는 `http://localhost:5173` 하나다.
36. 파이썬 프로젝트와 버전 관리는 uv로 한다.
37. 백엔드 라이브러리: `fastapi`, `uvicorn`, `pydantic-settings`, `sqlalchemy`, `aiosqlite`, `alembic`, `httpx`, `aiosmtplib`, `cryptography`, `itsdangerous`. 테스트용: `pytest`, `pytest-asyncio`, `respx`. 이 밖의 라이브러리는 먼저 묻는다.
38. DB 구조 변경은 alembic 이력으로 관리한다.
39. (56으로 대체) 사용자 승인은 터미널 명령으로 한다(예: `uv run python -m scripts.approve someone@gmail.com`). admin 화면은 만들지 않는다(기획서 12장).
40. (56으로 대체, 현재 미사용) admin 알림 메일은 `ADMIN_EMAIL` 계정이 자기 자신에게 보낸다(`SMTP_USER` = `ADMIN_EMAIL`).
41. 작업은 사용자마다 동시에 진행할 수 있다. 한 사용자의 작업 안에서는 항목을 한 개씩 순서대로 처리한다(기획서 8-1의 1인 1작업 유지).
42. 기획서 9장 테이블에 아래 칸과 값을 추가한다. 새로운 종류의 개인정보는 없다.
    - `jobs`: `target_playlist_title`, 작업을 멈춘 오류(`fatal_error_status`, `fatal_error_reason`, `fatal_error_message`), 429 대기 정보(`rate_limit_attempt`, `rate_limit_retry_at`)
    - `jobs.status` 값: `running` / `completed` / `stopped`
    - `job_items`: `playlist_item_id`, `error_reason`, 처리 순서(`position`)
    - `job_items.status`에 `pending`(아직 처리 전) 추가
43. PoC와 실제 동작 테스트에는 별도 테스트용 Google 계정을 쓴다. 기존 계정으로 할 때는 2~3개 소량으로만 한다.
    - (2026-10-04 갱신) 테스트 계정은 기존 계정 `hajin300@gmail.com`을 쓴다. 따라서 실제로 바꾸는 작업은 항상 2~3개 소량으로, 지워져도 되는 영상만 고른다. 테스트용 재생목록은 이름을 `LC Test 1`, `LC Test 2`처럼 지어 테스트 후 지우기 쉽게 한다.
    - P2-3의 "새 사용자 → 승인 대기" 확인에는 두 번째 Google 계정이 필요하다. 그 계정도 GCP 테스트 사용자로 등록한다(DECISIONS 51).
44. 로그인 유지 기간은 7일이다. 서버 재시작으로 메모리의 좋아요 목록이 사라지면 화면이 자동으로 다시 불러온다.
45. 사용자가 Google 계정 설정에서 권한을 끊어 토큰 갱신이 실패하면(`invalid_grant`), 2단계(YouTube 권한) 로그인으로 다시 보낸다.
46. YouTube 카테고리 이름은 `hl=en`, `regionCode=US`로 조회한다.
47. mock 모드는 지우지 않고, 개발 중에만 설정 하나로 mock / 실제 API를 바꿀 수 있게 남긴다. DEV 패널은 mock 모드일 때만 보인다. 운영 결과물(build)에는 mock과 DEV 패널이 들어가지 않는다. (PHASE1_NOTES 4장의 "mock 삭제"를 대체)
48. 실제 API를 쓸 때 진행 상황 조회 간격은 1.5초로 한다(mock은 0.7초 유지 가능).
49. 기획서 2장의 환경 변수에 두 가지를 더한다: `SESSION_SECRET`(로그인 쿠키 서명용 무작위 문자열), `DATABASE_URL`(선택, 기본값은 `backend/data/likecleaner.db`). `TOKEN_ENCRYPTION_KEY`와 `SESSION_SECRET`은 처음 설정할 때 자동 생성해 `backend/.env`에만 둔다.
50. 서버가 켜질 때 DB 구조를 자동으로 최신 상태로 맞춘다(alembic upgrade). 따로 DB 준비 명령을 실행할 필요가 없다.

## Phase 2 진행 중 결정 (2026-10-04)

51. Google OAuth 앱은 P2-1~P2-6 동안 **"테스트 중(Testing)" 상태**로 개발한다. 게시(In production)하려면 브랜딩의 홈페이지, 개인정보처리방침 주소, 승인된 도메인이 필요한데, 실제 인터넷 주소가 생기기 전에는 채울 수 없기 때문이다.
    - 개발 중에는 테스트 계정과 `hajin300@gmail.com`을 GCP 콘솔의 테스트 사용자로 등록해 쓴다. refresh token이 7일 뒤 만료되므로 가끔 다시 로그인한다.
    - P2-7에서 운영 주소가 생기면 홈페이지와 개인정보처리방침 주소를 넣고 게시해, 기획서 3-1의 운영 방식(In production, 검증 없음)으로 바꾼다. 브랜딩 로고는 올리지 않는다(올리면 앱 검증이 필요해진다).
    - 기획서 14장 PoC 2번("In production 상태에서 `youtube` 스코프 로그인과 refresh token 발급")은 P2-2가 아니라 P2-7에서 확인한다. P2-2에서는 테스트 상태에서 같은 로그인과 발급이 되는지만 확인한다.

## P2-2 PoC 결과로 정한 것 (2026-10-04, 자세한 내용은 `docs/POC_RESULTS.md`)

52. (59로 대체) 좋아요 목록은 기획서대로 `videos.list?myRating=like`로 마지막 페이지까지 가져온다. YouTube가 최근 약 1,000개(PoC: 969개)까지만 돌려주므로, Liked Videos 화면에는 **최근 좋아요 약 1,000개만** 보인다. 한 번에 전부 보여줄 필요는 없다는 판단이다.
    - "좋아요 표시한 동영상" 재생목록(`LL`)으로 전부(약 5,000개) 가져오는 방법은 쓰지 않는다. 불러올 때마다 약 200 units가 들고, 삭제/비공개 영상까지 섞여 나오기 때문이다.
    - `pageInfo.totalResults`는 실제로 받을 수 있는 개수와 달라(PoC: 6,173) 화면 숫자에 쓰지 않는다.
    - (2026-10-04 보완) 이 제한을 사용자에게 알린다. Liked Videos 화면 목록 위에 회색(`muted`) 안내 문구 `Showing your most recent liked videos (up to about 1,000, a YouTube limit).`를 표시한다. P2-4에서 화면을 연결할 때 반영한다.
53. 재생목록 항목의 상태 판정(`VideoAvailability`): `videoOwnerChannelTitle`이 없으면 볼 수 없는 영상이다. 그중 `status.privacyStatus`가 `private`이면 `private`, 그 밖에는 `deleted`로 본다. 나머지는 `available`이다. 자기 비공개 영상은 채널 이름이 있으므로 `available`이 된다.
    - (2026-10-04 확인) 내가 직접 올린 비공개 영상은 내가 볼 수 있으므로 `Remove Unavailable Videos` 대상에서 빠져야 한다. 실제 계정에서 확인한 결과, 내 비공개 영상(4개)은 `privacyStatus`가 `private`이지만 실제 제목, `videoOwnerChannelTitle`, 썸네일이 모두 있었다. 그래서 이 규칙으로 `available`이 되므로 규칙은 그대로 둔다(`POC_RESULTS.md` 3장).
54. 자동 정렬 재생목록에서도 `position=0` 추가가 오류 없이 됐다(`manualSortRequired`가 나지 않음). 그래도 기획서 6장의 "위치 없이 다시 추가" 처리와 DECISIONS 30의 예상 소모량 50 units 추가는 혹시 모를 경우를 위해 그대로 둔다.
55. 재생목록 추가·삭제는 몇 초(PoC: 약 5초) 뒤에야 조회에 반영된다. 작업이 끝난 직후 재생목록을 다시 불러오면 이전 상태가 보일 수 있다. 처리 방법은 P2-5/P2-6에서 정하되, 화면 동작이 바뀌면 먼저 묻는다.
    - (2026-10-04 결정) 작업이 끝난 직후에는 목록을 다시 불러오지 않는다. 작업 결과(성공한 항목)를 기준으로 화면을 바로 갱신한다.
    - 작업 완료 후 10초 안에 `Resync`를 누르면 버튼을 잠시 비활성화하고 `Syncing with YouTube...`를 표시한다. 10초가 지나면 다시 불러온다. 작업 완료 후 10초가 지났거나 작업이 없었으면 `Resync`는 바로 다시 조회한다.
    - 적용은 P2-5, P2-6에서 한다.

## 승인 흐름 단순화: 허용 목록 방식 (2026-10-04)

56. 회원가입이 없으므로 승인 대기(pending)와 알림 메일을 없애고, **admin이 미리 등록한 이메일만 쓸 수 있는 허용 목록 방식**으로 바꾼다. 기획서 3-3, 5장 화면 목록, 9장 `users` 테이블, 13장 Acceptance Criteria의 관련 내용은 이 결정으로 대체된다. DECISIONS 39, 40도 대체한다.
    - 사용자는 admin이 DB에 이메일을 미리 등록해야 쓸 수 있다. 등록은 터미널의 사용자 관리 명령으로 한다(admin 화면은 만들지 않는다, 기획서 12장). 등록되지 않은 이메일로 로그인하면 **Access Denied** 화면을 보여준다.
    - `users.status`는 `active` / `disabled` 두 가지만 쓴다. `pending`, `rejected`는 없앤다. `active`인 사용자만 2단계(YouTube 권한)로 가고 YouTube 관련 API를 쓸 수 있다. `disabled`도 Access Denied 화면을 본다.
    - 화면과 API(`User.status`)에서는 등록되지 않은 경우를 `not_registered`로 나타낸다. DB에는 저장하지 않는다.
    - Pending Approval 화면과 admin 알림 메일 기능을 없앤다. SMTP 관련 환경 변수(`SMTP_USER`, `SMTP_APP_PASSWORD`)와, 메일에만 쓰던 백엔드의 `ADMIN_EMAIL`은 현재 쓰지 않는다. 메일 발송 client(`clients/mail_client.py`)는 나중을 위해 지우지 않고 쓰지 않는 상태로 둔다.
    - Access Denied 화면 문구: `This Google account ({email}) doesn't have access to LikeCleaner. Please contact the admin.` 로그인한 이메일을 보여주고 `Sign in with a different account` 버튼을 둔다. 이 버튼은 로그아웃한 뒤 Google 로그인을 다시 시작한다. 다른 계정을 고를 수 있도록 Google 로그인은 항상 계정 선택 화면을 보여준다.
    - Acceptance Criteria(13장 "로그인과 승인")는 다음으로 바꾼다: 등록되지 않았거나 `disabled`인 사용자는 로그인 후 Access Denied 화면에서 자기 이메일을 본다. `active`인 사용자만 좋아요 목록과 재생목록을 볼 수 있다.

## P2-3 로그인 세부 사항 (2026-10-04)

57. 로그인 구현 세부 사항
    - YouTube 권한(2단계)은 **처음 한 번만** 요청한다. YouTube 권한이 포함된 refresh token이 저장돼 있으면 다음 로그인부터는 1단계 뒤 바로 메인 화면으로 간다. 토큰이 끊기면(`invalid_grant`) 토큰을 지우고 403 `youtubeReauthRequired`를 준다. 다음 로그인 때 2단계를 다시 거친다(DECISIONS 45).
    - 2단계에서 YouTube 권한을 거부하거나 취소하면 로그인 화면으로 돌아가 빨간 글씨로 `LikeCleaner needs access to your YouTube account. Please sign in again and allow access.`를 보여준다(기획서에 없던 문구).
    - 로그인 세션은 서명된 쿠키(`lc_session`, 7일, HttpOnly, SameSite=Lax, https 주소에서는 Secure)로 관리한다. 쿠키에는 사용자 번호, Access Denied 화면용 이메일·이름·사진, 로그인 진행 확인값(state)만 넣고 토큰은 넣지 않는다. 사용자 상태는 매 요청마다 DB에서 다시 확인하므로, `disabled`로 바꾸면 바로 막힌다.
    - 환경 변수 `APP_BASE_URL`(비우면 `http://localhost:5173`)을 더한다. Google 리디렉션 주소는 이 값에 `/api/auth/google/callback`을 붙여 만든다. 운영 주소는 P2-7에서 넣는다.
    - P2-3에서는 화면 중 로그인 부분만 실제 백엔드에 연결한다(`npm run dev:real`). 나머지는 P2-4 전까지 `notAvailableYet` 오류로 보인다. `npm run dev`는 mock 그대로다.
    - Access Denied를 본 사람이 나중에 등록되면, 다음 화면 갱신 때 로그인 화면으로 돌아간다. 다시 로그인하면 들어갈 수 있다.

## P2-4 조회 세부 사항 (2026-10-04)

58. 조회 API와 서버 메모리
    - 좋아요 목록과 재생목록 항목은 사용자별로 서버 메모리에만 둔다(DB 저장 안 함). (좋아요 목록을 불러오는 방법은 59로 대체) 메모리에 있으면 그대로 돌려준다(0 units). 비어 있으면(서버 재시작 등) 자동으로 YouTube에서 다시 불러온다. `Resync`는 `refresh=true`로 항상 다시 전체 조회한다. 로그아웃하면 그 사용자의 메모리를 지우고, 7일이 지난 데이터도 쓰지 않는다.
    - 모든 YouTube 호출은 `services/youtube_gateway.py` 한 곳을 거치며, 호출마다 `quota_usage`에 한 줄씩 기록한다(성공·실패·재시도 모두).
    - access token은 만료 1분 전까지 서버 메모리에 두고 다시 쓴다(DB에는 refresh token만 암호화해 저장).
    - 카테고리 이름: YouTube는 `id`와 `regionCode`를 함께 받지 않는다. 그래서 먼저 미국(`regionCode=US`, `hl=en`) 카테고리 전체 목록을 한 번 받아 서버 메모리에 둔다. 그 목록에 없는 번호만 `id`로 다시 묻는다. 서버 한 번 실행에 보통 1 unit이다.
    - `Quota` 응답에 `remaining`(남은 양)과 `resetsInSeconds`(리셋까지 남은 초)를 더한다. 화면 표시는 기존처럼 `limit`, `used`, `resetsAt`을 쓴다.
    - Liked Videos 목록 위에 DECISIONS 52의 안내 문구를 표시한다(mock 모드 포함).

## P2-4 보완 (2026-10-04)

59. 좋아요 목록은 **전체**를 불러온다(52번 대체). 자세한 비교는 `POC_RESULTS.md` 1장.
    - 방법: "좋아요 표시한 동영상" 재생목록(`playlistItems.list`, `playlistId=LL`)을 끝까지 읽는다. 페이지마다 볼 수 있는 영상만 `videos.list(id=…)` 50개씩으로 길이·카테고리 등을 가져온다.
    - 실제 계정 기준: 4,919개를 읽어 4,637개를 보여주고 282개를 숨겼다. 약 70~80초, 199 units가 들었다. 지금 방식(`myRating`)은 969개, 20 units였다. 다만 YouTube가 `myRating`에서 알려준 6,173개와는 차이가 있다. 웹에서도 5,000개까지만 보이므로, LL로 받을 수 있는 수가 YouTube가 허락하는 최대치로 본다.
    - 삭제/비공개이거나 `videos.list`에 없는 영상은 목록에서 빼고, 개수 옆에 작게 `N unavailable videos hidden`만 표시한다(0이면 표시 안 함). 52번 보완의 회색 안내 문구(`up to about 1,000`)는 지운다.
    - 오래 걸리므로 서버의 백그라운드 작업으로 불러온다. 순서는 `POST /api/likes/load`(Resync는 `refresh=true`) → `GET /api/likes/status`(1초마다) → `GET /api/likes`다. 불러오는 동안 화면에 `Loading your liked videos… N loaded`를 보여주고, 다른 요청(재생목록, 할당량 등)은 막히지 않는다. 로그아웃하거나 서버가 꺼지면 진행 중인 불러오기를 멈춘다.
    - 서버 메모리 규칙(58)은 그대로다. 새로고침은 0 units이고, Resync는 다시 전체를 읽으므로 약 200 units가 든다.
    - P2-2 PoC에서 쓴 할당량(약 1,300 units)이 기록에 빠져 있어, `quota_usage`에 `PoC manual adjustment` 1,300 units(2026-10-04, 태평양 시간)를 한 번만 직접 넣었다. 앱 코드와 테스트에는 영향이 없다.

60. 목록에 YouTube 링크를 둔다.
    - Liked Videos와 재생목록 항목 표의 맨 끝에 `Link` 열을 둔다. 외부 링크 아이콘을 누르면 `https://www.youtube.com/watch?v={videoId}`가 새 탭으로 열린다(`rel="noopener noreferrer"`). 아이콘을 눌러도 행의 체크박스 선택은 바뀌지 않는다.
    - 삭제/비공개로 볼 수 없는 영상은 아이콘을 회색 비활성으로 두고 `Not available` 툴팁을 보여준다.
    - Playlists 화면의 재생목록 목록에도 각 재생목록 링크(`https://www.youtube.com/playlist?list={playlistId}`)를 둔다. 재생목록 선택 버튼 옆에 따로 둔다.
    - 주소는 `frontend/src/utils/youtubeLinks.ts` 한 곳에서 만들고, 아이콘은 `components/YouTubeLink.tsx`를 함께 쓴다. mock/실제 모드 모두 같고, API 호출이나 할당량은 쓰지 않는다.

## P2-5 전 보완 (2026-10-05)

61. 좋아요가 YouTube 상한(약 5,000개)보다 많으면 안내한다.
    - 좋아요를 불러올 때 맨 먼저 `videos.list(myRating=like, part=id, maxResults=1)`를 한 번 불러 `pageInfo.totalResults`(YouTube가 아는 좋아요 전체 수)를 받는다(1 unit). 이 호출이 실패해도 불러오기는 계속하고, 안내만 보이지 않는다.
    - 전체 수가 불러온 개수(보이는 영상 + 숨긴 영상)보다 크면 Liked Videos 목록 위에 회색(`muted`) 안내를 보여준다: `YouTube lets us read about 5,000 of your N liked videos. Remove some likes and press Resync to reach older ones.` 같으면(또는 전체 수를 모르면) 보여주지 않는다.
    - N은 "불러온 개수 + 못 불러온 개수"로 계산하므로, 작업으로 좋아요를 취소하면 그만큼 줄어든다.
    - 52번에서 "`totalResults`는 화면 숫자에 쓰지 않는다"고 했지만, 이 안내 문구에만 쓴다. mock 계정은 전부 읽히므로 안내가 나오지 않는다.
62. `Resync` 버튼에 예상 소모량을 보여준다.
    - 마우스를 올리면 `Uses about N units` 툴팁이 나온다. 작업 중일 때는 기존처럼 `Available when the current job finishes`.
    - Liked Videos: `(지난번 읽은 좋아요 수 ÷ 50, 올림) × 2 + 2` (LL 페이지 + `videos.list` + 전체 수 1 + 카테고리 약 1). 4,919개면 약 200 units.
    - Playlists: `(항목 수 ÷ 50, 올림) + (볼 수 있는 영상 수 ÷ 50, 올림)`. 열려 있는 재생목록 기준이다.
    - 남은 할당량이 예상보다 적으면 `Resync`를 비활성화하고 버튼 왼쪽에 빨간 글씨 `Not enough quota to resync (needs about N units).`를 표시한다.
    - 로그인 직후 처음 불러오는 동안 로딩 문구 아래에 작게 `The first load after sign-in uses up to about 200 units of today's quota.`를 표시한다(최대 5,000개 기준 202 units를 반올림).

## P2-5 작업 처리 (2026-10-05)

63. 작업 처리 세부 사항
    - **서버 재시작 시 중단 처리(사용자 결정).** 서버가 켜질 때 `running`으로 남은 작업은 이어서 하지 않고 `stopped`로 바꾼다. 남은 항목은 `Not processed`, 작업을 멈춘 오류는 `503 serverRestarted` `The server restarted while this job was running. Use Retry Failed to continue.`이다. 끊긴 순간 처리 중이던 항목은 실제로는 처리됐어도 `Not processed`로 보일 수 있다. 이어서 할지는 사용자가 `Retry Failed`로 정한다. (PHASE2_PLAN의 "이어서 처리"를 대체)
    - **429는 항목 전체가 아니라 그 호출만** 2/4/8초 뒤 다시 시도한다. 이미 성공한 "재생목록 추가"를 다시 해서 영상이 두 번 들어가는 일을 막기 위해서다. 대기 중에는 `jobs.rate_limit_*`에 기록해 진행 패널에 `Rate limited. Retrying in N s...`를 보여준다.
    - **작업을 멈추는 오류:** `quotaExceeded`, 3번 재시도 후에도 나는 429, YouTube 권한 끊김(`youtubeReauthRequired`) 등 다음 항목도 실패할 것이 확실한 오류. 그 밖의 오류(404 등)는 그 항목만 `Failed`로 두고 계속한다.
    - **멈출 때 반쯤 된 항목을 남기지 않는다.** 이동+좋아요 취소에서 추가는 됐는데 좋아요 취소에서 작업이 멈추면, 먼저 추가한 항목을 지운다(롤백). 성공하면 `Failed`, 실패하면 `Rollback failed`로 두고 작업을 멈춘다.
    - **이동 작업의 중복 확인**은 대상 재생목록을 YouTube에서 새로 읽는다(재생목록 화면을 여는 것과 같은 조회, `videos.list` 포함). 그래서 작업이 끝나면 서버 메모리에 대상 재생목록이 최신으로 있고, 화면은 YouTube를 다시 부르지 않고 서버 메모리에서 결과를 받는다(0 units, 몇 초 지연 문제 없음). 대신 예상 소모량의 중복 확인 부분이 `항목 50개당 1`에서 `항목 50개당 1 + 50개당 1`로 늘었다(프론트, 서버, mock 모두 같은 공식).
    - 성공한 항목은 서버 메모리에 바로 반영한다(DECISIONS 55): 좋아요 취소 → 좋아요 목록과 전체 좋아요 수에서 뺀다, 재생목록 삭제 → 그 재생목록에서 뺀다, 추가 → 대상 재생목록 맨 앞(자동 정렬이면 끝)에 넣는다.
    - 서버도 작업을 만들 때 1인 1작업, 1~100개, 할당량(DB 기록 기준)을 다시 확인한다. 동시에 두 번 눌러도 작업은 하나만 생긴다.
    - 작업 화면 연결(P2-6에서 앞당김): `POST /api/jobs`, `POST /api/jobs/{id}/retry`, `GET /api/jobs/latest`. 진행 상황은 실제 모드 1.5초, mock 0.7초마다 조회한다(DECISIONS 48).
    - DECISIONS 55의 `Resync` 대기: 작업이 끝난 시각(`finishedAt`)에서 10초 안에 누르면 버튼이 `Syncing with YouTube...`로 바뀌고 꺼졌다가, 10초가 되면 자동으로 다시 불러온다.
    - 30일 지난 `jobs`, `job_items`, `quota_usage`는 서버가 켜질 때 한 번, 그 뒤 24시간마다 지운다.

# 진드기 CREW API

SOOP 라이브 상태, 게시글 등을 실시간으로 가져오는 FastAPI 백엔드입니다.

## 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 서버 상태 확인 |
| GET | `/api/live` | 전체 멤버 라이브 상태 |
| GET | `/api/live/{soopId}` | 특정 멤버 라이브 상태 |
| GET | `/api/posts` | 전체 멤버 최신 게시글 |
| GET | `/api/posts/{soopId}` | 특정 멤버 게시글 |
| GET | `/api/members` | 멤버 목록 |

## Render 배포 방법

1. GitHub에 이 폴더를 push
2. [render.com](https://render.com) → New → Web Service
3. GitHub 레포 연결
4. 아래 설정:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. 배포 완료 후 URL 복사 (예: `https://jindeugi-crew-api.onrender.com`)

## HTML 파일 연동

`jindeugi-crew.html` 파일 상단의:
```javascript
const API_BASE = 'https://YOUR-APP-NAME.onrender.com';
```
→ 실제 Render URL로 교체하면 끝!

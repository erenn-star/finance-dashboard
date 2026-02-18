# 금융 IT 뉴스 크롤링 대시보드

국내 15개 언론사/기관에서 금융/IT 뉴스를 자동 수집하고, 전문 키워드를 분석하여 시각화하는 대시보드입니다.

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | Python, FastAPI, SQLAlchemy |
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| DB | PostgreSQL (배포) / SQLite (로컬) |
| 크롤링 | requests, BeautifulSoup4, feedparser |
| 키워드 분석 | 금융IT 전문용어 사전 기반 매칭 (120+ 키워드) |
| 시각화 | Recharts (바 차트 + 도넛 차트) |
| 배포 | Railway (백엔드) + Vercel (프론트엔드) |

## 주요 기능

- RSS 피드 + 웹 크롤링으로 15개 소스에서 뉴스 자동 수집
- 금융IT 전문 키워드 사전 기반 키워드 추출 및 TOP 20 시각화
- 키워드 빈도 도넛 차트 + 바 차트 이중 시각화
- 키워드 클릭 시 관련 뉴스 목록 (제목 + 언론사 + 날짜 + 원문 링크)
- 사주 기반 오늘의 운세 (금전운/사업운)
- 다크 모드 지원

## 크롤링 소스 (15개)

**RSS 피드 (12개)**:
전자신문(IT/경제), 아이뉴스24(IT/경제), 비즈니스워치, 파이낸셜뉴스(전체/IT), 머니투데이, 이투데이, 한국경제, 뉴시스(경제/금융)

**웹 크롤링 (3개)**:
지디넷코리아, KDI 한국개발연구원, 은행연합회

---

## 로컬 개발 환경 설정

### 사전 요구사항

- Python 3.9+
- Node.js 18+ (nvm 권장)
- PostgreSQL 또는 SQLite (기본값)

### 1. 백엔드 실행

```bash
cd backend

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치 (로컬용 — PostgreSQL/konlpy 제외)
pip install -r requirements-local.txt

# 서버 실행 (SQLite 자동 사용)
uvicorn main:app --reload --port 8000
```

### 2. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 접속 후 "지금 수집" 버튼 클릭.

---

## 배포 가이드

### 아키텍처

```
[사용자 브라우저]
       |
   [Vercel] ── 프론트엔드 (React + Vite)
       |
       | /api/* 요청을 Rewrite
       |
   [Railway] ── 백엔드 (FastAPI)
       |
   [Railway PostgreSQL] ── 데이터베이스
```

### Step 1: GitHub 리포지토리 준비

```bash
cd finance-dashboard
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/finance-dashboard.git
git push -u origin main
```

### Step 2: Backend → Railway

1. [Railway](https://railway.app) 로그인 → **New Project** → **Deploy from GitHub repo**
2. 리포지토리 선택 후 **Root Directory**를 `backend`로 설정
3. **Add Plugin** → **PostgreSQL** 추가
   - `DATABASE_URL` 환경변수가 자동으로 설정됨
4. **Variables** 탭에서 환경변수 추가:

   | 변수명 | 값 |
   |--------|-----|
   | `CORS_ORIGIN` | `https://your-app.vercel.app` (Step 3 이후 설정) |

5. **Settings** → **Networking** → **Generate Domain** 클릭
6. 생성된 도메인 복사 (예: `https://finance-dashboard-production.up.railway.app`)

### Step 3: Frontend → Vercel

1. [Vercel](https://vercel.com) 로그인 → **Add New Project** → GitHub 리포지토리 선택
2. **Root Directory**를 `frontend`로 설정
3. **Framework Preset**: `Vite` 선택
4. **Environment Variables** 추가:

   | 변수명 | 값 |
   |--------|-----|
   | `VITE_API_URL` | `https://your-app.up.railway.app` (Railway 도메인) |

5. **Deploy** 클릭
6. 배포 완료 후 Vercel 도메인 확인 (예: `https://finance-dashboard.vercel.app`)

### Step 4: vercel.json 수정

`frontend/vercel.json`의 `YOUR_RAILWAY_DOMAIN`을 실제 Railway 도메인으로 교체:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://finance-dashboard-production.up.railway.app/api/:path*"
    },
    { "source": "/(.*)", "destination": "/" }
  ]
}
```

변경 후 커밋 & 푸시하면 Vercel이 자동 재배포합니다.

### Step 5: CORS 연결

Railway **Variables**에서 `CORS_ORIGIN`을 Vercel 도메인으로 설정:

```
CORS_ORIGIN=https://finance-dashboard.vercel.app
```

### 배포 확인

```bash
# 백엔드 헬스체크
curl https://your-app.up.railway.app/api/health

# 뉴스 수집 테스트
curl -X POST https://your-app.up.railway.app/api/collect

# 프론트엔드 접속
open https://finance-dashboard.vercel.app
```

---

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| `POST` | `/api/collect` | RSS/웹 크롤링 실행 |
| `GET` | `/api/stats` | 대시보드 통계 |
| `GET` | `/api/keywords/{period}` | 키워드 TOP 20 (`1d` / `7d`) |
| `GET` | `/api/articles?keyword=&source=&period=` | 뉴스 목록 |
| `GET` | `/api/sources` | 언론사별 수집 현황 |
| `GET` | `/api/fortune` | 오늘의 운세 |
| `GET` | `/api/health` | 헬스 체크 |

## 환경변수

`.env.example` 파일 참고:

| 변수 | 위치 | 설명 |
|------|------|------|
| `DATABASE_URL` | Backend | DB 연결 문자열 (기본: SQLite) |
| `CORS_ORIGIN` | Backend | 허용할 프론트엔드 도메인 |
| `VITE_API_URL` | Frontend | 백엔드 API 도메인 (로컬은 빈 값) |

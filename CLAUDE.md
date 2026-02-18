# Project: 금융 IT 뉴스 크롤링 대시보드

## Structure
- `backend/` — Python FastAPI 서버 (port 8000)
- `frontend/` — React + TypeScript + Vite (port 5173)
- DB: SQLite (로컬) / PostgreSQL (Railway 배포)

## Backend
- **Framework**: FastAPI + SQLAlchemy + uvicorn
- **Python 3.9** (system) — `str | None` 사용 불가, `Optional[str]` 사용
- **키워드 추출**: `analyzer.py` — konlpy 없이 금융IT 전문용어 사전(120+) 기반 정규식 매칭
- **크롤링**: `crawler.py` — RSS 12개 + 웹 크롤링 3개 (지디넷코리아, KDI, 은행연합회)
- **DB 분기**: `database.py` — `_is_sqlite` 플래그로 SQLite/PostgreSQL 자동 분기
- **main.py 주의**: `nullslast()`는 SQLite 미지원 → `_is_sqlite` 조건 분기 필요
- **requirements.txt**: 배포용 (psycopg2 포함)
- **requirements-local.txt**: 로컬용 (psycopg2/konlpy 제외)

## Frontend
- **React 19** + TypeScript + Vite 6 + Tailwind CSS 3
- **Recharts**: BarChart (키워드 TOP 20), PieChart (도넛 TOP 10)
- `vite.config.ts`에서 `/api` 프록시 → localhost:8000
- 다크 모드 지원

## Commands
```bash
# 백엔드 실행 (로컬)
cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000

# 프론트엔드 실행
cd frontend && npm run dev

# 뉴스 수집 테스트
curl -X POST http://localhost:8000/api/collect
```

## Deploy
- **Backend** → Railway (root: `backend`, PostgreSQL plugin)
- **Frontend** → Vercel (root: `frontend`, framework: Vite)
- `vercel.json`에서 `/api/*`를 Railway 도메인으로 rewrite
- Railway `CORS_ORIGIN` = Vercel 도메인

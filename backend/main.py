import hashlib
import logging
import os
from datetime import datetime, timedelta, date
from typing import Optional

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from collections import Counter

from analyzer import extract_keywords_from_title, get_top_keywords
from crawler import crawl_all
from job_crawler import crawl_jobs
from database import Article, CollectionLog, Job, SessionLocal, _is_sqlite, init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Finance IT News Dashboard API")

# CORS
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in CORS_ORIGIN.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("Database initialized")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post("/api/collect")
def collect_news(db: Session = Depends(get_db)):
    """Crawl all RSS feeds, store new articles, and return summary."""
    articles = crawl_all()
    new_count = 0

    for art in articles:
        keywords = extract_keywords_from_title(art["title"])
        # Check if article already exists (by link)
        exists = db.query(Article.id).filter(Article.link == art["link"]).first()
        if exists:
            continue
        article = Article(
            title=art["title"],
            link=art["link"],
            source=art["source"],
            published_at=art["published_at"],
            collected_at=datetime.utcnow(),
            keywords=keywords,
        )
        db.add(article)
        new_count += 1

    log = CollectionLog(
        collected_at=datetime.utcnow(),
        total_articles=len(articles),
        new_articles=new_count,
    )
    db.add(log)
    db.commit()

    logger.info(f"Collected {new_count} new articles out of {len(articles)}")

    # ── 수집된 키워드 집계 로그 ──
    kw_counter: Counter = Counter()
    all_rows = db.query(Article.keywords).filter(Article.collected_at >= datetime.utcnow() - timedelta(days=1)).all()
    for (kws,) in all_rows:
        if kws:
            for k in kws.split(","):
                k = k.strip()
                if k:
                    kw_counter[k] += 1
    if kw_counter:
        logger.info("=== 키워드 집계 (최근 1일) ===")
        for kw, cnt in kw_counter.most_common(30):
            logger.info(f"  {kw}: {cnt}회")
        logger.info(f"  (총 {len(kw_counter)}개 고유 키워드)")
    else:
        logger.info("추출된 키워드 없음")

    return {
        "total_crawled": len(articles),
        "new_articles": new_count,
        "collected_at": log.collected_at.isoformat(),
    }


@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """Return dashboard summary stats."""
    total_articles = db.query(func.count(Article.id)).scalar() or 0
    last_log = (
        db.query(CollectionLog)
        .order_by(CollectionLog.collected_at.desc())
        .first()
    )
    return {
        "total_articles": total_articles,
        "last_collected_at": (
            last_log.collected_at.isoformat() if last_log else None
        ),
    }


@app.get("/api/keywords/{period}")
def get_keywords(period: str, db: Session = Depends(get_db)):
    """Return top 20 keywords for '1d' or '7d' period."""
    if period == "1d":
        since = datetime.utcnow() - timedelta(days=1)
    elif period == "7d":
        since = datetime.utcnow() - timedelta(days=7)
    else:
        since = datetime.utcnow() - timedelta(days=1)

    rows = (
        db.query(Article.keywords, Article.source)
        .filter(Article.collected_at >= since)
        .all()
    )
    keyword_source_pairs = [(r[0], r[1]) for r in rows if r[0]]

    min_count = 2 if period == "1d" else 3

    top = get_top_keywords(
        keyword_source_pairs,
        top_n=20,
        min_count=min_count,
    )

    # 키워드별 대표 뉴스 제목 요약 생성
    for kw_entry in top:
        kw = kw_entry["keyword"]
        articles = (
            db.query(Article.title)
            .filter(
                Article.collected_at >= since,
                Article.keywords.contains(kw),
            )
            .order_by(Article.published_at.desc())
            .limit(5)
            .all()
        )
        titles = [a[0] for a in articles]
        kw_entry["summary"] = _summarize_titles(kw, titles)

    return {"period": period, "keywords": top}


def _summarize_titles(keyword: str, titles: list) -> str:
    """뉴스 제목들에서 키워드 관련 핵심 내용을 추출하여 한줄 요약 생성."""
    if not titles:
        return ""
    # 가장 최신 제목에서 키워드 부분을 제외한 핵심 내용 추출
    # 여러 제목의 공통 주제를 찾아 요약
    clean_titles = []
    for t in titles[:3]:
        # 대괄호/괄호 안 부연 정보 제거
        import re
        t = re.sub(r"\[.*?\]", "", t)
        t = re.sub(r"\(.*?\)", "", t)
        t = t.strip().rstrip("…").rstrip(".")
        if t:
            clean_titles.append(t)
    if not clean_titles:
        return titles[0][:50] if titles else ""
    # 첫 번째(최신) 제목을 대표로, 50자 제한
    summary = clean_titles[0]
    if len(summary) > 50:
        summary = summary[:47] + "..."
    return summary


@app.get("/api/articles")
def get_articles(
    keyword: Optional[str] = None,
    source: Optional[str] = None,
    period: str = "7d",
    db: Session = Depends(get_db),
):
    """Return articles filtered by keyword and/or source."""
    if period == "1d":
        since = datetime.utcnow() - timedelta(days=1)
    else:
        since = datetime.utcnow() - timedelta(days=7)

    q = db.query(Article).filter(Article.collected_at >= since)

    if keyword:
        q = q.filter(Article.keywords.contains(keyword))
    if source:
        q = q.filter(Article.source == source)

    if _is_sqlite:
        # SQLite: sort NULLs last using CASE expression
        from sqlalchemy import case
        q = q.order_by(
            case((Article.published_at.is_(None), 1), else_=0),
            Article.published_at.desc(),
        ).limit(100)
    else:
        q = q.order_by(Article.published_at.desc().nullslast()).limit(100)

    return [
        {
            "id": a.id,
            "title": a.title,
            "link": a.link,
            "source": a.source,
            "published_at": (
                a.published_at.isoformat() if a.published_at else None
            ),
            "keywords": a.keywords,
        }
        for a in q.all()
    ]


@app.get("/api/sources")
def get_sources(db: Session = Depends(get_db)):
    """Return article count per source for the last 7 days."""
    since = datetime.utcnow() - timedelta(days=7)
    rows = (
        db.query(Article.source, func.count(Article.id))
        .filter(Article.collected_at >= since)
        .group_by(Article.source)
        .order_by(func.count(Article.id).desc())
        .all()
    )
    return [{"source": name, "count": cnt} for name, cnt in rows]


@app.get("/api/fortune")
def get_fortune():
    """사주 기반 오늘의 금전운/사업운 반환."""
    today = date.today()
    seed = int(hashlib.md5(today.isoformat().encode()).hexdigest(), 16)

    # 사주 정보: 신사년 경인월 경신일 병술시 — 일주 庚금
    # 오행: 목1 화2 토1 금4 수0
    # 금이 과다, 수가 부족 → 날짜별 오행 기운 변화로 운세 생성

    천간 = ["甲목", "乙목", "丙화", "丁화", "戊토", "己토", "庚금", "辛금", "壬수", "癸수"]
    지지 = ["子수", "丑토", "寅목", "卯목", "辰토", "巳화", "午화", "未토", "申금", "酉금", "戌토", "亥수"]

    day_num = (today - date(2024, 1, 1)).days
    today_천간 = 천간[day_num % 10]
    today_지지 = 지지[day_num % 12]

    # 일주 庚금 기준 오행 상성 판단
    오행_element = today_천간[-1]  # 목/화/토/금/수

    오행_names = {"목": "木", "화": "火", "토": "土", "금": "金", "수": "水"}
    오행_emoji = {"목": "\U0001f331", "화": "\U0001f525", "토": "\u26f0\ufe0f", "금": "\u2728", "수": "\U0001f4a7"}

    운세_messages = {
        "목": [
            "목(木) 기운의 성장하는 날 \U0001f331 새로운 기획과 아이디어가 빛을 발해요",
            "목(木)의 생명력이 넘치는 하루 \U0001f333 배움의 기운이 당신을 감싸고 있어요",
            "목(木)이 하늘을 향해 뻗듯, 당신의 커리어도 쭉쭉 \U0001f331 한 걸음씩 전진하고 있어요",
        ],
        "화": [
            "화(火)의 날, 열정이 넘치는 하루! \U0001f525 면접도 PT도 자신감 있게 도전하세요",
            "화(火) 기운으로 표현력이 빛나는 날 \U0001f525 당신의 이야기에 사람들이 귀 기울여요",
            "화(火)의 에너지가 가득! \U0001f4aa 지금 준비하는 모든 것이 빛날 순간이 와요",
        ],
        "토": [
            "토(土) 기운의 안정적인 하루 \u26f0\ufe0f 기본기를 다지는 공부가 큰 힘이 돼요",
            "토(土)의 묵직한 기운 \u26f0\ufe0f 차근차근 쌓아온 실력이 곧 인정받을 거예요",
            "토(土)가 모든 것의 기반이듯, 오늘의 노력이 미래의 토대가 돼요 \u26f0\ufe0f",
        ],
        "금": [
            "금(金) 기운이 강한 오늘, 논리적 사고가 빛을 발해요 \u2728 분석 능력이 돋보이는 날!",
            "금(金)의 날카로운 통찰력 \u2728 복잡한 문제도 명쾌하게 정리할 수 있어요",
            "庚금 일주에 금(金) 기운이 더해져 강한 추진력! \u2728 결단의 시간이에요",
        ],
        "수": [
            "수(水)의 유연한 기운 \U0001f4a7 창의적 사고가 돋보이는 날, 새로운 관점을 시도해보세요",
            "수(水)가 흐르듯 자연스러운 하루 \U0001f4a7 기술 학습에 최적의 날이에요",
            "수(水)의 지혜로운 기운 \U0001f30a 유연한 대처가 좋은 결과를 만들어요",
        ],
    }

    응원_messages = [
        "오늘의 당신은 이미 충분히 잘하고 있어요 \U0001f49b",
        "작은 진전도 큰 성장이에요, 자신을 칭찬해주세요 \U0001f44f",
        "당신의 노력은 반드시 결실을 맺을 거예요 \U0001f31f",
        "포기하지 않는 것 자체가 대단한 일이에요 \U0001f4aa",
        "지금 이 순간에도 당신은 성장하고 있어요 \U0001f680",
        "힘든 시간도 지나고 나면 소중한 경험이 돼요 \U0001f338",
        "당신만의 속도로 괜찮아요, 비교하지 마세요 \U0001f30c",
        "오늘 하루도 수고했어요, 내일은 더 좋은 날이 올 거예요 \u2600\ufe0f",
        "꿈을 향해 달리는 당신이 멋져요 \U0001f3c3",
        "세상에 쓸모없는 노력은 없어요 \U0001f48e",
    ]

    idx = seed % 3
    cheer_idx = (seed >> 8) % len(응원_messages)

    금전_score = 60 + (seed % 36)
    사업_score = 60 + ((seed >> 4) % 36)

    colors = ["파란색", "빨간색", "노란색", "초록색", "보라색", "흰색", "검정색", "주황색"]
    lucky_color = colors[seed % len(colors)]
    lucky_number = (seed % 9) + 1

    return {
        "date": today.isoformat(),
        "천간": today_천간,
        "지지": today_지지,
        "element": 오행_element,
        "element_hanja": 오행_names.get(오행_element, ""),
        "element_emoji": 오행_emoji.get(오행_element, ""),
        "fortune_message": 운세_messages[오행_element][idx],
        "cheer_message": 응원_messages[cheer_idx],
        "money": {
            "score": 금전_score,
            "message": 운세_messages[오행_element][idx],
        },
        "business": {
            "score": 사업_score,
            "message": 운세_messages[오행_element][(idx + 1) % 3],
        },
        "lucky_color": lucky_color,
        "lucky_number": lucky_number,
    }


@app.post("/api/collect-jobs")
def collect_jobs(db: Session = Depends(get_db)):
    """채용공고 수집."""
    jobs = crawl_jobs()
    new_count = 0

    for j in jobs:
        if not j.get("url"):
            continue
        exists = db.query(Job.id).filter(Job.url == j["url"]).first()
        if exists:
            continue
        job = Job(
            company=j["company"],
            title=j["title"],
            region=j.get("region", ""),
            job_type=j.get("job_type", ""),
            url=j["url"],
            posted_date=j.get("posted_date", ""),
            collected_at=datetime.utcnow(),
        )
        db.add(job)
        new_count += 1

    db.commit()
    logger.info(f"채용공고 {new_count}건 신규 저장 (총 크롤링 {len(jobs)}건)")
    return {"total_crawled": len(jobs), "new_jobs": new_count}


@app.get("/api/jobs")
def get_jobs(
    region: Optional[str] = None,
    type: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """채용공고 목록 (필터링)."""
    q = db.query(Job).order_by(Job.collected_at.desc())

    if region:
        q = q.filter(Job.region == region)
    if type:
        q = q.filter(Job.job_type == type)
    if keyword:
        q = q.filter(Job.title.contains(keyword))

    jobs = q.limit(200).all()
    return [
        {
            "id": j.id,
            "company": j.company,
            "title": j.title,
            "region": j.region,
            "job_type": j.job_type,
            "url": j.url,
            "posted_date": j.posted_date,
        }
        for j in jobs
    ]


@app.get("/api/job-stats")
def get_job_stats(db: Session = Depends(get_db)):
    """채용공고 지역별/유형별 통계."""
    by_region = (
        db.query(Job.region, func.count(Job.id))
        .filter(Job.region != None, Job.region != "")
        .group_by(Job.region)
        .order_by(func.count(Job.id).desc())
        .all()
    )
    by_type = (
        db.query(Job.job_type, func.count(Job.id))
        .filter(Job.job_type != None, Job.job_type != "")
        .group_by(Job.job_type)
        .order_by(func.count(Job.id).desc())
        .all()
    )
    total = db.query(func.count(Job.id)).scalar() or 0
    return {
        "total": total,
        "by_region": [{"region": r, "count": c} for r, c in by_region],
        "by_type": [{"type": t, "count": c} for t, c in by_type],
    }


@app.get("/api/job-companies")
def get_job_companies(db: Session = Depends(get_db)):
    """크롤링 대상 기업 목록 + 최근 수집 시간."""
    from job_crawler import COMPANIES

    # 기업별 최근 수집 시간 조회
    latest_rows = (
        db.query(Job.company, func.max(Job.collected_at))
        .group_by(Job.company)
        .all()
    )
    latest_map = {name: ts.isoformat() if ts else None for name, ts in latest_rows}

    result = []
    for name, info in COMPANIES.items():
        result.append({
            "company": name,
            "region": info["region"],
            "type": info["type"],
            "last_collected": latest_map.get(name),
        })

    # 유형 → 지역 → 이름 순 정렬
    type_order = {"공기업": 0, "은행": 1, "연구기관": 2}
    result.sort(key=lambda x: (type_order.get(x["type"], 9), x["region"], x["company"]))
    return result


@app.get("/api/health")
def health():
    return {"status": "ok"}

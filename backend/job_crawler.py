"""채용공고 크롤러 — 사람인 + ALIO (비동기 병렬 처리)."""

import asyncio
import logging
import re
from typing import Dict, List
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ── 기업 목록: 이름 → {region, type} ──────────────────────────

COMPANIES: Dict[str, Dict[str, str]] = {
    # 공기업 — 서울
    "한국전력공사": {"region": "서울", "type": "공기업"},
    "한국토지주택공사": {"region": "서울", "type": "공기업"},
    "한국도로공사": {"region": "서울", "type": "공기업"},
    "한국수자원공사": {"region": "서울", "type": "공기업"},
    "한국가스공사": {"region": "서울", "type": "공기업"},
    "한국석유공사": {"region": "서울", "type": "공기업"},
    "한국마사회": {"region": "서울", "type": "공기업"},
    "인천국제공항공사": {"region": "서울", "type": "공기업"},
    "한국공항공사": {"region": "서울", "type": "공기업"},
    "코레일": {"region": "서울", "type": "공기업"},
    "한국철도공사": {"region": "서울", "type": "공기업"},
    "서울교통공사": {"region": "서울", "type": "공기업"},
    "한국조폐공사": {"region": "대전", "type": "공기업"},
    "한국수력원자력": {"region": "경기", "type": "공기업"},
    "한국남동발전": {"region": "서울", "type": "공기업"},
    "한국서부발전": {"region": "서울", "type": "공기업"},
    "한국중부발전": {"region": "서울", "type": "공기업"},
    # 은행
    "국민은행": {"region": "서울", "type": "은행"},
    "신한은행": {"region": "서울", "type": "은행"},
    "하나은행": {"region": "서울", "type": "은행"},
    "우리은행": {"region": "서울", "type": "은행"},
    "농협은행": {"region": "서울", "type": "은행"},
    "기업은행": {"region": "서울", "type": "은행"},
    "산업은행": {"region": "서울", "type": "은행"},
    "수출입은행": {"region": "서울", "type": "은행"},
    "카카오뱅크": {"region": "경기", "type": "은행"},
    "케이뱅크": {"region": "서울", "type": "은행"},
    "토스뱅크": {"region": "서울", "type": "은행"},
    # 연구기관
    "한국개발연구원": {"region": "서울", "type": "연구기관"},
    "한국은행": {"region": "서울", "type": "연구기관"},
    "금융감독원": {"region": "서울", "type": "연구기관"},
    "금융위원회": {"region": "서울", "type": "연구기관"},
    "한국금융연구원": {"region": "서울", "type": "연구기관"},
    "한국정보화진흥원": {"region": "대전", "type": "연구기관"},
    "한국인터넷진흥원": {"region": "서울", "type": "연구기관"},
    "정보통신산업진흥원": {"region": "대전", "type": "연구기관"},
    "한국전자통신연구원": {"region": "대전", "type": "연구기관"},
    "금융보안원": {"region": "서울", "type": "연구기관"},
    "한국정보통신기술협회": {"region": "경기", "type": "연구기관"},
    "한국과학기술정보연구원": {"region": "대전", "type": "연구기관"},
    # 공기업 — 추가
    "예금보험공사": {"region": "서울", "type": "공기업"},
    "한국예탁결제원": {"region": "서울", "type": "공기업"},
    "한국거래소": {"region": "서울", "type": "공기업"},
    "신용보증기금": {"region": "대전", "type": "공기업"},
    "기술보증기금": {"region": "서울", "type": "공기업"},
    "한국자산관리공사": {"region": "서울", "type": "공기업"},
    "한국주택금융공사": {"region": "서울", "type": "공기업"},
    "한국투자공사": {"region": "서울", "type": "공기업"},
    "국민건강보험공단": {"region": "서울", "type": "공기업"},
    "국민연금공단": {"region": "서울", "type": "공기업"},
    "근로복지공단": {"region": "서울", "type": "공기업"},
}

# ── IT 관련 키워드 필터 ──────────────────────────────────────

JOB_KEYWORDS = [
    "IT", "전산", "디지털", "정보보호", "데이터", "시스템",
    "개발", "SW", "보안", "클라우드", "인프라", "정보기술",
    "소프트웨어", "네트워크", "DBA", "서버", "운영", "AI",
    "빅데이터", "핀테크",
]

_kw_pattern = re.compile("|".join(re.escape(k) for k in JOB_KEYWORDS), re.IGNORECASE)


def _matches_it_job(title: str) -> bool:
    return bool(_kw_pattern.search(title))


# ── 비동기 사람인 크롤링 ─────────────────────────────────────

BATCH_SIZE = 8  # 동시 요청 수


async def _fetch(session: aiohttp.ClientSession, url: str, params: dict) -> str:
    """단일 HTTP GET 요청."""
    try:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            resp.raise_for_status()
            return await resp.text()
    except Exception as e:
        logger.warning(f"HTTP 요청 실패: {url} — {e}")
        return ""


def _parse_saramin(html: str, company: str) -> List[dict]:
    """사람인 HTML 파싱."""
    if not html:
        return []
    results = []
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(".item_recruit")
    for item in items:
        title_tag = item.select_one(".job_tit a")
        company_tag = item.select_one(".corp_name a")
        if not title_tag or not company_tag:
            continue
        job_title = title_tag.get_text(strip=True)
        corp_name = company_tag.get_text(strip=True)
        if company not in corp_name and corp_name not in company:
            continue
        if not _matches_it_job(job_title):
            continue
        href = title_tag.get("href", "")
        job_url = urljoin("https://www.saramin.co.kr", href)
        date_tag = item.select_one(".job_date .date")
        posted = date_tag.get_text(strip=True) if date_tag else ""
        results.append({
            "company": corp_name,
            "title": job_title,
            "url": job_url,
            "posted_date": posted,
        })
    return results


async def _scrape_saramin_batch(
    session: aiohttp.ClientSession, companies: List[str]
) -> List[dict]:
    """배치 단위 사람인 크롤링."""
    tasks = []
    for company in companies:
        url = "https://www.saramin.co.kr/zf_user/search/recruit"
        params = {
            "searchType": "search",
            "searchword": company,
            "recruitPage": "1",
            "recruitSort": "relation",
            "recruitPageCount": "20",
        }
        tasks.append((company, _fetch(session, url, params)))

    htmls = await asyncio.gather(*(t[1] for t in tasks))
    all_jobs = []
    for (company, _), html in zip(tasks, htmls):
        jobs = _parse_saramin(html, company)
        for j in jobs:
            info = COMPANIES.get(j["company"], COMPANIES.get(company, {}))
            j["region"] = info.get("region", "")
            j["job_type"] = info.get("type", "")
        all_jobs.extend(jobs)
    return all_jobs


# ── 비동기 ALIO 크롤링 ──────────────────────────────────────


async def _scrape_alio(session: aiohttp.ClientSession) -> List[dict]:
    """ALIO 공공기관 채용정보 크롤링."""
    url = "https://job.alio.go.kr/recruit.do"
    params = {"pageNo": "1", "pageSize": "30"}
    html = await _fetch(session, url, params)
    if not html:
        return []

    results = []
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("table tbody tr")
    for row in rows:
        cols = row.select("td")
        if len(cols) < 4:
            continue
        corp_name = cols[1].get_text(strip=True)
        job_title = cols[2].get_text(strip=True)
        posted = cols[3].get_text(strip=True)
        link_tag = cols[2].select_one("a")
        href = link_tag.get("href", "") if link_tag else ""
        job_url = urljoin("https://job.alio.go.kr/", href) if href else ""

        matched_company = None
        for comp in COMPANIES:
            if comp in corp_name or corp_name in comp:
                matched_company = comp
                break
        if not matched_company:
            continue
        if not _matches_it_job(job_title):
            continue

        info = COMPANIES[matched_company]
        results.append({
            "company": matched_company,
            "title": job_title,
            "url": job_url,
            "posted_date": posted,
            "region": info.get("region", ""),
            "job_type": info.get("type", ""),
        })
    return results


# ── 메인 비동기 수집 ─────────────────────────────────────────


async def _crawl_jobs_async() -> List[dict]:
    """비동기 병렬 크롤링 메인."""
    all_jobs: List[dict] = []
    company_list = list(COMPANIES.keys())

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        # 사람인: 배치 단위 병렬 처리
        logger.info(f"사람인 비동기 크롤링 시작: {len(company_list)}개 기업, 배치 {BATCH_SIZE}개씩")
        for i in range(0, len(company_list), BATCH_SIZE):
            batch = company_list[i : i + BATCH_SIZE]
            jobs = await _scrape_saramin_batch(session, batch)
            all_jobs.extend(jobs)
            # 배치 간 짧은 딜레이
            if i + BATCH_SIZE < len(company_list):
                await asyncio.sleep(0.3)

        # ALIO: 1회 요청
        logger.info("ALIO 비동기 크롤링 시작")
        alio_jobs = await _scrape_alio(session)
        all_jobs.extend(alio_jobs)

    logger.info(f"채용공고 총 {len(all_jobs)}건 수집 완료")
    return all_jobs


def crawl_jobs() -> List[dict]:
    """동기 래퍼 — FastAPI 동기 엔드포인트에서 호출."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # 이미 이벤트 루프가 돌고 있으면 새 루프에서 실행
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(lambda: asyncio.run(_crawl_jobs_async())).result()
    else:
        return asyncio.run(_crawl_jobs_async())

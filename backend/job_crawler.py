"""채용공고 크롤러 — 사람인 + ALIO 공공기관 채용정보."""

import logging
import re
import time
from typing import Dict, List, Optional
from urllib.parse import quote, urljoin

import requests
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
    # 공기업 — 경기/대전
    "한국전자통신연구원": {"region": "대전", "type": "연구기관"},
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
    """채용 공고 제목이 IT/전산 관련인지 확인."""
    return bool(_kw_pattern.search(title))


# ── 사람인 크롤링 ────────────────────────────────────────────


def scrape_saramin(company: str) -> List[dict]:
    """사람인에서 회사명으로 채용공고 검색."""
    results = []
    try:
        url = "https://www.saramin.co.kr/zf_user/search/recruit"
        params = {
            "searchType": "search",
            "searchword": company,
            "recruitPage": "1",
            "recruitSort": "relation",
            "recruitPageCount": "20",
        }
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        items = soup.select(".item_recruit")
        for item in items:
            title_tag = item.select_one(".job_tit a")
            company_tag = item.select_one(".corp_name a")
            if not title_tag or not company_tag:
                continue

            job_title = title_tag.get_text(strip=True)
            corp_name = company_tag.get_text(strip=True)

            # 회사명이 검색어와 매칭되는지 확인
            if company not in corp_name and corp_name not in company:
                continue

            # IT 관련 공고만 필터
            if not _matches_it_job(job_title):
                continue

            href = title_tag.get("href", "")
            job_url = urljoin("https://www.saramin.co.kr", href)

            # 날짜
            date_tag = item.select_one(".job_date .date")
            posted = date_tag.get_text(strip=True) if date_tag else ""

            # 지역
            conditions = item.select(".job_condition span")
            region_text = conditions[0].get_text(strip=True) if conditions else ""

            results.append({
                "company": corp_name,
                "title": job_title,
                "url": job_url,
                "posted_date": posted,
                "region_hint": region_text,
            })
    except Exception as e:
        logger.warning(f"사람인 크롤링 실패 ({company}): {e}")

    return results


# ── ALIO 공공기관 크롤링 ─────────────────────────────────────


def scrape_alio() -> List[dict]:
    """ALIO 공공기관 채용정보 크롤링."""
    results = []
    try:
        url = "https://job.alio.go.kr/recruit.do"
        params = {"pageNo": "1", "pageSize": "30"}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        rows = soup.select("table tbody tr")
        for row in rows:
            cols = row.select("td")
            if len(cols) < 4:
                continue

            corp_name = cols[1].get_text(strip=True) if len(cols) > 1 else ""
            job_title = cols[2].get_text(strip=True) if len(cols) > 2 else ""
            posted = cols[3].get_text(strip=True) if len(cols) > 3 else ""

            link_tag = cols[2].select_one("a") if len(cols) > 2 else None
            href = link_tag.get("href", "") if link_tag else ""
            job_url = urljoin("https://job.alio.go.kr/", href) if href else ""

            # 우리 기업 목록에 있는지 확인
            matched_company = None
            for comp in COMPANIES:
                if comp in corp_name or corp_name in comp:
                    matched_company = comp
                    break

            if not matched_company:
                continue

            # IT 관련 공고만
            if not _matches_it_job(job_title):
                continue

            results.append({
                "company": matched_company,
                "title": job_title,
                "url": job_url,
                "posted_date": posted,
                "region_hint": "",
            })
    except Exception as e:
        logger.warning(f"ALIO 크롤링 실패: {e}")

    return results


# ── 메인 수집 함수 ───────────────────────────────────────────


def crawl_jobs() -> List[dict]:
    """모든 소스에서 채용공고 수집 후 통합 반환."""
    all_jobs = []

    # 1. 사람인 — 주요 기업별 검색 (요청 간 딜레이)
    company_list = list(COMPANIES.keys())
    logger.info(f"사람인 크롤링 시작: {len(company_list)}개 기업")
    for i, company in enumerate(company_list):
        jobs = scrape_saramin(company)
        for j in jobs:
            info = COMPANIES.get(j["company"], COMPANIES.get(company, {}))
            j["region"] = info.get("region", "")
            j["job_type"] = info.get("type", "")
        all_jobs.extend(jobs)
        if i < len(company_list) - 1:
            time.sleep(0.5)  # 서버 부하 방지

    # 2. ALIO 공공기관
    logger.info("ALIO 크롤링 시작")
    alio_jobs = scrape_alio()
    for j in alio_jobs:
        info = COMPANIES.get(j["company"], {})
        j["region"] = info.get("region", "")
        j["job_type"] = info.get("type", "")
    all_jobs.extend(alio_jobs)

    logger.info(f"채용공고 총 {len(all_jobs)}건 수집 완료")
    return all_jobs

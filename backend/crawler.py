import logging
import re
from datetime import datetime
from typing import Optional

import feedparser
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

RSS_FEEDS: dict = {
    # IT/디지털 전문지
    "전자신문 IT": "http://rss.etnews.com/03.xml",
    "전자신문 경제": "http://rss.etnews.com/02.xml",
    "아이뉴스24 IT": "https://www.inews24.com/rss/news_it.xml",
    "아이뉴스24 경제": "https://www.inews24.com/rss/news_economy.xml",
    "비즈니스워치": "http://news.bizwatch.co.kr/rss/service/mobile",
    # 금융 전문지
    "파이낸셜뉴스": "https://www.fnnews.com/rss/r20/fn_realnews_all.xml",
    "파이낸셜뉴스 IT": "https://www.fnnews.com/rss/r20/fn_realnews_it.xml",
    "머니투데이": "http://rss.mt.co.kr/mt_news.xml",
    "이투데이": "https://rss.etoday.co.kr/eto/etoday_news_all.xml",
    # 경제 종합지
    "한국경제": "https://www.hankyung.com/feed/economy",
    "뉴시스 경제": "https://www.newsis.com/RSS/economy.xml",
    "뉴시스 금융": "https://www.newsis.com/RSS/bank.xml",
}

# 웹 크롤링 대상 (RSS 미제공 사이트)
WEB_SCRAPE_SOURCES: list = [
    {
        "name": "지디넷코리아",
        "url": "https://zdnet.co.kr/news/",
        "parser": "zdnet",
    },
    {
        "name": "은행연합회",
        "url": "https://www.kfb.or.kr/news/info_news.php",
        "parser": "kfb",
    },
    {
        "name": "KDI",
        "url": "https://www.kdi.re.kr/research/reportList",
        "parser": "kdi",
    },
]

FILTER_KEYWORDS: list = [
    "금융", "은행", "증권", "보험", "핀테크", "디지털", "IT", "AI",
    "블록체인", "클라우드", "마이데이터", "오픈뱅킹", "인터넷은행",
    "카카오뱅크", "토스", "빅테크", "API", "사이버보안", "전산",
    "시스템", "플랫폼", "데이터", "반도체", "GPU", "양자",
    "가상자산", "암호화폐", "비트코인", "ESG", "대출", "금리",
    "연금", "펀드", "ETF", "IPO", "리스크", "규제",
]

REQUEST_TIMEOUT = 15
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


def _parse_date(entry: dict) -> Optional[datetime]:
    """Parse published date from a feed entry."""
    for field in ("published_parsed", "updated_parsed"):
        t = entry.get(field)
        if t:
            try:
                return datetime(*t[:6])
            except Exception:
                pass
    return None


def _matches_filter(title: str) -> bool:
    """Check if the title contains any of the filter keywords."""
    title_upper = title.upper()
    for kw in FILTER_KEYWORDS:
        if kw.upper() in title_upper:
            return True
    return False


def _clean_html(raw: str) -> str:
    """Strip HTML tags from text."""
    return BeautifulSoup(raw, "html.parser").get_text(strip=True)


def fetch_feed(source_name: str, feed_url: str) -> list:
    """Fetch and parse a single RSS feed. Returns list of article dicts."""
    articles = []
    try:
        resp = requests.get(
            feed_url, timeout=REQUEST_TIMEOUT, headers=REQUEST_HEADERS
        )
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)

        for entry in feed.entries:
            title = _clean_html(entry.get("title", ""))
            if not title or not _matches_filter(title):
                continue

            link = entry.get("link", "")
            published_at = _parse_date(entry)

            articles.append(
                {
                    "title": title,
                    "link": link,
                    "source": source_name,
                    "published_at": published_at,
                }
            )

        logger.info(f"[{source_name}] {len(articles)} articles matched")

    except requests.RequestException as e:
        logger.warning(f"[{source_name}] RSS fetch failed: {e}")
    except Exception as e:
        logger.warning(f"[{source_name}] Parse error: {e}")

    return articles


# ---------------------------------------------------------------------------
# 웹 크롤링 파서들
# ---------------------------------------------------------------------------

def _scrape_zdnet() -> list:
    """지디넷코리아 최신 뉴스 크롤링."""
    articles = []
    try:
        resp = requests.get(
            "https://zdnet.co.kr/news/",
            timeout=REQUEST_TIMEOUT,
            headers=REQUEST_HEADERS,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for a_tag in soup.select("a[href*='/view/']"):
            title = a_tag.get_text(strip=True)
            href = a_tag.get("href", "")
            if not title or len(title) < 10 or not _matches_filter(title):
                continue
            if not href.startswith("http"):
                href = "https://zdnet.co.kr" + href
            articles.append({
                "title": title[:200],
                "link": href,
                "source": "지디넷코리아",
                "published_at": None,
            })

        # 중복 링크 제거
        seen = set()
        unique = []
        for a in articles:
            if a["link"] not in seen:
                seen.add(a["link"])
                unique.append(a)
        articles = unique

        logger.info(f"[지디넷코리아] {len(articles)} articles scraped")
    except Exception as e:
        logger.warning(f"[지디넷코리아] Scrape failed: {e}")
    return articles


def _scrape_kfb() -> list:
    """은행연합회 보도자료 크롤링."""
    articles = []
    try:
        resp = requests.get(
            "https://www.kfb.or.kr/news/info_news.php",
            timeout=REQUEST_TIMEOUT,
            headers=REQUEST_HEADERS,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for tr in soup.select("tr"):
            tds = tr.select("td")
            if len(tds) < 3:
                continue
            # 제목은 보통 2번째 td
            title_td = tds[1]
            title = title_td.get_text(strip=True)
            if not title or len(title) < 5:
                continue

            # 날짜는 3번째 td
            date_text = tds[2].get_text(strip=True) if len(tds) > 2 else ""
            published_at = None
            date_match = re.search(r"(\d{4})/(\d{2})/(\d{2})", date_text)
            if date_match:
                published_at = datetime(
                    int(date_match.group(1)),
                    int(date_match.group(2)),
                    int(date_match.group(3)),
                )

            # 은행연합회 보도자료는 대부분 금융 관련이므로 필터 통과
            articles.append({
                "title": title,
                "link": "https://www.kfb.or.kr/news/info_news.php",
                "source": "은행연합회",
                "published_at": published_at,
            })

        logger.info(f"[은행연합회] {len(articles)} articles scraped")
    except Exception as e:
        logger.warning(f"[은행연합회] Scrape failed: {e}")
    return articles


def _scrape_kdi() -> list:
    """KDI 한국개발연구원 연구보고서 크롤링."""
    articles = []
    try:
        resp = requests.get(
            "https://www.kdi.re.kr/research/reportList",
            timeout=REQUEST_TIMEOUT,
            headers=REQUEST_HEADERS,
            verify=False,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for a_tag in soup.select("a[href*='reportView'], a[href*='report']"):
            title = a_tag.get_text(strip=True)
            href = a_tag.get("href", "")
            if not title or len(title) < 5:
                continue
            if not href.startswith("http"):
                href = "https://www.kdi.re.kr" + href
            articles.append({
                "title": title,
                "link": href,
                "source": "KDI",
                "published_at": None,
            })

        # 중복 제거
        seen = set()
        unique = []
        for a in articles:
            if a["link"] not in seen:
                seen.add(a["link"])
                unique.append(a)
        articles = unique

        logger.info(f"[KDI] {len(articles)} reports scraped")
    except Exception as e:
        logger.warning(f"[KDI] Scrape failed: {e}")
    return articles


_SCRAPER_MAP = {
    "zdnet": _scrape_zdnet,
    "kfb": _scrape_kfb,
    "kdi": _scrape_kdi,
}


def crawl_all() -> list:
    """Crawl all RSS feeds and web sources, return filtered articles."""
    all_articles = []

    # RSS 피드 수집
    for source_name, feed_url in RSS_FEEDS.items():
        articles = fetch_feed(source_name, feed_url)
        all_articles.extend(articles)

    # 웹 크롤링 수집
    for source_cfg in WEB_SCRAPE_SOURCES:
        parser_name = source_cfg["parser"]
        scraper = _SCRAPER_MAP.get(parser_name)
        if scraper:
            articles = scraper()
            all_articles.extend(articles)

    logger.info(f"Total crawled: {len(all_articles)} articles")
    return all_articles

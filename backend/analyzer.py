import logging
import re
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 금융/IT 전문 키워드 사전 — 구체적 키워드만 (일반 단어 제외)
# ---------------------------------------------------------------------------

FINANCE_IT_DICT: set = {
    # ── 회사/기관명 ──
    "카카오뱅크", "토스", "토스뱅크", "케이뱅크", "네이버파이낸셜",
    "네이버페이", "카카오페이", "삼성페이", "삼성증권", "미래에셋증권",
    "KB증권", "NH투자증권", "한국투자증권", "키움증권", "대신증권",
    "KB국민은행", "신한은행", "하나은행", "우리은행", "NH농협",
    "신한카드", "삼성카드", "현대카드", "KB손해보험", "삼성생명",
    "삼성화재", "한화생명", "교보생명", "DB손해보험",
    "금융위원회", "금융감독원", "금융위", "금감원", "한국은행",
    "예금보험공사", "신용보증기금", "기술보증기금",
    "비바리퍼블리카", "뱅크샐러드", "핀다", "8퍼센트",

    # ── 서비스/제도명 ──
    "마이데이터", "오픈뱅킹", "인터넷전문은행", "인터넷은행",
    "BNPL", "간편결제", "간편송금", "모바일뱅킹",
    "오픈API", "공인인증서", "전자서명", "본인인증", "DID",
    "로보어드바이저", "자산관리", "WM",

    # ── AI/기술 ──
    "ChatGPT", "GPT", "LLM", "생성형AI", "생성AI", "초거대AI",
    "AI챗봇", "챗봇", "딥러닝", "머신러닝", "자연어처리",
    "컴퓨터비전", "AI신용평가", "AI심사",
    "블록체인", "스마트컨트랙트", "클라우드컴퓨팅",
    "엣지컴퓨팅", "양자컴퓨팅", "양자암호",
    "랜섬웨어", "제로트러스트", "사이버보안", "정보보안",
    "빅데이터", "데이터분석", "데이터레이크",
    "RPA", "자동화", "로봇프로세스",
    "DevOps", "MLOps", "MSA", "마이크로서비스",
    "쿠버네티스", "컨테이너", "오픈소스", "데이터센터",
    "메타버스", "디지털트윈", "디지털전환",
    "5G", "6G", "IoT", "사물인터넷",
    "반도체", "GPU", "NPU", "HBM",

    # ── 블록체인/디지털자산 ──
    "NFT", "CBDC", "DeFi", "STO", "토큰증권",
    "가상자산", "암호화폐", "비트코인", "이더리움",
    "스테이블코인", "디지털화폐", "디지털원화",

    # ── 정책/규제 ──
    "금융규제샌드박스", "규제샌드박스", "전자금융거래법",
    "금융소비자보호법", "자본시장법", "데이터3법",
    "개인정보보호법", "신용정보법", "마이데이터사업",
    "RegTech", "SupTech",

    # ── 구체적 이슈/상품 ──
    "배당주", "ESG", "금리인상", "금리인하", "기준금리",
    "부동산PF", "프로젝트파이낸싱", "공매도",
    "IPO", "ETF", "ELS", "DLS", "공모주",
    "전세대출", "주택담보대출", "신용대출", "DSR",
    "퇴직연금", "연금저축", "ISA", "IRP",
    "전산장애", "전산마비", "시스템장애",

    # ── 산업 트렌드 ──
    "핀테크", "빅테크", "테크핀", "네오뱅크", "챌린저뱅크",
    "인슈어테크", "프롭테크", "레그테크",
    "슈퍼앱", "임베디드금융", "BaaS",
    "SaaS", "PaaS", "IaaS",
}

# 긴 키워드부터 매칭 (e.g. "인터넷전문은행"이 "은행"보다 먼저)
_SORTED_KEYWORDS = sorted(FINANCE_IT_DICT, key=len, reverse=True)

_PATTERNS = []
for kw in _SORTED_KEYWORDS:
    if re.match(r"^[A-Za-z0-9]", kw):
        _PATTERNS.append((re.compile(r"(?i)\b" + re.escape(kw) + r"\b"), kw))
    else:
        _PATTERNS.append((re.compile(re.escape(kw)), kw))


def extract_keywords_from_title(title: str) -> str:
    """사전 기반으로 제목에서 금융/IT 키워드를 추출하여 쉼표 구분 문자열로 반환."""
    found = []
    remaining = title
    for pat, kw in _PATTERNS:
        if pat.search(remaining):
            found.append(kw)
            remaining = pat.sub("", remaining)
    return ",".join(found)


def get_top_keywords(
    keyword_source_pairs: list,
    top_n: int = 20,
    min_count: int = 1,
    min_sources: int = 1,
) -> list:
    """
    (keyword_string, source_name) 튜플 리스트에서
    TOP N 키워드를 빈도수 + 언론사 수와 함께 반환.
    """
    counter: Counter = Counter()
    source_map: dict = defaultdict(set)

    for ks, source in keyword_source_pairs:
        if not ks:
            continue
        for kw in ks.split(","):
            kw = kw.strip()
            if kw:
                counter[kw] += 1
                source_map[kw].add(source)

    results = []
    for kw, cnt in counter.most_common(top_n * 3):
        sc = len(source_map[kw])
        if cnt >= min_count and sc >= min_sources:
            results.append({
                "keyword": kw,
                "count": cnt,
                "source_count": sc,
            })
        if len(results) >= top_n:
            break

    return results

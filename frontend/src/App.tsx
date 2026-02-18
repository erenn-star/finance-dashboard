import { useEffect, useState, useCallback } from "react";
import { api, Stats, Keyword, Article, SourceCount } from "./api";
import KeywordChart from "./KeywordChart";
import KeywordDonut from "./KeywordDonut";
import ArticleList from "./ArticleList";
import SourceTable from "./SourceTable";
import Fortune from "./Fortune";
import JobBoard from "./JobBoard";

type Period = "1d" | "7d";

const SIDE_IMAGES = [
  { src: "/images/m1.jpg", top: "5%", side: "left" },
  { src: "/images/m2.webp", top: "30%", side: "right" },
  { src: "/images/m3.jpeg", top: "55%", side: "left" },
  { src: "/images/m4.jpeg", top: "75%", side: "right" },
  { src: "/images/m5.jpeg", top: "95%", side: "left" },
] as const;

function DarkModeToggle() {
  const [dark, setDark] = useState(() => {
    if (typeof window === "undefined") return false;
    return (
      localStorage.getItem("theme") === "dark" ||
      (!localStorage.getItem("theme") &&
        window.matchMedia("(prefers-color-scheme: dark)").matches)
    );
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

  return (
    <button
      onClick={() => setDark(!dark)}
      className="p-2 rounded-lg bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
      title={dark ? "라이트 모드" : "다크 모드"}
    >
      {dark ? "\u2600\uFE0F" : "\uD83C\uDF19"}
    </button>
  );
}

export default function App() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [period, setPeriod] = useState<Period>("1d");
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [selectedKeyword, setSelectedKeyword] = useState<string | null>(null);
  const [articles, setArticles] = useState<Article[]>([]);
  const [sources, setSources] = useState<SourceCount[]>([]);
  const [collecting, setCollecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSources, setShowSources] = useState(false);

  const loadDashboard = useCallback(async () => {
    try {
      setError(null);
      const [s, k, src] = await Promise.all([
        api.getStats(),
        api.getKeywords(period),
        api.getSources(),
      ]);
      setStats(s);
      setKeywords(k.keywords);
      setSources(src);
    } catch (e) {
      setError("데이터를 불러오는 데 실패했습니다. 백엔드 서버를 확인해주세요.");
    }
  }, [period]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    if (!selectedKeyword) {
      setArticles([]);
      return;
    }
    api
      .getArticles({ keyword: selectedKeyword, period })
      .then(setArticles)
      .catch(() => setArticles([]));
  }, [selectedKeyword, period]);

  const handleCollect = async () => {
    setCollecting(true);
    try {
      await api.collect();
      await loadDashboard();
      setSelectedKeyword(null);
    } catch {
      setError("수집 중 오류가 발생했습니다.");
    } finally {
      setCollecting(false);
    }
  };

  const formatDate = (iso: string | null) => {
    if (!iso) return "-";
    const d = new Date(iso);
    return d.toLocaleString("ko-KR", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 transition-colors">
      {/* Side Images — light mode only */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden dark:hidden" style={{ zIndex: 1 }}>
        {SIDE_IMAGES.map((img, i) => (
          <img
            key={i}
            src={img.src}
            alt=""
            className="absolute w-48 xl:w-56 rounded-2xl opacity-40 shadow-lg"
            style={{
              top: img.top,
              [img.side]: "-2rem",
              transform: img.side === "left" ? "rotate(-6deg)" : "rotate(6deg)",
            }}
          />
        ))}
      </div>
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-lg sm:text-xl font-bold text-gray-900 dark:text-white">
              싱싱혜의 싱싱한 금융 IT 대시보드 🩵
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
              마지막 수집: {formatDate(stats?.last_collected_at ?? null)}
              {stats && (
                <span className="ml-3 font-medium text-blue-600 dark:text-blue-400">
                  총 {stats.total_articles.toLocaleString()}건
                </span>
              )}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCollect}
              disabled={collecting}
              className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {collecting ? "수집 중..." : "지금 수집"}
            </button>
            <DarkModeToggle />
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {error && (
          <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Period Tabs + Source Toggle */}
        <div className="flex items-center gap-3">
          <div className="flex gap-1 bg-gray-200/80 backdrop-blur-sm dark:bg-gray-800 rounded-lg p-1 w-fit">
            {(["1d", "7d"] as Period[]).map((p) => (
              <button
                key={p}
                onClick={() => {
                  setPeriod(p);
                  setSelectedKeyword(null);
                }}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  period === p
                    ? "bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm"
                    : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                }`}
              >
                {p === "1d" ? "오늘 (1일)" : "이번 주 (7일)"}
              </button>
            ))}
          </div>
          <button
            onClick={() => setShowSources(true)}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          >
            언론사 현황 ({sources.length})
          </button>
        </div>

        {/* Keyword Donut */}
        {keywords.length > 0 && (
          <section className="bg-white/80 backdrop-blur-sm dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5">
            <h2 className="text-lg font-semibold mb-2">키워드 비율 TOP 10</h2>
            <KeywordDonut keywords={keywords} onSelect={setSelectedKeyword} />
          </section>
        )}

        {/* Keyword Chart */}
        <section className="bg-white/80 backdrop-blur-sm dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5">
          <h2 className="text-lg font-semibold mb-4">
            키워드 TOP 20
            {selectedKeyword && (
              <span className="ml-2 text-sm font-normal text-blue-600 dark:text-blue-400">
                — "{selectedKeyword}" 선택됨
                <button
                  onClick={() => setSelectedKeyword(null)}
                  className="ml-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  ✕
                </button>
              </span>
            )}
          </h2>
          <KeywordChart
            keywords={keywords}
            selectedKeyword={selectedKeyword}
            onSelect={setSelectedKeyword}
          />
        </section>

        {/* Articles (shown when keyword selected) */}
        {selectedKeyword && (
          <section className="bg-white/80 backdrop-blur-sm dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5">
            <h2 className="text-lg font-semibold mb-4">
              "{selectedKeyword}" 관련 뉴스
            </h2>
            <ArticleList articles={articles} />
          </section>
        )}

        {/* Job Board */}
        <JobBoard />

        {/* Fortune */}
        <Fortune />
      </main>

      <footer className="text-center text-xs text-gray-500 dark:text-gray-600 py-6">
        Finance IT News Dashboard
      </footer>

      {/* Source Modal */}
      {showSources && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40"
          onClick={() => setShowSources(false)}
        >
          <div
            className="bg-white/90 backdrop-blur-md dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto mx-4 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                언론사별 수집 현황 (7일)
              </h2>
              <button
                onClick={() => setShowSources(false)}
                className="p-1 rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                ✕
              </button>
            </div>
            <SourceTable sources={sources} />
          </div>
        </div>
      )}
    </div>
  );
}

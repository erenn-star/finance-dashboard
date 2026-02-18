import { useEffect, useState } from "react";
import { api, Job, JobStats, JobCompany } from "./api";

const REGIONS = ["전체", "서울", "경기", "대전"];
const TYPES = ["전체", "공기업", "은행", "연구기관"];

export default function JobBoard() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState<JobStats | null>(null);
  const [region, setRegion] = useState("전체");
  const [type, setType] = useState("전체");
  const [collecting, setCollecting] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [showScope, setShowScope] = useState(false);
  const [companies, setCompanies] = useState<JobCompany[]>([]);

  const loadJobs = async () => {
    try {
      const [jobList, jobStats] = await Promise.all([
        api.getJobs({
          region: region === "전체" ? undefined : region,
          type: type === "전체" ? undefined : type,
        }),
        api.getJobStats(),
      ]);
      setJobs(jobList);
      setStats(jobStats);
      setLoaded(true);
    } catch {
      setLoaded(true);
    }
  };

  useEffect(() => {
    loadJobs();
  }, [region, type]);

  const handleCollect = async () => {
    setCollecting(true);
    try {
      await api.collectJobs();
      await loadJobs();
    } catch {
      // ignore
    } finally {
      setCollecting(false);
    }
  };

  const handleShowScope = async () => {
    if (!showScope && companies.length === 0) {
      try {
        const data = await api.getJobCompanies();
        setCompanies(data);
      } catch {
        // ignore
      }
    }
    setShowScope(!showScope);
  };

  const badgeColor = (val: string) => {
    const map: Record<string, string> = {
      서울: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
      경기: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300",
      대전: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300",
      공기업: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
      은행: "bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300",
      연구기관: "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300",
    };
    return map[val] || "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300";
  };

  const formatRelativeTime = (iso: string | null) => {
    if (!iso) return "미수집";
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}분 전`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}시간 전`;
    const days = Math.floor(hours / 24);
    return `${days}일 전`;
  };

  if (!loaded) return null;

  // 크롤링 범위: 유형별 그룹
  const groupedCompanies = companies.reduce<Record<string, JobCompany[]>>((acc, c) => {
    (acc[c.type] = acc[c.type] || []).push(c);
    return acc;
  }, {});

  return (
    <section className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <h2 className="text-lg font-semibold">
          채용 포지션
          {stats && stats.total > 0 && (
            <span className="ml-2 text-sm font-normal text-gray-500 dark:text-gray-400">
              총 {stats.total}건
            </span>
          )}
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={handleShowScope}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              showScope
                ? "bg-gray-800 text-white dark:bg-gray-200 dark:text-gray-900"
                : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
            }`}
          >
            크롤링 범위
          </button>
          <button
            onClick={handleCollect}
            disabled={collecting}
            className="px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {collecting ? "수집 중..." : "채용공고 수집"}
          </button>
        </div>
      </div>

      {/* Crawling Scope Panel */}
      {showScope && (
        <div className="mb-4 p-4 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
            총 {companies.length}개 기업 · 사람인 + ALIO 크롤링
          </p>
          <div className="space-y-4">
            {(["공기업", "은행", "연구기관"] as const).map((typeName) => {
              const group = groupedCompanies[typeName] || [];
              if (group.length === 0) return null;
              return (
                <div key={typeName}>
                  <h4 className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1.5">
                    <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] mr-1.5 ${badgeColor(typeName)}`}>
                      {typeName}
                    </span>
                    {group.length}개
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-1">
                    {group.map((c) => (
                      <div
                        key={c.company}
                        className="flex items-center justify-between px-2 py-1 rounded text-xs"
                      >
                        <span className="text-gray-800 dark:text-gray-200 truncate">
                          <span className={`inline-block w-1.5 h-1.5 rounded-full mr-1.5 ${
                            c.last_collected ? "bg-emerald-500" : "bg-gray-300 dark:bg-gray-600"
                          }`} />
                          {c.company}
                        </span>
                        <span className={`ml-2 shrink-0 ${
                          c.last_collected
                            ? "text-gray-400 dark:text-gray-500"
                            : "text-gray-300 dark:text-gray-600"
                        }`}>
                          {formatRelativeTime(c.last_collected)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-4">
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-gray-500 dark:text-gray-400">지역</span>
          <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-0.5">
            {REGIONS.map((r) => (
              <button
                key={r}
                onClick={() => setRegion(r)}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                  region === r
                    ? "bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm"
                    : "text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                }`}
              >
                {r}
                {stats && r !== "전체" && (
                  <span className="ml-1 text-gray-400 dark:text-gray-500">
                    {stats.by_region.find((x) => x.region === r)?.count || 0}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-gray-500 dark:text-gray-400">유형</span>
          <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-0.5">
            {TYPES.map((t) => (
              <button
                key={t}
                onClick={() => setType(t)}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                  type === t
                    ? "bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm"
                    : "text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                }`}
              >
                {t}
                {stats && t !== "전체" && (
                  <span className="ml-1 text-gray-400 dark:text-gray-500">
                    {stats.by_type.find((x) => x.type === t)?.count || 0}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Job List */}
      {jobs.length === 0 ? (
        <div className="text-center py-10 text-gray-400 dark:text-gray-500">
          <p className="text-2xl mb-2">📋</p>
          <p className="text-sm">
            {stats && stats.total > 0
              ? "해당 조건의 채용공고가 없습니다."
              : "아직 수집된 채용공고가 없습니다. \"채용공고 수집\" 버튼을 눌러주세요."}
          </p>
        </div>
      ) : (
        <div className="space-y-2 max-h-[480px] overflow-y-auto">
          {jobs.map((job) => (
            <div
              key={job.id}
              className="flex flex-wrap items-start gap-2 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {job.title}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  {job.company}
                  {job.posted_date && (
                    <span className="ml-2">{job.posted_date}</span>
                  )}
                </p>
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                {job.region && (
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${badgeColor(job.region)}`}>
                    {job.region}
                  </span>
                )}
                {job.job_type && (
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${badgeColor(job.job_type)}`}>
                    {job.job_type}
                  </span>
                )}
                {job.url && (
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-blue-600 dark:text-blue-400 hover:underline whitespace-nowrap"
                  >
                    상세보기
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

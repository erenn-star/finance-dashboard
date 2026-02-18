import { useEffect, useState } from "react";
import { api, Job, JobStats } from "./api";

const REGIONS = ["전체", "서울", "경기", "대전"];
const TYPES = ["전체", "공기업", "은행", "연구기관"];

export default function JobBoard() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState<JobStats | null>(null);
  const [region, setRegion] = useState("전체");
  const [type, setType] = useState("전체");
  const [collecting, setCollecting] = useState(false);
  const [loaded, setLoaded] = useState(false);

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
      // 아직 수집 전이면 빈 상태
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

  if (!loaded) return null;

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
        <button
          onClick={handleCollect}
          disabled={collecting}
          className="px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {collecting ? "수집 중..." : "채용공고 수집"}
        </button>
      </div>

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

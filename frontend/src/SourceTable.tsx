import type { SourceCount } from "./api";

interface Props {
  sources: SourceCount[];
}

export default function SourceTable({ sources }: Props) {
  if (sources.length === 0) {
    return (
      <p className="text-gray-400 dark:text-gray-500 text-sm py-6 text-center">
        수집된 데이터가 없습니다.
      </p>
    );
  }

  const maxCount = Math.max(...sources.map((s) => s.count));

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {sources.map((s) => (
        <div
          key={s.source}
          className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50"
        >
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
              {s.source}
            </p>
            <div className="mt-1.5 h-1.5 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
              <div
                className="h-full rounded-full bg-blue-500 transition-all duration-500"
                style={{ width: `${(s.count / maxCount) * 100}%` }}
              />
            </div>
          </div>
          <span className="text-sm font-semibold text-gray-700 dark:text-gray-300 tabular-nums">
            {s.count}
          </span>
        </div>
      ))}
    </div>
  );
}

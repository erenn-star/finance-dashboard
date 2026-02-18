import type { Article } from "./api";

interface Props {
  articles: Article[];
}

export default function ArticleList({ articles }: Props) {
  if (articles.length === 0) {
    return (
      <p className="text-gray-400 dark:text-gray-500 text-sm py-6 text-center">
        관련 뉴스가 없습니다.
      </p>
    );
  }

  const formatDate = (iso: string | null) => {
    if (!iso) return "";
    const d = new Date(iso);
    return d.toLocaleDateString("ko-KR", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="divide-y divide-gray-100 dark:divide-gray-800">
      {articles.map((a) => (
        <div
          key={a.id}
          className="py-3 px-2 -mx-2"
        >
          <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 leading-snug">
            {a.title}
          </h3>
          <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-500 dark:text-gray-400">
            <span className="px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 font-medium">
              {a.source}
            </span>
            {a.published_at && <span>{formatDate(a.published_at)}</span>}
            <a
              href={a.link}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 hover:underline"
            >
              (원문 기사)
            </a>
          </div>
        </div>
      ))}
    </div>
  );
}

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import type { Keyword } from "./api";

interface Props {
  keywords: Keyword[];
  onSelect: (keyword: string) => void;
}

const COLORS = [
  "#3b82f6", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981",
  "#06b6d4", "#f97316", "#6366f1", "#14b8a6", "#e11d48",
];

function DonutTooltip({ active, payload }: any) {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0].payload;
  return (
    <div
      style={{
        backgroundColor: "#fff",
        border: "1px solid #e5e7eb",
        borderRadius: "8px",
        padding: "8px 12px",
        fontSize: "12px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
      }}
    >
      <p style={{ fontWeight: 600, margin: 0 }}>
        {data.keyword} — {data.count}건 ({data.percent}%)
      </p>
    </div>
  );
}

export default function KeywordDonut({ keywords, onSelect }: Props) {
  if (keywords.length === 0) return null;

  const top10 = keywords.slice(0, 10);
  const total = top10.reduce((sum, k) => sum + k.count, 0);
  const data = top10.map((k) => ({
    ...k,
    percent: Math.round((k.count / total) * 100),
  }));

  return (
    <div className="flex flex-col items-center">
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={90}
            paddingAngle={2}
            dataKey="count"
            cursor="pointer"
            onClick={(entry) => onSelect(entry.keyword)}
          >
            {data.map((_, i) => (
              <Cell
                key={i}
                fill={COLORS[i % COLORS.length]}
                stroke="none"
              />
            ))}
          </Pie>
          <Tooltip content={<DonutTooltip />} />
        </PieChart>
      </ResponsiveContainer>
      <div className="flex flex-wrap justify-center gap-x-3 gap-y-1 mt-1">
        {data.map((k, i) => (
          <button
            key={k.keyword}
            onClick={() => onSelect(k.keyword)}
            className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
          >
            <span
              className="inline-block w-2 h-2 rounded-full"
              style={{ backgroundColor: COLORS[i % COLORS.length] }}
            />
            {k.keyword} ({k.percent}%)
          </button>
        ))}
      </div>
    </div>
  );
}

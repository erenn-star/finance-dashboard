import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { Keyword } from "./api";

interface Props {
  keywords: Keyword[];
  selectedKeyword: string | null;
  onSelect: (keyword: string) => void;
}

function CustomTooltip({ active, payload }: any) {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0].payload as Keyword;
  return (
    <div
      style={{
        backgroundColor: "#fff",
        border: "1px solid #e5e7eb",
        borderRadius: "8px",
        padding: "10px 14px",
        fontSize: "13px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.12)",
        maxWidth: 360,
      }}
    >
      <p style={{ fontWeight: 700, marginBottom: 4, fontSize: 14 }}>
        {data.keyword} ({data.count}건)
      </p>
      <p style={{ margin: "0 0 6px", color: "#6b7280", fontSize: 12 }}>
        총 {data.count}회 언급 / {data.source_count}개 언론사
      </p>
      {data.summary && (
        <p
          style={{
            margin: 0,
            color: "#1f2937",
            fontSize: 12,
            lineHeight: 1.5,
            borderTop: "1px solid #f3f4f6",
            paddingTop: 6,
          }}
        >
          {data.summary}
        </p>
      )}
    </div>
  );
}

export default function KeywordChart({
  keywords,
  selectedKeyword,
  onSelect,
}: Props) {
  if (keywords.length === 0) {
    return (
      <p className="text-gray-400 dark:text-gray-500 text-sm py-12 text-center">
        수집된 키워드가 없습니다. "지금 수집" 버튼을 눌러 뉴스를 수집해주세요.
      </p>
    );
  }

  const chartHeight = Math.max(420, keywords.length * 32);

  return (
    <ResponsiveContainer width="100%" height={chartHeight}>
      <BarChart
        data={keywords}
        layout="vertical"
        margin={{ top: 0, right: 30, bottom: 0, left: 10 }}
      >
        <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
        <XAxis type="number" tick={{ fontSize: 12 }} />
        <YAxis
          type="category"
          dataKey="keyword"
          width={110}
          tick={{ fontSize: 13 }}
          interval={0}
        />
        <Tooltip content={<CustomTooltip />} />
        <Bar
          dataKey="count"
          radius={[0, 4, 4, 0]}
          cursor="pointer"
          onClick={(data) => onSelect(data.keyword)}
        >
          {keywords.map((entry) => (
            <Cell
              key={entry.keyword}
              fill={
                entry.keyword === selectedKeyword ? "#2563eb" : "#60a5fa"
              }
              opacity={
                selectedKeyword && entry.keyword !== selectedKeyword
                  ? 0.4
                  : 1
              }
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

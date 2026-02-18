import { useEffect, useState } from "react";
import { api, Fortune as FortuneType } from "./api";

function ScoreBar({ score, color }: { score: number; color: string }) {
  return (
    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-1000 ${color}`}
        style={{ width: `${score}%` }}
      />
    </div>
  );
}

const DAYS = ["일", "월", "화", "수", "목", "금", "토"];

function formatKoreanDate(isoDate: string): string {
  const d = new Date(isoDate + "T00:00:00");
  const y = d.getFullYear();
  const m = d.getMonth() + 1;
  const day = d.getDate();
  const dow = DAYS[d.getDay()];
  return `${y}년 ${m}월 ${day}일 (${dow})`;
}

export default function Fortune() {
  const [fortune, setFortune] = useState<FortuneType | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    api.getFortune().then(setFortune).catch(() => {});
  }, []);

  if (!fortune) return null;

  return (
    <div className="space-y-3">
      {/* Toggle Button */}
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-amber-50 to-orange-50 dark:from-gray-900 dark:to-gray-800 border border-amber-200 dark:border-amber-900/50 hover:shadow-md transition-all duration-300 group"
      >
        <span className="text-xl group-hover:scale-110 transition-transform">{"\uD83D\uDD2E"}</span>
        <span className="text-sm font-semibold text-amber-800 dark:text-amber-200">
          오늘의 운세 {open ? "숨기기" : "보기"}
        </span>
      </button>

      {/* Fortune Card */}
      <div
        className={`overflow-hidden transition-all duration-500 ease-in-out ${
          open ? "max-h-[600px] opacity-100" : "max-h-0 opacity-0"
        }`}
      >
        <div className="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-gray-900 dark:to-gray-800 rounded-xl border border-amber-200 dark:border-amber-900/50 p-5 shadow-lg shadow-amber-100/50 dark:shadow-black/20">
          {/* 날짜 + 사주 */}
          <div className="text-center mb-3">
            <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
              {formatKoreanDate(fortune.date)}
            </p>
            <p className="text-[10px] text-amber-500 dark:text-amber-500/60 mt-0.5">
              {fortune.천간} {fortune.지지} {fortune.element_emoji}
            </p>
          </div>

          {/* 메인 운세 메시지 */}
          <div className="bg-white/70 dark:bg-gray-800/70 rounded-lg p-4 mb-4">
            <p className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed">
              {fortune.fortune_message}
            </p>
            <p className="text-sm text-amber-700 dark:text-amber-300 mt-2 leading-relaxed font-medium">
              {fortune.cheer_message}
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* 금전운 */}
            <div className="bg-white/50 dark:bg-gray-800/50 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1.5">
                <span>{"\uD83D\uDCB0"}</span>
                <span className="font-semibold text-xs text-gray-700 dark:text-gray-300">
                  금전운
                </span>
                <span className="ml-auto text-xs font-bold text-amber-600 dark:text-amber-400">
                  {fortune.money.score}점
                </span>
              </div>
              <ScoreBar score={fortune.money.score} color="bg-amber-400" />
            </div>

            {/* 사업운 */}
            <div className="bg-white/50 dark:bg-gray-800/50 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1.5">
                <span>{"\uD83D\uDCBC"}</span>
                <span className="font-semibold text-xs text-gray-700 dark:text-gray-300">
                  사업운
                </span>
                <span className="ml-auto text-xs font-bold text-blue-600 dark:text-blue-400">
                  {fortune.business.score}점
                </span>
              </div>
              <ScoreBar score={fortune.business.score} color="bg-blue-400" />
            </div>
          </div>

          {/* 럭키 아이템 */}
          <div className="flex items-center justify-center gap-6 mt-3 text-xs text-gray-500 dark:text-gray-400">
            <span>{"\uD83C\uDFA8"} {fortune.lucky_color}</span>
            <span>{"\uD83C\uDFB2"} {fortune.lucky_number}</span>
          </div>

          <p className="text-center text-[10px] text-amber-400/50 dark:text-amber-600/30 mt-2">
            신사년 경인월 경신일 병술시 · 일주 庚금
          </p>
        </div>
      </div>
    </div>
  );
}

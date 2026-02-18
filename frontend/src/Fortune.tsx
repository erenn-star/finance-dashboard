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

export default function Fortune() {
  const [fortune, setFortune] = useState<FortuneType | null>(null);

  useEffect(() => {
    api.getFortune().then(setFortune).catch(() => {});
  }, []);

  if (!fortune) return null;

  return (
    <div className="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-gray-900 dark:to-gray-800 rounded-xl border border-amber-200 dark:border-amber-900/50 p-5">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-2xl">{"\uD83D\uDD2E"}</span>
        <h2 className="text-lg font-semibold text-amber-900 dark:text-amber-200">
          {"\uC624\uB298\uC758 \uC6B4\uC138"}
        </h2>
        <span className="ml-auto text-xs text-amber-600 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/40 px-2 py-0.5 rounded-full">
          {fortune.천간} {fortune.지지} {fortune.element_emoji}
        </span>
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
              {"\uAE08\uC804\uC6B4"}
            </span>
            <span className="ml-auto text-xs font-bold text-amber-600 dark:text-amber-400">
              {fortune.money.score}{"\uC810"}
            </span>
          </div>
          <ScoreBar score={fortune.money.score} color="bg-amber-400" />
        </div>

        {/* 사업운 */}
        <div className="bg-white/50 dark:bg-gray-800/50 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1.5">
            <span>{"\uD83D\uDCBC"}</span>
            <span className="font-semibold text-xs text-gray-700 dark:text-gray-300">
              {"\uC0AC\uC5C5\uC6B4"}
            </span>
            <span className="ml-auto text-xs font-bold text-blue-600 dark:text-blue-400">
              {fortune.business.score}{"\uC810"}
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
        {"\uC2E0\uC0AC\uB144 \uACBD\uC778\uC6D4 \uACBD\uC2E0\uC77C \uBCD1\uC220\uC2DC \u00B7 \uC77C\uC8FC \u5E9A\uAE08"}
      </p>
    </div>
  );
}

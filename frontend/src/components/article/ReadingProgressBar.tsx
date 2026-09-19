interface Props {
  /** Current reading percentage (0–100) */
  percent: number;
  /** Whether article is fully read */
  isComplete: boolean;
}

export default function ReadingProgressBar({ percent, isComplete }: Props) {
  if (percent <= 0) return null;

  return (
    <div className="mb-4">
      {/* Bar track */}
      <div className="h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-200 ease-out ${
            isComplete
              ? "bg-green-500 dark:bg-green-400"
              : "bg-indigo-500 dark:bg-indigo-400"
          }`}
          style={{ width: `${percent}%` }}
        />
      </div>

      {/* Percentage label */}
      <div className="flex items-center justify-between mt-1">
        <span className="text-[11px] text-gray-400 dark:text-gray-500 select-none">
          {isComplete ? "✅ Article complete" : "Reading…"}
        </span>
        <span
          className={`text-[11px] font-mono select-none ${
            isComplete
              ? "text-green-500 dark:text-green-400"
              : "text-gray-400 dark:text-gray-500"
          }`}
        >
          {percent}%
        </span>
      </div>
    </div>
  );
}

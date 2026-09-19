import { useState } from "react";
import { useReviews } from "@/hooks/useReviews";
import QuizCard from "@/components/review/QuizCard";
import Spinner from "@/components/common/Spinner";
import EmptyState from "@/components/common/EmptyState";

export default function ReviewPage() {
  const { items, totalDue, stats, loading, error, submitAnswer } = useReviews();
  const [currentIdx, setCurrentIdx] = useState(0);

  const current = items[currentIdx];

  const handleAnswer = async (vocabularyId: string, correct: boolean) => {
    await submitAnswer(vocabularyId, correct);
    setTimeout(() => {
      setCurrentIdx((prev) => prev + 1);
    }, 1500);
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Daily Review</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {totalDue} words due for review
        </p>
      </div>

      {stats && (
        <>
          <div className="grid grid-cols-4 gap-3 mb-4">
            <StatCard label="Total Words" value={stats.total_words} />
            <StatCard label="Mastered" value={stats.words_mastered} color="text-green-600 dark:text-green-400" />
            <StatCard label="Learning" value={stats.words_learning} color="text-yellow-600 dark:text-yellow-400" />
            <StatCard label="Retention" value={`${stats.retention_rate}%`} color="text-indigo-600 dark:text-indigo-400" />
          </div>
          <div className="flex items-center gap-4 mb-6 text-sm">
            <span className="flex items-center gap-1.5">
              <span>🔥</span>
              <span className="text-gray-600 dark:text-gray-400">
                <strong className="text-gray-900 dark:text-gray-100">{stats.reading_streak_days}</strong> day reading streak
              </span>
            </span>
            <span className="flex items-center gap-1.5">
              <span>🧠</span>
              <span className="text-gray-600 dark:text-gray-400">
                <strong className="text-gray-900 dark:text-gray-100">{stats.quiz_streak_days}</strong> day quiz streak
              </span>
            </span>
          </div>
        </>
      )}

      {loading ? (
        <Spinner />
      ) : error ? (
        <p className="text-red-600 dark:text-red-400 text-sm text-center py-8">{error}</p>
      ) : items.length === 0 ? (
        <EmptyState
          icon="🎉"
          title="All caught up!"
          description="No words due for review right now. Keep reading!"
        />
      ) : current ? (
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center mb-4">
            {currentIdx + 1} / {items.length}
          </p>
          <QuizCard item={current} onAnswer={handleAnswer} />
        </div>
      ) : (
        <EmptyState
          icon="✅"
          title="Review complete!"
          description="Great job! Come back tomorrow for more."
        />
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  color = "text-gray-900 dark:text-gray-100",
}: {
  label: string;
  value: string | number;
  color?: string;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3 text-center transition-colors">
      <div className={`text-xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{label}</div>
    </div>
  );
}

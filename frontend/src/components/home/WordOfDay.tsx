import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Lightbulb, ArrowRight, Star, Brain } from "lucide-react";
import { vocabularyApi, type WordOfDay } from "@/lib/api";

const REASON_LABELS: Record<string, { label: string; color: string }> = {
  due_for_review: {
    label: "Due for review",
    color: "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400",
  },
  new_word: {
    label: "New word",
    color: "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400",
  },
  weakest_word: {
    label: "Needs practice",
    color: "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400",
  },
};

const DIFFICULTY_COLORS: Record<string, string> = {
  Easy: "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400",
  Medium: "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400",
  Hard: "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400",
};

export default function WordOfDay() {
  const [word, setWord] = useState<WordOfDay | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    vocabularyApi
      .wordOfDay()
      .then(setWord)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading || !word) return null;

  const reason = REASON_LABELS[word.reason] || REASON_LABELS.new_word;
  const masteryPct = Math.round(word.mastery_level * 100);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 mb-6 transition-colors">
      <div className="flex items-center gap-2 mb-3">
        <Lightbulb size={18} className="text-amber-500" />
        <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">
          Word of the Day
        </h3>
        <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${reason.color}`}>
          {reason.label}
        </span>
      </div>

      <div className="flex items-start gap-4">
        {/* Word + meaning */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="text-xl font-bold text-gray-900 dark:text-gray-100 uppercase">
              {word.word}
            </h4>
            <span
              className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                DIFFICULTY_COLORS[word.difficulty] || ""
              }`}
            >
              {word.difficulty}
            </span>
          </div>

          {word.meaning && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
              {word.meaning}
            </p>
          )}

          <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
            <span className="flex items-center gap-1">
              <Brain size={12} />
              {word.times_reviewed} reviews
            </span>
            <span className="flex items-center gap-1">
              <Star size={12} className={masteryPct >= 70 ? "text-green-500" : masteryPct >= 30 ? "text-yellow-500" : "text-red-500"} />
              {masteryPct}% mastery
            </span>
          </div>

          {/* Mastery bar */}
          <div className="mt-2 h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden w-32">
            <div
              className={`h-full rounded-full transition-all ${
                masteryPct >= 70
                  ? "bg-green-500"
                  : masteryPct >= 30
                  ? "bg-yellow-500"
                  : "bg-red-500"
              }`}
              style={{ width: `${masteryPct}%` }}
            />
          </div>
        </div>

        {/* Action */}
        <Link
          to={`/vocabulary`}
          className="flex items-center gap-1.5 px-3 py-2 bg-indigo-50 dark:bg-indigo-900/30 hover:bg-indigo-100 dark:hover:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 rounded-lg text-xs font-medium transition-colors flex-shrink-0"
        >
          Review now
          <ArrowRight size={12} />
        </Link>
      </div>
    </div>
  );
}

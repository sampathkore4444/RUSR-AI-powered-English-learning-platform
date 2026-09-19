import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { BookOpen, Brain, Star, ArrowRight } from "lucide-react";
import { reviewApi, articlesApi, type ReviewStats, type Article } from "@/lib/api";

export default function DailySummary() {
  const [stats, setStats] = useState<ReviewStats | null>(null);
  const [lastArticle, setLastArticle] = useState<Article | null>(null);
  const [dueCount, setDueCount] = useState(0);

  useEffect(() => {
    reviewApi.getStats().then(setStats).catch(() => {});
    reviewApi.getDue(1).then((d) => setDueCount(d.total_due)).catch(() => {});
    articlesApi.list(0, 1).then((d) => {
      if (d.articles.length > 0) setLastArticle(d.articles[0]);
    }).catch(() => {});
  }, []);

  const greeting = getGreeting();

  return (
    <div className="bg-gradient-to-br from-indigo-50 to-white dark:from-indigo-950/30 dark:to-gray-900 rounded-xl border border-indigo-100 dark:border-indigo-900/50 p-6 mb-6 transition-colors">
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-1">{greeting}</h2>

      {stats && (
        <div className="flex gap-4 mt-3 mb-4">
          <div className="flex items-center gap-1.5 text-sm">
            <Star size={14} className="text-yellow-500" />
            <span className="text-gray-600 dark:text-gray-400">
              <strong className="text-gray-900 dark:text-gray-100">{stats.words_new}</strong> new words
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-sm">
            <Brain size={14} className="text-indigo-500" />
            <span className="text-gray-600 dark:text-gray-400">
              <strong className="text-gray-900 dark:text-gray-100">{dueCount}</strong> to review
            </span>
          </div>
          {stats.reading_streak_days > 0 && (
            <div className="flex items-center gap-1.5 text-sm">
              <span>🔥</span>
              <span className="text-gray-600 dark:text-gray-400">
                <strong className="text-gray-900 dark:text-gray-100">{stats.reading_streak_days}</strong> day reading
              </span>
            </div>
          )}
          {stats.quiz_streak_days > 0 && (
            <div className="flex items-center gap-1.5 text-sm">
              <span>🧠</span>
              <span className="text-gray-600 dark:text-gray-400">
                <strong className="text-gray-900 dark:text-gray-100">{stats.quiz_streak_days}</strong> day quiz
              </span>
            </div>
          )}
        </div>
      )}

      {lastArticle && (
        <Link
          to={`/article/${lastArticle.id}`}
          className="flex items-center justify-between bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3 hover:shadow-md transition-all"
        >
          <div className="flex items-center gap-3 min-w-0">
            <BookOpen size={18} className="text-indigo-500 flex-shrink-0" />
            <div className="min-w-0">
              <p className="text-xs text-gray-500 dark:text-gray-400">Continue Reading</p>
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                {lastArticle.title}
              </p>
            </div>
          </div>
          <ArrowRight size={16} className="text-gray-400 dark:text-gray-500 flex-shrink-0" />
        </Link>
      )}
    </div>
  );
}

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "☀️ Good Morning";
  if (hour < 17) return "🌤️ Good Afternoon";
  return "🌙 Good Evening";
}

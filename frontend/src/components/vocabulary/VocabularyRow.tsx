import { Trash2 } from "lucide-react";
import type { VocabularyWord } from "@/lib/api";

interface Props {
  word: VocabularyWord;
  onDelete: (id: string) => void;
}

const difficultyColors: Record<string, string> = {
  Easy: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400",
  Medium: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-400",
  Hard: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400",
};

export default function VocabularyRow({ word, onDelete }: Props) {
  const masteryPct = Math.round(word.mastery_level * 100);

  return (
    <div className="flex items-center gap-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 transition-colors">
      {/* Word + meaning */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-gray-900 dark:text-gray-100">{word.word}</span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full ${
              difficultyColors[word.difficulty] || "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400"
            }`}
          >
            {word.difficulty}
          </span>
        </div>
        {word.meaning && (
          <p className="text-sm text-gray-600 dark:text-gray-400 truncate mt-0.5">
            {word.meaning}
          </p>
        )}
      </div>

      {/* Mastery bar */}
      <div className="w-24 flex-shrink-0">
        <div className="text-xs text-gray-500 dark:text-gray-400 text-right mb-0.5">
          {masteryPct}%
        </div>
        <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-indigo-500 dark:bg-indigo-400 rounded-full transition-all"
            style={{ width: `${masteryPct}%` }}
          />
        </div>
      </div>

      {/* Reviews count */}
      <div className="text-xs text-gray-500 dark:text-gray-400 w-16 text-center flex-shrink-0">
        {word.times_reviewed} reviews
      </div>

      {/* Delete */}
      <button
        onClick={() => onDelete(word.id)}
        className="p-1.5 text-gray-400 dark:text-gray-500 hover:text-red-500 dark:hover:text-red-400 transition-colors"
        title="Remove"
      >
        <Trash2 size={16} />
      </button>
    </div>
  );
}

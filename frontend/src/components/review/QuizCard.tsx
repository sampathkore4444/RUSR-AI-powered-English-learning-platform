import { useState } from "react";
import { CheckCircle, XCircle } from "lucide-react";
import type { ReviewItem } from "@/lib/api";

interface Props {
  item: ReviewItem;
  onAnswer: (vocabularyId: string, correct: boolean) => void;
}

const FAKE_OPTIONS = [
  "to announce publicly",
  "to increase rapidly",
  "to calculate precisely",
  "to control or reduce",
  "to investigate thoroughly",
  "to suggest politely",
  "to ignore completely",
  "to demand forcefully",
];

function shuffleArray<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export default function QuizCard({ item, onAnswer }: Props) {
  const [answered, setAnswered] = useState(false);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);
  const [resultCorrect, setResultCorrect] = useState<boolean | null>(null);

  const correctAnswer = item.meaning || "unknown meaning";
  const fakePool = FAKE_OPTIONS.filter((f) => f !== correctAnswer);
  const shuffledFakes = shuffleArray(fakePool).slice(0, 3);
  const options = shuffleArray([correctAnswer, ...shuffledFakes]);
  const correctIdx = options.indexOf(correctAnswer);

  const handleSelect = (idx: number) => {
    if (answered) return;
    setSelectedIdx(idx);
    setAnswered(true);
    const isCorrect = idx === correctIdx;
    setResultCorrect(isCorrect);
    onAnswer(item.vocabulary_id, isCorrect);
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-md p-6 max-w-lg mx-auto transition-colors">
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">What does this word mean?</p>
      <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">{item.word}</h3>

      <div className="space-y-2">
        {options.map((opt, idx) => {
          const isCorrect = idx === correctIdx;
          const isSelected = idx === selectedIdx;

          let style =
            "border-gray-200 dark:border-gray-600 hover:border-indigo-300 dark:hover:border-indigo-500 hover:bg-indigo-50 dark:hover:bg-indigo-950/30";
          if (answered && isCorrect)
            style = "border-green-400 dark:border-green-500 bg-green-50 dark:bg-green-950/30";
          if (answered && isSelected && !isCorrect)
            style = "border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-950/30";

          return (
            <button
              key={idx}
              onClick={() => handleSelect(idx)}
              disabled={answered}
              className={`w-full text-left px-4 py-3 rounded-lg border text-sm font-medium transition-colors flex items-center gap-2 ${style}`}
            >
              {answered && isCorrect && <CheckCircle size={16} className="text-green-600 dark:text-green-400" />}
              {answered && isSelected && !isCorrect && (
                <XCircle size={16} className="text-red-600 dark:text-red-400" />
              )}
              <span className="text-gray-800 dark:text-gray-200">{opt}</span>
            </button>
          );
        })}
      </div>

      {answered && resultCorrect !== null && (
        <div className="mt-4 text-center">
          <p
            className={`text-sm font-medium ${
              resultCorrect
                ? "text-green-600 dark:text-green-400"
                : "text-red-600 dark:text-red-400"
            }`}
          >
            {resultCorrect ? "✓ Correct!" : "✗ Incorrect"}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {resultCorrect ? "Interval extended" : "Will review again soon"}
          </p>
        </div>
      )}
    </div>
  );
}

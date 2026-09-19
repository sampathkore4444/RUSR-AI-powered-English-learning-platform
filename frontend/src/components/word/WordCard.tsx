import { useRef, useEffect, useState } from "react";
import { Star } from "lucide-react";
import type { WordInspectResponse } from "@/lib/api";

interface Props {
  data: WordInspectResponse;
  onSave: () => void;
  saving: boolean;
}

export default function WordCard({ data, onSave, saving }: Props) {
  const [visible, setVisible] = useState(false);
  const prevWordRef = useRef<string>("");

  useEffect(() => {
    if (data.word !== prevWordRef.current) {
      setVisible(false);
      prevWordRef.current = data.word;
      const frame = requestAnimationFrame(() => {
        requestAnimationFrame(() => setVisible(true));
      });
      return () => cancelAnimationFrame(frame);
    }
  }, [data.word]);

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-lg p-5 w-full max-w-md transition-all duration-300 ease-out ${
        visible ? "opacity-100 translate-x-0" : "opacity-0 translate-x-4"
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 uppercase">
            {data.word}
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {data.lemma} · {data.dictionary.pos}
          </p>
        </div>
        <button
          onClick={onSave}
          disabled={saving}
          className="flex items-center gap-1 px-3 py-1.5 bg-yellow-400 hover:bg-yellow-500 text-white rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
        >
          <Star size={14} />
          {saving ? "Saving..." : "Save"}
        </button>
      </div>

      <hr className="mb-3 border-gray-200 dark:border-gray-700" />

      <Section title="Meaning" content={data.dictionary.definition} />

      {data.context_meaning && (
        <Section title="In this sentence" content={data.context_meaning} highlight />
      )}

      {data.dictionary.pronunciation && (
        <Section title="Pronunciation" content={data.dictionary.pronunciation} />
      )}

      {data.example && <Section title="Example" content={data.example} />}

      {data.dictionary.synonyms.length > 0 && (
        <div className="mt-3">
          <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-1">
            Synonyms
          </h4>
          <div className="flex flex-wrap gap-1.5">
            {data.dictionary.synonyms.map((syn) => (
              <span
                key={syn}
                className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full text-xs"
              >
                {syn}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Section({
  title,
  content,
  highlight = false,
}: {
  title: string;
  content: string;
  highlight?: boolean;
}) {
  return (
    <div className="mt-3">
      <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-0.5">
        {title}
      </h4>
      <p
        className={`text-sm leading-relaxed ${
          highlight
            ? "text-indigo-700 dark:text-indigo-400 font-medium"
            : "text-gray-700 dark:text-gray-300"
        }`}
      >
        {content}
      </p>
    </div>
  );
}

import type { Paragraph } from "@/lib/api";

interface Props {
  paragraphs: Paragraph[];
  onWordTap: (word: string, sentence: string) => void;
  onSentenceTap?: (sentence: string) => void;
  highlightWord?: string | null;
}

export default function ArticleText({
  paragraphs,
  onWordTap,
  onSentenceTap,
  highlightWord,
}: Props) {
  const hl = highlightWord?.toLowerCase() ?? null;

  return (
    <div className="space-y-4">
      {paragraphs.map((para) => (
        <p key={para.id} className="text-base leading-relaxed text-gray-800 dark:text-gray-200">
          {para.sentences.map((sent) => (
            <span
              key={sent.id}
              onClick={() => onSentenceTap?.(sent.text)}
              className="cursor-pointer hover:bg-indigo-50 dark:hover:bg-indigo-950/30 rounded px-0.5 transition-colors"
              title="Click to explain with AI"
            >
              {sent.tokens.map((tok, i) => {
                const isHighlighted = hl !== null && tok.text.toLowerCase() === hl;

                return (
                  <span
                    key={i}
                    onClick={(e) => {
                      e.stopPropagation();
                      onWordTap(tok.text, sent.text);
                    }}
                    className={`cursor-pointer rounded px-0.5 transition-all ${
                      isHighlighted
                        ? "bg-yellow-200 dark:bg-yellow-700/50 text-indigo-800 dark:text-yellow-200 font-semibold ring-1 ring-yellow-300 dark:ring-yellow-600"
                        : "hover:bg-yellow-100 dark:hover:bg-yellow-900/30 hover:text-indigo-700 dark:hover:text-yellow-300"
                    }`}
                    title={`${tok.lemma} (${tok.pos})`}
                  >
                    {tok.text}
                  </span>
                );
              })}{" "}
            </span>
          ))}
        </p>
      ))}
    </div>
  );
}

import { useState, useRef, useEffect, useCallback } from "react";
import {
  Sparkles,
  BookOpen,
  MessageSquare,
  Lightbulb,
  Languages,
  HelpCircle,
  RefreshCw,
  AlertCircle,
  Minus,
  Copy,
  Check,
} from "lucide-react";
import { wordsApi } from "@/lib/api";
import AiLoadingSkeleton from "./AiLoadingSkeleton";

interface Props {
  sentence: string;
  onClose: () => void;
  onMinimize?: () => void;
}

const ACTIONS = [
  { key: "simple", label: "Simple English", icon: MessageSquare, description: "Rewrite in simpler words" },
  { key: "grammar", label: "Grammar", icon: BookOpen, description: "Explain grammatical structure" },
  { key: "vocabulary", label: "Vocabulary", icon: Lightbulb, description: "Define key words" },
  { key: "usage", label: "Why this word?", icon: HelpCircle, description: "Explain word choice" },
  { key: "examples", label: "Examples", icon: Sparkles, description: "Generate 3 examples" },
  { key: "translate", label: "Simplify", icon: Languages, description: "Translate to simple English" },
];

export default function AiExplanationPanel({ sentence, onClose, onMinimize }: Props) {
  const [activeAction, setActiveAction] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [copied, setCopied] = useState(false);

  const cacheRef = useRef<Map<string, string>>(new Map());
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    cacheRef.current.clear();
  }, [sentence]);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      if (e.ctrlKey || e.altKey || e.metaKey) return;

      const num = parseInt(e.key, 10);
      if (num >= 1 && num <= 6) {
        e.preventDefault();
        handleExplain(ACTIONS[num - 1].key);
      }

      if (e.key === "Escape") {
        e.preventDefault();
        handleClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  });

  const handleClose = useCallback(() => {
    abortRef.current?.abort();
    onClose();
  }, [onClose]);

  const handleExplain = useCallback(
    async (action: string, isRetry = false) => {
      const cached = cacheRef.current.get(action);
      if (cached && !isRetry) {
        setActiveAction(action);
        setExplanation(cached);
        setError(null);
        setLoading(false);
        return;
      }

      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setActiveAction(action);
      setLoading(true);
      setError(null);
      setExplanation(null);
      if (isRetry) setRetryCount((c) => c + 1);

      try {
        const result = await wordsApi.explain({ sentence, action });
        if (!controller.signal.aborted) {
          setExplanation(result.explanation);
          cacheRef.current.set(action, result.explanation);
        }
      } catch (err) {
        if (controller.signal.aborted) return;
        const message = err instanceof Error ? err.message : "Failed to get explanation";
        if (message.includes("Failed to fetch") || message.includes("NetworkError")) {
          setError("Network error — check your connection and try again.");
        } else if (message.includes("504") || message.includes("timeout")) {
          setError("AI service timed out — it may be busy. Please retry.");
        } else {
          setError(message);
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    },
    [sentence]
  );

  const handleRetry = useCallback(() => {
    if (activeAction) {
      cacheRef.current.delete(activeAction);
      handleExplain(activeAction, true);
    }
  }, [activeAction, handleExplain]);

  const handleCopy = useCallback(async () => {
    if (!explanation) return;
    try {
      await navigator.clipboard.writeText(explanation);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const textarea = document.createElement("textarea");
      textarea.value = explanation;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [explanation]);

  const cachedActions = Array.from(cacheRef.current.keys());

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-indigo-200 dark:border-indigo-800/50 shadow-lg p-5 mt-4 transition-all animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Sparkles size={18} className="text-indigo-600 dark:text-indigo-400" />
          <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">AI Assistant</h3>
          {retryCount > 0 && (
            <span className="text-[10px] bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 px-1.5 py-0.5 rounded-full font-medium">
              Retry {retryCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <kbd className="text-[10px] bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-gray-400 px-1.5 py-0.5 rounded font-mono">
            esc
          </kbd>
          {onMinimize && (
            <button
              onClick={onMinimize}
              title="Minimize to floating pill"
              className="flex items-center justify-center w-6 h-6 rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <Minus size={14} />
            </button>
          )}
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 text-xs transition-colors"
          >
            ✕ close
          </button>
        </div>
      </div>

      {/* Selected sentence */}
      <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 mb-3">
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Selected sentence:</p>
        <p className="text-sm text-gray-800 dark:text-gray-200 italic">"{sentence}"</p>
      </div>

      {/* Action buttons */}
      <div className="grid grid-cols-3 gap-2 mb-2">
        {ACTIONS.map(({ key, label, icon: Icon, description }, index) => {
          const isActive = activeAction === key;
          const isCurrentLoading = loading && isActive;
          const isCached = cachedActions.includes(key);

          return (
            <button
              key={key}
              onClick={() => handleExplain(key)}
              disabled={loading}
              title={`${description} [${index + 1}]${isCached ? " (cached)" : ""}`}
              className={`relative flex flex-col items-center gap-1 p-2.5 rounded-lg border text-xs font-medium transition-all ${
                isActive
                  ? "border-indigo-400 dark:border-indigo-500 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 shadow-sm"
                  : "border-gray-200 dark:border-gray-600 hover:border-indigo-300 dark:hover:border-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-950/20 text-gray-600 dark:text-gray-400"
              } disabled:opacity-60`}
            >
              {isCurrentLoading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-300 dark:border-gray-500 border-t-indigo-600 dark:border-t-indigo-400" />
              ) : (
                <Icon size={16} />
              )}
              <span className="leading-tight">{label}</span>

              <span className="absolute top-1 left-1.5 text-[9px] text-gray-300 dark:text-gray-600 font-mono select-none">
                {index + 1}
              </span>

              {isActive && !isCurrentLoading && (
                <div className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-indigo-500" />
              )}

              {isCached && !isActive && (
                <div className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-green-400" />
              )}
            </button>
          );
        })}
      </div>

      {/* Keyboard hint */}
      <div className="flex items-center justify-center gap-1.5 mb-3 text-[10px] text-gray-300 dark:text-gray-600 select-none">
        <span>Press</span>
        {[1, 2, 3, 4, 5, 6].map((n) => (
          <kbd
            key={n}
            className="inline-flex items-center justify-center w-4 h-4 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-[9px] font-mono text-gray-500 dark:text-gray-400"
          >
            {n}
          </kbd>
        ))}
        <span>for quick actions</span>
      </div>

      {/* Loading */}
      {loading && (
        <div className="bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/50 rounded-lg p-4 animate-fade-in">
          <AiLoadingSkeleton />
          <p className="text-[11px] text-indigo-400 dark:text-indigo-500 text-center mt-3 animate-pulse">
            AI is thinking…
          </p>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 rounded-lg p-4 animate-fade-in">
          <div className="flex items-start gap-2.5">
            <AlertCircle size={16} className="text-red-500 dark:text-red-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm text-red-700 dark:text-red-400 mb-2">{error}</p>
              <button
                onClick={handleRetry}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white dark:bg-gray-800 border border-red-300 dark:border-red-800 text-red-700 dark:text-red-400 rounded-lg text-xs font-medium hover:bg-red-100 dark:hover:bg-red-950/30 transition-colors"
              >
                <RefreshCw size={12} />
                Retry
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Explanation result */}
      {explanation && !loading && !error && (
        <div className="bg-indigo-50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/50 rounded-lg p-4 animate-fade-in">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5">
              <Sparkles size={14} className="text-indigo-600 dark:text-indigo-400" />
              <span className="text-xs font-semibold text-indigo-700 dark:text-indigo-300 uppercase">
                {ACTIONS.find((a) => a.key === activeAction)?.label}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleCopy}
                className="inline-flex items-center gap-1 text-[11px] text-indigo-400 hover:text-indigo-600 dark:hover:text-indigo-300 transition-colors"
                title="Copy explanation to clipboard"
              >
                {copied ? (
                  <>
                    <Check size={12} className="text-green-500" />
                    <span className="text-green-600 dark:text-green-400">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy size={12} />
                    <span>Copy</span>
                  </>
                )}
              </button>
              <span className="text-gray-300 dark:text-gray-600">|</span>
              <button
                onClick={() => {
                  setExplanation(null);
                  setActiveAction(null);
                }}
                className="text-[11px] text-indigo-400 hover:text-indigo-600 dark:hover:text-indigo-300 transition-colors"
              >
                Try another action
              </button>
            </div>
          </div>
          <p className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-line">
            {explanation}
          </p>
        </div>
      )}
    </div>
  );
}

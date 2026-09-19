import { useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import { Sparkles, MessageSquare } from "lucide-react";
import { useArticle } from "@/hooks/useArticles";
import { useWordInspect } from "@/hooks/useWordInspect";
import { useReadingProgress } from "@/hooks/useReadingProgress";
import ArticleText from "@/components/article/ArticleText";
import ReadingProgressBar from "@/components/article/ReadingProgressBar";
import WordCard from "@/components/word/WordCard";
import AiExplanationPanel from "@/components/word/AiExplanationPanel";
import Spinner from "@/components/common/Spinner";
import ErrorBoundary from "@/components/common/ErrorBoundary";

export default function ArticleReaderPage() {
  const { id } = useParams<{ id: string }>();
  const { article, loading, error } = useArticle(id);
  const {
    data: wordData,
    loading: wordLoading,
    saving,
    saved,
    error: wordError,
    inspect,
    save,
    reset,
  } = useWordInspect();

  const { percent, isComplete, containerRef } = useReadingProgress(id);

  const [selectedSentence, setSelectedSentence] = useState<string | null>(null);
  const [selectedWord, setSelectedWord] = useState<string | null>(null);
  const [showAiPanel, setShowAiPanel] = useState(false);
  const [aiMinimized, setAiMinimized] = useState(false);

  const handleWordTap = (word: string, sentence: string) => {
    inspect(word, sentence);
    setSelectedWord(word);
    setSelectedSentence(sentence);
  };

  const handleSentenceSelect = (sentence: string) => {
    setSelectedSentence(sentence);
    setShowAiPanel(true);
    setAiMinimized(false);
  };

  const handleAiClose = useCallback(() => {
    setShowAiPanel(false);
    setSelectedSentence(null);
    setAiMinimized(false);
  }, []);

  const handleAiMinimize = useCallback(() => {
    setAiMinimized(true);
  }, []);

  const handleAiRestore = useCallback(() => {
    setAiMinimized(false);
  }, []);

  const handleResetWord = useCallback(() => {
    reset();
    setSelectedWord(null);
  }, [reset]);

  if (loading) return <Spinner />;
  if (error) return <p className="text-red-600 dark:text-red-400 text-center py-8">{error}</p>;
  if (!article) return null;

  return (
    <div className="flex gap-6">
      <div className="flex-1 min-w-0">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-1">{article.title}</h1>
        {article.author && (
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">by {article.author}</p>
        )}

        {/* Reading progress */}
        <ReadingProgressBar percent={percent} isComplete={isComplete} />

        {/* Article content with ref for scroll tracking */}
        <div ref={containerRef}>
          <ArticleText
            paragraphs={article.paragraphs}
            onWordTap={handleWordTap}
            onSentenceTap={handleSentenceSelect}
            highlightWord={selectedWord}
          />
        </div>

        {showAiPanel && selectedSentence && !aiMinimized && (
          <div className="animate-slide-up">
            <ErrorBoundary onError={(err) => console.error("AI Panel crashed:", err)}>
              <AiExplanationPanel
                sentence={selectedSentence}
                onClose={handleAiClose}
                onMinimize={handleAiMinimize}
              />
            </ErrorBoundary>
          </div>
        )}

        {selectedSentence && !showAiPanel && !aiMinimized && (
          <button
            onClick={() => setShowAiPanel(true)}
            className="mt-4 flex items-center gap-2 px-4 py-2 bg-indigo-100 dark:bg-indigo-900/40 hover:bg-indigo-200 dark:hover:bg-indigo-800/40 text-indigo-700 dark:text-indigo-300 rounded-lg text-sm font-medium transition-colors animate-fade-in"
          >
            <Sparkles size={16} />
            Explain this sentence with AI
          </button>
        )}
      </div>

      <div className="w-80 flex-shrink-0">
        <div className="sticky top-20">
          <ErrorBoundary onError={(err) => console.error("Word card crashed:", err)}>
            {wordLoading && (
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 text-center animate-fade-in">
                <div className="animate-spin rounded-full h-6 w-6 border-2 border-gray-300 dark:border-gray-600 border-t-indigo-600 dark:border-t-indigo-400 mx-auto mb-3" />
                <p className="text-sm text-gray-500 dark:text-gray-400">Looking up word…</p>
              </div>
            )}

            {wordError && !wordLoading && (
              <div className="bg-red-50 dark:bg-red-950/20 rounded-xl border border-red-200 dark:border-red-900/50 p-4 text-sm text-red-600 dark:text-red-400 animate-fade-in">
                {wordError}
              </div>
            )}

            {wordData && (
              <div className="animate-fade-in">
                <WordCard data={wordData} onSave={save} saving={saving} />
                {saved && (
                  <p className="mt-2 text-sm text-green-600 dark:text-green-400 text-center font-medium animate-fade-in">
                    ✅ Word saved to vocabulary!
                  </p>
                )}
                <button
                  onClick={handleResetWord}
                  className="mt-2 w-full text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 text-center transition-colors"
                >
                  ← tap another word
                </button>
              </div>
            )}

            {!wordLoading && !wordData && !wordError && (
              <div className="bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-dashed border-gray-300 dark:border-gray-600 p-6 text-center">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  👆 Tap any word in the article to see its meaning
                </p>
              </div>
            )}
          </ErrorBoundary>
        </div>
      </div>

      {/* Minimized AI pill */}
      {showAiPanel && selectedSentence && aiMinimized && (
        <button
          onClick={handleAiRestore}
          className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all animate-slide-up"
          title={`Restore AI Assistant — "${selectedSentence.slice(0, 40)}…"`}
        >
          <MessageSquare size={16} />
          <span className="text-sm font-medium">AI Assistant</span>
          <span className="text-[10px] bg-indigo-500 px-1.5 py-0.5 rounded-full">
            {selectedSentence.split(" ").length} words
          </span>
        </button>
      )}
    </div>
  );
}

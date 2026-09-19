import { useState } from "react";
import { Plus, Link, FileText, AlertCircle } from "lucide-react";
import { useArticles } from "@/hooks/useArticles";
import { articlesApi } from "@/lib/api";
import ArticleCard from "@/components/article/ArticleCard";
import DailySummary from "@/components/home/DailySummary";
import WordOfDay from "@/components/home/WordOfDay";
import Spinner from "@/components/common/Spinner";
import EmptyState from "@/components/common/EmptyState";

export default function HomePage() {
  const { articles, loading, error, refetch } = useArticles();
  const [showForm, setShowForm] = useState(false);
  const [mode, setMode] = useState<"url" | "text">("url");
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [text, setText] = useState("");
  const [ingesting, setIngesting] = useState(false);
  const [ingestError, setIngestError] = useState<string | null>(null);

  const handleIngest = async () => {
    try {
      setIngesting(true);
      setIngestError(null);
      if (mode === "url") {
        await articlesApi.ingestFromUrl(url);
      } else {
        await articlesApi.ingestFromText({ title, text });
      }
      setTitle("");
      setUrl("");
      setText("");
      setShowForm(false);
      refetch();
    } catch (err) {
      setIngestError(err instanceof Error ? err.message : "Failed to ingest article");
    } finally {
      setIngesting(false);
    }
  };

  return (
    <div>
      <DailySummary />
      <WordOfDay />

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">My Articles</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Tap any word to understand it in context
          </p>
        </div>
        <button
          onClick={() => {
            setShowForm(!showForm);
            setIngestError(null);
          }}
          className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors"
        >
          <Plus size={16} />
          Add Article
        </button>
      </div>

      {showForm && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 mb-6 shadow-sm transition-colors">
          {ingestError && (
            <div className="flex items-center gap-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm rounded-lg p-3 mb-4">
              <AlertCircle size={16} className="flex-shrink-0" />
              {ingestError}
            </div>
          )}

          <div className="flex gap-2 mb-4">
            <button
              onClick={() => setMode("url")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium ${
                mode === "url"
                  ? "bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300"
                  : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400"
              }`}
            >
              <Link size={14} />
              URL
            </button>
            <button
              onClick={() => setMode("text")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium ${
                mode === "text"
                  ? "bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300"
                  : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400"
              }`}
            >
              <FileText size={14} />
              Paste Text
            </button>
          </div>

          {mode === "url" ? (
            <input
              type="url"
              placeholder="https://example.com/article..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          ) : (
            <>
              <input
                type="text"
                placeholder="Article title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg px-3 py-2 text-sm mb-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <textarea
                placeholder="Paste article text here..."
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={6}
                className="w-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
              />
            </>
          )}

          <div className="flex justify-end gap-2">
            <button
              onClick={() => setShowForm(false)}
              className="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
            >
              Cancel
            </button>
            <button
              onClick={handleIngest}
              disabled={ingesting || (mode === "url" ? !url : !text)}
              className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg disabled:opacity-50 transition-colors"
            >
              {ingesting ? "Processing..." : "Ingest"}
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <Spinner />
      ) : error ? (
        <p className="text-red-600 dark:text-red-400 text-sm text-center py-8">{error}</p>
      ) : articles.length === 0 ? (
        <EmptyState
          icon="📰"
          title="No articles yet"
          description="Add your first newspaper article to start learning."
        />
      ) : (
        <div className="space-y-3">
          {articles.map((a) => (
            <ArticleCard key={a.id} article={a} />
          ))}
        </div>
      )}
    </div>
  );
}

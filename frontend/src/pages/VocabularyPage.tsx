import { useState, useMemo } from "react";
import { Search, X, Filter, ArrowUpDown } from "lucide-react";
import { useVocabulary } from "@/hooks/useVocabulary";
import VocabularyRow from "@/components/vocabulary/VocabularyRow";
import ExportMenu from "@/components/vocabulary/ExportMenu";
import Spinner from "@/components/common/Spinner";
import EmptyState from "@/components/common/EmptyState";

type SortOption = "newest" | "oldest" | "mastery-asc" | "mastery-desc" | "alpha" | "difficulty";
type DifficultyFilter = "all" | "Easy" | "Medium" | "Hard";

const SORT_LABELS: Record<SortOption, string> = {
  newest: "Newest first",
  oldest: "Oldest first",
  "mastery-asc": "Mastery ↑",
  "mastery-desc": "Mastery ↓",
  alpha: "A → Z",
  difficulty: "Difficulty",
};

const DIFFICULTY_ORDER: Record<string, number> = { Easy: 0, Medium: 1, Hard: 2 };

export default function VocabularyPage() {
  const { words, total, loading, error, deleteWord } = useVocabulary();

  const [search, setSearch] = useState("");
  const [difficultyFilter, setDifficultyFilter] = useState<DifficultyFilter>("all");
  const [sortBy, setSortBy] = useState<SortOption>("newest");
  const [showFilters, setShowFilters] = useState(false);

  const filtered = useMemo(() => {
    let result = [...words];

    // Text search — matches word, lemma, meaning, personal note
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (w) =>
          w.word.toLowerCase().includes(q) ||
          w.lemma.toLowerCase().includes(q) ||
          (w.meaning && w.meaning.toLowerCase().includes(q)) ||
          (w.personal_note && w.personal_note.toLowerCase().includes(q))
      );
    }

    // Difficulty filter
    if (difficultyFilter !== "all") {
      result = result.filter((w) => w.difficulty === difficultyFilter);
    }

    // Sort
    switch (sortBy) {
      case "newest":
        result.sort((a, b) => new Date(b.first_seen).getTime() - new Date(a.first_seen).getTime());
        break;
      case "oldest":
        result.sort((a, b) => new Date(a.first_seen).getTime() - new Date(b.first_seen).getTime());
        break;
      case "mastery-asc":
        result.sort((a, b) => a.mastery_level - b.mastery_level);
        break;
      case "mastery-desc":
        result.sort((a, b) => b.mastery_level - a.mastery_level);
        break;
      case "alpha":
        result.sort((a, b) => a.word.localeCompare(b.word));
        break;
      case "difficulty":
        result.sort(
          (a, b) => (DIFFICULTY_ORDER[a.difficulty] ?? 99) - (DIFFICULTY_ORDER[b.difficulty] ?? 99)
        );
        break;
    }

    return result;
  }, [words, search, difficultyFilter, sortBy]);

  const activeFilterCount =
    (difficultyFilter !== "all" ? 1 : 0) + (sortBy !== "newest" ? 1 : 0);

  const clearSearch = () => {
    setSearch("");
    setDifficultyFilter("all");
    setSortBy("newest");
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">My Vocabulary</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {total} words saved
            {search && ` · ${filtered.length} matching`}
          </p>
        </div>
        {total > 0 && <ExportMenu />}
      </div>

      {/* Search bar */}
      <div className="mb-4 flex items-center gap-2">
        <div className="relative flex-1">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500"
          />
          <input
            type="text"
            placeholder="Search words, meanings, notes…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-8 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-colors"
          />
          {search && (
            <button
              onClick={() => setSearch("")}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <X size={14} />
            </button>
          )}
        </div>

        {/* Filter toggle */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-1.5 px-3 py-2.5 rounded-lg border text-sm font-medium transition-colors ${
            showFilters || activeFilterCount > 0
              ? "bg-indigo-50 dark:bg-indigo-900/30 border-indigo-300 dark:border-indigo-700 text-indigo-700 dark:text-indigo-300"
              : "bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700"
          }`}
        >
          <Filter size={14} />
          Filters
          {activeFilterCount > 0 && (
            <span className="ml-1 w-4 h-4 bg-indigo-500 text-white rounded-full text-[10px] flex items-center justify-center">
              {activeFilterCount}
            </span>
          )}
        </button>
      </div>

      {/* Expanded filter panel */}
      {showFilters && (
        <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg animate-fade-in">
          <div className="flex flex-wrap items-center gap-4">
            {/* Difficulty filter */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Difficulty:</span>
              <div className="flex gap-1">
                {(["all", "Easy", "Medium", "Hard"] as DifficultyFilter[]).map((d) => (
                  <button
                    key={d}
                    onClick={() => setDifficultyFilter(d)}
                    className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                      difficultyFilter === d
                        ? "bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300"
                        : "bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-600"
                    }`}
                  >
                    {d === "all" ? "All" : d}
                  </button>
                ))}
              </div>
            </div>

            {/* Sort */}
            <div className="flex items-center gap-2">
              <ArrowUpDown size={12} className="text-gray-400" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortOption)}
                className="px-2.5 py-1 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-md text-xs font-medium text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                {Object.entries(SORT_LABELS).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            {/* Clear all */}
            {(difficultyFilter !== "all" || sortBy !== "newest") && (
              <button
                onClick={clearSearch}
                className="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 underline"
              >
                Clear filters
              </button>
            )}
          </div>
        </div>
      )}

      {/* Content */}
      {loading ? (
        <Spinner />
      ) : error ? (
        <p className="text-red-600 dark:text-red-400 text-sm text-center py-8">{error}</p>
      ) : words.length === 0 ? (
        <EmptyState
          icon="📚"
          title="No saved words yet"
          description="Read an article and tap words to save them here."
        />
      ) : filtered.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-400 dark:text-gray-500 text-sm mb-2">
            No words match "{search}"
          </p>
          <button
            onClick={clearSearch}
            className="text-sm text-indigo-600 dark:text-indigo-400 hover:underline"
          >
            Clear search
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((w) => (
            <VocabularyRow key={w.id} word={w} onDelete={deleteWord} />
          ))}
        </div>
      )}
    </div>
  );
}

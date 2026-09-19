import { useState, useEffect, useCallback } from "react";
import { vocabularyApi, type VocabularyWord } from "@/lib/api";

export function useVocabulary() {
  const [words, setWords] = useState<VocabularyWord[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWords = useCallback(async () => {
    try {
      setLoading(true);
      const data = await vocabularyApi.list();
      setWords(data.vocabulary);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load vocabulary");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWords();
  }, [fetchWords]);

  const deleteWord = useCallback(
    async (id: string) => {
      await vocabularyApi.delete(id);
      setWords((prev) => prev.filter((w) => w.id !== id));
      setTotal((prev) => prev - 1);
    },
    []
  );

  return { words, total, loading, error, refetch: fetchWords, deleteWord };
}

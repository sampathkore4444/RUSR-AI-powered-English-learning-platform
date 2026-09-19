import { useState, useEffect, useCallback } from "react";
import { reviewApi, type ReviewItem, type ReviewStats } from "@/lib/api";

export function useReviews() {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [totalDue, setTotalDue] = useState(0);
  const [stats, setStats] = useState<ReviewStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDue = useCallback(async () => {
    try {
      setLoading(true);
      const data = await reviewApi.getDue();
      setItems(data.items);
      setTotalDue(data.total_due);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load reviews");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const s = await reviewApi.getStats();
      setStats(s);
    } catch {
      // non-critical, ignore
    }
  }, []);

  useEffect(() => {
    fetchDue();
    fetchStats();
  }, [fetchDue, fetchStats]);

  const submitAnswer = useCallback(
    async (vocabularyId: string, correct: boolean) => {
      await reviewApi.submitAnswer({
        vocabulary_id: vocabularyId,
        answer_correct: correct,
      });
      // Remove answered item from list
      setItems((prev) => prev.filter((i) => i.vocabulary_id !== vocabularyId));
      setTotalDue((prev) => Math.max(0, prev - 1));
      fetchStats();
    },
    [fetchStats]
  );

  return { items, totalDue, stats, loading, error, submitAnswer, refetch: fetchDue };
}

import { useState, useCallback, useRef, useEffect } from "react";
import { wordsApi, vocabularyApi, type WordInspectResponse } from "@/lib/api";

export function useWordInspect() {
  const [data, setData] = useState<WordInspectResponse | null>(null);
  const [contextSentence, setContextSentence] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const inspectAbortRef = useRef<AbortController | null>(null);
  const saveAbortRef = useRef<AbortController | null>(null);

  // Cleanup on unmount — abort any in-flight requests
  useEffect(() => {
    return () => {
      inspectAbortRef.current?.abort();
      saveAbortRef.current?.abort();
    };
  }, []);

  const inspect = useCallback(async (word: string, sentence: string) => {
    // Cancel any previous inspect request
    inspectAbortRef.current?.abort();
    const controller = new AbortController();
    inspectAbortRef.current = controller;

    try {
      setLoading(true);
      setError(null);
      setData(null);
      setSaved(false);
      setContextSentence(sentence);
      const result = await wordsApi.inspect({ word, sentence });

      if (!controller.signal.aborted) {
        setData(result);
      }
    } catch (err) {
      if (controller.signal.aborted) return;
      setError(err instanceof Error ? err.message : "Failed to inspect word");
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false);
      }
    }
  }, []);

  const save = useCallback(async () => {
    if (!data) return;

    // Cancel any previous save request
    saveAbortRef.current?.abort();
    const controller = new AbortController();
    saveAbortRef.current = controller;

    try {
      setSaving(true);
      await vocabularyApi.save({
        word: data.word,
        lemma: data.lemma,
        meaning: data.dictionary.definition,
        context_sentence: contextSentence || undefined,
      });

      if (!controller.signal.aborted) {
        setSaved(true);
      }
    } catch (err) {
      if (controller.signal.aborted) return;
      setError(err instanceof Error ? err.message : "Failed to save word");
    } finally {
      if (!controller.signal.aborted) {
        setSaving(false);
      }
    }
  }, [data, contextSentence]);

  const reset = useCallback(() => {
    // Cancel any in-flight requests before resetting
    inspectAbortRef.current?.abort();
    saveAbortRef.current?.abort();

    setData(null);
    setContextSentence(null);
    setLoading(false);
    setSaving(false);
    setSaved(false);
    setError(null);
  }, []);

  return { data, loading, saving, saved, error, inspect, save, reset };
}

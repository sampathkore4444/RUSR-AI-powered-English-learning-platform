import { useState, useEffect, useCallback, useRef } from "react";

interface ReadingProgress {
  /** Percentage read (0–100) */
  percent: number;
  /** Whether user has scrolled to the bottom */
  isComplete: boolean;
  /** Ref to attach to the article content container */
  containerRef: React.RefObject<HTMLDivElement | null>;
}

export function useReadingProgress(articleId?: string): ReadingProgress {
  const [percent, setPercent] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const calculateProgress = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;

    const rect = el.getBoundingClientRect();
    const articleTop = rect.top + window.scrollY;
    const articleHeight = rect.height;
    const windowHeight = window.innerHeight;
    const scrollY = window.scrollY;

    // How far into the article the viewport bottom has reached
    const scrolledIntoArticle = scrollY + windowHeight - articleTop;
    const totalScrollable = articleHeight + windowHeight;

    if (scrolledIntoArticle <= 0) {
      setPercent(0);
      setIsComplete(false);
    } else if (scrolledIntoArticle >= totalScrollable) {
      setPercent(100);
      setIsComplete(true);
    } else {
      const pct = Math.round((scrolledIntoArticle / totalScrollable) * 100);
      setPercent(Math.min(100, Math.max(0, pct)));
      setIsComplete(pct >= 95);
    }
  }, []);

  // Reset when article changes
  useEffect(() => {
    setPercent(0);
    setIsComplete(false);
  }, [articleId]);

  // Listen to scroll events (throttled via requestAnimationFrame)
  useEffect(() => {
    let ticking = false;

    const onScroll = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          calculateProgress();
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    // Initial calculation
    calculateProgress();

    return () => window.removeEventListener("scroll", onScroll);
  }, [calculateProgress]);

  return { percent, isComplete, containerRef };
}

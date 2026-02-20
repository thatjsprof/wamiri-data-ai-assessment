import { useCallback, useState } from "react";

export function useReviewStats() {
  const [reviewedToday, setReviewedToday] = useState(0);
  const [reviewTimes, setReviewTimes] = useState<number[]>([]);

  const avgReviewSec =
    reviewTimes.length > 0
      ? Math.round(reviewTimes.reduce((a, b) => a + b, 0) / reviewTimes.length)
      : 0;

  const recordReview = useCallback(() => {
    setReviewedToday((n) => n + 1);
    setReviewTimes((t) => {
      const next = [...t, 45];
      return next.length > 100 ? next.slice(1) : next;
    });
  }, []);

  return { reviewedToday, avgReviewSec, recordReview };
}

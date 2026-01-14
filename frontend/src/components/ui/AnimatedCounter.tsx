import { useEffect, useRef, useState } from 'react';
import { cn } from '@/lib/utils';

interface AnimatedCounterProps {
  value: number;
  duration?: number;
  className?: string;
  /** If true, formats number with commas (e.g., 1,234) */
  formatNumber?: boolean;
  /** Custom formatter function */
  formatter?: (value: number) => string;
  /** Delay before animation starts (ms) */
  delay?: number;
}

/**
 * AnimatedCounter - iOS-style number counting animation
 *
 * Counts from 0 to target value with spring-based easing.
 * Runs on every component mount (no persistence).
 * Respects prefers-reduced-motion preference.
 *
 * @example
 * <AnimatedCounter value={1234} duration={1500} formatNumber />
 */
export const AnimatedCounter: React.FC<AnimatedCounterProps> = ({
  value,
  duration = 1500,
  className,
  formatNumber = true,
  formatter,
  delay = 0,
}) => {
  const [count, setCount] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const frameRef = useRef<number>();
  const startTimeRef = useRef<number>();

  // Check for reduced motion preference
  const prefersReducedMotion =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  useEffect(() => {
    // If user prefers reduced motion, show final value immediately
    if (prefersReducedMotion) {
      setCount(value);
      return;
    }

    // Wait for delay if specified
    const delayTimeout = setTimeout(() => {
      setIsAnimating(true);

      // Easing function - ease out cubic for natural deceleration
      const easeOutCubic = (t: number): number => {
        return 1 - Math.pow(1 - t, 3);
      };

      const animate = (timestamp: number) => {
        if (!startTimeRef.current) {
          startTimeRef.current = timestamp;
        }

        const elapsed = timestamp - startTimeRef.current;
        const progress = Math.min(elapsed / duration, 1);
        const easedProgress = easeOutCubic(progress);
        const currentCount = Math.floor(easedProgress * value);

        setCount(currentCount);

        if (progress < 1) {
          frameRef.current = requestAnimationFrame(animate);
        } else {
          setCount(value); // Ensure we end at exact value
          setIsAnimating(false);
        }
      };

      frameRef.current = requestAnimationFrame(animate);
    }, delay);

    return () => {
      clearTimeout(delayTimeout);
      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current);
      }
    };
  }, [value, duration, delay, prefersReducedMotion]);

  // Format the displayed number
  const displayValue = formatter
    ? formatter(count)
    : formatNumber
      ? count.toLocaleString()
      : count.toString();

  return (
    <span
      className={cn(
        'tabular-nums',
        isAnimating && 'animate-count-up',
        className
      )}
      aria-live="polite"
      aria-atomic="true"
    >
      {displayValue}
    </span>
  );
};

/**
 * Mobile-First Hooks & Utilities
 * Comprehensive collection of hooks for building futuristic, mobile-first applications
 */

import { useState, useEffect, useRef, useCallback } from 'react';

// ============================================================================
// BREAKPOINT HOOKS
// ============================================================================

const breakpoints = {
  xs: 0,
  sm: 360,
  md: 480,
  lg: 768,
  xl: 1024,
  '2xl': 1280,
} as const;

type Breakpoint = keyof typeof breakpoints;

/**
 * Hook to detect current breakpoint and device type
 */
export const useBreakpoint = () => {
  const [breakpoint, setBreakpoint] = useState<Breakpoint>('xs');
  const [isMobile, setIsMobile] = useState(true);
  const [isTablet, setIsTablet] = useState(false);
  const [isDesktop, setIsDesktop] = useState(false);

  useEffect(() => {
    const checkBreakpoint = () => {
      const width = window.innerWidth;

      if (width >= 1280) setBreakpoint('2xl');
      else if (width >= 1024) setBreakpoint('xl');
      else if (width >= 768) setBreakpoint('lg');
      else if (width >= 480) setBreakpoint('md');
      else if (width >= 360) setBreakpoint('sm');
      else setBreakpoint('xs');

      setIsMobile(width < 768);
      setIsTablet(width >= 768 && width < 1024);
      setIsDesktop(width >= 1024);
    };

    checkBreakpoint();
    window.addEventListener('resize', checkBreakpoint);
    return () => window.removeEventListener('resize', checkBreakpoint);
  }, []);

  return { breakpoint, isMobile, isTablet, isDesktop };
};

/**
 * Hook to check if a specific breakpoint is active
 */
export const useMediaQuery = (query: string) => {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);
    setMatches(mediaQuery.matches);

    const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, [query]);

  return matches;
};

// ============================================================================
// TOUCH GESTURE HOOKS
// ============================================================================

interface SwipeState {
  onTouchStart: (e: React.TouchEvent) => void;
  onTouchMove: (e: React.TouchEvent) => void;
  onTouchEnd: () => void;
}

/**
 * Hook for swipe gesture detection
 */
export const useSwipeGesture = (
  onSwipeLeft?: () => void,
  onSwipeRight?: () => void,
  onSwipeUp?: () => void,
  onSwipeDown?: () => void,
  threshold = 50
): SwipeState => {
  const touchStartRef = useRef<{ x: number; y: number } | null>(null);
  const touchEndRef = useRef<{ x: number; y: number } | null>(null);

  const onTouchStart = useCallback((e: React.TouchEvent) => {
    touchEndRef.current = null;
    touchStartRef.current = {
      x: e.targetTouches[0].clientX,
      y: e.targetTouches[0].clientY,
    };
  }, []);

  const onTouchMove = useCallback((e: React.TouchEvent) => {
    touchEndRef.current = {
      x: e.targetTouches[0].clientX,
      y: e.targetTouches[0].clientY,
    };
  }, []);

  const onTouchEnd = useCallback(() => {
    if (!touchStartRef.current || !touchEndRef.current) return;

    const deltaX = touchStartRef.current.x - touchEndRef.current.x;
    const deltaY = touchStartRef.current.y - touchEndRef.current.y;
    const absX = Math.abs(deltaX);
    const absY = Math.abs(deltaY);

    // Determine if horizontal or vertical swipe
    if (Math.max(absX, absY) > threshold) {
      if (absX > absY) {
        // Horizontal swipe
        if (deltaX > 0) {
          onSwipeLeft?.();
        } else {
          onSwipeRight?.();
        }
      } else {
        // Vertical swipe
        if (deltaY > 0) {
          onSwipeUp?.();
        } else {
          onSwipeDown?.();
        }
      }
    }
  }, [onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown, threshold]);

  return { onTouchStart, onTouchMove, onTouchEnd };
};

/**
 * Hook for pull-to-refresh gesture
 */
export const usePullToRefresh = (onRefresh: () => Promise<void>) => {
  const [isPulling, setIsPulling] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const startY = useRef(0);
  const threshold = 80;

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (window.scrollY === 0) {
      startY.current = e.touches[0].clientY;
      setIsPulling(true);
    }
  }, []);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (!isPulling) return;
    const currentY = e.touches[0].clientY;
    const distance = Math.max(0, (currentY - startY.current) * 0.5);
    setPullDistance(Math.min(distance, threshold * 1.5));
  }, [isPulling]);

  const handleTouchEnd = useCallback(async () => {
    if (pullDistance >= threshold && !isRefreshing) {
      setIsRefreshing(true);
      try {
        await onRefresh();
      } finally {
        setIsRefreshing(false);
      }
    }
    setIsPulling(false);
    setPullDistance(0);
  }, [pullDistance, isRefreshing, onRefresh]);

  return {
    isPulling,
    isRefreshing,
    pullDistance,
    pullProgress: Math.min(pullDistance / threshold, 1),
    handlers: {
      onTouchStart: handleTouchStart,
      onTouchMove: handleTouchMove,
      onTouchEnd: handleTouchEnd,
    },
  };
};

/**
 * Hook for pinch-to-zoom gesture
 */
export const usePinchZoom = (minScale = 1, maxScale = 4) => {
  const [scale, setScale] = useState(1);
  const initialDistance = useRef<number | null>(null);
  const initialScale = useRef(1);

  const getDistance = (touches: React.TouchList) => {
    return Math.hypot(
      touches[0].clientX - touches[1].clientX,
      touches[0].clientY - touches[1].clientY
    );
  };

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 2) {
      initialDistance.current = getDistance(e.touches);
      initialScale.current = scale;
    }
  }, [scale]);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 2 && initialDistance.current) {
      const currentDistance = getDistance(e.touches);
      const scaleChange = currentDistance / initialDistance.current;
      const newScale = Math.min(
        maxScale,
        Math.max(minScale, initialScale.current * scaleChange)
      );
      setScale(newScale);
    }
  }, [minScale, maxScale]);

  const handleTouchEnd = useCallback(() => {
    initialDistance.current = null;
  }, []);

  const resetScale = useCallback(() => setScale(1), []);

  return {
    scale,
    setScale,
    resetScale,
    handlers: {
      onTouchStart: handleTouchStart,
      onTouchMove: handleTouchMove,
      onTouchEnd: handleTouchEnd,
    },
  };
};

/**
 * Hook for long press gesture
 */
export const useLongPress = (onLongPress: () => void, delay = 500) => {
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [isPressed, setIsPressed] = useState(false);

  const start = useCallback(() => {
    setIsPressed(true);
    timeoutRef.current = setTimeout(() => {
      onLongPress();
      // Trigger haptic feedback if available
      if (typeof navigator !== 'undefined' && 'vibrate' in navigator) {
        navigator.vibrate(20);
      }
    }, delay);
  }, [onLongPress, delay]);

  const stop = useCallback(() => {
    setIsPressed(false);
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  }, []);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return {
    isPressed,
    handlers: {
      onTouchStart: start,
      onTouchEnd: stop,
      onTouchCancel: stop,
      onMouseDown: start,
      onMouseUp: stop,
      onMouseLeave: stop,
    },
  };
};

// ============================================================================
// HAPTIC FEEDBACK
// ============================================================================

/**
 * Hook for haptic feedback (vibration)
 */
export const useHaptic = () => {
  const isSupported =
    typeof navigator !== 'undefined' && 'vibrate' in navigator;

  const vibrate = useCallback((pattern: number | number[]) => {
    if (isSupported) {
      navigator.vibrate(pattern);
    }
  }, [isSupported]);

  return {
    isSupported,
    // Light tap - button press
    light: useCallback(() => vibrate(10), [vibrate]),
    // Medium - selection change
    medium: useCallback(() => vibrate(20), [vibrate]),
    // Heavy - important action
    heavy: useCallback(() => vibrate([30, 10, 30]), [vibrate]),
    // Success pattern
    success: useCallback(() => vibrate([10, 50, 20]), [vibrate]),
    // Error pattern
    error: useCallback(() => vibrate([50, 30, 50, 30, 50]), [vibrate]),
    // Warning pattern
    warning: useCallback(() => vibrate([30, 50, 30]), [vibrate]),
    // Custom pattern
    custom: vibrate,
  };
};

// ============================================================================
// DEVICE CAPABILITIES
// ============================================================================

interface DeviceCapabilities {
  isLowPower: boolean;
  isTouchDevice: boolean;
  hasReducedMotion: boolean;
  connectionType: string;
  deviceMemory: number;
  hardwareConcurrency: number;
}

/**
 * Hook to detect device capabilities for adaptive UI
 */
export const useDeviceCapabilities = (): DeviceCapabilities => {
  const [capabilities, setCapabilities] = useState<DeviceCapabilities>({
    isLowPower: false,
    isTouchDevice: false,
    hasReducedMotion: false,
    connectionType: 'unknown',
    deviceMemory: 8,
    hardwareConcurrency: 4,
  });

  useEffect(() => {
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    const hasLowMemory =
      (navigator as any).deviceMemory && (navigator as any).deviceMemory < 4;
    const hasSlowCPU =
      navigator.hardwareConcurrency && navigator.hardwareConcurrency < 4;
    const hasReducedMotion = window.matchMedia(
      '(prefers-reduced-motion: reduce)'
    ).matches;
    const isTouchDevice =
      'ontouchstart' in window || navigator.maxTouchPoints > 0;

    // Network information
    const connection = (navigator as any).connection;
    const connectionType = connection?.effectiveType || 'unknown';
    const isSlowConnection = ['slow-2g', '2g', '3g'].includes(connectionType);

    setCapabilities({
      isLowPower: isMobile || hasLowMemory || hasSlowCPU || isSlowConnection,
      isTouchDevice,
      hasReducedMotion,
      connectionType,
      deviceMemory: (navigator as any).deviceMemory || 8,
      hardwareConcurrency: navigator.hardwareConcurrency || 4,
    });
  }, []);

  return capabilities;
};

/**
 * Hook for reduced motion preference
 */
export const usePrefersReducedMotion = () => {
  const [prefersReduced, setPrefersReduced] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReduced(mediaQuery.matches);

    const handler = (e: MediaQueryListEvent) => setPrefersReduced(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  return prefersReduced;
};

/**
 * Hook for color scheme preference
 */
export const usePrefersColorScheme = () => {
  const [scheme, setScheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    setScheme(mediaQuery.matches ? 'dark' : 'light');

    const handler = (e: MediaQueryListEvent) =>
      setScheme(e.matches ? 'dark' : 'light');
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  return scheme;
};

// ============================================================================
// SCROLL & INTERSECTION
// ============================================================================

/**
 * Hook for scroll-triggered animations
 */
export const useScrollReveal = (threshold = 0.1) => {
  const ref = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { threshold }
    );

    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [threshold]);

  return { ref, isVisible };
};

/**
 * Hook for infinite scroll
 */
export const useInfiniteScroll = (
  onLoadMore: () => Promise<void>,
  hasMore: boolean
) => {
  const [isLoading, setIsLoading] = useState(false);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!hasMore || isLoading) return;

    const observer = new IntersectionObserver(
      async ([entry]) => {
        if (entry.isIntersecting && hasMore && !isLoading) {
          setIsLoading(true);
          try {
            await onLoadMore();
          } finally {
            setIsLoading(false);
          }
        }
      },
      { rootMargin: '100px' }
    );

    if (loadMoreRef.current) observer.observe(loadMoreRef.current);
    return () => observer.disconnect();
  }, [hasMore, isLoading, onLoadMore]);

  return { loadMoreRef, isLoading };
};

/**
 * Hook for scroll position
 */
export const useScrollPosition = () => {
  const [scrollPosition, setScrollPosition] = useState({
    x: 0,
    y: 0,
    direction: 'up' as 'up' | 'down',
    isAtTop: true,
    isAtBottom: false,
  });

  const prevScrollY = useRef(0);

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      const direction = currentScrollY > prevScrollY.current ? 'down' : 'up';
      const isAtTop = currentScrollY < 10;
      const isAtBottom =
        window.innerHeight + currentScrollY >=
        document.documentElement.scrollHeight - 10;

      setScrollPosition({
        x: window.scrollX,
        y: currentScrollY,
        direction,
        isAtTop,
        isAtBottom,
      });

      prevScrollY.current = currentScrollY;
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return scrollPosition;
};

// ============================================================================
// FOCUS MANAGEMENT
// ============================================================================

/**
 * Hook for focus trap (for modals/dialogs)
 */
export const useFocusTrap = (isActive: boolean) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isActive || !containerRef.current) return;

    const focusableElements = containerRef.current.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    // Focus first element
    firstElement?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement?.focus();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement?.focus();
      }
    };

    containerRef.current.addEventListener('keydown', handleKeyDown);
    return () =>
      containerRef.current?.removeEventListener('keydown', handleKeyDown);
  }, [isActive]);

  return containerRef;
};

// ============================================================================
// SCREEN READER ANNOUNCEMENTS
// ============================================================================

/**
 * Hook for screen reader announcements
 */
export const useAnnounce = () => {
  const announce = useCallback(
    (message: string, priority: 'polite' | 'assertive' = 'polite') => {
      const el = document.createElement('div');
      el.setAttribute('role', 'status');
      el.setAttribute('aria-live', priority);
      el.setAttribute('aria-atomic', 'true');
      el.className = 'sr-only';
      el.textContent = message;
      document.body.appendChild(el);
      setTimeout(() => el.remove(), 1000);
    },
    []
  );

  return { announce };
};

// ============================================================================
// KEYBOARD NAVIGATION
// ============================================================================

/**
 * Hook for arrow key navigation in lists/grids
 */
export const useArrowNavigation = (itemCount: number) => {
  const [activeIndex, setActiveIndex] = useState(0);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
        case 'ArrowRight':
          e.preventDefault();
          setActiveIndex((i) => (i + 1) % itemCount);
          break;
        case 'ArrowUp':
        case 'ArrowLeft':
          e.preventDefault();
          setActiveIndex((i) => (i - 1 + itemCount) % itemCount);
          break;
        case 'Home':
          e.preventDefault();
          setActiveIndex(0);
          break;
        case 'End':
          e.preventDefault();
          setActiveIndex(itemCount - 1);
          break;
      }
    },
    [itemCount]
  );

  return { activeIndex, setActiveIndex, handleKeyDown };
};

// ============================================================================
// SAFE AREA
// ============================================================================

/**
 * Hook for safe area insets (notch, home indicator, etc.)
 */
export const useSafeArea = () => {
  const [safeArea, setSafeArea] = useState({
    top: 0,
    bottom: 0,
    left: 0,
    right: 0,
  });

  useEffect(() => {
    const computeInsets = () => {
      const style = getComputedStyle(document.documentElement);
      setSafeArea({
        top:
          parseInt(
            style.getPropertyValue('--safe-area-inset-top') || '0',
            10
          ) || 0,
        bottom:
          parseInt(
            style.getPropertyValue('--safe-area-inset-bottom') || '0',
            10
          ) || 0,
        left:
          parseInt(
            style.getPropertyValue('--safe-area-inset-left') || '0',
            10
          ) || 0,
        right:
          parseInt(
            style.getPropertyValue('--safe-area-inset-right') || '0',
            10
          ) || 0,
      });
    };

    computeInsets();
    window.addEventListener('resize', computeInsets);
    return () => window.removeEventListener('resize', computeInsets);
  }, []);

  return safeArea;
};

// ============================================================================
// ONLINE STATUS
// ============================================================================

/**
 * Hook for online/offline status
 */
export const useOnlineStatus = () => {
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
};

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  useBreakpoint,
  useMediaQuery,
  useSwipeGesture,
  usePullToRefresh,
  usePinchZoom,
  useLongPress,
  useHaptic,
  useDeviceCapabilities,
  usePrefersReducedMotion,
  usePrefersColorScheme,
  useScrollReveal,
  useInfiniteScroll,
  useScrollPosition,
  useFocusTrap,
  useAnnounce,
  useArrowNavigation,
  useSafeArea,
  useOnlineStatus,
};

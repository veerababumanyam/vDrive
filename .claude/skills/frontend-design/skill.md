---
name: frontend-design
aliases: [ui-design, frontend, react-components, pages, premium-ui, cinematic, landing-page, glassmorphism, mobile-first, futuristic]
description: Create distinctive, production-grade, mobile-first, futuristic frontend interfaces with high design quality for vDrive. Use this skill when the user asks to build web components, pages, or applications. Generates creative, polished code that avoids generic AI aesthetics while leveraging vDrive's design system.
---

# vDrive Frontend Design Skill

Create **distinctive, production-grade, futuristic, mobile-first** frontend interfaces that avoid generic "AI slop" aesthetics. vDrive is a **premium photography SaaS platform**. Every interface should feel:

- **Futuristic** - Cutting-edge visual effects and interactions
- **Mobile-First** - Touch-optimized, gesture-driven, native app feel
- **Cinematic** - Like a high-end photo editing suite
- **Premium** - Luxury brand quality for professional photographers
- **Memorable** - Distinctive enough to be recognized instantly

> **For brand colors, tokens, and component APIs**: See the `design-system` skill.

---

## Mobile-First Design Philosophy

**CRITICAL**: Always design mobile first, then enhance for larger screens.

### Core Principles

1. **Touch-First**: Design for fingers, not cursors
2. **Thumb Zone**: Critical actions within thumb reach
3. **Native Feel**: Gestures, haptics, smooth 60fps animations
4. **Safe Areas**: Respect notches, home indicators, dynamic islands
5. **Offline-Ready**: Optimistic UI, graceful degradation

---

## Mobile-First Design System

### Safe Area Handling (REQUIRED for Modern Devices)

```css
/* Critical for iPhones with notch/Dynamic Island */
:root {
  --safe-area-top: env(safe-area-inset-top, 0px);
  --safe-area-bottom: env(safe-area-inset-bottom, 0px);
  --safe-area-left: env(safe-area-inset-left, 0px);
  --safe-area-right: env(safe-area-inset-right, 0px);
}

/* Full-screen container with safe areas */
.mobile-safe-container {
  padding-top: var(--safe-area-top);
  padding-bottom: var(--safe-area-bottom);
  padding-left: var(--safe-area-left);
  padding-right: var(--safe-area-right);
}

/* Fixed header respecting notch */
.mobile-header {
  padding-top: calc(var(--safe-area-top) + 12px);
  padding-left: calc(var(--safe-area-left) + 16px);
  padding-right: calc(var(--safe-area-right) + 16px);
}

/* Bottom navigation with home indicator */
.mobile-bottom-nav {
  padding-bottom: calc(var(--safe-area-bottom) + 8px);
}

/* Tailwind utilities */
.pt-safe { padding-top: env(safe-area-inset-top); }
.pb-safe { padding-bottom: env(safe-area-inset-bottom); }
.pl-safe { padding-left: env(safe-area-inset-left); }
.pr-safe { padding-right: env(safe-area-inset-right); }
```

### Touch Gesture System

```typescript
// Swipe gesture hook for mobile navigation
const useSwipeGesture = (
  onSwipeLeft?: () => void,
  onSwipeRight?: () => void,
  threshold = 50
) => {
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [touchEnd, setTouchEnd] = useState<number | null>(null);

  const onTouchStart = (e: TouchEvent) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
  };

  const onTouchMove = (e: TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    const distance = touchStart - touchEnd;
    const isSwipe = Math.abs(distance) > threshold;

    if (isSwipe) {
      if (distance > 0) {
        onSwipeLeft?.();
      } else {
        onSwipeRight?.();
      }
    }
  };

  return { onTouchStart, onTouchMove, onTouchEnd };
};

// Pull-to-refresh pattern
const usePullToRefresh = (onRefresh: () => Promise<void>) => {
  const [isPulling, setIsPulling] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const startY = useRef(0);
  const threshold = 80;

  const handleTouchStart = (e: TouchEvent) => {
    if (window.scrollY === 0) {
      startY.current = e.touches[0].clientY;
      setIsPulling(true);
    }
  };

  const handleTouchMove = (e: TouchEvent) => {
    if (!isPulling) return;
    const currentY = e.touches[0].clientY;
    const distance = Math.max(0, (currentY - startY.current) * 0.5);
    setPullDistance(Math.min(distance, threshold * 1.5));
  };

  const handleTouchEnd = async () => {
    if (pullDistance >= threshold && !isRefreshing) {
      setIsRefreshing(true);
      await onRefresh();
      setIsRefreshing(false);
    }
    setIsPulling(false);
    setPullDistance(0);
  };

  return {
    isPulling,
    isRefreshing,
    pullDistance,
    pullProgress: Math.min(pullDistance / threshold, 1),
    handlers: { onTouchStart: handleTouchStart, onTouchMove: handleTouchMove, onTouchEnd: handleTouchEnd }
  };
};

// Pinch-to-zoom gesture
const usePinchZoom = (minScale = 1, maxScale = 4) => {
  const [scale, setScale] = useState(1);
  const initialDistance = useRef<number | null>(null);
  const initialScale = useRef(1);

  const getDistance = (touches: TouchList) => {
    return Math.hypot(
      touches[0].clientX - touches[1].clientX,
      touches[0].clientY - touches[1].clientY
    );
  };

  const handleTouchStart = (e: TouchEvent) => {
    if (e.touches.length === 2) {
      initialDistance.current = getDistance(e.touches);
      initialScale.current = scale;
    }
  };

  const handleTouchMove = (e: TouchEvent) => {
    if (e.touches.length === 2 && initialDistance.current) {
      const currentDistance = getDistance(e.touches);
      const scaleChange = currentDistance / initialDistance.current;
      const newScale = Math.min(maxScale, Math.max(minScale, initialScale.current * scaleChange));
      setScale(newScale);
    }
  };

  const handleTouchEnd = () => {
    initialDistance.current = null;
  };

  return { scale, setScale, handlers: { onTouchStart: handleTouchStart, onTouchMove: handleTouchMove, onTouchEnd: handleTouchEnd } };
};

// Long press gesture
const useLongPress = (onLongPress: () => void, delay = 500) => {
  const timeoutRef = useRef<NodeJS.Timeout>();
  const [isPressed, setIsPressed] = useState(false);

  const start = useCallback(() => {
    setIsPressed(true);
    timeoutRef.current = setTimeout(() => {
      onLongPress();
      // Trigger haptic feedback
      navigator.vibrate?.(20);
    }, delay);
  }, [onLongPress, delay]);

  const stop = useCallback(() => {
    setIsPressed(false);
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
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
    }
  };
};
```

### Haptic Feedback System

```typescript
// Haptic feedback utilities for native feel
const useHaptic = () => {
  const isSupported = typeof navigator !== 'undefined' && 'vibrate' in navigator;

  return {
    isSupported,
    // Light tap - button press
    light: () => navigator.vibrate?.(10),
    // Medium - selection change
    medium: () => navigator.vibrate?.(20),
    // Heavy - important action
    heavy: () => navigator.vibrate?.([30, 10, 30]),
    // Success pattern
    success: () => navigator.vibrate?.([10, 50, 20]),
    // Error pattern
    error: () => navigator.vibrate?.([50, 30, 50, 30, 50]),
    // Warning pattern
    warning: () => navigator.vibrate?.([30, 50, 30]),
    // Custom pattern
    custom: (pattern: number | number[]) => navigator.vibrate?.(pattern),
  };
};

// Usage with button
const HapticButton = ({ children, hapticType = 'light', onClick, ...props }) => {
  const haptic = useHaptic();

  const handleClick = (e) => {
    haptic[hapticType]?.();
    onClick?.(e);
  };

  return (
    <button onClick={handleClick} {...props}>
      {children}
    </button>
  );
};
```

### Responsive Breakpoint System

```typescript
// Mobile-first breakpoints
const breakpoints = {
  xs: 0,      // 0-359px: Small phones
  sm: 360,    // 360-479px: Standard phones
  md: 480,    // 480-767px: Large phones, small tablets
  lg: 768,    // 768-1023px: Tablets
  xl: 1024,   // 1024-1279px: Small laptops, tablets landscape
  '2xl': 1280, // 1280px+: Desktops
};

// Responsive hook
const useBreakpoint = () => {
  const [breakpoint, setBreakpoint] = useState<keyof typeof breakpoints>('xs');
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

// Responsive component wrapper
const Responsive = ({ mobile, tablet, desktop, children }) => {
  const { isMobile, isTablet, isDesktop } = useBreakpoint();

  if (isMobile && mobile) return mobile;
  if (isTablet && tablet) return tablet;
  if (isDesktop && desktop) return desktop;
  return children;
};
```

---

## Futuristic Visual Effects

### Morphing Blob Backgrounds

```typescript
const MorphingBlobBackground = ({ color = 'accent' }) => (
  <div className="absolute inset-0 -z-10 overflow-hidden">
    <svg
      viewBox="0 0 200 200"
      className="absolute w-[150%] h-[150%] -top-1/4 -left-1/4"
    >
      <defs>
        <linearGradient id="blob-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="var(--color-accent)" stopOpacity="0.4" />
          <stop offset="50%" stopColor="var(--color-primary)" stopOpacity="0.2" />
          <stop offset="100%" stopColor="var(--color-accent)" stopOpacity="0.1" />
        </linearGradient>
        <filter id="blob-blur">
          <feGaussianBlur in="SourceGraphic" stdDeviation="20" />
        </filter>
      </defs>
      <path
        fill="url(#blob-gradient)"
        filter="url(#blob-blur)"
        className="animate-morph"
      >
        <animate
          attributeName="d"
          dur="20s"
          repeatCount="indefinite"
          values="
            M44.7,-76.4C58.8,-69.2,71.8,-59.1,79.6,-45.8C87.4,-32.5,90,-16.3,88.5,-0.9C87,14.5,81.4,29,73.1,42.3C64.8,55.6,53.8,67.7,40.3,75.2C26.8,82.7,10.9,85.6,-3.6,91.9C-18.1,98.2,-31.2,107.9,-43.3,104.6C-55.4,101.3,-66.5,85,-74.3,69.1C-82.1,53.2,-86.6,37.7,-87.8,22.6C-89,7.5,-86.9,-7.2,-82.3,-21.1C-77.7,-35,-70.6,-48.1,-59.8,-57.4C-49,-66.7,-34.5,-72.2,-19.8,-76.4C-5.1,-80.6,9.8,-83.5,24.4,-81.9C39,-80.3,53.3,-74.2,44.7,-76.4Z;
            M47.7,-79.8C62.3,-72.4,75.1,-60.5,82.6,-45.9C90.1,-31.3,92.3,-14,90.6,2.4C88.9,18.8,83.3,34.3,74.3,47.4C65.3,60.5,52.9,71.2,38.7,77.8C24.5,84.4,8.5,86.9,-7.2,95.2C-22.9,103.5,-38.3,117.6,-51.5,114.3C-64.7,111,-75.7,90.3,-81.9,71C-88.1,51.7,-89.5,33.8,-88.8,17.2C-88.1,0.6,-85.3,-14.7,-79.5,-28.6C-73.7,-42.5,-64.9,-55,-52.8,-63.5C-40.7,-72,-25.3,-76.5,-9.4,-81.8C6.5,-87.1,22.4,-93.2,47.7,-79.8Z;
            M44.7,-76.4C58.8,-69.2,71.8,-59.1,79.6,-45.8C87.4,-32.5,90,-16.3,88.5,-0.9C87,14.5,81.4,29,73.1,42.3C64.8,55.6,53.8,67.7,40.3,75.2C26.8,82.7,10.9,85.6,-3.6,91.9C-18.1,98.2,-31.2,107.9,-43.3,104.6C-55.4,101.3,-66.5,85,-74.3,69.1C-82.1,53.2,-86.6,37.7,-87.8,22.6C-89,7.5,-86.9,-7.2,-82.3,-21.1C-77.7,-35,-70.6,-48.1,-59.8,-57.4C-49,-66.7,-34.5,-72.2,-19.8,-76.4C-5.1,-80.6,9.8,-83.5,24.4,-81.9C39,-80.3,53.3,-74.2,44.7,-76.4Z
          "
        />
      </path>
    </svg>
  </div>
);

// CSS keyframes for morph animation
// Add to tailwind.config.js or index.css
/*
@keyframes morph {
  0%, 100% {
    border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%;
    transform: rotate(0deg);
  }
  50% {
    border-radius: 30% 60% 70% 40% / 50% 60% 30% 60%;
    transform: rotate(180deg);
  }
}
.animate-morph {
  animation: morph 15s ease-in-out infinite;
}
*/
```

### Holographic / Iridescent Effects

```typescript
// Rainbow shimmer on glass surfaces
const HolographicCard = ({ children, className }) => (
  <div className={cn("relative group", className)}>
    {/* Holographic shimmer layer */}
    <div className={cn(
      "absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100",
      "bg-[linear-gradient(45deg,#ff0080,#ff8c00,#40e0d0,#ff0080)]",
      "bg-[length:400%_400%] animate-gradient-xy",
      "transition-opacity duration-500 blur-xl"
    )} />
    {/* Card content */}
    <div className={cn(
      "relative bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl",
      "group-hover:border-white/30 transition-all duration-500"
    )}>
      {children}
    </div>
  </div>
);

// Iridescent text effect
const IridescentText = ({ children, className }) => (
  <span className={cn(
    "bg-[linear-gradient(90deg,#ff0080,#ff8c00,#40e0d0,#7b68ee,#ff0080)]",
    "bg-[length:200%_auto] bg-clip-text text-transparent",
    "animate-gradient-x",
    className
  )}>
    {children}
  </span>
);

// Chrome/metallic text
const ChromeText = ({ children, className }) => (
  <span className={cn(
    "bg-[linear-gradient(180deg,#fff_0%,#999_40%,#fff_50%,#666_60%,#fff_100%)]",
    "bg-clip-text text-transparent",
    "drop-shadow-[0_1px_1px_rgba(0,0,0,0.5)]",
    className
  )}>
    {children}
  </span>
);
```

### Neon Glow System

```typescript
// Neon glow utilities
const neonGlowClasses = {
  // Accent neon
  'neon-accent-sm': 'shadow-[0_0_10px_var(--color-accent),0_0_20px_var(--color-accent-50)]',
  'neon-accent-md': 'shadow-[0_0_20px_var(--color-accent),0_0_40px_var(--color-accent-50)]',
  'neon-accent-lg': 'shadow-[0_0_30px_var(--color-accent),0_0_60px_var(--color-accent-50),0_0_90px_var(--color-accent-100)]',

  // Primary neon
  'neon-primary-sm': 'shadow-[0_0_10px_var(--color-primary),0_0_20px_rgba(37,99,235,0.3)]',
  'neon-primary-md': 'shadow-[0_0_20px_var(--color-primary),0_0_40px_rgba(37,99,235,0.3)]',
  'neon-primary-lg': 'shadow-[0_0_30px_var(--color-primary),0_0_60px_rgba(37,99,235,0.3)]',

  // Success neon (green)
  'neon-success': 'shadow-[0_0_20px_rgba(16,185,129,0.6),0_0_40px_rgba(16,185,129,0.3)]',

  // Warning neon (amber)
  'neon-warning': 'shadow-[0_0_20px_rgba(245,158,11,0.6),0_0_40px_rgba(245,158,11,0.3)]',

  // Error neon (red)
  'neon-error': 'shadow-[0_0_20px_rgba(239,68,68,0.6),0_0_40px_rgba(239,68,68,0.3)]',
};

// Animated neon pulse button
const NeonButton = ({ children, color = 'accent', className, ...props }) => (
  <motion.button
    whileHover={{ scale: 1.02 }}
    whileTap={{ scale: 0.98 }}
    className={cn(
      "relative px-6 py-3 rounded-xl font-medium",
      "bg-transparent border-2",
      color === 'accent' && "border-accent-500 text-accent-400",
      color === 'primary' && "border-primary-500 text-primary-400",
      "transition-all duration-300",
      "hover:shadow-[0_0_30px_var(--color-accent),0_0_60px_var(--color-accent-50)]",
      "active:shadow-[0_0_15px_var(--color-accent)]",
      className
    )}
    {...props}
  >
    {/* Glow background on hover */}
    <span className="absolute inset-0 rounded-xl bg-accent-500/10 opacity-0 group-hover:opacity-100 transition-opacity" />
    <span className="relative">{children}</span>
  </motion.button>
);

// Neon border animation
const NeonBorderCard = ({ children }) => (
  <div className="relative p-[2px] rounded-2xl overflow-hidden group">
    {/* Animated border */}
    <div className={cn(
      "absolute inset-0",
      "bg-[conic-gradient(from_0deg,transparent,var(--color-accent),transparent_120deg)]",
      "animate-spin-slow opacity-0 group-hover:opacity-100 transition-opacity duration-500"
    )} />
    {/* Static border fallback */}
    <div className="absolute inset-0 bg-gradient-to-r from-accent-500/50 via-primary-500/50 to-accent-500/50 opacity-50" />
    {/* Content */}
    <div className="relative bg-warm-950 rounded-2xl p-6">
      {children}
    </div>
  </div>
);
```

### Liquid / Fluid Animations

```typescript
// Liquid button with fill effect
const LiquidButton = ({ children, className, ...props }) => (
  <button
    className={cn(
      "relative overflow-hidden px-6 py-3 rounded-xl",
      "bg-transparent border-2 border-accent-500 text-accent-400",
      "transition-colors duration-500",
      "hover:text-white",
      "group",
      className
    )}
    {...props}
  >
    {/* Liquid fill effect */}
    <span className={cn(
      "absolute inset-0 bg-accent-500",
      "transform origin-bottom scale-y-0 group-hover:scale-y-100",
      "transition-transform duration-500 ease-out"
    )} />
    {/* Ripple effect on click */}
    <span className="absolute inset-0 overflow-hidden rounded-xl">
      <span className={cn(
        "absolute w-0 h-0 rounded-full bg-white/30",
        "left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2",
        "group-active:w-[300%] group-active:h-[300%]",
        "transition-all duration-500"
      )} />
    </span>
    <span className="relative z-10">{children}</span>
  </button>
);

// Liquid card reveal
const LiquidRevealCard = ({ children, direction = 'bottom' }) => {
  const [isRevealed, setIsRevealed] = useState(false);
  const { ref, isVisible } = useScrollReveal(0.3);

  useEffect(() => {
    if (isVisible) setIsRevealed(true);
  }, [isVisible]);

  const origins = {
    bottom: 'origin-bottom',
    top: 'origin-top',
    left: 'origin-left',
    right: 'origin-right',
  };

  return (
    <div ref={ref} className="relative overflow-hidden rounded-2xl">
      {/* Reveal mask */}
      <div className={cn(
        "absolute inset-0 bg-accent-500/20 backdrop-blur-xl z-10",
        "transform transition-transform duration-1000 ease-out",
        origins[direction],
        isRevealed ? 'scale-y-0' : 'scale-y-100'
      )} />
      {/* Content */}
      <div className={cn(
        "transition-opacity duration-500 delay-300",
        isRevealed ? 'opacity-100' : 'opacity-0'
      )}>
        {children}
      </div>
    </div>
  );
};
```

### Particle Effects

```typescript
// Floating particles background
const ParticleField = ({ count = 50, color = 'accent' }) => {
  const particles = useMemo(() =>
    Array.from({ length: count }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 4 + 1,
      duration: Math.random() * 20 + 10,
      delay: Math.random() * 5,
    })), [count]
  );

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {particles.map(particle => (
        <motion.div
          key={particle.id}
          className={cn(
            "absolute rounded-full",
            color === 'accent' && "bg-accent-500/30",
            color === 'primary' && "bg-primary-500/30",
            color === 'white' && "bg-white/20"
          )}
          style={{
            width: particle.size,
            height: particle.size,
            left: `${particle.x}%`,
            top: `${particle.y}%`,
          }}
          animate={{
            y: [0, -30, 0],
            x: [0, Math.random() * 20 - 10, 0],
            opacity: [0.3, 0.8, 0.3],
          }}
          transition={{
            duration: particle.duration,
            delay: particle.delay,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
};

// Cursor trail effect
const useCursorTrail = (trailLength = 10) => {
  const [trail, setTrail] = useState<{ x: number; y: number; id: number }[]>([]);
  const idRef = useRef(0);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setTrail(prev => {
        const newPoint = { x: e.clientX, y: e.clientY, id: idRef.current++ };
        return [...prev.slice(-trailLength + 1), newPoint];
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [trailLength]);

  return trail;
};

const CursorTrail = () => {
  const trail = useCursorTrail();

  return (
    <div className="fixed inset-0 pointer-events-none z-50">
      {trail.map((point, index) => (
        <motion.div
          key={point.id}
          className="absolute w-4 h-4 rounded-full bg-accent-500/50"
          style={{ left: point.x, top: point.y }}
          initial={{ scale: 1, opacity: 0.8 }}
          animate={{ scale: 0, opacity: 0 }}
          transition={{ duration: 0.5 }}
        />
      ))}
    </div>
  );
};
```

---

## Mobile Navigation Patterns

### Bottom Sheet Navigation

```typescript
const BottomSheet = ({
  isOpen,
  onClose,
  children,
  snapPoints = [0.5, 0.9], // 50% and 90% of screen
  initialSnap = 0
}) => {
  const [currentSnap, setCurrentSnap] = useState(initialSnap);
  const sheetRef = useRef<HTMLDivElement>(null);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
            onClick={onClose}
          />

          {/* Sheet */}
          <motion.div
            ref={sheetRef}
            initial={{ y: '100%' }}
            animate={{ y: `${(1 - snapPoints[currentSnap]) * 100}%` }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            drag="y"
            dragConstraints={{ top: 0 }}
            dragElastic={0.2}
            onDragEnd={(_, { offset, velocity }) => {
              if (offset.y > 100 || velocity.y > 500) {
                onClose();
              } else if (offset.y < -50 && currentSnap < snapPoints.length - 1) {
                setCurrentSnap(currentSnap + 1);
              } else if (offset.y > 50 && currentSnap > 0) {
                setCurrentSnap(currentSnap - 1);
              }
            }}
            className={cn(
              "fixed bottom-0 inset-x-0 z-50",
              "bg-warm-900 rounded-t-3xl",
              "shadow-[0_-10px_40px_rgba(0,0,0,0.3)]",
              "max-h-[90vh] overflow-hidden"
            )}
            style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
          >
            {/* Drag handle */}
            <div className="flex justify-center pt-3 pb-2">
              <div className="w-10 h-1 bg-warm-600 rounded-full" />
            </div>

            {/* Content */}
            <div className="overflow-y-auto max-h-[calc(90vh-40px)] px-4 pb-4">
              {children}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

// Usage
const MobilePhotoActions = ({ isOpen, onClose, photo }) => (
  <BottomSheet isOpen={isOpen} onClose={onClose}>
    <div className="space-y-2">
      <h3 className="text-lg font-semibold text-white mb-4">Photo Actions</h3>

      <button className="w-full flex items-center gap-3 p-4 rounded-xl bg-warm-800 hover:bg-warm-700 text-white">
        <Share2 className="w-5 h-5" />
        <span>Share</span>
      </button>

      <button className="w-full flex items-center gap-3 p-4 rounded-xl bg-warm-800 hover:bg-warm-700 text-white">
        <Download className="w-5 h-5" />
        <span>Download</span>
      </button>

      <button className="w-full flex items-center gap-3 p-4 rounded-xl bg-warm-800 hover:bg-warm-700 text-white">
        <Edit3 className="w-5 h-5" />
        <span>Edit</span>
      </button>

      <button className="w-full flex items-center gap-3 p-4 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-400">
        <Trash2 className="w-5 h-5" />
        <span>Delete</span>
      </button>
    </div>
  </BottomSheet>
);
```

### Floating Action Button (FAB)

```typescript
const FloatingActionButton = ({
  actions,
  position = 'bottom-right',
  mainIcon = Plus
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const haptic = useHaptic();
  const MainIcon = mainIcon;

  const positions = {
    'bottom-right': 'fixed bottom-6 right-6',
    'bottom-left': 'fixed bottom-6 left-6',
    'bottom-center': 'fixed bottom-6 left-1/2 -translate-x-1/2',
  };

  return (
    <div
      className={cn(positions[position], "z-50")}
      style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
    >
      <div className="flex flex-col-reverse items-center gap-3">
        {/* Main FAB */}
        <motion.button
          whileTap={{ scale: 0.95 }}
          onClick={() => {
            haptic.medium();
            setIsExpanded(!isExpanded);
          }}
          className={cn(
            "w-14 h-14 rounded-full",
            "bg-accent-500 shadow-[0_4px_20px_rgba(59,130,246,0.5)]",
            "flex items-center justify-center text-white",
            "focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
          )}
        >
          <motion.div animate={{ rotate: isExpanded ? 45 : 0 }}>
            <MainIcon className="w-6 h-6" />
          </motion.div>
        </motion.button>

        {/* Expanded actions */}
        <AnimatePresence>
          {isExpanded && (
            <>
              {/* Backdrop for closing */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 -z-10"
                onClick={() => setIsExpanded(false)}
              />

              {/* Action buttons */}
              {actions.map((action, index) => (
                <motion.div
                  key={action.id}
                  initial={{ scale: 0, opacity: 0, y: 20 }}
                  animate={{ scale: 1, opacity: 1, y: 0 }}
                  exit={{ scale: 0, opacity: 0, y: 20 }}
                  transition={{ delay: index * 0.05, type: 'spring', stiffness: 300 }}
                  className="flex items-center gap-3"
                >
                  {/* Label */}
                  <motion.span
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 10 }}
                    className="px-3 py-1.5 rounded-lg bg-warm-800 text-white text-sm whitespace-nowrap"
                  >
                    {action.label}
                  </motion.span>

                  {/* Button */}
                  <button
                    onClick={() => {
                      haptic.light();
                      action.onClick();
                      setIsExpanded(false);
                    }}
                    className={cn(
                      "w-12 h-12 rounded-full",
                      "bg-warm-800 border border-warm-700",
                      "flex items-center justify-center",
                      "shadow-float transition-colors",
                      "hover:bg-warm-700 active:scale-95"
                    )}
                  >
                    <action.icon className="w-5 h-5 text-white" />
                  </button>
                </motion.div>
              ))}
            </>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

// Usage
<FloatingActionButton
  actions={[
    { id: 'upload', label: 'Upload Photo', icon: Upload, onClick: handleUpload },
    { id: 'camera', label: 'Take Photo', icon: Camera, onClick: handleCamera },
    { id: 'folder', label: 'New Album', icon: FolderPlus, onClick: handleNewAlbum },
  ]}
/>
```

### Mobile Tab Bar

```typescript
const MobileTabBar = ({ tabs, activeTab, onTabChange }) => {
  const haptic = useHaptic();

  return (
    <nav
      className={cn(
        "fixed bottom-0 inset-x-0 z-40",
        "bg-warm-900/95 backdrop-blur-xl border-t border-warm-800",
        "pb-safe"
      )}
    >
      <div className="flex items-center justify-around h-16 px-2">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          const Icon = tab.icon;

          return (
            <button
              key={tab.id}
              onClick={() => {
                haptic.light();
                onTabChange(tab.id);
              }}
              className={cn(
                "flex flex-col items-center justify-center",
                "w-16 h-14 rounded-xl transition-all duration-200",
                "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500",
                isActive ? "text-accent-500" : "text-warm-400 hover:text-warm-200"
              )}
            >
              <motion.div
                animate={{ scale: isActive ? 1.1 : 1 }}
                transition={{ type: 'spring', stiffness: 400 }}
              >
                <Icon className="w-6 h-6" />
              </motion.div>
              <span className={cn(
                "text-xs mt-1 transition-all",
                isActive ? "font-medium" : "font-normal"
              )}>
                {tab.label}
              </span>

              {/* Active indicator */}
              {isActive && (
                <motion.div
                  layoutId="tab-indicator"
                  className="absolute -top-0.5 w-8 h-1 bg-accent-500 rounded-full"
                />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
};
```

### Swipeable Cards

```typescript
const SwipeableCard = ({
  children,
  onSwipeLeft,
  onSwipeRight,
  leftAction,
  rightAction
}) => {
  const [offset, setOffset] = useState(0);
  const threshold = 100;

  return (
    <div className="relative overflow-hidden rounded-xl">
      {/* Left action (swipe right reveals) */}
      <div className={cn(
        "absolute inset-y-0 left-0 flex items-center justify-center",
        "w-20 bg-emerald-500 text-white",
        "transform transition-transform",
        offset > 20 ? "translate-x-0" : "-translate-x-full"
      )}>
        {leftAction || <Check className="w-6 h-6" />}
      </div>

      {/* Right action (swipe left reveals) */}
      <div className={cn(
        "absolute inset-y-0 right-0 flex items-center justify-center",
        "w-20 bg-rose-500 text-white",
        "transform transition-transform",
        offset < -20 ? "translate-x-0" : "translate-x-full"
      )}>
        {rightAction || <Trash2 className="w-6 h-6" />}
      </div>

      {/* Main card */}
      <motion.div
        drag="x"
        dragConstraints={{ left: -threshold * 1.5, right: threshold * 1.5 }}
        dragElastic={0.1}
        onDrag={(_, { offset }) => setOffset(offset.x)}
        onDragEnd={(_, { offset, velocity }) => {
          if (offset.x > threshold || velocity.x > 500) {
            onSwipeRight?.();
          } else if (offset.x < -threshold || velocity.x < -500) {
            onSwipeLeft?.();
          }
          setOffset(0);
        }}
        animate={{ x: 0 }}
        className="relative bg-warm-800 rounded-xl cursor-grab active:cursor-grabbing"
      >
        {children}
      </motion.div>
    </div>
  );
};
```

---

## Performance Optimizations for Mobile

### Virtual Scrolling for Large Lists

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

const VirtualPhotoGrid = ({ photos, columns = 2 }) => {
  const parentRef = useRef<HTMLDivElement>(null);
  const rows = Math.ceil(photos.length / columns);

  const virtualizer = useVirtualizer({
    count: rows,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 200, // Estimated row height
    overscan: 3, // Render 3 extra rows
  });

  return (
    <div ref={parentRef} className="h-full overflow-auto">
      <div
        style={{ height: virtualizer.getTotalSize(), position: 'relative' }}
      >
        {virtualizer.getVirtualItems().map((virtualRow) => {
          const startIndex = virtualRow.index * columns;
          const rowPhotos = photos.slice(startIndex, startIndex + columns);

          return (
            <div
              key={virtualRow.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                transform: `translateY(${virtualRow.start}px)`,
              }}
              className={`grid grid-cols-${columns} gap-2 p-2`}
            >
              {rowPhotos.map((photo) => (
                <PhotoCard key={photo.id} photo={photo} />
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
};
```

### Progressive Image Loading

```typescript
const ProgressiveImage = ({
  src,
  placeholder,
  alt,
  className,
  aspectRatio = '4/3'
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      { rootMargin: '50px' }
    );

    if (imgRef.current) observer.observe(imgRef.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={imgRef}
      className={cn("relative overflow-hidden bg-warm-800", className)}
      style={{ aspectRatio }}
    >
      {/* Blur placeholder */}
      {placeholder && (
        <img
          src={placeholder}
          alt=""
          aria-hidden="true"
          className={cn(
            "absolute inset-0 w-full h-full object-cover",
            "blur-lg scale-110 transition-opacity duration-500",
            isLoaded ? "opacity-0" : "opacity-100"
          )}
        />
      )}

      {/* Shimmer skeleton while loading */}
      {!isLoaded && !placeholder && (
        <div className="absolute inset-0 bg-warm-800 animate-pulse" />
      )}

      {/* Full resolution image */}
      {isInView && (
        <img
          src={src}
          alt={alt}
          onLoad={() => setIsLoaded(true)}
          className={cn(
            "w-full h-full object-cover transition-opacity duration-500",
            isLoaded ? "opacity-100" : "opacity-0"
          )}
          loading="lazy"
          decoding="async"
        />
      )}
    </div>
  );
};
```

### Mobile-Optimized Skeleton Loading

```typescript
const PhotoGridSkeleton = ({ count = 6, columns = 2 }) => (
  <div className={`grid grid-cols-${columns} gap-2 p-4`}>
    {Array.from({ length: count }).map((_, i) => (
      <div
        key={i}
        className="aspect-square rounded-xl bg-warm-800 overflow-hidden"
        style={{ animationDelay: `${i * 50}ms` }}
      >
        <div className="w-full h-full animate-shimmer bg-gradient-to-r from-warm-800 via-warm-700 to-warm-800 bg-[length:200%_100%]" />
      </div>
    ))}
  </div>
);

// Dashboard skeleton
const DashboardSkeleton = () => (
  <div className="p-4 space-y-6">
    {/* Header skeleton */}
    <div className="flex items-center justify-between">
      <div className="w-32 h-8 rounded-lg bg-warm-800 animate-pulse" />
      <div className="w-10 h-10 rounded-full bg-warm-800 animate-pulse" />
    </div>

    {/* Stats skeleton */}
    <div className="grid grid-cols-2 gap-4">
      {[0, 1, 2, 3].map((i) => (
        <div
          key={i}
          className="h-24 rounded-xl bg-warm-800 animate-pulse"
          style={{ animationDelay: `${i * 100}ms` }}
        />
      ))}
    </div>

    {/* Recent photos skeleton */}
    <div className="space-y-3">
      <div className="w-24 h-6 rounded bg-warm-800 animate-pulse" />
      <PhotoGridSkeleton count={4} columns={2} />
    </div>
  </div>
);
```

### Device Capability Detection

```typescript
const useDeviceCapabilities = () => {
  const [capabilities, setCapabilities] = useState({
    isLowPower: false,
    isTouchDevice: false,
    hasReducedMotion: false,
    connectionType: 'unknown',
    deviceMemory: 8,
    hardwareConcurrency: 4,
  });

  useEffect(() => {
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    const hasLowMemory = navigator.deviceMemory && navigator.deviceMemory < 4;
    const hasSlowCPU = navigator.hardwareConcurrency && navigator.hardwareConcurrency < 4;
    const hasReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

    // Network information
    const connection = (navigator as any).connection;
    const connectionType = connection?.effectiveType || 'unknown';
    const isSlowConnection = ['slow-2g', '2g', '3g'].includes(connectionType);

    setCapabilities({
      isLowPower: isMobile || hasLowMemory || hasSlowCPU || isSlowConnection,
      isTouchDevice,
      hasReducedMotion,
      connectionType,
      deviceMemory: navigator.deviceMemory || 8,
      hardwareConcurrency: navigator.hardwareConcurrency || 4,
    });
  }, []);

  return capabilities;
};

// Adaptive component based on capabilities
const AdaptiveGlassCard = ({ children, className }) => {
  const { isLowPower, hasReducedMotion } = useDeviceCapabilities();

  return (
    <div className={cn(
      "rounded-2xl border transition-all",
      isLowPower
        ? "bg-warm-900/95 border-warm-700" // Simple fallback
        : "bg-white/10 backdrop-blur-xl border-white/20", // Full glass effect
      !hasReducedMotion && "duration-300",
      className
    )}>
      {children}
    </div>
  );
};
```

---

## Glassmorphism Toolkit

### Core Glass Styles (Apple iOS-Inspired)

```typescript
// Standard frosted glass - Apple iOS style
const GlassCard = ({ children, className }) => (
  <div className={cn(
    "bg-white/[0.12] backdrop-blur-xl border border-white/25 rounded-2xl",
    "shadow-[0_8px_40px_rgba(0,0,0,0.4),inset_0_1px_0_rgba(255,255,255,0.1)]",
    className
  )}>
    {children}
  </div>
);

// Glass input field - high visibility
const GlassInput = ({ icon: Icon, className, ...props }) => (
  <div className="relative">
    {Icon && (
      <Icon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/50" />
    )}
    <input
      className={cn(
        "w-full bg-white/[0.08] backdrop-blur-xl",
        "border border-white/25 rounded-xl",
        "px-4 py-3 text-white placeholder-white/40",
        "focus:outline-none focus:border-white/40 focus:bg-white/[0.12]",
        "transition-all duration-200",
        Icon && "pl-12",
        className
      )}
      {...props}
    />
  </div>
);

// Dark mode glass (for light backgrounds)
const GlassDark = ({ children, className }) => (
  <div className={cn(
    "bg-warm-900/70 backdrop-blur-xl border border-warm-700/50 rounded-2xl",
    className
  )}>
    {children}
  </div>
);
```

### Glass Opacity Guidelines

| Element | Background | Border | Blur |
|---------|------------|--------|------|
| Cards | `white/[0.12]` | `white/25` | `blur-xl` |
| Inputs | `white/[0.08]` | `white/25` | `blur-xl` |
| Modals | `white/[0.15]` | `white/30` | `blur-2xl` |
| Tooltips | `white/[0.10]` | `white/20` | `blur-lg` |
| Mobile (performance) | `white/[0.15]` | `white/25` | `blur-md` |

**CRITICAL**: Never use `white/5` or `blur-sm` - too subtle, looks muddy.

### Multi-Layer Glass (Advanced Depth)

```typescript
const FloatingGlassPanel = ({ children }) => (
  <div className="relative">
    {/* Background blur layer */}
    <div className="absolute inset-0 bg-white/5 backdrop-blur-3xl rounded-3xl" />
    {/* Mid layer with subtle border */}
    <div className="absolute inset-2 bg-white/10 backdrop-blur-xl rounded-2xl border border-white/10" />
    {/* Content layer */}
    <div className="relative p-6 bg-white/5 backdrop-blur-md rounded-xl border border-white/20">
      {children}
    </div>
  </div>
);
```

### Responsive Glassmorphism

```typescript
// Reduce blur on mobile for performance
const ResponsiveGlass = ({ children, className }) => (
  <div className={cn(
    "bg-white/10 border border-white/20 rounded-2xl",
    "backdrop-blur-md md:backdrop-blur-xl", // Less blur on mobile
    "backdrop-saturate-150", // Boost colors through blur
    className
  )}>
    {children}
  </div>
);
```

---

## Advanced Animation System

### CSS-Only Entrance Animations

```css
/* Keyframe definitions (in index.css) */
@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fade-in-down {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fade-in-scale {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes slide-in-left {
  from { opacity: 0; transform: translateX(-30px); }
  to { opacity: 1; transform: translateX(0); }
}

@keyframes slide-in-right {
  from { opacity: 0; transform: translateX(30px); }
  to { opacity: 1; transform: translateX(0); }
}

@keyframes slide-up-mobile {
  from { opacity: 0; transform: translateY(100%); }
  to { opacity: 1; transform: translateY(0); }
}

/* Utility classes */
.animate-fade-in-up { animation: fade-in-up 0.6s ease-out forwards; opacity: 0; }
.animate-fade-in-down { animation: fade-in-down 0.6s ease-out forwards; opacity: 0; }
.animate-fade-in-scale { animation: fade-in-scale 0.5s ease-out forwards; opacity: 0; }
.animate-slide-in-left { animation: slide-in-left 0.6s ease-out forwards; opacity: 0; }
.animate-slide-in-right { animation: slide-in-right 0.6s ease-out forwards; opacity: 0; }
.animate-slide-up-mobile { animation: slide-up-mobile 0.4s ease-out forwards; }

/* Stagger utilities */
.stagger-1 { animation-delay: 50ms; }
.stagger-2 { animation-delay: 100ms; }
.stagger-3 { animation-delay: 150ms; }
.stagger-4 { animation-delay: 200ms; }
.stagger-5 { animation-delay: 250ms; }
.stagger-6 { animation-delay: 300ms; }
.stagger-7 { animation-delay: 350ms; }
.stagger-8 { animation-delay: 400ms; }

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-delay: 0ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Framer Motion Integration

```typescript
import { motion, AnimatePresence, useScroll, useTransform } from 'framer-motion';

// Spring physics for natural motion
const springTransition = {
  type: "spring",
  stiffness: 300,
  damping: 30,
};

// Mobile-optimized transitions (faster)
const mobileTransition = {
  type: "spring",
  stiffness: 400,
  damping: 35,
};

// Smooth easing for UI elements
const smoothTransition = {
  duration: 0.5,
  ease: [0.22, 1, 0.36, 1],
};

// Stagger children animation
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: smoothTransition,
  },
};
```

### Scroll-Driven Animations

```typescript
const useScrollReveal = (threshold = 0.1) => {
  const ref = useRef(null);
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

const RevealOnScroll = ({ children, direction = 'up' }) => {
  const { ref, isVisible } = useScrollReveal();
  const prefersReduced = usePrefersReducedMotion();

  const variants = {
    up: { y: prefersReduced ? 0 : 40 },
    down: { y: prefersReduced ? 0 : -40 },
    left: { x: prefersReduced ? 0 : 40 },
    right: { x: prefersReduced ? 0 : -40 },
  };

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, ...variants[direction] }}
      animate={isVisible ? { opacity: 1, y: 0, x: 0 } : {}}
      transition={{ duration: prefersReduced ? 0 : 0.6, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  );
};
```

### Micro-Interactions

```typescript
// Button press effect with haptics
const PressableButton = ({ children, onPress, ...props }) => {
  const haptic = useHaptic();

  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: "spring", stiffness: 400, damping: 17 }}
      onClick={(e) => {
        haptic.light();
        onPress?.(e);
      }}
      {...props}
    >
      {children}
    </motion.button>
  );
};

// Hover tilt effect (3D) - Desktop only
const TiltCard = ({ children, disabled = false }) => {
  const [rotateX, setRotateX] = useState(0);
  const [rotateY, setRotateY] = useState(0);
  const { isMobile } = useBreakpoint();

  // Disable on mobile for performance
  if (isMobile || disabled) return <div>{children}</div>;

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    setRotateX(-y * 10);
    setRotateY(x * 10);
  };

  return (
    <motion.div
      onMouseMove={handleMouseMove}
      onMouseLeave={() => { setRotateX(0); setRotateY(0); }}
      animate={{ rotateX, rotateY }}
      style={{ transformStyle: "preserve-3d" }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
    >
      {children}
    </motion.div>
  );
};
```

---

## Premium Component Recipes

### Mobile Photo Card with Actions

```typescript
const MobilePhotoCard = ({ photo, onSelect, onLongPress }) => {
  const haptic = useHaptic();
  const { handlers: longPressHandlers, isPressed } = useLongPress(() => {
    haptic.heavy();
    onLongPress?.(photo);
  });

  return (
    <motion.div
      {...longPressHandlers}
      whileTap={{ scale: 0.98 }}
      className={cn(
        "relative overflow-hidden rounded-xl bg-warm-900",
        "active:ring-2 active:ring-accent-500/50",
        isPressed && "ring-2 ring-accent-500"
      )}
      onClick={() => {
        haptic.light();
        onSelect?.(photo);
      }}
    >
      <ProgressiveImage
        src={photo.url}
        placeholder={photo.thumbnail}
        alt={photo.title}
        aspectRatio="1/1"
      />

      {/* Selection overlay */}
      {photo.isSelected && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="absolute inset-0 bg-accent-500/30 flex items-center justify-center"
        >
          <div className="w-8 h-8 rounded-full bg-accent-500 flex items-center justify-center">
            <Check className="w-5 h-5 text-white" />
          </div>
        </motion.div>
      )}

      {/* Favorite indicator */}
      {photo.isFavorite && (
        <div className="absolute top-2 right-2">
          <Heart className="w-5 h-5 text-rose-500 fill-rose-500" />
        </div>
      )}
    </motion.div>
  );
};
```

### Futuristic Stats Dashboard

```typescript
const FuturisticDashboard = ({ stats }) => (
  <div className="p-4 space-y-6">
    {/* Hero stat with neon glow */}
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={cn(
        "relative p-6 rounded-2xl overflow-hidden",
        "bg-gradient-to-br from-accent-500/20 to-primary-500/10",
        "border border-accent-500/30",
        "shadow-[0_0_40px_rgba(59,130,246,0.2)]"
      )}
    >
      <ParticleField count={20} color="accent" />
      <div className="relative">
        <p className="text-sm text-white/60 mb-1">Total Photos</p>
        <AnimatedCounter value={stats.totalPhotos} className="text-5xl font-bold text-white" />
        <p className="text-sm text-emerald-400 mt-2 flex items-center gap-1">
          <TrendingUp className="w-4 h-4" />
          +{stats.photosThisMonth} this month
        </p>
      </div>
    </motion.div>

    {/* Stats grid */}
    <div className="grid grid-cols-2 gap-3">
      {[
        { label: 'Albums', value: stats.albums, icon: FolderOpen, color: 'primary' },
        { label: 'Shared', value: stats.shared, icon: Share2, color: 'accent' },
        { label: 'Storage', value: `${stats.storageUsed}GB`, icon: HardDrive, color: 'warning' },
        { label: 'Views', value: stats.views, icon: Eye, color: 'success' },
      ].map((stat, i) => (
        <motion.div
          key={stat.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1 }}
          className="p-4 rounded-xl bg-warm-800/50 border border-warm-700/50"
        >
          <stat.icon className={cn(
            "w-5 h-5 mb-2",
            stat.color === 'primary' && "text-primary-400",
            stat.color === 'accent' && "text-accent-400",
            stat.color === 'warning' && "text-amber-400",
            stat.color === 'success' && "text-emerald-400"
          )} />
          <p className="text-2xl font-bold text-white">{stat.value}</p>
          <p className="text-xs text-warm-400">{stat.label}</p>
        </motion.div>
      ))}
    </div>
  </div>
);

// Animated counter component
const AnimatedCounter = ({ value, className }) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const duration = 1500;
    const steps = 60;
    const increment = value / steps;
    let current = 0;

    const timer = setInterval(() => {
      current += increment;
      if (current >= value) {
        setCount(value);
        clearInterval(timer);
      } else {
        setCount(Math.floor(current));
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [value]);

  return <span className={className}>{count.toLocaleString()}</span>;
};
```

### Aurora Background (Mobile-Optimized)

```typescript
const AuroraBackground = ({ intensity = 'normal' }) => {
  const { isLowPower } = useDeviceCapabilities();

  // Simplified version for low-power devices
  if (isLowPower) {
    return (
      <div className="fixed inset-0 -z-10 bg-gradient-to-br from-warm-950 via-warm-900 to-warm-950" />
    );
  }

  return (
    <div className="fixed inset-0 -z-10 overflow-hidden">
      <div className={cn(
        "absolute -top-1/2 -left-1/2 w-[200%] h-[200%]",
        intensity === 'subtle' ? "animate-aurora-slow opacity-50" : "animate-aurora"
      )}>
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-accent-500/30 rounded-full blur-[128px]" />
        <div className="absolute top-1/2 right-1/4 w-80 h-80 bg-primary-600/30 rounded-full blur-[128px]" />
        <div className="absolute bottom-1/4 left-1/2 w-64 h-64 bg-purple-500/20 rounded-full blur-[100px]" />
      </div>
    </div>
  );
};
```

---

## Accessibility Requirements

### Touch Targets (44x44px minimum)

```typescript
// Icon button with adequate touch target
const TouchableIconButton = ({ icon: Icon, label, size = 'md', ...props }) => {
  const sizes = {
    sm: 'min-w-[44px] min-h-[44px] p-2',
    md: 'min-w-[48px] min-h-[48px] p-3',
    lg: 'min-w-[56px] min-h-[56px] p-4',
  };

  return (
    <button
      aria-label={label}
      className={cn(
        sizes[size],
        "rounded-xl flex items-center justify-center",
        "bg-warm-800 hover:bg-warm-700 active:bg-warm-600",
        "transition-colors",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500"
      )}
      {...props}
    >
      <Icon className="w-6 h-6 text-white" aria-hidden="true" />
    </button>
  );
};
```

### Reduced Motion Support

```typescript
const usePrefersReducedMotion = () => {
  const [prefersReduced, setPrefersReduced] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setPrefersReduced(mediaQuery.matches);

    const handler = (e) => setPrefersReduced(e.matches);
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, []);

  return prefersReduced;
};

// Motion-safe wrapper
const MotionSafe = ({ children, animation }) => {
  const prefersReduced = usePrefersReducedMotion();

  if (prefersReduced) {
    return <div>{children}</div>;
  }

  return (
    <motion.div {...animation}>
      {children}
    </motion.div>
  );
};
```

---

## Anti-Patterns (NEVER Do)

| Problem | Fix |
|---------|-----|
| Touch targets < 44px | Use min-w-[44px] min-h-[44px] |
| No safe area handling | Use env(safe-area-inset-*) |
| Heavy effects on mobile | Use useDeviceCapabilities() to adapt |
| Ignoring reduced motion | Always check prefers-reduced-motion |
| No haptic feedback | Add navigator.vibrate() for native feel |
| Fixed viewports | Use 100dvh instead of 100vh |
| No gesture support | Implement swipe, pinch, long-press |
| Loading entire lists | Use virtual scrolling |
| Full-res images always | Use progressive loading |
| Same effects everywhere | Adapt to device capabilities |

---

## Execution Checklist

### Mobile-First
- [ ] **Touch targets**: All interactive elements 44x44px minimum?
- [ ] **Safe areas**: Respecting notch, home indicator, rounded corners?
- [ ] **Gestures**: Swipe, pull-to-refresh, long-press implemented?
- [ ] **Haptics**: Tactile feedback on key interactions?
- [ ] **Performance**: Effects reduced on low-power devices?
- [ ] **Virtual scroll**: Large lists virtualized?

### Futuristic Design
- [ ] **Bold effects**: Neon glows, particles, morphing backgrounds?
- [ ] **Glassmorphism**: Used strategically with proper opacity?
- [ ] **Animations**: Smooth, purposeful, GPU-accelerated?
- [ ] **Visual hierarchy**: Clear focus, dramatic contrast?

### Accessibility
- [ ] **Reduced motion**: Animations disabled when preferred?
- [ ] **Color contrast**: 4.5:1 for text, 3:1 for UI?
- [ ] **Focus visible**: Clear indicators on all interactive elements?
- [ ] **Screen reader**: Proper ARIA labels and landmarks?

### Performance
- [ ] **Lazy loading**: Images and effects load on demand?
- [ ] **Skeleton states**: Immediate visual feedback?
- [ ] **Adaptive quality**: Effects scale with device capability?
- [ ] **60fps**: Animations smooth on target devices?

---

## Creative Philosophy

Every interface should feel like it belongs in a design portfolio. Not safe. Not generic. **Exceptional.**

**Mobile-first is not mobile-only.** Start with the constraints of mobile, then progressively enhance. The best mobile experiences feel native, not like shrunken desktop sites.

**Futuristic means intentional.** Neon glows, glass effects, and particles should serve the experience, not distract from it. Every effect should have a purpose.

**Performance is design.** A beautiful interface that stutters is not beautiful. Adapt to device capabilities, respect user preferences, and optimize relentlessly.

Remember: Claude is capable of extraordinary creative work. Don't hold back.

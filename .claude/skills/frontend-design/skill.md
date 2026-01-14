---
name: frontend-design
aliases: [ui-design, frontend, react-components, pages, premium-ui, cinematic, landing-page, glassmorphism]
description: Create distinctive, production-grade frontend interfaces with high design quality for vDrive. Use this skill when the user asks to build web components, pages, or applications. Generates creative, polished code that avoids generic AI aesthetics while leveraging vDrive's design system.
---

# vDrive Frontend Design Skill

Create **distinctive, production-grade, futuristic** frontend interfaces that avoid generic "AI slop" aesthetics. vDrive is a **premium photography SaaS platform**. Every interface should feel:

- **Cinematic** - Like a high-end photo editing suite
- **Premium** - Luxury brand quality for professional photographers
- **Memorable** - Distinctive enough to be recognized instantly

> **For brand colors, tokens, and component APIs**: See the `design-system` skill.

---

## Design Thinking Process

Before coding, commit to a **BOLD** aesthetic direction:

### Aesthetic Directions

| Direction | Characteristics | Best For |
|-----------|----------------|----------|
| **Cinematic Dark** | Deep blacks, dramatic lighting, film grain | Gallery views, photo editing |
| **Premium Editorial** | Generous whitespace, serif headlines, magazine layout | Portfolio, landing pages |
| **Futuristic Glass** | Glassmorphism, aurora gradients, floating elements | Dashboards, AI features |
| **Neo-Retro** | Film camera aesthetics, vintage color grades | Photography features |

**CRITICAL**: Choose a clear direction and execute with precision. Ask: "What's the ONE thing someone will remember?"

---

## Glassmorphism Toolkit

Glassmorphism creates depth through translucent layers. Use it intentionally for premium feel.

### Core Glass Styles

```typescript
// Standard frosted glass
const GlassCard = ({ children, className }) => (
  <div className={cn(
    "bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl",
    "shadow-[0_8px_32px_rgba(0,0,0,0.12)]",
    className
  )}>
    {children}
  </div>
);

// Dark mode glass (for light backgrounds)
const GlassDark = ({ children }) => (
  <div className="bg-slate-900/70 backdrop-blur-xl border border-slate-700/50 rounded-2xl">
    {children}
  </div>
);
```

### Multi-Layer Glass (Advanced Depth)

```typescript
// Creates illusion of floating above surface
const FloatingGlassPanel = () => (
  <div className="relative">
    {/* Background blur layer */}
    <div className="absolute inset-0 bg-white/5 backdrop-blur-3xl rounded-3xl" />
    {/* Mid layer with subtle border */}
    <div className="absolute inset-2 bg-white/10 backdrop-blur-xl rounded-2xl border border-white/10" />
    {/* Content layer */}
    <div className="relative p-6 bg-white/5 backdrop-blur-md rounded-xl border border-white/20">
      {/* Your content */}
    </div>
  </div>
);
```

### Tinted Glass Variations

```typescript
// Brand-tinted glass (use sparingly for accents)
const tintedGlassStyles = {
  accent: "bg-accent-500/10 backdrop-blur-xl border border-accent-400/20",
  gold: "bg-gold-500/10 backdrop-blur-xl border border-gold-400/20",
  success: "bg-emerald-500/10 backdrop-blur-xl border border-emerald-400/20",
  danger: "bg-rose-500/10 backdrop-blur-xl border border-rose-400/20",
};
```

### Glass with Noise Texture

```typescript
// Add subtle grain for realism (requires noise.svg in assets)
const GlassWithGrain = () => (
  <div className="relative bg-white/10 backdrop-blur-xl rounded-2xl overflow-hidden">
    {/* Noise overlay */}
    <div
      className="absolute inset-0 opacity-[0.03] mix-blend-overlay pointer-events-none"
      style={{ backgroundImage: "url('/assets/noise.svg')" }}
    />
    {/* Content */}
    <div className="relative p-6">{/* ... */}</div>
  </div>
);

// CSS-only grain alternative
const grainOverlay = `
  before:absolute before:inset-0 before:opacity-[0.015]
  before:bg-[url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")]
  before:pointer-events-none before:rounded-inherit
`;
```

### Glass Borders & Glows

```typescript
// Gradient border glow
const GlassBorderGlow = () => (
  <div className="relative p-[1px] rounded-2xl bg-gradient-to-br from-white/30 via-white/10 to-transparent">
    <div className="bg-slate-900/80 backdrop-blur-xl rounded-2xl p-6">
      {/* Content */}
    </div>
  </div>
);

// Inner light effect (top edge highlight)
const innerLightStyles = `
  before:absolute before:inset-x-0 before:top-0 before:h-px
  before:bg-gradient-to-r before:from-transparent before:via-white/30 before:to-transparent
`;

// Outer glow on hover
const glowOnHover = `
  hover:shadow-[0_0_30px_rgba(6,182,212,0.3)]
  transition-shadow duration-500
`;
```

### Responsive Glassmorphism

```typescript
// Reduce blur on mobile for performance
const ResponsiveGlass = () => (
  <div className={cn(
    "bg-white/10 border border-white/20 rounded-2xl",
    "backdrop-blur-md md:backdrop-blur-xl", // Less blur on mobile
    "backdrop-saturate-150" // Boost colors through blur
  )}>
    {/* Content */}
  </div>
);
```

---

## Advanced Animation System

### Framer Motion Integration

```typescript
import { motion, AnimatePresence, useScroll, useTransform } from 'framer-motion';

// Spring physics for natural motion
const springTransition = {
  type: "spring",
  stiffness: 300,
  damping: 30,
};

// Smooth easing for UI elements
const smoothTransition = {
  duration: 0.5,
  ease: [0.22, 1, 0.36, 1], // Custom cubic-bezier
};

// Stagger children animation
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
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

// Usage
const StaggeredList = ({ items }) => (
  <motion.div
    variants={containerVariants}
    initial="hidden"
    animate="visible"
  >
    {items.map((item) => (
      <motion.div key={item.id} variants={itemVariants}>
        {item.content}
      </motion.div>
    ))}
  </motion.div>
);
```

### Scroll-Driven Animations

```typescript
// Parallax effect
const ParallaxSection = () => {
  const { scrollYProgress } = useScroll();
  const y = useTransform(scrollYProgress, [0, 1], [0, -200]);
  const opacity = useTransform(scrollYProgress, [0, 0.5, 1], [1, 0.8, 0]);

  return (
    <motion.div style={{ y, opacity }}>
      {/* Content moves up as you scroll */}
    </motion.div>
  );
};

// Scroll reveal with intersection observer
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

// Usage
const RevealOnScroll = ({ children }) => {
  const { ref, isVisible } = useScrollReveal();

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={isVisible ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  );
};
```

### Page Transitions

```typescript
// Wrap pages in AnimatePresence
const PageTransition = ({ children }) => (
  <motion.div
    initial={{ opacity: 0, x: 20 }}
    animate={{ opacity: 1, x: 0 }}
    exit={{ opacity: 0, x: -20 }}
    transition={{ duration: 0.3 }}
  >
    {children}
  </motion.div>
);

// Shared layout animations (morphing between states)
const ExpandableCard = ({ isExpanded, children }) => (
  <motion.div
    layout
    layoutId="expandable-card"
    transition={springTransition}
    className={cn(
      "bg-surface rounded-2xl overflow-hidden",
      isExpanded ? "fixed inset-4 z-50" : "relative"
    )}
  >
    {children}
  </motion.div>
);
```

### Loading States & Skeletons

```typescript
// Shimmer skeleton
const SkeletonShimmer = ({ className }) => (
  <div className={cn(
    "relative overflow-hidden bg-slate-200 dark:bg-slate-800 rounded-lg",
    className
  )}>
    <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/20 to-transparent" />
  </div>
);

// Add to tailwind.config.js:
// animation: { shimmer: 'shimmer 2s infinite' }
// keyframes: { shimmer: { '100%': { transform: 'translateX(100%)' } } }

// Pulse skeleton alternative
const SkeletonPulse = ({ className }) => (
  <div className={cn(
    "animate-pulse bg-slate-200 dark:bg-slate-800 rounded-lg",
    className
  )} />
);

// Content skeleton pattern
const PhotoCardSkeleton = () => (
  <div className="space-y-3">
    <SkeletonShimmer className="aspect-[4/3] rounded-xl" />
    <SkeletonShimmer className="h-4 w-3/4" />
    <SkeletonShimmer className="h-3 w-1/2" />
  </div>
);
```

### Micro-Interactions

```typescript
// Button press effect
const PressableButton = ({ children, ...props }) => (
  <motion.button
    whileHover={{ scale: 1.02 }}
    whileTap={{ scale: 0.98 }}
    transition={{ type: "spring", stiffness: 400, damping: 17 }}
    {...props}
  >
    {children}
  </motion.button>
);

// Hover tilt effect (3D)
const TiltCard = ({ children }) => {
  const [rotateX, setRotateX] = useState(0);
  const [rotateY, setRotateY] = useState(0);

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
      className="relative"
    >
      {children}
    </motion.div>
  );
};

// Magnetic button (follows cursor)
const MagneticButton = ({ children }) => {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const ref = useRef(null);

  const handleMouseMove = (e) => {
    const rect = ref.current?.getBoundingClientRect();
    if (!rect) return;
    const x = (e.clientX - rect.left - rect.width / 2) * 0.3;
    const y = (e.clientY - rect.top - rect.height / 2) * 0.3;
    setPosition({ x, y });
  };

  return (
    <motion.button
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setPosition({ x: 0, y: 0 })}
      animate={position}
      transition={{ type: "spring", stiffness: 150, damping: 15 }}
    >
      {children}
    </motion.button>
  );
};
```

---

## Depth System

### Elevation Tokens

```typescript
// Consistent elevation scale
const elevation = {
  flat: "shadow-none",
  raised: "shadow-sm",
  card: "shadow-md shadow-black/5",
  dropdown: "shadow-lg shadow-black/10",
  modal: "shadow-xl shadow-black/15",
  floating: "shadow-2xl shadow-black/20",
};

// Premium dramatic shadows
const dramaticShadows = {
  soft: "shadow-[0_20px_60px_-15px_rgba(0,0,0,0.25)]",
  medium: "shadow-[0_25px_80px_-20px_rgba(0,0,0,0.35)]",
  heavy: "shadow-[0_35px_100px_-25px_rgba(0,0,0,0.45)]",
};

// Colored shadow (matches element color)
const coloredShadow = (color) => `shadow-[0_20px_50px_-12px_${color}]`;
// Usage: coloredShadow('rgba(6,182,212,0.4)') for accent glow
```

### Floating Elements

```typescript
// Floating action panel
const FloatingPanel = ({ children, position = "bottom-right" }) => {
  const positions = {
    "bottom-right": "fixed bottom-6 right-6",
    "bottom-center": "fixed bottom-6 left-1/2 -translate-x-1/2",
    "top-center": "fixed top-6 left-1/2 -translate-x-1/2",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 20, scale: 0.95 }}
      className={cn(
        positions[position],
        "z-50 bg-white/10 backdrop-blur-xl border border-white/20",
        "rounded-2xl p-4 shadow-2xl shadow-black/20"
      )}
    >
      {children}
    </motion.div>
  );
};
```

### Parallax Layers

```typescript
// Multi-speed parallax background
const ParallaxBackground = () => {
  const { scrollY } = useScroll();
  const y1 = useTransform(scrollY, [0, 1000], [0, -100]);
  const y2 = useTransform(scrollY, [0, 1000], [0, -200]);
  const y3 = useTransform(scrollY, [0, 1000], [0, -300]);

  return (
    <div className="fixed inset-0 -z-10 overflow-hidden">
      {/* Slowest layer */}
      <motion.div style={{ y: y1 }} className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-accent-500/20 rounded-full blur-[128px]" />
      </motion.div>
      {/* Medium layer */}
      <motion.div style={{ y: y2 }} className="absolute inset-0">
        <div className="absolute top-1/2 right-1/4 w-80 h-80 bg-primary-600/20 rounded-full blur-[100px]" />
      </motion.div>
      {/* Fastest layer */}
      <motion.div style={{ y: y3 }} className="absolute inset-0">
        <div className="absolute bottom-1/4 left-1/2 w-64 h-64 bg-gold-500/15 rounded-full blur-[80px]" />
      </motion.div>
    </div>
  );
};
```

### 3D Perspective Effects

```typescript
// Perspective container for 3D children
const PerspectiveContainer = ({ children }) => (
  <div style={{ perspective: "1000px" }} className="relative">
    {children}
  </div>
);

// Card flip animation
const FlipCard = ({ front, back, isFlipped }) => (
  <div style={{ perspective: "1000px" }} className="relative w-full h-full">
    <motion.div
      animate={{ rotateY: isFlipped ? 180 : 0 }}
      transition={{ duration: 0.6, ease: "easeInOut" }}
      style={{ transformStyle: "preserve-3d" }}
      className="relative w-full h-full"
    >
      {/* Front */}
      <div className="absolute inset-0 backface-hidden">{front}</div>
      {/* Back */}
      <div
        className="absolute inset-0 backface-hidden"
        style={{ transform: "rotateY(180deg)" }}
      >
        {back}
      </div>
    </motion.div>
  </div>
);
```

---

## Premium Form Patterns

### Floating Label Input

```typescript
const FloatingLabelInput = ({ label, type = "text", error, ...props }) => {
  const [isFocused, setIsFocused] = useState(false);
  const [hasValue, setHasValue] = useState(false);

  return (
    <div className="relative">
      <input
        type={type}
        className={cn(
          "peer w-full px-4 pt-6 pb-2 rounded-xl border bg-transparent",
          "transition-all duration-200 outline-none",
          "border-slate-200 dark:border-slate-700",
          "focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20",
          error && "border-rose-500 focus:border-rose-500 focus:ring-rose-500/20"
        )}
        placeholder=" "
        onFocus={() => setIsFocused(true)}
        onBlur={(e) => {
          setIsFocused(false);
          setHasValue(!!e.target.value);
        }}
        {...props}
      />
      <label
        className={cn(
          "absolute left-4 transition-all duration-200 pointer-events-none",
          "text-slate-500 dark:text-slate-400",
          "peer-placeholder-shown:top-4 peer-placeholder-shown:text-base",
          "peer-focus:top-2 peer-focus:text-xs peer-focus:text-accent-500",
          (hasValue || isFocused) && "top-2 text-xs"
        )}
      >
        {label}
      </label>
      {error && (
        <p className="mt-1 text-sm text-rose-500">{error}</p>
      )}
    </div>
  );
};
```

### Glass Input

```typescript
const GlassInput = ({ icon: Icon, ...props }) => (
  <div className="relative">
    {Icon && (
      <Icon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/50" />
    )}
    <input
      className={cn(
        "w-full bg-white/10 backdrop-blur-xl",
        "border border-white/20 rounded-xl",
        "px-4 py-3 text-white placeholder-white/40",
        "focus:outline-none focus:border-white/40 focus:bg-white/15",
        "transition-all duration-200",
        Icon && "pl-12"
      )}
      {...props}
    />
  </div>
);
```

### Validation States

```typescript
const ValidatedInput = ({ isValid, isInvalid, ...props }) => (
  <div className="relative">
    <input
      className={cn(
        "w-full px-4 py-3 rounded-xl border-2 transition-all duration-200",
        "focus:outline-none",
        isValid && "border-emerald-500 bg-emerald-500/5 focus:ring-emerald-500/20",
        isInvalid && "border-rose-500 bg-rose-500/5 focus:ring-rose-500/20",
        !isValid && !isInvalid && "border-slate-200 focus:border-accent-500"
      )}
      {...props}
    />
    {/* Animated checkmark */}
    {isValid && (
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        className="absolute right-4 top-1/2 -translate-y-1/2"
      >
        <CheckCircle className="w-5 h-5 text-emerald-500" />
      </motion.div>
    )}
  </div>
);
```

### Multi-Step Form Progress

```typescript
const StepIndicator = ({ steps, currentStep }) => (
  <div className="flex items-center justify-center gap-2">
    {steps.map((step, index) => (
      <React.Fragment key={step.id}>
        {/* Step circle */}
        <motion.div
          animate={{
            scale: index === currentStep ? 1.1 : 1,
            backgroundColor: index <= currentStep ? "var(--color-accent)" : "transparent",
          }}
          className={cn(
            "w-10 h-10 rounded-full flex items-center justify-center",
            "border-2 transition-colors",
            index <= currentStep ? "border-accent-500" : "border-slate-300"
          )}
        >
          {index < currentStep ? (
            <Check className="w-5 h-5 text-white" />
          ) : (
            <span className={index <= currentStep ? "text-white" : "text-slate-400"}>
              {index + 1}
            </span>
          )}
        </motion.div>
        {/* Connector line */}
        {index < steps.length - 1 && (
          <div className="w-12 h-0.5 bg-slate-200 relative overflow-hidden">
            <motion.div
              initial={{ scaleX: 0 }}
              animate={{ scaleX: index < currentStep ? 1 : 0 }}
              className="absolute inset-0 bg-accent-500 origin-left"
            />
          </div>
        )}
      </React.Fragment>
    ))}
  </div>
);
```

---

## Data Visualization Patterns

### Animated Stat Card

```typescript
const AnimatedStatCard = ({ label, value, prefix = "", suffix = "", trend }) => {
  const [count, setCount] = useState(0);
  const { ref, isVisible } = useScrollReveal();

  useEffect(() => {
    if (!isVisible) return;
    const duration = 2000;
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
  }, [isVisible, value]);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={isVisible ? { opacity: 1, y: 0 } : {}}
      className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20"
    >
      <p className="text-sm text-white/60 mb-2">{label}</p>
      <p className="text-4xl font-bold text-white">
        {prefix}{count.toLocaleString()}{suffix}
      </p>
      {trend && (
        <div className={cn(
          "flex items-center gap-1 mt-2 text-sm",
          trend > 0 ? "text-emerald-400" : "text-rose-400"
        )}>
          {trend > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
          <span>{Math.abs(trend)}%</span>
        </div>
      )}
    </motion.div>
  );
};
```

### Gradient Progress Ring

```typescript
const ProgressRing = ({ progress, size = 120, strokeWidth = 8 }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (progress / 100) * circumference;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg className="transform -rotate-90" width={size} height={size}>
        {/* Background ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="none"
          className="text-slate-200 dark:text-slate-800"
        />
        {/* Progress ring with gradient */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="url(#progress-gradient)"
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-1000 ease-out"
        />
        <defs>
          <linearGradient id="progress-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="var(--color-accent)" />
            <stop offset="100%" stopColor="var(--color-primary)" />
          </linearGradient>
        </defs>
      </svg>
      {/* Center content */}
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-2xl font-bold">{progress}%</span>
      </div>
    </div>
  );
};
```

### Premium Empty State

```typescript
const EmptyState = ({ icon: Icon, title, description, action }) => (
  <motion.div
    initial={{ opacity: 0, scale: 0.95 }}
    animate={{ opacity: 1, scale: 1 }}
    className="flex flex-col items-center justify-center py-16 px-8 text-center"
  >
    {/* Gradient icon background */}
    <div className="relative mb-6">
      <div className="absolute inset-0 bg-gradient-to-br from-accent-500/30 to-primary-600/30 rounded-full blur-2xl" />
      <div className="relative w-20 h-20 rounded-full bg-white/10 backdrop-blur-xl border border-white/20 flex items-center justify-center">
        <Icon className="w-10 h-10 text-white/60" />
      </div>
    </div>
    <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
    <p className="text-white/60 max-w-sm mb-6">{description}</p>
    {action && (
      <AppButton variant="accent" className="shadow-accent-glow">
        {action.icon && <action.icon className="w-4 h-4 mr-2" />}
        {action.label}
      </AppButton>
    )}
  </motion.div>
);
```

---

## Premium Component Recipes

### Glass Navigation Bar

```typescript
const GlassNavbar = ({ onScrolled = false }) => {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className={cn(
        "fixed top-0 inset-x-0 z-50 transition-all duration-300",
        scrolled
          ? "bg-white/10 backdrop-blur-xl border-b border-white/10 shadow-lg"
          : "bg-transparent"
      )}
    >
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <a href="/" className="font-serif text-xl text-white font-bold">
          vDrive
        </a>
        {/* Nav links */}
        <div className="hidden md:flex items-center gap-8">
          {["Features", "Pricing", "Gallery"].map((item) => (
            <a
              key={item}
              href={`#${item.toLowerCase()}`}
              className="text-white/70 hover:text-white transition-colors relative group"
            >
              {item}
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-accent-500 group-hover:w-full transition-all duration-300" />
            </a>
          ))}
        </div>
        {/* CTA */}
        <AppButton variant="accent" size="sm" className="hidden md:flex">
          Get Started
        </AppButton>
      </div>
    </motion.nav>
  );
};
```

### Bento Grid Layout

```typescript
const BentoGrid = ({ items }) => (
  <div className="grid grid-cols-4 gap-4 md:grid-rows-3">
    {items.map((item, index) => {
      // Define different spans for visual interest
      const spans = [
        "col-span-2 row-span-2", // Large featured
        "col-span-2 row-span-1", // Wide
        "col-span-1 row-span-1", // Small
        "col-span-1 row-span-1", // Small
        "col-span-2 row-span-1", // Wide
        "col-span-2 row-span-1", // Wide
      ];

      return (
        <motion.div
          key={item.id}
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: index * 0.1 }}
          className={cn(
            spans[index % spans.length],
            "group relative overflow-hidden rounded-2xl",
            "bg-white/5 backdrop-blur-xl border border-white/10",
            "hover:border-white/20 transition-all duration-300"
          )}
        >
          {item.image && (
            <img
              src={item.image}
              alt={item.title}
              className="absolute inset-0 w-full h-full object-cover opacity-50 group-hover:opacity-70 group-hover:scale-105 transition-all duration-700"
            />
          )}
          <div className="relative p-6 h-full flex flex-col justify-end">
            <h3 className="font-semibold text-white text-lg">{item.title}</h3>
            <p className="text-white/60 text-sm mt-1">{item.description}</p>
          </div>
        </motion.div>
      );
    })}
  </div>
);
```

### Pricing Table with Highlight

```typescript
const PricingCard = ({ plan, isPopular }) => (
  <motion.div
    whileHover={{ y: -8 }}
    className={cn(
      "relative rounded-3xl p-8 transition-all duration-300",
      isPopular
        ? "bg-gradient-to-b from-accent-500/20 to-transparent border-2 border-accent-500/50 shadow-[0_0_60px_rgba(6,182,212,0.3)]"
        : "bg-white/5 border border-white/10"
    )}
  >
    {/* Popular badge */}
    {isPopular && (
      <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-accent-500 text-white text-sm font-medium rounded-full">
        Most Popular
      </div>
    )}

    <h3 className="text-xl font-semibold text-white">{plan.name}</h3>
    <p className="text-white/60 mt-2">{plan.description}</p>

    {/* Price */}
    <div className="mt-6 mb-8">
      <span className="text-5xl font-bold text-white">${plan.price}</span>
      <span className="text-white/60">/month</span>
    </div>

    {/* Features */}
    <ul className="space-y-3 mb-8">
      {plan.features.map((feature, i) => (
        <li key={i} className="flex items-center gap-3 text-white/80">
          <Check className="w-5 h-5 text-accent-500" />
          {feature}
        </li>
      ))}
    </ul>

    <AppButton
      variant={isPopular ? "accent" : "outline"}
      className={cn("w-full", isPopular && "shadow-accent-glow")}
    >
      Get Started
    </AppButton>
  </motion.div>
);
```

### Testimonial Carousel

```typescript
const TestimonialCarousel = ({ testimonials }) => {
  const [current, setCurrent] = useState(0);

  return (
    <div className="relative max-w-4xl mx-auto">
      <AnimatePresence mode="wait">
        <motion.div
          key={current}
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -50 }}
          transition={{ duration: 0.5 }}
          className="bg-white/5 backdrop-blur-xl rounded-3xl p-8 md:p-12 border border-white/10"
        >
          {/* Quote */}
          <blockquote className="text-xl md:text-2xl text-white/90 font-light leading-relaxed">
            "{testimonials[current].quote}"
          </blockquote>

          {/* Author */}
          <div className="flex items-center gap-4 mt-8">
            <img
              src={testimonials[current].avatar}
              alt={testimonials[current].name}
              className="w-12 h-12 rounded-full object-cover"
            />
            <div>
              <p className="text-white font-medium">{testimonials[current].name}</p>
              <p className="text-white/60 text-sm">{testimonials[current].role}</p>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>

      {/* Navigation dots */}
      <div className="flex justify-center gap-2 mt-6">
        {testimonials.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrent(index)}
            className={cn(
              "w-2 h-2 rounded-full transition-all duration-300",
              index === current ? "w-8 bg-accent-500" : "bg-white/30"
            )}
          />
        ))}
      </div>
    </div>
  );
};
```

---

## Aurora Backgrounds

```typescript
const AuroraBackground = () => (
  <div className="fixed inset-0 -z-10 overflow-hidden">
    <div className="absolute -top-1/2 -left-1/2 w-[200%] h-[200%] animate-aurora-slow">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-accent-500/30 rounded-full blur-[128px]" />
      <div className="absolute top-1/2 right-1/4 w-80 h-80 bg-primary-600/30 rounded-full blur-[128px]" />
    </div>
  </div>
);
```

---

## Dramatic Shadows & Glows

```typescript
// Floating Card with lift effect
className="shadow-[0_20px_60px_-10px_rgba(0,0,0,0.3)] hover:shadow-[0_30px_80px_-10px_rgba(0,0,0,0.4)] hover:-translate-y-1 transition-all duration-500"

// Glowing border (use brand colors from design-system)
className="before:absolute before:inset-0 before:rounded-2xl before:p-[1px] before:bg-gradient-to-br before:from-accent-500 before:to-primary-600 before:-z-10 before:opacity-50 before:blur-sm"

// Accent glow
className="shadow-[0_0_40px_rgba(6,182,212,0.4)]"
```

---

## Premium Photo Card

```typescript
const PremiumPhotoCard = ({ photo, onSelect }) => (
  <div className="group relative overflow-hidden rounded-2xl bg-neutral-900">
    <img
      src={photo.thumbnailUrl}
      alt={photo.title}
      className="w-full aspect-[4/3] object-cover transition-transform duration-700 group-hover:scale-105"
      loading="lazy"
    />
    {/* Gradient overlay on hover */}
    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
    {/* Slide-up content */}
    <div className="absolute inset-x-0 bottom-0 p-4 transform translate-y-full group-hover:translate-y-0 transition-transform duration-500">
      <h3 className="font-serif text-lg text-white truncate">{photo.title}</h3>
    </div>
  </div>
);
```

---

## AI Feature Hero

```typescript
const AIFeatureHero = () => (
  <section className="relative min-h-[80vh] flex items-center overflow-hidden">
    <AuroraBackground />
    <div className="max-w-7xl mx-auto px-6 py-20">
      {/* Premium badge */}
      <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-8">
        <Sparkles className="w-4 h-4 text-gold-500 animate-pulse-glow" />
        <span className="text-sm font-medium text-white/80">AI-Powered</span>
      </div>
      {/* Headline with gradient */}
      <h1 className="text-5xl md:text-7xl font-serif font-bold text-white animate-fade-in-up">
        Your Photos,{' '}
        <span className="bg-gradient-to-r from-accent-400 to-primary-500 bg-clip-text text-transparent">
          Intelligently Curated
        </span>
      </h1>
      <div className="flex gap-4 mt-10 animate-fade-in-up animation-delay-200">
        <AppButton variant="accent" size="lg" className="shadow-accent-glow">
          <Sparkles className="w-5 h-5 mr-2" /> Try AI Features
        </AppButton>
      </div>
    </div>
  </section>
);
```

---

## Performance Guidelines

### GPU-Accelerated Properties

```typescript
// PREFER: These properties are GPU-accelerated
const optimizedTransitions = `
  transform  // translate, scale, rotate
  opacity
  filter     // blur, brightness
`;

// AVOID: These cause layout recalculation
const slowProperties = `
  width, height, top, left  // Use transform instead
  margin, padding           // Use transform instead
  border-radius             // Animate sparingly
`;

// Example: Animated expand
// BAD
className="hover:w-[120%] transition-all"
// GOOD
className="hover:scale-110 transition-transform"
```

### Reduced Motion Support

```typescript
// Hook for respecting user preferences
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

// Usage
const AnimatedComponent = () => {
  const prefersReduced = usePrefersReducedMotion();

  return (
    <motion.div
      animate={{ y: prefersReduced ? 0 : [0, -10, 0] }}
      transition={prefersReduced ? { duration: 0 } : { repeat: Infinity }}
    >
      Content
    </motion.div>
  );
};

// CSS alternative
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Conditional Effects

```typescript
// Reduce effects on mobile/low-power devices
const useDeviceCapabilities = () => {
  const [isLowPower, setIsLowPower] = useState(false);

  useEffect(() => {
    // Check for low-power indicators
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    const hasLowMemory = navigator.deviceMemory && navigator.deviceMemory < 4;
    const hasSlowCPU = navigator.hardwareConcurrency && navigator.hardwareConcurrency < 4;

    setIsLowPower(isMobile || hasLowMemory || hasSlowCPU);
  }, []);

  return { isLowPower };
};

// Usage: Reduce glassmorphism on low-power devices
const ResponsiveGlassCard = ({ children }) => {
  const { isLowPower } = useDeviceCapabilities();

  return (
    <div className={cn(
      "rounded-2xl border",
      isLowPower
        ? "bg-slate-900/90 border-slate-700" // Simple fallback
        : "bg-white/10 backdrop-blur-xl border-white/20" // Full effect
    )}>
      {children}
    </div>
  );
};
```

### Lazy Loading Effects

```typescript
// Only apply blur when visible
const LazyGlass = ({ children }) => {
  const { ref, isVisible } = useScrollReveal(0);

  return (
    <div
      ref={ref}
      className={cn(
        "rounded-2xl border border-white/20 transition-all duration-500",
        isVisible ? "bg-white/10 backdrop-blur-xl" : "bg-slate-900/50"
      )}
    >
      {children}
    </div>
  );
};
```

---

## Dark/Light Theme System

### Theme Context & Hook

```typescript
import { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: Theme;
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider = ({ children }: { children: React.ReactNode }) => {
  const [theme, setTheme] = useState<Theme>('system');
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('dark');

  useEffect(() => {
    const root = document.documentElement;
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const updateTheme = () => {
      const resolved = theme === 'system'
        ? (mediaQuery.matches ? 'dark' : 'light')
        : theme;

      setResolvedTheme(resolved);
      root.setAttribute('data-theme', resolved);
      root.classList.remove('light', 'dark');
      root.classList.add(resolved);
    };

    updateTheme();
    mediaQuery.addEventListener('change', updateTheme);
    return () => mediaQuery.removeEventListener('change', updateTheme);
  }, [theme]);

  const toggleTheme = () => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within ThemeProvider');
  return context;
};
```

### CSS Variables for Theming

```css
/* Light theme (default) */
:root,
[data-theme="light"] {
  /* Backgrounds */
  --color-background: #F8FAFC;
  --color-surface: #FFFFFF;
  --color-surface-hover: #F1F5F9;
  --color-surface-elevated: #FFFFFF;

  /* Text - WCAG AA compliant contrast */
  --color-text-primary: #0F172A;      /* 15.3:1 on white */
  --color-text-secondary: #334155;    /* 8.5:1 on white */
  --color-text-tertiary: #64748B;     /* 4.6:1 on white - large text only */
  --color-text-on-accent: #FFFFFF;

  /* Borders */
  --color-border: #E2E8F0;
  --color-border-strong: #CBD5E1;
  --color-border-focus: #2563EB;

  /* Interactive */
  --color-primary: #2563EB;
  --color-primary-hover: #1D4ED8;
  --color-accent: #0891B2;
  --color-accent-hover: #0E7490;

  /* Status */
  --color-success: #059669;
  --color-warning: #D97706;
  --color-error: #DC2626;

  /* Glass effects */
  --glass-bg: rgba(255, 255, 255, 0.8);
  --glass-border: rgba(0, 0, 0, 0.1);
}

/* Dark theme */
[data-theme="dark"] {
  /* Backgrounds */
  --color-background: #030712;
  --color-surface: #0F172A;
  --color-surface-hover: #1E293B;
  --color-surface-elevated: #1E293B;

  /* Text - WCAG AA compliant contrast */
  --color-text-primary: #F8FAFC;      /* 15.3:1 on dark bg */
  --color-text-secondary: #CBD5E1;    /* 9.1:1 on dark bg */
  --color-text-tertiary: #94A3B8;     /* 5.5:1 on dark bg */
  --color-text-on-accent: #FFFFFF;

  /* Borders */
  --color-border: #1E293B;
  --color-border-strong: #334155;
  --color-border-focus: #3B82F6;

  /* Interactive */
  --color-primary: #3B82F6;
  --color-primary-hover: #2563EB;
  --color-accent: #06B6D4;
  --color-accent-hover: #0891B2;

  /* Status */
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-error: #EF4444;

  /* Glass effects */
  --glass-bg: rgba(15, 23, 42, 0.8);
  --glass-border: rgba(255, 255, 255, 0.1);
}
```

### Theme-Aware Components

```typescript
// Theme toggle button with accessibility
const ThemeToggle = () => {
  const { resolvedTheme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className={cn(
        "p-2 rounded-xl transition-all duration-300",
        "bg-surface hover:bg-surface-hover",
        "border border-border hover:border-border-strong",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
      )}
      aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
    >
      {resolvedTheme === 'dark' ? (
        <Sun className="w-5 h-5 text-text-primary" aria-hidden="true" />
      ) : (
        <Moon className="w-5 h-5 text-text-primary" aria-hidden="true" />
      )}
    </button>
  );
};

// Theme-aware glass card
const ThemedGlassCard = ({ children, className }) => {
  const { resolvedTheme } = useTheme();

  return (
    <div className={cn(
      "rounded-2xl border backdrop-blur-xl transition-colors duration-300",
      resolvedTheme === 'dark'
        ? "bg-white/5 border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.4)]"
        : "bg-black/5 border-black/10 shadow-[0_8px_32px_rgba(0,0,0,0.1)]",
      className
    )}>
      {children}
    </div>
  );
};
```

### Semantic Theme Classes

```typescript
// Use semantic color classes that auto-switch with theme
const themeClasses = {
  background: "bg-background",
  surface: "bg-surface",
  surfaceHover: "hover:bg-surface-hover",
  textPrimary: "text-text-primary",
  textSecondary: "text-text-secondary",
  textTertiary: "text-text-tertiary",  // Large text only (18px+)
  border: "border-border",
  primary: "bg-primary hover:bg-primary-hover text-white",
};

// Theme transitions CSS
const themeTransitions = `
  :root { color-scheme: light dark; }

  *, *::before, *::after {
    transition: background-color 200ms, border-color 200ms, color 200ms;
  }
`;
```

---

## WCAG 2.1 AA Accessibility Standards

### Color Contrast Requirements

| Text Type | Minimum Ratio | Example |
|-----------|---------------|---------|
| Normal text (<18px) | 4.5:1 | Body copy, labels |
| Large text (18px+ or 14px bold) | 3.0:1 | Headings, buttons |
| UI components | 3.0:1 | Icons, borders, focus rings |

```typescript
// Pre-validated vDrive color pairs
const accessibleColors = {
  light: {
    textOnWhite: { fg: '#0F172A', ratio: 15.3 },      // AAA
    secondaryOnWhite: { fg: '#334155', ratio: 8.5 },  // AAA
    primaryOnWhite: { fg: '#2563EB', ratio: 4.6 },    // AA
    accentOnWhite: { fg: '#0891B2', ratio: 4.5 },     // AA
  },
  dark: {
    textOnDark: { fg: '#F8FAFC', ratio: 15.3 },       // AAA
    secondaryOnDark: { fg: '#CBD5E1', ratio: 9.1 },   // AAA
    primaryOnDark: { fg: '#3B82F6', ratio: 5.2 },     // AA
    accentOnDark: { fg: '#06B6D4', ratio: 6.8 },      // AA
  },
};
```

### Focus Management (REQUIRED)

```typescript
// Visible focus indicators - NEVER remove
const focusStyles = {
  default: "focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2",
  onDark: "focus-visible:ring-white focus-visible:ring-offset-slate-900",
  inset: "focus-visible:ring-inset focus-visible:ring-white/50",
};

// Accessible button
const AccessibleButton = ({ children, ...props }) => (
  <button
    className={cn(
      "px-4 py-2 rounded-xl font-medium",
      "bg-primary hover:bg-primary-hover text-white",
      "focus:outline-none focus-visible:ring-2 focus-visible:ring-primary",
      "focus-visible:ring-offset-2 focus-visible:ring-offset-background"
    )}
    {...props}
  >
    {children}
  </button>
);

// Focus trap hook for modals
const useFocusTrap = (isOpen: boolean) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen || !containerRef.current) return;

    const focusable = containerRef.current.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    first?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last?.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first?.focus();
      }
    };

    containerRef.current.addEventListener('keydown', handleKeyDown);
    return () => containerRef.current?.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  return containerRef;
};
```

### Keyboard Navigation

```typescript
// Arrow key navigation for menus/lists
const useArrowNavigation = (itemCount: number) => {
  const [activeIndex, setActiveIndex] = useState(0);

  const handleKeyDown = (e: KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
      case 'ArrowRight':
        e.preventDefault();
        setActiveIndex(i => (i + 1) % itemCount);
        break;
      case 'ArrowUp':
      case 'ArrowLeft':
        e.preventDefault();
        setActiveIndex(i => (i - 1 + itemCount) % itemCount);
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
  };

  return { activeIndex, setActiveIndex, handleKeyDown };
};
```

### ARIA Patterns

```typescript
// Icon buttons MUST have labels
<button aria-label="Close dialog">
  <X className="w-5 h-5" aria-hidden="true" />
</button>

// Loading states
<button disabled aria-busy="true">
  <Spinner aria-hidden="true" />
  <span>Uploading...</span>
</button>

// Live regions for dynamic content
<div aria-live="polite" aria-atomic="true" className="sr-only">
  {statusMessage}
</div>

// Form fields with error handling
<div>
  <label htmlFor="email">Email <span aria-hidden="true">*</span></label>
  <input
    id="email"
    type="email"
    aria-required="true"
    aria-invalid={hasError}
    aria-describedby={hasError ? "email-error" : undefined}
  />
  {hasError && (
    <p id="email-error" role="alert" className="text-error">
      Please enter a valid email
    </p>
  )}
</div>

// Page landmarks
<header role="banner">...</header>
<nav aria-label="Main navigation">...</nav>
<main id="main-content">...</main>
<footer role="contentinfo">...</footer>
```

### Screen Reader Content

```typescript
// Visually hidden, screen reader accessible
const srOnlyClass = `
  absolute w-px h-px p-0 -m-px overflow-hidden
  whitespace-nowrap border-0 clip-[rect(0,0,0,0)]
`;

// Skip link (REQUIRED for keyboard users)
const SkipLink = () => (
  <a
    href="#main-content"
    className={cn(
      "sr-only focus:not-sr-only",
      "focus:fixed focus:top-4 focus:left-4 focus:z-[100]",
      "focus:px-4 focus:py-2 focus:bg-primary focus:text-white",
      "focus:rounded-lg focus:shadow-lg"
    )}
  >
    Skip to main content
  </a>
);
```

### Touch Targets (44x44px minimum)

```typescript
// Icon button with adequate touch target
const IconButton = ({ icon: Icon, label, ...props }) => (
  <button
    aria-label={label}
    className={cn(
      "p-3 rounded-xl min-w-[44px] min-h-[44px]",
      "bg-surface hover:bg-surface-hover",
      "focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
    )}
    {...props}
  >
    <Icon className="w-6 h-6" aria-hidden="true" />
  </button>
);

// Touch-friendly list items
<ul className="space-y-2">
  {items.map(item => (
    <li key={item.id}>
      <button className="w-full min-h-[44px] px-4 py-3 text-left">
        {item.label}
      </button>
    </li>
  ))}
</ul>
```

### Motion Accessibility

```typescript
// Respect prefers-reduced-motion
const MotionSafe = ({ children }) => {
  const prefersReduced = usePrefersReducedMotion();

  return (
    <motion.div
      initial={{ opacity: 0, y: prefersReduced ? 0 : 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: prefersReduced ? 0 : 0.3 }}
    >
      {children}
    </motion.div>
  );
};

// CSS fallback
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Accessibility Testing Checklist

| Test | Tool | Requirement |
|------|------|-------------|
| Color contrast | axe, Chrome DevTools | 4.5:1 text, 3:1 UI |
| Keyboard nav | Manual | All elements reachable |
| Focus visible | Manual | Clear focus indicator |
| Screen reader | NVDA, VoiceOver | Content announced |
| Touch targets | Manual | 44x44px minimum |
| Zoom 200% | Browser | No horizontal scroll |
| Reduced motion | prefers-reduced-motion | Animations respect |
| Headings | axe, WAVE | Logical hierarchy |

---

## Anti-Patterns (NEVER Do)

| Problem | Fix |
|---------|-----|
| Generic fonts (Inter, Roboto, Arial) | Use serif for headlines, vary fonts |
| Purple gradient on white | Use brand colors: blue-cyan or gold |
| Centered everything | Embrace asymmetry |
| Stock illustrations | Use photography or abstract gradients |
| Boring shadows (`shadow-md`) | Use dramatic shadows or glows |
| Rainbow gradients | Stick to 2-3 brand colors |
| Same aesthetic every time | Vary between directions |
| Backdrop-blur everywhere | Use strategically, consider performance |
| Animations without purpose | Every animation should communicate |
| Ignoring reduced-motion | Always provide fallbacks |

---

## Execution Checklist

### Design Quality
- [ ] **Bold Direction**: Clear, intentional aesthetic chosen?
- [ ] **Brand Alignment**: Using design-system tokens and components?
- [ ] **Premium Feel**: Would a professional photographer be impressed?
- [ ] **Glassmorphism**: Used strategically, not everywhere?
- [ ] **Motion**: Key moments animated (stagger, reveal, hover)?
- [ ] **Micro-interactions**: Buttons, cards, inputs have feedback?
- [ ] **No AI Slop**: Avoided generic patterns?

### Theme Support
- [ ] **Light Theme**: Tested and visually polished?
- [ ] **Dark Theme**: Tested and visually polished?
- [ ] **Theme Toggle**: Accessible with proper aria-label?
- [ ] **CSS Variables**: Using semantic tokens that auto-switch?
- [ ] **Smooth Transitions**: Theme changes animate smoothly?

### WCAG 2.1 AA Compliance
- [ ] **Color Contrast**: 4.5:1 for text, 3:1 for UI components?
- [ ] **Focus Visible**: All interactive elements have visible focus?
- [ ] **Keyboard Nav**: All elements reachable via keyboard?
- [ ] **Touch Targets**: Minimum 44x44px for interactive elements?
- [ ] **ARIA Labels**: Icon buttons and images properly labeled?
- [ ] **Skip Link**: Skip to main content link present?
- [ ] **Form Errors**: Errors announced with role="alert"?
- [ ] **Reduced Motion**: Respects prefers-reduced-motion?
- [ ] **Zoom 200%**: No horizontal scroll, content readable?
- [ ] **Heading Hierarchy**: Logical h1-h6 order, no skipped levels?

### Performance
- [ ] **GPU Acceleration**: Using transform/opacity for animations?
- [ ] **Lazy Effects**: Blur/glass effects load on visibility?
- [ ] **Mobile Optimized**: Reduced effects on low-power devices?

---

## Creative Philosophy

Every interface should feel like it belongs in a design portfolio. Not safe. Not generic. **Exceptional.**

NEVER use generic AI-generated aesthetics:
- Overused font families (Inter, Roboto, Arial, system fonts)
- Cliched color schemes (purple gradients on white)
- Predictable layouts and patterns
- Cookie-cutter design lacking context-specific character

**Interpret creatively.** Make unexpected choices that feel genuinely designed. No design should be the same. Vary between light/dark themes, different fonts, different aesthetics. NEVER converge on common choices (Space Grotesk, etc.) across generations.

**Match complexity to vision.** Maximalist designs need elaborate code with extensive animations. Minimalist designs need restraint, precision, and careful attention to spacing and typography. Elegance comes from executing the vision well.

**Performance is design.** A beautiful interface that stutters is not beautiful. Consider device capabilities, respect user preferences, and optimize for smoothness.

Remember: Claude is capable of extraordinary creative work. Don't hold back.

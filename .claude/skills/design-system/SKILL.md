---
name: design-system
aliases: [ui, styling, tokens, theme, colors, components, tailwind, css, responsive, mobile-first]
description: Design system guidelines for vDrive. Use when styling components, using color tokens, implementing themes, responsive layouts, or following UI patterns. Mobile-first, futuristic design system.
---

# vDrive Design System

A **mobile-first, futuristic** design system for a premium photography SaaS platform.

## Core Files

| Purpose | Location |
|---------|----------|
| CSS Variables & Tokens | `frontend/src/index.css` |
| Tailwind Config | `frontend/tailwind.config.js` |
| UI Components | `frontend/src/components/ui/` |
| Layout Components | `frontend/src/components/layout/` |
| Mobile Hooks | `frontend/src/hooks/useMobile.ts` |

---

## Mobile-First Breakpoint System

### Breakpoint Scale

| Breakpoint | Min Width | Target Devices |
|------------|-----------|----------------|
| `xs` | 0px | Small phones (iPhone SE) |
| `sm` | 360px | Standard phones |
| `md` | 480px | Large phones, small tablets |
| `lg` | 768px | Tablets |
| `xl` | 1024px | Small laptops, tablets landscape |
| `2xl` | 1280px | Desktops |

### Tailwind Usage

```html
<!-- Mobile-first: base styles apply to mobile, then enhance -->
<div class="
  p-4          <!-- Mobile: 16px padding -->
  md:p-6       <!-- Tablet+: 24px padding -->
  xl:p-8       <!-- Desktop: 32px padding -->
">
  <h1 class="
    text-2xl   <!-- Mobile: 24px -->
    md:text-3xl <!-- Tablet: 30px -->
    xl:text-4xl <!-- Desktop: 36px -->
  ">
    Responsive Heading
  </h1>
</div>

<!-- Grid: 1 col mobile, 2 col tablet, 4 col desktop -->
<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
```

### Container Queries (Modern CSS)

```css
/* Component-level responsiveness */
.photo-grid-container {
  container-type: inline-size;
  container-name: photo-grid;
}

@container photo-grid (min-width: 400px) {
  .photo-card {
    grid-template-columns: auto 1fr;
  }
}

@container photo-grid (min-width: 600px) {
  .photo-card {
    grid-template-columns: repeat(2, 1fr);
  }
}
```

---

## Fluid Typography System

### Scale (Mobile → Desktop)

| Token | Mobile | Desktop | Usage |
|-------|--------|---------|-------|
| `text-fluid-xs` | 0.75rem | 0.875rem | Captions, labels |
| `text-fluid-sm` | 0.875rem | 1rem | Body small |
| `text-fluid-base` | 1rem | 1.125rem | Body |
| `text-fluid-lg` | 1.125rem | 1.25rem | Lead text |
| `text-fluid-xl` | 1.25rem | 1.5rem | Subheadings |
| `text-fluid-2xl` | 1.5rem | 2rem | Section headings |
| `text-fluid-3xl` | 2rem | 3rem | Page headings |
| `text-fluid-4xl` | 2.5rem | 4rem | Hero headings |

### CSS Implementation

```css
:root {
  /* Fluid typography using clamp() */
  --text-fluid-xs: clamp(0.75rem, 0.7rem + 0.25vw, 0.875rem);
  --text-fluid-sm: clamp(0.875rem, 0.8rem + 0.4vw, 1rem);
  --text-fluid-base: clamp(1rem, 0.9rem + 0.5vw, 1.125rem);
  --text-fluid-lg: clamp(1.125rem, 1rem + 0.6vw, 1.25rem);
  --text-fluid-xl: clamp(1.25rem, 1rem + 1.25vw, 1.5rem);
  --text-fluid-2xl: clamp(1.5rem, 1.25rem + 1.5vw, 2rem);
  --text-fluid-3xl: clamp(2rem, 1.5rem + 2.5vw, 3rem);
  --text-fluid-4xl: clamp(2.5rem, 2rem + 3vw, 4rem);
}
```

### Tailwind Classes

```html
<h1 class="text-[length:var(--text-fluid-4xl)] font-bold">Hero Title</h1>
<p class="text-[length:var(--text-fluid-base)]">Body text</p>
```

---

## Safe Area Handling (CRITICAL)

### CSS Variables

```css
:root {
  --safe-area-top: env(safe-area-inset-top, 0px);
  --safe-area-bottom: env(safe-area-inset-bottom, 0px);
  --safe-area-left: env(safe-area-inset-left, 0px);
  --safe-area-right: env(safe-area-inset-right, 0px);
}
```

### Utility Classes

```css
/* Safe area padding utilities */
.pt-safe { padding-top: env(safe-area-inset-top); }
.pb-safe { padding-bottom: env(safe-area-inset-bottom); }
.pl-safe { padding-left: env(safe-area-inset-left); }
.pr-safe { padding-right: env(safe-area-inset-right); }
.p-safe {
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
}

/* Dynamic viewport height (respects mobile browser chrome) */
.h-screen-dynamic { height: 100dvh; }
.min-h-screen-dynamic { min-height: 100dvh; }
```

### Usage Patterns

```html
<!-- Fixed header with notch support -->
<header class="fixed top-0 inset-x-0 pt-safe px-4 bg-warm-900/95 backdrop-blur-xl">

<!-- Bottom navigation with home indicator -->
<nav class="fixed bottom-0 inset-x-0 pb-safe bg-warm-900/95">

<!-- Full-screen container -->
<main class="min-h-screen-dynamic p-safe">
```

---

## Touch Target Guidelines

### Minimum Sizes

| Element | Min Size | Tailwind |
|---------|----------|----------|
| Buttons | 44×44px | `min-w-[44px] min-h-[44px]` |
| Icon buttons | 44×44px | `p-3` (48px total with 24px icon) |
| List items | 44px height | `min-h-[44px]` |
| Links in text | 44px tap area | Add padding or use `py-2` |

### Touch Target Spacing

```css
/* Minimum 8px between touch targets */
.touch-target-spacing > * + * {
  margin-top: 8px;
}
```

### Examples

```html
<!-- Icon button with proper touch target -->
<button class="p-3 min-w-[44px] min-h-[44px] rounded-xl">
  <Icon class="w-6 h-6" />
</button>

<!-- List items with proper touch targets -->
<ul class="space-y-2">
  <li>
    <button class="w-full min-h-[44px] px-4 py-3 text-left rounded-xl">
      Menu Item
    </button>
  </li>
</ul>
```

---

## Brand Colors

```css
/* Primary - Sky Blue (Brand Core) */
--color-primary: #0ea5e9;       /* sky-500 */
--color-primary-hover: #0284c7; /* sky-600 */

/* Accent - Apple Blue (clean, professional) */
--color-accent: #3B82F6;        /* blue-500 */
--color-accent-hover: #2563EB;  /* blue-600 */

/* Gold - Premium accents */
--color-gold: #D4AF37;
--color-gold-light: #FDE68A;
```

## Semantic Tokens

### Light Mode

```css
/* Backgrounds */
--color-background: #F8FAFC;
--color-surface: #FFFFFF;
--color-surface-hover: #F1F5F9;
--color-surface-elevated: #FFFFFF;

/* Text - WCAG AA compliant */
--color-text-primary: #0F172A;    /* 15.3:1 on white */
--color-text-secondary: #334155;  /* 8.5:1 on white */
--color-text-tertiary: #64748B;   /* 4.6:1 - large text only */

/* Borders */
--color-border: #E2E8F0;
--color-border-strong: #CBD5E1;
--color-border-focus: #2563EB;

/* Status */
--color-success: #059669;
--color-warning: #D97706;
--color-error: #DC2626;
```

### Dark Mode (Warm Neutrals)

```css
/* Backgrounds - Warm espresso/taupe undertones */
--color-background: #0f0d0c;      /* warm-950 - rich warm black */
--color-surface: #1a1614;         /* warm-900 - deep espresso */
--color-surface-hover: #2a2523;   /* warm-800 - warm cocoa */
--color-surface-elevated: #2a2523;

/* Text - WCAG AA compliant on warm backgrounds */
--color-text-primary: #f7f6f5;    /* warm-50 - 16.5:1 on warm-950 */
--color-text-secondary: #b5afac;  /* warm-300 - 8.2:1 on warm-950 */
--color-text-tertiary: #8a8380;   /* warm-400 - 5.2:1 on warm-950 */

/* Borders - warm tones */
--color-border: #2a2523;          /* warm-800 */
--color-border-strong: #3d3835;   /* warm-700 */
--color-border-focus: #3B82F6;

/* Status */
--color-success: #10B981;
--color-warning: #F59E0B;
--color-error: #EF4444;
```

## Warm Palette (Tailwind)

Custom warm neutral scale for dark mode with espresso/brown undertones:

| Token | Hex | Usage |
|-------|-----|-------|
| `warm-950` | `#0f0d0c` | Primary dark background |
| `warm-900` | `#1a1614` | Secondary surface |
| `warm-800` | `#2a2523` | Cards, borders |
| `warm-700` | `#3d3835` | Hover states |
| `warm-600` | `#524d4a` | Active states |
| `warm-500` | `#6b6562` | Muted text |
| `warm-400` | `#8a8380` | Secondary text |
| `warm-300` | `#b5afac` | Tertiary text |
| `warm-200` | `#d9d5d3` | Subtle borders (light) |
| `warm-100` | `#eceae9` | Light surfaces |
| `warm-50` | `#f7f6f5` | Light background |

**Why warm neutrals:**

- Subtle brown/taupe undertones feel inviting, not cold
- Better for viewing photos (pure grays can color-cast)
- Premium, distinctive feel for photography platform

---

## Futuristic Effects

### Neon Glow Scale

```css
/* Neon glow utilities */
--glow-accent-sm: 0 0 10px var(--color-accent), 0 0 20px rgba(59, 130, 246, 0.3);
--glow-accent-md: 0 0 20px var(--color-accent), 0 0 40px rgba(59, 130, 246, 0.3);
--glow-accent-lg: 0 0 30px var(--color-accent), 0 0 60px rgba(59, 130, 246, 0.3);

--glow-primary-sm: 0 0 10px var(--color-primary), 0 0 20px rgba(14, 165, 233, 0.3);
--glow-primary-md: 0 0 20px var(--color-primary), 0 0 40px rgba(14, 165, 233, 0.3);
--glow-primary-lg: 0 0 30px var(--color-primary), 0 0 60px rgba(14, 165, 233, 0.3);
```

### Tailwind Shadows

```javascript
// tailwind.config.js
boxShadow: {
  'glow-sm': '0 0 10px rgba(59, 130, 246, 0.3)',
  'glow': '0 0 20px rgba(59, 130, 246, 0.3)',
  'glow-lg': '0 0 40px rgba(59, 130, 246, 0.4)',
  'glow-accent': '0 0 40px rgba(59, 130, 246, 0.4)',
  'glow-primary': '0 0 40px rgba(14, 165, 233, 0.4)',
  'neon-accent': '0 0 20px var(--color-accent), 0 0 40px rgba(59, 130, 246, 0.3)',
  'glass': '0 8px 32px rgba(0, 0, 0, 0.12)',
  'glass-lg': '0 25px 80px rgba(0, 0, 0, 0.35)',
  'float': '0 20px 60px -10px rgba(0, 0, 0, 0.3)',
  'inner-glow': 'inset 0 1px 0 rgba(255, 255, 255, 0.1)',
}
```

### Glassmorphism Tokens

| Element | Background | Border | Blur |
|---------|------------|--------|------|
| Cards | `white/[0.12]` | `white/25` | `blur-xl` |
| Inputs | `white/[0.08]` | `white/25` | `blur-xl` |
| Modals | `white/[0.15]` | `white/30` | `blur-2xl` |
| Tooltips | `white/[0.10]` | `white/20` | `blur-lg` |
| Mobile | `white/[0.15]` | `white/25` | `blur-md` |

```html
<!-- Standard glass card -->
<div class="bg-white/[0.12] backdrop-blur-xl border border-white/25 rounded-2xl">

<!-- Mobile-optimized glass (reduced blur) -->
<div class="bg-white/[0.15] backdrop-blur-md md:backdrop-blur-xl border border-white/25 rounded-2xl">

<!-- Warm glass for dark mode -->
<div class="bg-warm-900/70 backdrop-blur-xl border border-warm-700/50 rounded-2xl">
```

---

## Animation System

### Keyframes (CSS)

```css
/* Entrance animations */
@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fade-in-scale {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes slide-up-mobile {
  from { opacity: 0; transform: translateY(100%); }
  to { opacity: 1; transform: translateY(0); }
}

/* Futuristic effects */
@keyframes morph {
  0%, 100% { border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }
  50% { border-radius: 30% 60% 70% 40% / 50% 60% 30% 60%; }
}

@keyframes gradient-x {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

@keyframes gradient-xy {
  0%, 100% { background-position: 0% 0%; }
  50% { background-position: 100% 100%; }
}

@keyframes shimmer {
  100% { transform: translateX(100%); }
}

@keyframes aurora {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  50% { transform: translate(30px, -30px) rotate(180deg); }
}

@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes neon-pulse {
  0%, 100% { opacity: 1; box-shadow: var(--glow-accent-md); }
  50% { opacity: 0.8; box-shadow: var(--glow-accent-sm); }
}
```

### Tailwind Animation Config

```javascript
// tailwind.config.js
animation: {
  'fade-in': 'fadeIn 0.5s ease-out',
  'fade-up': 'fadeUp 0.5s ease-out',
  'fade-in-up': 'fade-in-up 0.6s ease-out forwards',
  'fade-in-scale': 'fade-in-scale 0.5s ease-out forwards',
  'slide-up-mobile': 'slide-up-mobile 0.4s ease-out forwards',
  'slide-in-right': 'slideInRight 0.3s ease-out',
  'slide-in-left': 'slideInLeft 0.3s ease-out',
  'float': 'float 6s ease-in-out infinite',
  'pulse-glow': 'pulseGlow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
  'aurora': 'aurora 15s ease-in-out infinite',
  'aurora-slow': 'aurora 25s ease-in-out infinite',
  'shimmer': 'shimmer 2s infinite',
  'morph': 'morph 15s ease-in-out infinite',
  'gradient-x': 'gradient-x 3s ease infinite',
  'gradient-xy': 'gradient-xy 5s ease infinite',
  'spin-slow': 'spin-slow 8s linear infinite',
  'neon-pulse': 'neon-pulse 2s ease-in-out infinite',
}
```

### Stagger Utilities

```css
.stagger-1 { animation-delay: 50ms; }
.stagger-2 { animation-delay: 100ms; }
.stagger-3 { animation-delay: 150ms; }
.stagger-4 { animation-delay: 200ms; }
.stagger-5 { animation-delay: 250ms; }
.stagger-6 { animation-delay: 300ms; }
.stagger-7 { animation-delay: 350ms; }
.stagger-8 { animation-delay: 400ms; }
```

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-delay: 0ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Component Library

### Required Imports

```typescript
import { AppButton, AppInput, AppCard, AppBadge } from '@/components/ui';
import { Modal, Toast, Spinner, Skeleton } from '@/components/ui';
import { BottomSheet, FloatingActionButton, MobileTabBar } from '@/components/ui/mobile';
import { AppShell, Sidebar } from '@/components/layout';
import { useTheme, useBreakpoint, useHaptic } from '@/hooks';
```

### AppButton

```typescript
// Variants: primary, secondary, outline, ghost, destructive, gold, neon
<AppButton variant="primary">Save</AppButton>
<AppButton variant="outline">Cancel</AppButton>
<AppButton variant="destructive">Delete</AppButton>
<AppButton variant="gold">Upgrade</AppButton>
<AppButton variant="neon">Futuristic</AppButton>

// Sizes: sm, md, lg, icon
// All sizes meet 44px minimum touch target
<AppButton size="sm">Small</AppButton>  {/* 44px min height */}
<AppButton size="icon"><X size={20} /></AppButton>  {/* 44x44px */}

// States
<AppButton isLoading>Saving...</AppButton>
<AppButton disabled>Disabled</AppButton>

// With icons
<AppButton leftIcon={<Plus size={16} />}>Add</AppButton>
```

### AppInput

```typescript
<AppInput
  label="Email"
  type="email"
  placeholder="Enter email"
  isRequired
/>

<AppInput
  label="Password"
  error={errors.password?.message}
  helperText="Must be 8+ characters"
/>

<AppInput
  leftIcon={<Search size={16} />}
  rightIcon={<X size={16} />}
/>
```

### AppCard

```typescript
// Variants: default, elevated, glass, neon
<AppCard variant="glass" hoverable onClick={handleClick}>
  <Card.Header>
    <Card.Title>Title</Card.Title>
  </Card.Header>
  <Card.Content>Content</Card.Content>
  <Card.Footer>
    <AppButton>Action</AppButton>
  </Card.Footer>
</AppCard>

// Neon variant with glow
<AppCard variant="neon" glowColor="accent">
  <Card.Content>Futuristic card</Card.Content>
</AppCard>
```

### Mobile Components

```typescript
// Bottom Sheet
<BottomSheet isOpen={isOpen} onClose={onClose} snapPoints={[0.5, 0.9]}>
  <div className="space-y-4">
    <h3>Sheet Title</h3>
    <p>Content</p>
  </div>
</BottomSheet>

// Floating Action Button
<FloatingActionButton
  actions={[
    { id: 'upload', label: 'Upload', icon: Upload, onClick: handleUpload },
    { id: 'camera', label: 'Camera', icon: Camera, onClick: handleCamera },
  ]}
/>

// Mobile Tab Bar
<MobileTabBar
  tabs={[
    { id: 'home', label: 'Home', icon: Home },
    { id: 'search', label: 'Search', icon: Search },
    { id: 'profile', label: 'Profile', icon: User },
  ]}
  activeTab={activeTab}
  onTabChange={setActiveTab}
/>
```

---

## Theme System

```typescript
import { useTheme } from '@/hooks';

const { theme, toggleTheme, isDark, resolvedTheme } = useTheme();

<AppButton variant="ghost" size="icon" onClick={toggleTheme}>
  {isDark ? <Sun size={20} /> : <Moon size={20} />}
</AppButton>
```

### CSS Variables

```css
/* Light theme (default) */
:root, [data-theme="light"] {
  --color-background: #F8FAFC;
  --color-surface: #FFFFFF;
  --color-text-primary: #0F172A;
  /* ... */
}

/* Dark theme - Warm neutrals */
[data-theme="dark"] {
  --color-background: #0f0d0c;
  --color-surface: #1a1614;
  --color-text-primary: #f7f6f5;
  /* ... */
}
```

### Tailwind Dark Mode

```html
<!-- Use warm-* classes for dark mode backgrounds -->
<div class="bg-white dark:bg-warm-950">...</div>
<div class="bg-gray-100 dark:bg-warm-900">...</div>
<div class="border-gray-200 dark:border-warm-800">...</div>
<div class="text-gray-900 dark:text-warm-50">...</div>
```

---

## Typography

```css
--font-sans: 'Inter', system-ui, sans-serif;
--font-display: 'Cal Sans', 'Inter', system-ui, sans-serif;
--font-serif: 'Playfair Display', Georgia, serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
```

### Heading Scale

```html
<h1 class="text-fluid-4xl font-bold">Hero Title</h1>
<h2 class="text-fluid-3xl font-bold">Page Title</h2>
<h3 class="text-fluid-2xl font-semibold">Section</h3>
<h4 class="text-fluid-xl font-semibold">Subsection</h4>
```

### Gradient Text

```html
<span class="bg-gradient-to-r from-accent-400 to-primary-500 bg-clip-text text-transparent">
  Gradient Text
</span>
```

---

## Spacing System

### Base Scale (4px)

| Class | Value | Mobile Use | Desktop Use |
|-------|-------|------------|-------------|
| `p-1` | 4px | Inline tight | Same |
| `p-2` | 8px | Default inline | Same |
| `p-3` | 12px | Touch target pad | Card inner |
| `p-4` | 16px | Card padding | Section inner |
| `p-6` | 24px | Section spacing | Large padding |
| `p-8` | 32px | - | Section padding |

### Fluid Spacing

```css
--space-fluid-1: clamp(0.25rem, 0.5vw, 0.5rem);
--space-fluid-2: clamp(0.5rem, 1vw, 1rem);
--space-fluid-4: clamp(1rem, 2vw, 2rem);
--space-fluid-8: clamp(2rem, 4vw, 4rem);
--space-fluid-16: clamp(4rem, 8vw, 8rem);
```

---

## Design Rules

### ALWAYS Do

1. **Mobile-first**: Base styles for mobile, enhance with breakpoints
2. **Touch targets**: Minimum 44×44px for all interactive elements
3. **Safe areas**: Use `env(safe-area-inset-*)` for fixed elements
4. **Design tokens**: Use semantic tokens like `bg-surface`, `text-text-primary`
5. **Component library**: Use `AppButton`, `AppInput`, etc.
6. **Dark mode**: Support with warm-* palette
7. **Accessibility**: Include focus states, ARIA labels, reduced motion support
8. **Performance**: Adapt effects based on device capabilities

### NEVER Do

1. **Hardcode colors**: No `bg-blue-500`, `#ffffff`
2. **Fixed heights**: No `h-screen`, use `h-screen-dynamic` or `min-h-[100dvh]`
3. **Small touch targets**: Never less than 44px
4. **Skip safe areas**: Always respect notch/home indicator
5. **Create custom buttons/inputs**: Use component library
6. **Use `outline-none`**: Without visible focus replacement
7. **Skip loading/error states**: Always show feedback
8. **Ignore reduced motion**: Always provide fallbacks

---

## Performance Guidelines

### Device-Adaptive Effects

```typescript
// Detect device capabilities
const { isLowPower, hasReducedMotion } = useDeviceCapabilities();

// Adapt effects
<div className={cn(
  "rounded-2xl",
  isLowPower
    ? "bg-warm-900/95 border-warm-700"  // Simple
    : "bg-white/10 backdrop-blur-xl border-white/20"  // Full glass
)}>
```

### GPU-Accelerated Properties

```typescript
// PREFER: GPU-accelerated
transform: translateX(), translateY(), scale(), rotate()
opacity
filter: blur(), brightness()

// AVOID: Cause layout recalculation
width, height, top, left
margin, padding
border-radius (animate sparingly)
```

### Lazy Loading

```html
<!-- Images -->
<img loading="lazy" decoding="async" />

<!-- Effects: Only apply when visible -->
<div class="backdrop-blur-none intersection-visible:backdrop-blur-xl">
```

---

## Accessibility Checklist

| Requirement | Standard | Implementation |
|-------------|----------|----------------|
| Text contrast | 4.5:1 (AA) | Use semantic text tokens |
| UI contrast | 3:1 (AA) | Use design system colors |
| Touch targets | 44×44px | `min-w-[44px] min-h-[44px]` |
| Focus visible | Clear indicator | `focus-visible:ring-2` |
| Reduced motion | Respect preference | `prefers-reduced-motion` |
| Screen reader | Labels & landmarks | ARIA attributes |
| Keyboard nav | All elements reachable | `tabindex`, focus trap |

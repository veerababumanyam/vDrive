# RawDrive Design System

**Version:** 0.3.3 | **Last Updated:** January 2026

---

## Design Principles

### 1. Content-First
The photography is the hero. The UI should recede, providing a clean, distraction-free stage for images.

### 2. Premium & Polished
High attention to micro-interactions, smooth transitions, and consistent spacing.

### 3. Accessibility
WCAG 2.1 AA compliance is mandatory. High contrast modes and keyboard navigation are first-class citizens.

### 4. Responsive
Mobile-first design. The experience on a phone must be as powerful as on desktop.

---

## Technology Stack

| Technology | Purpose |
|------------|---------|
| **React 19+** | UI framework with hooks |
| **Tailwind CSS v3+** | Utility-first styling |
| **Radix UI** | Headless accessible primitives |
| **shadcn/ui** | Re-usable component library |
| **Lucide React** | Icon library (1000+ icons) |
| **Framer Motion** | Animation library |
| **Inter Font** | Primary typography |

---

## Typography

### Font Family

```css
font-family: 'Inter', system-ui, -apple-system, sans-serif;
```

**Why Inter?**
- Excellent legibility at all sizes
- Neutral character
- Standard for modern SaaS

### Font Weights

| Weight | Usage |
|--------|-------|
| 400 (Regular) | Body text |
| 500 (Medium) | UI labels, buttons |
| 600 (Semibold) | Subheadings |
| 700 (Bold) | Headings |

### Type Scale

| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| H1 | 2.25rem (36px) | 700 | 1.2 |
| H2 | 1.875rem (30px) | 700 | 1.25 |
| H3 | 1.5rem (24px) | 600 | 1.3 |
| H4 | 1.25rem (20px) | 600 | 1.4 |
| Body | 1rem (16px) | 400 | 1.5 |
| Small | 0.875rem (14px) | 400 | 1.5 |
| Caption | 0.75rem (12px) | 400 | 1.4 |

---

## Color System

### Neutral Scale (Slate)

Premium, slightly cool tone neutral palette:

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| `bg-background` | `#ffffff` | `#020617` | Page background |
| `bg-muted` | `#f1f5f9` | `#1e293b` | Secondary backgrounds |
| `text-foreground` | `#0f172a` | `#f8fafc` | Primary text |
| `text-muted-foreground` | `#64748b` | `#94a3b8` | Secondary text |
| `border` | `#e2e8f0` | `#334155` | Borders |

### Primary Brand (Indigo)

| Token | Value | Usage |
|-------|-------|-------|
| `bg-primary` | `#4f46e5` | Primary buttons, active states |
| `bg-primary/90` | `#4338ca` | Hover states |
| `text-primary-foreground` | `#ffffff` | Text on primary |

### Status Colors

| Status | Light | Dark | Hex |
|--------|-------|------|-----|
| Success | Emerald-600 | Emerald-400 | `#059669` |
| Destructive | Red-600 | Red-400 | `#dc2626` |
| Warning | Amber-500 | Amber-400 | `#f59e0b` |
| Info | Blue-600 | Blue-400 | `#2563eb` |

### Dark Mode Strategy

1. **No pure black** - Use rich dark grays (Slate-950: `#020617`)
2. **Subtle borders** - Slate-800 to define structure
3. **Depth with shadows** - `shadow-xl` with lighter background layers

---

## Component Library

### Button Variants

```typescript
type ButtonVariant = 'default' | 'secondary' | 'ghost' | 'destructive' | 'outline';
type ButtonSize = 'sm' | 'default' | 'lg' | 'icon';
```

| Variant | Usage |
|---------|-------|
| `default` | Primary actions |
| `secondary` | Secondary actions |
| `ghost` | Tertiary actions, inline |
| `destructive` | Destructive actions |
| `outline` | Alternative to secondary |

### Input Components

| Component | Location |
|-----------|----------|
| `AppButton` | `frontend/src/components/ui/AppButton.tsx` |
| `AppInput` | `frontend/src/components/ui/AppInput.tsx` |
| `AppSelect` | `frontend/src/components/ui/AppSelect.tsx` |
| `AppTextarea` | `frontend/src/components/ui/AppTextarea.tsx` |
| `AppCheckbox` | `frontend/src/components/ui/AppCheckbox.tsx` |

### Dialog/Modal

- Managed via Radix UI `Dialog` primitive
- Focus trapping for accessibility
- Screen reader support
- Escape key to close

### Toast Notifications

Using `sonner` library for polished notifications:

```typescript
import { toast } from 'sonner';

toast.success('Gallery created successfully');
toast.error('Failed to upload image');
toast.loading('Processing...');
```

---

## Gallery Themes

### Gradient Presets

RawDrive includes customizable gradient themes for galleries:

| Theme | Primary | Secondary |
|-------|---------|-----------|
| Sunset | `#f97316` | `#ec4899` |
| Ocean | `#0ea5e9` | `#6366f1` |
| Forest | `#22c55e` | `#14b8a6` |
| Midnight | `#1e293b` | `#3b82f6` |
| Rose | `#f43f5e` | `#ec4899` |

### Brand Themes (Personal Profiles)

| Theme | Description |
|-------|-------------|
| `dark` | Dark sophisticated background |
| `pastel` | Soft, muted colors |
| `bold` | Vibrant, high-contrast |
| `cinematic` | Film-inspired aesthetic |
| `minimal` | Clean, white-focused |

---

## Animation Guidelines

Use **Framer Motion** for purposeful animations:

### Duration
- Fast: 0.15-0.2s (micro-interactions)
- Normal: 0.2-0.3s (UI transitions)
- Slow: 0.3-0.5s (page transitions)

### Easing
```javascript
// Entrance: ease-out
{ ease: [0.22, 1, 0.36, 1] }

// Exit: ease-in
{ ease: [0.4, 0, 1, 1] }
```

### Micro-Interactions
- Scale down slightly (0.98) on button click
- Subtle color shifts on hover
- Skeleton loading states (no spinners for content)

### Example
```typescript
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  exit={{ opacity: 0, y: -20 }}
  transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
>
  Content
</motion.div>
```

---

## Icons

Using **Lucide React** for consistent iconography:

```typescript
import { Camera, Upload, Settings, User } from 'lucide-react';

<Camera className="w-5 h-5" />
```

### Icon Sizes

| Size | Class | Usage |
|------|-------|-------|
| XS | `w-3 h-3` | Inline indicators |
| SM | `w-4 h-4` | Button icons, compact |
| MD | `w-5 h-5` | Default |
| LG | `w-6 h-6` | Feature icons |
| XL | `w-8 h-8` | Hero icons |

---

## Spacing System

Based on 4px base unit:

| Token | Value | Usage |
|-------|-------|-------|
| `space-1` | 4px | Tight gaps |
| `space-2` | 8px | Compact spacing |
| `space-3` | 12px | Default gaps |
| `space-4` | 16px | Component padding |
| `space-6` | 24px | Section spacing |
| `space-8` | 32px | Large sections |
| `space-12` | 48px | Page sections |

---

## Responsive Breakpoints

```css
/* Tailwind defaults */
sm: 640px   /* Mobile landscape */
md: 768px   /* Tablet portrait */
lg: 1024px  /* Tablet landscape / small desktop */
xl: 1280px  /* Desktop */
2xl: 1536px /* Large desktop */
```

### Mobile-First Approach
```typescript
// Always start with mobile styles
<div className="p-4 md:p-6 lg:p-8">
  <h1 className="text-xl md:text-2xl lg:text-3xl">
    Gallery
  </h1>
</div>
```

---

## Accessibility

### Requirements
- WCAG 2.1 AA compliance
- Keyboard navigation (Tab, Enter, Escape)
- Focus indicators (visible focus rings)
- Screen reader support (ARIA labels)
- Contrast ratios ≥ 4.5:1 for text

### Focus States
```css
focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2
```

### Skip Links
```html
<a href="#main-content" class="sr-only focus:not-sr-only">
  Skip to main content
</a>
```

---

## AI Native UX Patterns

### Command Bar
Central "Cmd+K" interface for natural language commands:
```
"Find photos of the bride smiling at sunset"
```

### Skeleton Loading
Shimmer effects that mimic content shape during AI inference:
```typescript
<div className="animate-pulse bg-muted rounded h-4 w-full" />
```

### Smart Curation UI
- Masonry layouts with AI quality-based sizing
- Contextual action buttons based on content detection

---

## Component File Structure

```
frontend/src/components/
├── ui/                    # Design system primitives
│   ├── AppButton.tsx
│   ├── AppInput.tsx
│   ├── AppSelect.tsx
│   ├── AppDialog.tsx
│   ├── AppToast.tsx
│   └── index.ts
├── layout/                # Layout components
│   ├── Header.tsx
│   ├── Sidebar.tsx
│   └── Footer.tsx
└── features/              # Feature-specific components
    ├── gallery/
    ├── upload/
    └── profile/
```

---

## Implementation Checklist

1. [ ] Configure Tailwind CSS with color tokens in `globals.css`
2. [ ] Install dependencies: `lucide-react`, `class-variance-authority`, `clsx`, `tailwind-merge`
3. [ ] Configure Inter font in `tailwind.config.js`
4. [ ] Set up dark mode toggle with React context
5. [ ] Copy core primitives from shadcn/ui to `src/components/ui`
6. [ ] Implement focus management for accessibility
7. [ ] Test with screen readers (VoiceOver, NVDA)

---

## Related Documentation

- **Tech Stack:** [02-TECH-STACK.md](02-TECH-STACK.md)
- **Full Design System:** `docs/project/11-UI_UX_DESIGN_SYSTEM.md`
- **Components:** `frontend/src/components/ui/`

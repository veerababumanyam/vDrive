---
name: accessibility
aliases: [a11y, wcag, aria, keyboard-nav, screen-reader, touch-targets, mobile-a11y]
description: Accessibility guidelines for vDrive. Use when building UI components, handling keyboard navigation, implementing ARIA attributes, ensuring WCAG compliance, or optimizing for mobile accessibility.
---

# Accessibility Guidelines

A **mobile-first accessibility** approach ensuring all users can interact with vDrive effectively.

## WCAG 2.1 AA Compliance

All components and features must meet WCAG 2.1 Level AA standards.

---

## Mobile Accessibility (Priority)

### Touch Targets (CRITICAL)

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Interactive elements | 44×44px | 48×48px |
| Spacing between targets | 8px | 12px |
| Touch target expansion | Padding, not just visual size |

```typescript
// Icon button with adequate touch target
const TouchableIconButton = ({ icon: Icon, label, ...props }) => (
  <button
    aria-label={label}
    className={cn(
      "p-3 min-w-[44px] min-h-[44px]",  // Meets minimum
      "rounded-xl flex items-center justify-center",
      "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500"
    )}
    {...props}
  >
    <Icon className="w-6 h-6" aria-hidden="true" />
  </button>
);

// List items with proper touch targets
<ul className="space-y-2">
  {items.map(item => (
    <li key={item.id}>
      <button className="w-full min-h-[44px] px-4 py-3 text-left rounded-xl">
        {item.label}
      </button>
    </li>
  ))}
</ul>
```

### Gesture Alternatives

Every gesture must have an alternative:

| Gesture | Alternative Required |
|---------|---------------------|
| Swipe to delete | Delete button |
| Pinch to zoom | Zoom +/- buttons |
| Long press | Context menu button |
| Pull to refresh | Refresh button |
| Double tap | Single tap option |

```typescript
// Swipeable card with button alternative
const SwipeablePhotoCard = ({ photo, onDelete }) => (
  <div className="relative">
    {/* Swipeable area for gesture users */}
    <SwipeableCard onSwipeLeft={() => onDelete(photo.id)}>
      <PhotoCard photo={photo} />
    </SwipeableCard>

    {/* Button alternative for accessibility */}
    <button
      aria-label={`Delete ${photo.title}`}
      onClick={() => onDelete(photo.id)}
      className="absolute top-2 right-2 p-2 min-w-[44px] min-h-[44px]"
    >
      <Trash2 className="w-5 h-5" aria-hidden="true" />
    </button>
  </div>
);
```

### Safe Area Accessibility

Ensure content isn't hidden by device notches or home indicators:

```css
/* Screen reader content respecting safe areas */
.mobile-content {
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
}

/* Focus indicators must be visible within safe areas */
.mobile-focusable:focus-visible {
  outline-offset: 2px;
  outline: 2px solid var(--color-accent);
}
```

### Text Scaling Support

```css
/* Use relative units for font sizes */
.body-text {
  font-size: 1rem;      /* Not 16px */
  line-height: 1.5;     /* Not 24px */
}

/* Support browser zoom up to 200% */
.container {
  max-width: 100%;
  overflow-x: hidden;   /* Prevent horizontal scroll at 200% zoom */
}

/* Fluid typography respecting user preferences */
html {
  font-size: clamp(100%, 90% + 0.5vw, 125%);
}
```

---

## Contrast Requirements

### Color Contrast Ratios

| Text Type | Minimum Ratio | vDrive Implementation |
|-----------|---------------|----------------------|
| Normal text (<18px) | 4.5:1 | `text-text-primary` (15.3:1) |
| Large text (18px+ or 14px bold) | 3.0:1 | `text-text-secondary` (8.5:1) |
| UI components | 3.0:1 | All interactive elements |
| Focus indicators | 3.0:1 | `ring-accent-500` |

### Pre-Validated Color Pairs

```typescript
// Light mode - WCAG AA verified
const lightModeColors = {
  textOnWhite: { fg: '#0F172A', ratio: 15.3 },      // AAA
  secondaryOnWhite: { fg: '#334155', ratio: 8.5 },  // AAA
  primaryOnWhite: { fg: '#2563EB', ratio: 4.6 },    // AA
  accentOnWhite: { fg: '#0891B2', ratio: 4.5 },     // AA
};

// Dark mode (warm neutrals) - WCAG AA verified
const darkModeColors = {
  textOnDark: { fg: '#f7f6f5', bg: '#0f0d0c', ratio: 16.5 },     // AAA
  secondaryOnDark: { fg: '#b5afac', bg: '#0f0d0c', ratio: 8.2 }, // AAA
  tertiaryOnDark: { fg: '#8a8380', bg: '#0f0d0c', ratio: 5.2 },  // AA (large text)
  accentOnDark: { fg: '#3B82F6', bg: '#0f0d0c', ratio: 5.2 },    // AA
};
```

### Testing Contrast

```typescript
// Utility to check contrast ratio
const getContrastRatio = (fg: string, bg: string): number => {
  const getLuminance = (hex: string) => {
    const rgb = parseInt(hex.slice(1), 16);
    const r = ((rgb >> 16) & 0xff) / 255;
    const g = ((rgb >> 8) & 0xff) / 255;
    const b = (rgb & 0xff) / 255;

    const [rs, gs, bs] = [r, g, b].map(c =>
      c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
    );
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  };

  const l1 = getLuminance(fg);
  const l2 = getLuminance(bg);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
};
```

---

## Keyboard Navigation

### Requirements

- All interactive elements must be keyboard accessible
- Tab order must follow logical reading order
- Focus indicators must be visible and clear
- No keyboard traps (users can navigate away from all elements)
- Support standard keyboard patterns

### Standard Keyboard Patterns

| Key | Action |
|-----|--------|
| `Tab` | Move to next focusable element |
| `Shift+Tab` | Move to previous focusable element |
| `Enter` | Activate buttons, links |
| `Space` | Activate buttons, toggle checkboxes |
| `Escape` | Close modals, dismiss menus |
| `Arrow keys` | Navigate within components (menus, grids) |
| `Home`/`End` | Jump to first/last item in list |

### Focus Management

```typescript
// Focus trap for modals
const useFocusTrap = (isOpen: boolean) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen || !containerRef.current) return;

    const focusable = containerRef.current.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    // Focus first element
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

// Arrow key navigation for lists/menus
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

### Focus Styles (REQUIRED)

```css
/* NEVER remove focus indicators */
/* BAD: outline: none; */

/* GOOD: Enhanced focus indicators */
.focusable {
  /* Hide default outline */
  outline: none;

  /* Add custom focus ring */
  &:focus-visible {
    outline: 2px solid var(--color-accent);
    outline-offset: 2px;
  }
}

/* Tailwind classes */
.focus-ring {
  @apply focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500 focus-visible:ring-offset-2;
}

/* Dark mode focus */
.focus-ring-dark {
  @apply focus-visible:ring-white focus-visible:ring-offset-warm-950;
}
```

---

## Screen Reader Support

### Semantic HTML Elements

Always prefer semantic HTML over ARIA:

```html
<!-- GOOD: Semantic elements -->
<button>Click me</button>
<nav aria-label="Main navigation">...</nav>
<main id="main-content">...</main>
<header>...</header>
<footer>...</footer>
<article>...</article>
<aside>...</aside>

<!-- BAD: Div with role -->
<div role="button" tabindex="0">Click me</div>
```

### Heading Hierarchy

```html
<!-- Maintain proper hierarchy - no skipping levels -->
<h1>Page Title</h1>
  <h2>Section 1</h2>
    <h3>Subsection 1.1</h3>
    <h3>Subsection 1.2</h3>
  <h2>Section 2</h2>
    <h3>Subsection 2.1</h3>

<!-- BAD: Skipping levels -->
<h1>Page Title</h1>
<h3>Subsection</h3>  <!-- Missing h2! -->
```

### Form Accessibility

```typescript
// Accessible form field
const AccessibleInput = ({ id, label, error, required, helperText, ...props }) => {
  const errorId = error ? `${id}-error` : undefined;
  const helperId = helperText ? `${id}-helper` : undefined;
  const describedBy = [errorId, helperId].filter(Boolean).join(' ') || undefined;

  return (
    <div>
      <label htmlFor={id}>
        {label}
        {required && <span aria-hidden="true"> *</span>}
        {required && <span className="sr-only">(required)</span>}
      </label>

      <input
        id={id}
        aria-required={required}
        aria-invalid={!!error}
        aria-describedby={describedBy}
        {...props}
      />

      {helperText && (
        <p id={helperId} className="text-sm text-text-secondary">
          {helperText}
        </p>
      )}

      {error && (
        <p id={errorId} role="alert" className="text-sm text-error">
          {error}
        </p>
      )}
    </div>
  );
};
```

### ARIA Attributes

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

// Expanded/collapsed states
<button
  aria-expanded={isOpen}
  aria-controls="menu-content"
  onClick={toggleMenu}
>
  Menu
</button>
<div id="menu-content" hidden={!isOpen}>
  {/* Menu content */}
</div>

// Modal dialogs
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="dialog-title"
  aria-describedby="dialog-description"
>
  <h2 id="dialog-title">Confirm Delete</h2>
  <p id="dialog-description">Are you sure?</p>
</div>
```

### Live Regions

```typescript
// Announce dynamic content changes
const useAnnounce = () => {
  const announce = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    const el = document.createElement('div');
    el.setAttribute('role', 'status');
    el.setAttribute('aria-live', priority);
    el.setAttribute('aria-atomic', 'true');
    el.className = 'sr-only';
    el.textContent = message;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 1000);
  };

  return { announce };
};

// Usage
const { announce } = useAnnounce();
announce('Photo uploaded successfully');
announce('Error: Upload failed', 'assertive');
```

### Screen Reader Only Content

```css
/* Visually hidden but accessible to screen readers */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

/* Show on focus (for skip links) */
.sr-only-focusable:focus {
  position: static;
  width: auto;
  height: auto;
  padding: inherit;
  margin: inherit;
  overflow: visible;
  clip: auto;
  white-space: normal;
}
```

---

## Motion Accessibility

### Reduced Motion Support

```typescript
// Hook for respecting user preferences
const usePrefersReducedMotion = () => {
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

// Usage in components
const AnimatedComponent = ({ children }) => {
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
```

### CSS Reduced Motion

```css
/* Global reduced motion handling */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

/* Per-element control */
.animated-element {
  animation: fadeIn 0.5s ease-out;
}

@media (prefers-reduced-motion: reduce) {
  .animated-element {
    animation: none;
    opacity: 1;
  }
}
```

### Auto-Playing Media

```typescript
// Pause animations/videos when reduced motion is preferred
const AutoPlayVideo = ({ src, ...props }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const prefersReduced = usePrefersReducedMotion();

  useEffect(() => {
    if (videoRef.current) {
      if (prefersReduced) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
    }
  }, [prefersReduced]);

  return <video ref={videoRef} src={src} muted loop {...props} />;
};
```

---

## Component-Specific Guidelines

### Buttons (AppButton)

```typescript
// Accessible button component
const AppButton = ({
  children,
  variant,
  isLoading,
  disabled,
  leftIcon,
  rightIcon,
  ...props
}) => (
  <button
    type="button"  // Prevent form submission
    disabled={disabled || isLoading}
    aria-busy={isLoading}
    className={cn(
      "min-w-[44px] min-h-[44px]",  // Touch target
      "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500"
    )}
    {...props}
  >
    {isLoading && <Spinner aria-hidden="true" />}
    {leftIcon && <span aria-hidden="true">{leftIcon}</span>}
    <span>{children}</span>
    {rightIcon && <span aria-hidden="true">{rightIcon}</span>}
  </button>
);

// Icon-only button MUST have aria-label
<AppButton variant="ghost" size="icon" aria-label="Close">
  <X className="w-5 h-5" aria-hidden="true" />
</AppButton>
```

### Modals and Dialogs

```typescript
const AccessibleModal = ({ isOpen, onClose, title, children }) => {
  const modalRef = useFocusTrap(isOpen);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      previousActiveElement.current = document.activeElement as HTMLElement;
    } else {
      previousActiveElement.current?.focus();
    }
  }, [isOpen]);

  // Handle Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop - NOT keyboard interactive */}
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
        role="presentation"
        aria-hidden="true"
      />

      {/* Modal content */}
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        className="fixed inset-x-4 top-1/2 -translate-y-1/2 z-50 md:inset-x-auto md:left-1/2 md:-translate-x-1/2 md:w-full md:max-w-md"
      >
        <h2 id="modal-title" className="sr-only">{title}</h2>
        <button
          onClick={onClose}
          aria-label="Close dialog"
          className="absolute top-4 right-4 p-2 min-w-[44px] min-h-[44px]"
        >
          <X aria-hidden="true" />
        </button>
        {children}
      </div>
    </>
  );
};
```

### Bottom Sheet (Mobile)

```typescript
const AccessibleBottomSheet = ({ isOpen, onClose, title, children }) => {
  const sheetRef = useFocusTrap(isOpen);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 z-40"
            onClick={onClose}
            role="presentation"
            aria-hidden="true"
          />

          {/* Sheet */}
          <motion.div
            ref={sheetRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="sheet-title"
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            className="fixed bottom-0 inset-x-0 z-50 bg-warm-900 rounded-t-3xl pb-safe"
          >
            {/* Drag handle - decorative */}
            <div className="flex justify-center pt-3 pb-2" aria-hidden="true">
              <div className="w-10 h-1 bg-warm-600 rounded-full" />
            </div>

            <h2 id="sheet-title" className="sr-only">{title}</h2>

            {/* Close button */}
            <button
              onClick={onClose}
              aria-label="Close"
              className="absolute top-4 right-4 p-2 min-w-[44px] min-h-[44px]"
            >
              <X aria-hidden="true" />
            </button>

            <div className="px-4 pb-4 overflow-y-auto max-h-[70vh]">
              {children}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
```

### Photo Grid

```typescript
const AccessiblePhotoGrid = ({ photos, onSelect }) => (
  <div
    role="grid"
    aria-label="Photo gallery"
    className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2"
  >
    {photos.map((photo, index) => (
      <div key={photo.id} role="gridcell">
        <button
          onClick={() => onSelect(photo)}
          aria-label={`View ${photo.title || `photo ${index + 1}`}`}
          className="w-full aspect-square rounded-xl overflow-hidden focus-visible:ring-2 focus-visible:ring-accent-500"
        >
          <img
            src={photo.thumbnailUrl}
            alt={photo.alt || photo.title || ''}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        </button>
      </div>
    ))}
  </div>
);
```

---

## Skip Links

```typescript
// Skip link for keyboard users (REQUIRED)
const SkipLink = () => (
  <a
    href="#main-content"
    className={cn(
      "sr-only focus:not-sr-only",
      "focus:fixed focus:top-4 focus:left-4 focus:z-[100]",
      "focus:px-4 focus:py-2 focus:bg-accent-500 focus:text-white",
      "focus:rounded-lg focus:shadow-lg"
    )}
  >
    Skip to main content
  </a>
);

// Usage in layout
const Layout = ({ children }) => (
  <>
    <SkipLink />
    <header>...</header>
    <main id="main-content" tabIndex={-1}>
      {children}
    </main>
    <footer>...</footer>
  </>
);
```

---

## Testing Checklist

### Automated Testing

| Test | Tool | What It Catches |
|------|------|-----------------|
| Contrast | axe, Lighthouse | Color contrast issues |
| ARIA | axe, WAVE | Missing/invalid ARIA |
| HTML | W3C validator | Invalid markup |
| Headings | axe | Heading hierarchy |

### Manual Testing

| Test | How | What To Check |
|------|-----|---------------|
| Keyboard only | No mouse | All elements reachable, focus visible |
| Screen reader | NVDA/VoiceOver | Content announced correctly |
| Touch targets | Mobile device | 44px minimum, adequate spacing |
| Zoom 200% | Browser zoom | No horizontal scroll, content readable |
| Reduced motion | OS setting | Animations respect preference |

### Per-Component Checklist

- [ ] Focus indicator visible (3:1 contrast)
- [ ] Keyboard accessible
- [ ] Touch target 44×44px minimum
- [ ] ARIA labels for icon buttons
- [ ] Error messages announced
- [ ] Loading states announced
- [ ] Reduced motion fallback
- [ ] Color not only indicator

---

## Common Accessibility Errors

### DON'T

```typescript
// Missing label
<button><X /></button>

// Color-only feedback
<span className="text-red-500">Error</span>

// Removing focus outline
button { outline: none; }

// Non-focusable interactive
<div onClick={handleClick}>Click me</div>

// Auto-playing animation without control
<video autoPlay loop />

// Touch target too small
<button className="p-1">X</button>
```

### DO

```typescript
// With label
<button aria-label="Close"><X aria-hidden="true" /></button>

// Icon + text feedback
<span className="text-red-500">
  <AlertIcon aria-hidden="true" /> Error: Please try again
</span>

// Custom focus ring
button:focus-visible { ring: 2px solid var(--accent); }

// Semantic element
<button onClick={handleClick}>Click me</button>

// Pause control + reduced motion
<video autoPlay={!prefersReduced} loop controls />

// Adequate touch target
<button className="p-3 min-w-[44px] min-h-[44px]">X</button>
```

---

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [MDN Accessibility Guide](https://developer.mozilla.org/en-US/docs/Web/Accessibility)
- [Inclusive Components](https://inclusive-components.design/)
- [a11y Project Checklist](https://www.a11yproject.com/checklist/)

# Research: RawDrive Public Website

**Feature**: 002-public-website
**Date**: 2026-01-13

## Research Topics

### 1. AI Agent Optimization (llms.txt Standard)

**Decision**: Implement /llms.txt endpoint following the emerging llms.txt draft specification.

**Rationale**:
- AI agents (GPTBot, ClaudeBot, PerplexityBot) increasingly need structured content for RAG
- The llms.txt format provides machine-readable site summaries
- Better than relying solely on HTML parsing which may miss key information

**Format**:
```text
# RawDrive - AI-Powered Photography Platform

## Overview
RawDrive is a SaaS platform for professional photographers to manage client galleries, deliver photos, and sell prints with AI-powered features.

## Key Pages
- /: Landing page with product overview
- /features: 6 core AI features for photographers
- /pricing: INR pricing plans (Free, Starter ₹500, Pro ₹1,500, Business ₹3,000, Enterprise)
- /blog: Photography tips and platform updates
- /docs: User documentation and API guides

## Contact
- Website: https://www.RawDrive.io
- App: https://app.RawDrive.io
- Email: info@RawDrive.in
```

**Alternatives Considered**:
- ai.txt: Less adopted, no clear standard
- Extended robots.txt: Not designed for content structure
- Schema.org alone: Good but llms.txt adds plain text summary

---

### 2. JSON-LD Schema Markup

**Decision**: Implement Organization, Product, FAQPage, and WebSite schemas using JSON-LD.

**Rationale**:
- Required for rich results in Google Search (star ratings, pricing, FAQ accordions)
- Helps AI agents understand page structure and relationships
- 2026 SEO best practice for Lighthouse 100/100

**Schemas to Implement**:

1. **Organization** (on all pages):
   - name: "RawDrive"
   - url: "https://www.RawDrive.io"
   - logo, sameAs (social links)

2. **Product** (on pricing page):
   - One Product per pricing tier
   - name, description, offers (price in INR)

3. **FAQPage** (on FAQ section):
   - Question/Answer pairs from FAQ data

4. **WebSite** (on homepage):
   - potentialAction: SearchAction for site search

**Implementation**: Create `src/components/seo/JsonLd.astro` component that accepts schema type and data props, renders as `<script type="application/ld+json">`.

**Alternatives Considered**:
- Microdata: More verbose, harder to maintain
- RDFa: Less tooling support
- External JSON files: Harder to keep in sync with page content

---

### 3. Astro SEO Best Practices

**Decision**: Use existing @astrojs/sitemap, add custom schema utilities, optimize meta tags.

**Rationale**:
- Astro's static generation already provides excellent Core Web Vitals
- Sitemap integration is already configured
- Need to add missing elements: JSON-LD, canonical URLs, hreflang (future)

**Optimizations**:

1. **Meta Tags** (already in BaseLayout):
   - title, description, canonical (existing)
   - og:*, twitter:* (existing)
   - Add: article:* for blog posts

2. **Performance**:
   - Enable `astro:prefetch` for faster navigation
   - Use `<Image>` component for responsive images
   - Inline critical CSS (Astro does this by default)

3. **Sitemap** (existing):
   - Generates sitemap-index.xml automatically
   - Includes all static pages and content collections

**Alternatives Considered**:
- astro-seo package: Adds overhead, native approach sufficient
- Next.js: Would require rewrite, Astro is better for static marketing sites

---

### 4. Theme System Implementation

**Decision**: Use existing class-based dark mode with localStorage persistence. Add explicit "system" option.

**Rationale**:
- Already implemented in tailwind.config.mjs (`darkMode: 'class'`)
- Already implemented in BaseLayout with localStorage
- Only need to add visible toggle and "system" option

**Implementation**:

1. **ThemeToggle Component**:
   - Three states: light, dark, system
   - Icons: Sun, Moon, Monitor
   - Persist to localStorage as 'theme' key

2. **Theme Detection**:
   ```js
   // Existing logic in BaseLayout (enhanced)
   const getTheme = () => {
     const stored = localStorage.getItem('theme');
     if (stored === 'dark') return 'dark';
     if (stored === 'light') return 'light';
     // system or not set
     return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
   };
   ```

3. **Transition**:
   - Add `transition-colors duration-200` to html element
   - Prevents flash on theme change

**Alternatives Considered**:
- CSS custom properties only: Doesn't support full Tailwind dark: variant
- Server-side detection: Not applicable for static site, causes hydration mismatch

---

### 5. INR Currency Formatting

**Decision**: Use Intl.NumberFormat with 'en-IN' locale for consistent INR display.

**Rationale**:
- Native JavaScript API, no dependencies
- Handles Indian number formatting (lakhs/crores grouping)
- Consistent symbol placement

**Implementation**:

```typescript
// src/utils/currency.ts
export function formatINR(amount: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

// Usage: formatINR(1500) → "₹1,500"
```

**Pricing Tiers**:
| Tier | Price (INR) | Formatted |
|------|-------------|-----------|
| Free | 0 | ₹0 |
| Starter | 500 | ₹500 |
| Professional | 1500 | ₹1,500 |
| Business | 3000 | ₹3,000 |
| Enterprise | - | Contact us |

**Alternatives Considered**:
- Hardcoded strings: Inflexible, error-prone
- currency.js library: Unnecessary for simple formatting
- Server-side formatting: Not needed for static content

---

### 6. Core Web Vitals Optimization

**Decision**: Leverage Astro's built-in optimizations, add image lazy loading and font optimization.

**Rationale**:
- Astro SSG already provides excellent LCP through static HTML
- Main risks: images, fonts, third-party scripts

**Optimizations**:

1. **Images**:
   - Use Astro `<Image>` component for automatic optimization
   - Set explicit width/height to prevent CLS
   - Use `loading="lazy"` for below-fold images

2. **Fonts**:
   - Preconnect to fonts.googleapis.com (already done)
   - Use `display=swap` (already done)
   - Consider self-hosting Inter for better performance

3. **Scripts**:
   - Theme script is inline and blocking (necessary to prevent flash)
   - All other scripts should be `defer` or `async`
   - No third-party analytics in initial load

4. **CSS**:
   - Astro inlines critical CSS by default
   - Tailwind purges unused CSS

**Targets**:
- LCP: < 2.5s (target: < 1.5s)
- FID: < 100ms (static site, minimal JS)
- CLS: < 0.1 (explicit dimensions on all images)

**Alternatives Considered**:
- Partytown for third-party scripts: Overkill for marketing site
- Critical CSS extraction: Astro handles this automatically

---

## Resolved Clarifications

All technical questions resolved through research. No NEEDS CLARIFICATION items remain.

## Dependencies Identified

1. **@astrojs/sitemap**: Already installed, generates sitemap
2. **Playwright**: Need to add for E2E testing
3. **axe-core**: Need to add for accessibility testing

## Next Steps

Proceed to Phase 1: Design & Contracts
- Create data-model.md with content schemas
- Create contracts/schemas.md with JSON-LD schemas
- Create quickstart.md with development setup

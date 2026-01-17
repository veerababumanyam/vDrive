# Implementation Plan: RawDrive Public Website

**Branch**: `002-public-website` | **Date**: 2026-01-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-public-website/spec.md`

## Summary

Enhance the existing RawDrive public website microservice to production-grade quality with:
- Updated landing page with specific headline/subheadline and trust indicators
- INR pricing (₹) for Indian market with 5 tiers
- 2026 SEO standards including Lighthouse 100/100 and AI agent optimization
- Dark/light/system theme support with persistence
- Enhanced blog and documentation sections using MDX

## Technical Context

**Language/Version**: TypeScript 5.7, Node.js 20+
**Primary Dependencies**: Astro 5.1, React 19, Tailwind CSS 3.4, MDX 4.0
**Storage**: N/A (static site, content in MDX files)
**Testing**: Playwright (E2E), Lighthouse CI (performance/SEO)
**Target Platform**: Web (SSG with hybrid rendering for dynamic routes)
**Project Type**: Web microservice (Astro SSG)
**Performance Goals**: LCP < 2.5s, FID < 100ms, CLS < 0.1, Lighthouse 100/100 SEO
**Constraints**: Static HTML generation, no server-side auth, INR currency only
**Scale/Scope**: ~10 pages (landing, features, pricing, blog index, docs index, dynamic blog/doc pages)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Since the project constitution template is not yet customized, using CLAUDE.md principles:

| Principle | Status | Notes |
|-----------|--------|-------|
| KISS | PASS | Enhancing existing Astro service, no new frameworks |
| DRY | PASS | Reusing existing components and design tokens |
| YAGNI | PASS | Only implementing specified requirements |
| Boy Scout | PASS | Will improve existing components while modifying |
| Error Handling | PASS | Static site with graceful degradation |
| Multi-tenancy | N/A | Public marketing site, no user data |

## Project Structure

### Documentation (this feature)

```text
specs/002-public-website/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (content schemas)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── schemas.md       # JSON-LD and content schemas
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
services/website/
├── astro.config.mjs         # Astro configuration (update port, add integrations)
├── tailwind.config.mjs      # Tailwind config (existing, may extend)
├── package.json             # Dependencies
├── tsconfig.json            # TypeScript config
├── public/
│   ├── robots.txt           # UPDATE: Add AI bot permissions
│   ├── llms.txt             # NEW: AI agent structured content
│   └── favicon.svg          # Existing
├── src/
│   ├── styles/
│   │   └── global.css       # Existing design tokens (may extend)
│   ├── components/
│   │   ├── layout/
│   │   │   └── BaseLayout.astro  # UPDATE: Add JSON-LD, theme toggle
│   │   ├── shared/
│   │   │   ├── Header.astro      # UPDATE: Add theme toggle, nav links
│   │   │   ├── Footer.astro      # UPDATE: Add newsletter, social links
│   │   │   └── ThemeToggle.astro # NEW: Theme switcher component
│   │   ├── landing/
│   │   │   ├── HeroSection.astro    # UPDATE: New headline, trust indicators
│   │   │   ├── FeaturesSection.astro # UPDATE: 6 specific features
│   │   │   ├── PricingSection.astro  # UPDATE: INR pricing, 5 tiers
│   │   │   ├── FAQSection.astro      # UPDATE: FAQ schema
│   │   │   └── CTASection.astro      # Existing (review)
│   │   ├── blog/
│   │   │   ├── BlogCard.astro        # NEW: Blog post card
│   │   │   └── BlogLayout.astro      # NEW: Blog post layout
│   │   ├── docs/
│   │   │   ├── DocsSidebar.astro     # NEW: Docs navigation
│   │   │   └── DocsLayout.astro      # NEW: Docs page layout
│   │   └── seo/
│   │       ├── JsonLd.astro          # NEW: JSON-LD schema component
│   │       └── SchemaOrg.ts          # NEW: Schema generation utilities
│   ├── pages/
│   │   ├── index.astro               # UPDATE: Landing page
│   │   ├── features.astro            # UPDATE: Features page
│   │   ├── pricing.astro             # UPDATE: Pricing page with INR
│   │   ├── blog/
│   │   │   ├── index.astro           # UPDATE: Blog index
│   │   │   └── [...slug].astro       # Existing (review)
│   │   ├── docs/
│   │   │   ├── index.astro           # UPDATE: Docs index
│   │   │   └── [...slug].astro       # Existing (review)
│   │   ├── llms.txt.ts               # NEW: Dynamic llms.txt endpoint
│   │   └── 404.astro                 # NEW: Custom 404 page
│   ├── content/
│   │   ├── config.ts                 # Existing (may extend schema)
│   │   ├── blog/
│   │   │   └── *.mdx                 # Blog posts
│   │   └── docs/
│   │       └── *.mdx                 # Documentation pages
│   ├── data/
│   │   ├── pricing.ts                # NEW: INR pricing data
│   │   ├── features.ts               # NEW: Features data
│   │   └── navigation.ts             # NEW: Navigation config
│   └── utils/
│       ├── schema.ts                 # NEW: JSON-LD schema builders
│       └── seo.ts                    # NEW: SEO utilities
└── tests/
    └── e2e/
        ├── landing.spec.ts           # NEW: Landing page tests
        ├── seo.spec.ts               # NEW: SEO validation tests
        └── accessibility.spec.ts     # NEW: A11y tests
```

**Structure Decision**: Enhance existing Astro microservice at `services/website/`. The structure follows Astro conventions with content collections for MDX, component-based architecture, and utility modules for SEO/schema generation.

## Complexity Tracking

No constitution violations requiring justification. Implementation uses existing patterns.

## Phase 0 Research Summary

See [research.md](./research.md) for detailed findings:

1. **AI Agent Optimization (llms.txt)**: Follow emerging draft standard for structured content
2. **JSON-LD Schemas**: Organization, Product, FAQPage schemas for rich results
3. **Astro SEO Integration**: Use @astrojs/sitemap (existing), add schema utilities
4. **Theme Persistence**: Class-based dark mode with localStorage (already implemented)
5. **INR Formatting**: Use Intl.NumberFormat with 'en-IN' locale

## Phase 1 Design Summary

See [data-model.md](./data-model.md) for content schemas:

1. **PricingPlan**: INR pricing tiers with limits
2. **Feature**: 6 core features with icons and benefits
3. **BlogPost**: Enhanced with author, tags, featured image
4. **DocPage**: With sections, ordering, navigation

See [contracts/schemas.md](./contracts/schemas.md) for JSON-LD schemas.

## Implementation Phases

### Phase 1: Core Updates (P1 User Stories)
1. Update HeroSection with new headline, subheadline, trust indicators
2. Update PricingSection with INR tiers (₹0, ₹500, ₹1,500, ₹3,000, Enterprise)
3. Update FeaturesSection with 6 specified features
4. Add/update Header with theme toggle and nav links
5. Add JSON-LD schemas (Organization, Product, FAQPage)

### Phase 2: SEO & AI Optimization (P2-P3 User Stories)
1. Enhance robots.txt with AI bot permissions
2. Create llms.txt endpoint
3. Add JSON-LD to all pages
4. Optimize Core Web Vitals (images, CSS inlining)
5. Validate Lighthouse 100/100 SEO

### Phase 3: Blog & Docs Enhancement (P2 User Stories)
1. Create BlogCard and BlogLayout components
2. Create DocsSidebar and DocsLayout components
3. Add sample blog posts and documentation pages
4. Implement search within docs (client-side)

### Phase 4: Testing & Polish
1. Playwright E2E tests for all pages
2. Accessibility audit and fixes
3. Performance optimization
4. Mobile responsiveness verification

## Verification

1. **Build**: `cd services/website && npm run build` - must succeed
2. **Dev Server**: `npm run dev` - verify all pages render
3. **Lighthouse**: Run Lighthouse CI, verify SEO 100/100
4. **Accessibility**: Run axe-core, verify zero critical violations
5. **Theme Toggle**: Verify light/dark/system modes work
6. **Pricing**: Verify INR values display correctly (₹500, ₹1,500, etc.)
7. **AI Agents**: Verify /llms.txt and robots.txt accessible

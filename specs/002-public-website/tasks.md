# Tasks: vDrive Public Website

**Input**: Design documents from `/specs/002-public-website/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/schemas.md, research.md, quickstart.md

**Tests**: Optional - not explicitly requested in specification. E2E tests included in Polish phase for production readiness.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, etc.)
- Paths relative to `services/website/`

---

## Phase 1: Setup

**Purpose**: Data files and utility functions needed by multiple user stories

- [x] T001 Create pricing data file with INR tiers in src/data/pricing.ts
- [x] T002 [P] Create features data file with 6 features in src/data/features.ts
- [x] T003 [P] Create navigation config in src/data/navigation.ts
- [x] T004 [P] Create currency formatting utility in src/utils/currency.ts
- [x] T005 [P] Create JSON-LD schema builder utilities in src/utils/schema.ts
- [x] T006 [P] Create SEO helper utilities in src/utils/seo.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared components and infrastructure needed before user story work

**⚠️ CRITICAL**: Complete before starting any user story

- [x] T007 Create JsonLd component for schema injection in src/components/seo/JsonLd.astro
- [x] T008 [P] Create SchemaOrg type definitions in src/components/seo/SchemaOrg.ts
- [x] T009 [P] Create ThemeToggle component with light/dark/system modes in src/components/shared/ThemeToggle.astro
- [x] T010 Update BaseLayout to include JSON-LD slot and skip-to-content in src/components/layout/BaseLayout.astro
- [x] T011 Update Header with theme toggle and navigation links in src/components/shared/Header.astro
- [x] T012 [P] Update Footer with newsletter signup and social links in src/components/shared/Footer.astro
- [x] T013 Update astro.config.mjs to set port 8011 and add prefetch in astro.config.mjs

**Checkpoint**: Foundation ready - user story implementation can begin

---

## Phase 3: User Story 1 - Discover vDrive and Understand Value (Priority: P1) 🎯 MVP

**Goal**: Landing page with compelling headline, subheadline, trust indicators, and hero visual

**Independent Test**: Load homepage, verify headline "Professional Photography Client Galleries Made Simple" displays with trust indicators and CTA buttons

### Implementation for User Story 1

- [x] T014 [US1] Update HeroSection with new headline and subheadline in src/components/landing/HeroSection.astro
- [x] T015 [US1] Add trust indicators (No credit card, Setup in 2 minutes, Cancel anytime) to HeroSection in src/components/landing/HeroSection.astro
- [x] T016 [US1] Add dashboard mockup visual with floating stat cards to HeroSection in src/components/landing/HeroSection.astro
- [x] T017 [US1] Add social proof stats bar (20K+ photographers, 5M+ photos) to HeroSection in src/components/landing/HeroSection.astro
- [x] T018 [US1] Update CTASection with matching messaging in src/components/landing/CTASection.astro
- [x] T019 [US1] Add Organization and WebSite JSON-LD schemas to homepage in src/pages/index.astro
- [x] T020 [US1] Update meta description and OG tags for homepage in src/pages/index.astro
- [ ] T021 [US1] Verify Core Web Vitals targets (LCP < 2.5s) - optimize images if needed

**Checkpoint**: User Story 1 complete - homepage communicates value proposition

---

## Phase 4: User Story 2 - Explore Product Features (Priority: P1)

**Goal**: Features page showcasing 6 core AI-powered capabilities

**Independent Test**: Navigate to /features, verify all 6 features display with icons, descriptions, and benefits

### Implementation for User Story 2

- [x] T022 [US2] Update FeaturesSection to use features data from src/data/features.ts in src/components/landing/FeaturesSection.astro
- [ ] T023 [US2] Create FeatureCard component with icon, gradient, benefits list in src/components/landing/FeatureCard.astro
- [ ] T024 [US2] Add expandable details with use case examples to FeatureCard in src/components/landing/FeatureCard.astro
- [x] T025 [US2] Update features page with FeaturesSection and SEO metadata in src/pages/features.astro
- [x] T026 [US2] Add SoftwareApplication JSON-LD schema to features page in src/pages/features.astro
- [ ] T027 [US2] Ensure keyboard accessibility for feature cards (focus, expand) in src/components/landing/FeatureCard.astro

**Checkpoint**: User Story 2 complete - features page showcases product capabilities

---

## Phase 5: User Story 3 - Evaluate Pricing and Choose Plan (Priority: P1)

**Goal**: Pricing page with 5 INR tiers (Free, Starter, Professional, Business, Enterprise)

**Independent Test**: Navigate to /pricing, verify 5 plans with correct INR values (₹0, ₹500, ₹1,500, ₹3,000, Contact)

### Implementation for User Story 3

- [x] T028 [US3] Update PricingSection to use pricing data from src/data/pricing.ts in src/components/landing/PricingSection.astro
- [x] T029 [US3] Update pricing cards to display INR with Intl.NumberFormat in src/components/landing/PricingSection.astro
- [x] T030 [US3] Add storage/gallery/client limits to pricing cards in src/components/landing/PricingSection.astro
- [x] T031 [US3] Add "Most Popular" badge to Professional tier in src/components/landing/PricingSection.astro
- [x] T032 [US3] Update CTA links to app.vdrive.io/sign-up?plan={id} in src/components/landing/PricingSection.astro
- [x] T033 [US3] Create standalone pricing page with annual/monthly toggle in src/pages/pricing.astro
- [x] T034 [US3] Add Product JSON-LD schemas for each pricing tier in src/pages/pricing.astro
- [x] T035 [US3] Add FAQ section with FAQ schema to pricing page in src/pages/pricing.astro

**Checkpoint**: User Story 3 complete - pricing page enables plan selection

---

## Phase 6: User Story 4 - Learn from Documentation and Guides (Priority: P2)

**Goal**: Documentation section with categorized guides and MDX rendering

**Independent Test**: Navigate to /docs, verify index with categories, click doc to see formatted MDX content

### Implementation for User Story 4

- [ ] T036 [US4] Create DocsSidebar component with section grouping in src/components/docs/DocsSidebar.astro
- [x] T037 [P] [US4] Create DocsLayout component for doc pages in src/components/docs/DocsLayout.astro
- [x] T038 [US4] Update docs index page with category grid in src/pages/docs/index.astro
- [x] T039 [US4] Update docs slug page to use DocsLayout in src/pages/docs/[...slug].astro
- [x] T040 [US4] Extend docs content collection schema with lastUpdated field in src/content/config.ts
- [ ] T041 [P] [US4] Create sample doc: Getting Started with vDrive in src/content/docs/getting-started.mdx
- [ ] T042 [P] [US4] Create sample doc: Creating Your First Gallery in src/content/docs/first-gallery.mdx
- [ ] T043 [P] [US4] Create sample doc: AI Features Guide in src/content/docs/ai-features.mdx
- [ ] T044 [US4] Add client-side search for docs using content collection in src/components/docs/DocsSearch.astro
- [ ] T045 [US4] Add BreadcrumbList JSON-LD schema to doc pages in src/pages/docs/[...slug].astro

**Checkpoint**: User Story 4 complete - documentation helps users learn the platform

---

## Phase 7: User Story 5 - Read Industry Content and Updates (Priority: P2)

**Goal**: Blog section with index, post cards, and MDX content rendering

**Independent Test**: Navigate to /blog, verify post list with titles/dates/images, click post to see full content

### Implementation for User Story 5

- [ ] T046 [US5] Create BlogCard component with title, excerpt, image, date in src/components/blog/BlogCard.astro
- [ ] T047 [P] [US5] Create BlogLayout component for blog posts in src/components/blog/BlogLayout.astro
- [x] T048 [US5] Update blog index page with grid of BlogCards in src/pages/blog/index.astro
- [x] T049 [US5] Update blog slug page to use BlogLayout in src/pages/blog/[...slug].astro
- [ ] T050 [US5] Extend blog content collection schema with readingTime field in src/content/config.ts
- [x] T051 [P] [US5] Create sample post: Getting Started with AI Photo Tagging in src/content/blog/ai-photo-tagging.mdx
- [ ] T052 [P] [US5] Create sample post: 5 Tips for Client Gallery Delivery in src/content/blog/gallery-delivery-tips.mdx
- [x] T053 [US5] Add BlogPosting JSON-LD schema to blog posts in src/pages/blog/[...slug].astro
- [ ] T054 [US5] Add article:* Open Graph tags to blog posts in src/components/blog/BlogLayout.astro

**Checkpoint**: User Story 5 complete - blog provides valuable content for SEO and lead nurturing

---

## Phase 8: User Story 6 - Switch Between Light and Dark Mode (Priority: P2)

**Goal**: Theme toggle with light/dark/system modes, persistence, smooth transitions

**Independent Test**: Click theme toggle, verify colors change immediately with no flash, refresh and verify persisted

### Implementation for User Story 6

- [x] T055 [US6] Update ThemeToggle with three-state toggle (light/dark/system) in src/components/shared/ThemeToggle.astro
- [x] T056 [US6] Add system preference detection using matchMedia in src/components/shared/ThemeToggle.astro
- [x] T057 [US6] Update BaseLayout theme script to handle system mode in src/components/layout/BaseLayout.astro
- [x] T058 [US6] Add transition-colors duration-200 to html element for smooth transitions in src/styles/global.css
- [x] T059 [US6] Verify all components have proper dark: variants in src/styles/global.css
- [ ] T060 [US6] Test contrast ratios meet WCAG 2.1 AA (4.5:1) in dark mode across all pages

**Checkpoint**: User Story 6 complete - users can choose preferred theme

---

## Phase 9: User Story 7 - AI Agent Discovers and Indexes Content (Priority: P3)

**Goal**: AI bot permissions in robots.txt, llms.txt endpoint, comprehensive JSON-LD

**Independent Test**: Fetch /robots.txt and /llms.txt, verify AI bot permissions and structured content

### Implementation for User Story 7

- [x] T061 [US7] Update robots.txt with AI bot permissions (GPTBot, ClaudeBot, PerplexityBot) in public/robots.txt
- [x] T062 [US7] Create llms.txt static file with structured site summary in public/llms.txt
- [ ] T063 [US7] Create dynamic llms.txt endpoint (optional, for future dynamic content) in src/pages/llms.txt.ts
- [x] T064 [US7] Verify all pages include appropriate JSON-LD schemas - audit all page files
- [x] T065 [US7] Add semantic HTML5 landmark roles (main, nav, aside, article) across all pages
- [x] T066 [US7] Optimize meta descriptions for AI summarization (clear, descriptive, 150-160 chars)

**Checkpoint**: User Story 7 complete - AI agents can effectively index and summarize site content

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Quality assurance, performance, and final touches

- [x] T067 [P] Create custom 404 page with helpful navigation in src/pages/404.astro
- [x] T068 [P] Add skip-to-content link for accessibility in src/components/layout/BaseLayout.astro
- [x] T069 [P] Add keyboard focus indicators across all interactive elements in src/styles/global.css
- [ ] T070 Run Lighthouse audit and fix any SEO issues below 100/100
- [ ] T071 [P] Run axe-core accessibility audit and fix critical violations
- [ ] T072 Verify mobile responsiveness on all pages (320px-1440px viewports)
- [ ] T073 [P] Add image lazy loading to below-fold images across all components
- [ ] T074 Verify build succeeds with no errors: npm run build
- [ ] T075 Test full user journey: homepage → features → pricing → sign up redirect

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-9)**: All depend on Foundational phase completion
  - US1, US2, US3 (P1) can run in parallel after Foundation
  - US4, US5, US6 (P2) can run in parallel after Foundation
  - US7 (P3) can run after Foundation
- **Polish (Phase 10)**: Depends on all P1 stories being complete

### User Story Dependencies

| Story | Priority | Depends On | Independent |
|-------|----------|------------|-------------|
| US1 | P1 | Foundational | ✅ Yes |
| US2 | P1 | Foundational | ✅ Yes |
| US3 | P1 | Foundational | ✅ Yes |
| US4 | P2 | Foundational | ✅ Yes |
| US5 | P2 | Foundational | ✅ Yes |
| US6 | P2 | Foundational, US1 (ThemeToggle in header) | ⚠️ Partial |
| US7 | P3 | Foundational | ✅ Yes |

### Within Each User Story

- Data files before components using them
- Components before pages using them
- Core implementation before JSON-LD schemas
- Story complete before validation

### Parallel Opportunities

**Setup Phase (3 parallel tracks):**
```
Track A: T001 (pricing)
Track B: T002 (features), T003 (navigation)
Track C: T004 (currency), T005 (schema), T006 (seo)
```

**Foundational Phase (2 parallel tracks):**
```
Track A: T007 → T010 (JsonLd → BaseLayout)
Track B: T008, T009, T012 (SchemaOrg, ThemeToggle, Footer)
Then: T011, T013 (Header, astro.config)
```

**P1 Stories (3 parallel tracks):**
```
After Foundation complete:
Track A: US1 (T014-T021) - Landing
Track B: US2 (T022-T027) - Features
Track C: US3 (T028-T035) - Pricing
```

**P2 Stories (3 parallel tracks):**
```
After Foundation complete:
Track A: US4 (T036-T045) - Docs
Track B: US5 (T046-T054) - Blog
Track C: US6 (T055-T060) - Theme
```

---

## Implementation Strategy

### Production-Grade Full Implementation (No MVP)

**All 75 tasks required for production deployment.**

**Execution Order:**

1. **Phase 1: Setup** (T001-T006)
   - Create all data files and utilities
   - ~6 tasks, parallelizable

2. **Phase 2: Foundational** (T007-T013)
   - Shared components and infrastructure
   - BLOCKS all user stories
   - ~7 tasks

3. **Phase 3-5: P1 Stories** (T014-T035)
   - US1: Landing page with hero, trust indicators
   - US2: Features page with 6 capabilities
   - US3: Pricing page with INR tiers
   - Can run in 3 parallel tracks
   - ~22 tasks

4. **Phase 6-9: P2/P3 Stories** (T036-T066)
   - US4: Documentation section
   - US5: Blog section
   - US6: Theme toggle (light/dark/system)
   - US7: AI agent optimization (robots.txt, llms.txt)
   - Can run in parallel after P1 or concurrently
   - ~31 tasks

5. **Phase 10: Polish** (T067-T075)
   - 404 page, accessibility, Lighthouse 100/100
   - Mobile responsiveness verification
   - Full user journey test
   - ~9 tasks

**Quality Gates:**
- Lighthouse SEO: 100/100
- Accessibility: Zero critical violations
- Build: Must succeed with no errors
- All 7 user stories: Fully functional and tested

---

## Summary

| Metric | Count |
|--------|-------|
| **Total Tasks** | 75 |
| **Setup Tasks** | 6 |
| **Foundational Tasks** | 7 |
| **US1 Tasks** | 8 |
| **US2 Tasks** | 6 |
| **US3 Tasks** | 8 |
| **US4 Tasks** | 10 |
| **US5 Tasks** | 9 |
| **US6 Tasks** | 6 |
| **US7 Tasks** | 6 |
| **Polish Tasks** | 9 |
| **Parallelizable [P]** | 28 |

### MVP Scope
- **Minimum**: US1 only (Landing page) - 21 tasks
- **Recommended**: US1 + US2 + US3 (All P1 stories) - 35 tasks

### Key Files to Modify
- `src/components/landing/HeroSection.astro` (US1)
- `src/components/landing/FeaturesSection.astro` (US2)
- `src/components/landing/PricingSection.astro` (US3)
- `src/data/pricing.ts` (US3)
- `src/data/features.ts` (US2)
- `public/robots.txt` (US7)
- `public/llms.txt` (US7)

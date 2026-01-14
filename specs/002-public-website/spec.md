# Feature Specification: vDrive Public Website

**Feature Branch**: `002-public-website`
**Created**: 2026-01-13
**Status**: Draft
**Input**: Public Website microservice with Astro SSG for marketing pages, landing, features, pricing (INR), blog, docs - production-grade with 2026 SEO standards, AI agent optimization, mobile-first responsive design, dark/light/system modes

## Overview

The vDrive Public Website is a dedicated marketing microservice that serves as the primary acquisition channel for the photography platform. It provides comprehensive information about vDrive's features, pricing (optimized for Indian market in INR), documentation, and blog content. The website is built for 2026 SEO standards including AI agent crawling compatibility and achieves perfect Lighthouse scores.

**Service Details:**

| Attribute      | Value                                      |
| -------------- | ------------------------------------------ |
| Stack          | Astro 5 (Static Site Generation + Islands) |
| Location       | `services/website`                         |
| Port           | 8011                                       |
| Domain         | www.vdrive.io                              |
| Dependencies   | Backend API (for auth redirect/checkout)   |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover vDrive and Understand Value (Priority: P1)

A professional photographer visits www.vdrive.io for the first time through organic search or referral. They need to quickly understand what vDrive offers and why it's valuable for their business within 30 seconds of landing.

**Why this priority**: First impressions determine conversion. The landing page is the highest-traffic entry point and must immediately communicate value proposition to reduce bounce rate.

**Independent Test**: Can be fully tested by loading the homepage and verifying the headline, subheadline, trust indicators, and hero visuals load correctly within 3 seconds. Delivers clear value communication.

**Acceptance Scenarios**:

1. **Given** a user lands on the homepage, **When** the page loads, **Then** they see the headline "Professional Photography Client Galleries Made Simple" and subheadline prominently displayed.
2. **Given** a user is viewing the homepage, **When** they look at the hero section, **Then** they see trust indicators (No credit card required, Setup in 2 minutes, Cancel anytime) and a dashboard mockup with floating stat cards.
3. **Given** a user on any device, **When** the page loads, **Then** Core Web Vitals meet targets (LCP < 2.5s, FID < 100ms, CLS < 0.1).

---

### User Story 2 - Explore Product Features (Priority: P1)

A photographer wants to understand the specific capabilities of vDrive before signing up. They need detailed information about each feature to evaluate if it meets their business needs.

**Why this priority**: Feature understanding directly influences purchase decisions. Photographers need to validate that vDrive solves their specific pain points.

**Independent Test**: Can be tested by navigating to /features and verifying all 6 highlighted features are displayed with descriptions, benefits, and visual demonstrations.

**Acceptance Scenarios**:

1. **Given** a user is on the features page, **When** they scroll, **Then** they see 6 highlighted features: AI-Powered Gallery Management, Beautiful Client Portal, Print Album Designer, Face Tagging & Search, Client Management, Secure Cloud Storage.
2. **Given** a user clicks on a feature card, **When** the interaction occurs, **Then** they see expanded details including benefits list and use case examples.
3. **Given** a user with assistive technology, **When** navigating features, **Then** all content is accessible via keyboard and screen reader.

---

### User Story 3 - Evaluate Pricing and Choose Plan (Priority: P1)

A photographer ready to consider vDrive wants to see pricing options in their local currency (INR) to make an informed purchasing decision.

**Why this priority**: Pricing transparency in local currency is essential for conversion in the Indian market. Unclear pricing leads to drop-off.

**Independent Test**: Can be tested by navigating to /pricing and verifying all 5 plans display with INR pricing, feature lists, and clear CTAs.

**Acceptance Scenarios**:

1. **Given** a user visits the pricing page, **When** it loads, **Then** they see 5 pricing tiers in INR: Free (₹0), Starter (₹500), Professional (₹1,500), Business (₹3,000), Enterprise (Contact us).
2. **Given** a user views a pricing card, **When** examining details, **Then** they see storage limits, gallery limits, client limits, and included features clearly listed.
3. **Given** a user clicks "Get Started" on a plan, **When** the action occurs, **Then** they are redirected to app.vdrive.io/sign-up with the selected plan pre-populated.

---

### User Story 4 - Learn from Documentation and Guides (Priority: P2)

A potential or existing user wants to learn how to use vDrive effectively through documentation, tutorials, and guides before committing or to maximize their usage.

**Why this priority**: Self-service documentation reduces support burden and helps users get started quickly. Important for user success but secondary to initial conversion.

**Independent Test**: Can be tested by navigating to /docs and verifying documentation content renders correctly with navigation, search, and proper formatting.

**Acceptance Scenarios**:

1. **Given** a user visits /docs, **When** the page loads, **Then** they see a documentation index with categories (Getting Started, Features, API, FAQs).
2. **Given** a user searches documentation, **When** they enter a query, **Then** relevant results are displayed within the documentation section.
3. **Given** a user reads an MDX doc page, **When** viewing content, **Then** code blocks, images, and formatting render correctly.

---

### User Story 5 - Read Industry Content and Updates (Priority: P2)

A photographer interested in photography business tips, vDrive updates, or industry insights wants to consume valuable content that establishes vDrive as a thought leader.

**Why this priority**: Blog content supports SEO, builds trust, and nurtures leads. Secondary to core conversion pages but important for organic traffic.

**Independent Test**: Can be tested by navigating to /blog, viewing blog index, and reading individual blog posts with proper content rendering.

**Acceptance Scenarios**:

1. **Given** a user visits /blog, **When** the page loads, **Then** they see a list of blog posts with titles, excerpts, dates, and featured images.
2. **Given** a user clicks on a blog post, **When** navigating to the post, **Then** the full content renders with MDX support (code blocks, images, embeds).
3. **Given** a search engine crawler, **When** indexing blog posts, **Then** proper meta tags, Open Graph data, and structured data are present.

---

### User Story 6 - Switch Between Light and Dark Mode (Priority: P2)

A user with visual preferences or accessibility needs wants to switch between light mode, dark mode, or system default to optimize their browsing experience.

**Why this priority**: Theme support improves accessibility and user comfort. Standard expectation for modern websites.

**Independent Test**: Can be tested by toggling theme switcher and verifying all page elements correctly adapt their colors and contrast.

**Acceptance Scenarios**:

1. **Given** a user visits the website, **When** their system is in dark mode, **Then** the website defaults to dark mode automatically.
2. **Given** a user clicks the theme toggle, **When** switching from light to dark, **Then** all components transition smoothly without layout shift.
3. **Given** dark mode is active, **When** viewing any page, **Then** text contrast meets WCAG 2.1 AA standards (4.5:1 minimum).

---

### User Story 7 - AI Agent Discovers and Indexes Content (Priority: P3)

AI search agents and RAG systems need to efficiently crawl, understand, and index vDrive's website content for accurate retrieval and summarization.

**Why this priority**: AI agent optimization is emerging best practice for 2026 SEO but less critical than traditional SEO for current traffic.

**Independent Test**: Can be tested by validating robots.txt AI permissions, llms.txt presence, and structured data for RAG compatibility.

**Acceptance Scenarios**:

1. **Given** an AI crawler (GPTBot, ClaudeBot, etc.), **When** accessing robots.txt, **Then** appropriate permissions are granted with rate limiting guidance.
2. **Given** an AI agent, **When** accessing /llms.txt, **Then** they receive structured content summary optimized for RAG ingestion.
3. **Given** any page, **When** checking structured data, **Then** JSON-LD schema includes Organization, Product, FAQPage schemas as appropriate.

---

### Edge Cases

- What happens when a user visits with JavaScript disabled? Static content should render; interactive elements gracefully degrade.
- How does the system handle extremely slow network connections? Images lazy-load, critical CSS inlines, skeleton states show.
- What happens if the backend API is unavailable? Marketing pages function independently; only auth redirects may timeout.
- How does the site handle users from regions outside India? Prices display in INR with clear currency indication.

---

## Requirements *(mandatory)*

### Functional Requirements

**Core Pages:**

- **FR-001**: System MUST display a landing page at `/` with hero section containing headline "Professional Photography Client Galleries Made Simple", subheadline "Share, deliver, and sell your photos with AI-powered galleries. No technical skills needed. Start free, upgrade when you grow.", trust indicators, and dashboard mockup.
- **FR-002**: System MUST display a features page at `/features` showcasing 6 core features with descriptions, benefit lists, and visual elements.
- **FR-003**: System MUST display a pricing page at `/pricing` with 5 tiers in INR: Free (₹0, 1GB, 3 galleries, 5 clients), Starter (₹500, 10GB, 10 galleries, 20 clients), Professional (₹1,500, 100GB, 50 galleries, 100 clients), Business (₹3,000, 1TB, 200 galleries, 500 clients), Enterprise (Contact us).
- **FR-004**: System MUST display a blog index at `/blog` and individual posts at `/blog/[slug]` using MDX content.
- **FR-005**: System MUST display documentation at `/docs` and individual pages at `/docs/[slug]` using MDX content.

**Navigation & Layout:**

- **FR-006**: System MUST provide a consistent header with logo, navigation links (Features, Pricing, Blog, Docs), and CTAs (Sign In, Start Free).
- **FR-007**: System MUST provide a consistent footer with company info, navigation sections, social links, and newsletter signup.
- **FR-008**: System MUST implement responsive navigation with mobile hamburger menu and desktop horizontal nav.

**Theme Support:**

- **FR-009**: System MUST support three theme modes: light, dark, and system (auto-detect).
- **FR-010**: System MUST persist user theme preference across sessions using local storage.
- **FR-011**: System MUST provide a visible theme toggle in the header.

**SEO & Optimization:**

- **FR-012**: System MUST generate static HTML for all marketing pages using Astro SSG.
- **FR-013**: System MUST achieve Lighthouse score of 100 for SEO category.
- **FR-014**: System MUST include JSON-LD structured data for Organization, Product (pricing tiers), and FAQPage schemas.
- **FR-015**: System MUST generate sitemap.xml with all public pages.
- **FR-016**: System MUST provide robots.txt with AI bot permissions (GPTBot, ClaudeBot, PerplexityBot) and rate limiting guidance.

**AI Agent Optimization:**

- **FR-017**: System MUST provide /llms.txt endpoint with structured content summary for AI agents.
- **FR-018**: System MUST include clear, descriptive meta descriptions optimized for AI summarization.
- **FR-019**: System MUST use semantic HTML5 elements for content structure.

**Performance:**

- **FR-020**: System MUST achieve Core Web Vitals targets: LCP < 2.5s, FID < 100ms, CLS < 0.1.
- **FR-021**: System MUST implement image lazy loading for below-fold content.
- **FR-022**: System MUST inline critical CSS for above-fold rendering.

**Accessibility:**

- **FR-023**: System MUST comply with WCAG 2.1 AA standards.
- **FR-024**: System MUST support full keyboard navigation.
- **FR-025**: System MUST provide skip-to-content links.
- **FR-026**: System MUST maintain minimum 4.5:1 contrast ratio for text.

**India-Specific:**

- **FR-027**: System MUST display all prices in Indian Rupees (₹ symbol, INR currency).
- **FR-028**: System MUST include India-relevant contact information.

### Key Entities

- **Page**: Represents a static marketing page (landing, features, pricing) with metadata (title, description, canonical URL, OG image).
- **BlogPost**: Represents a blog article with title, slug, content (MDX), author, publishDate, tags, featuredImage, excerpt.
- **DocPage**: Represents documentation page with title, slug, content (MDX), category, sortOrder, lastUpdated.
- **PricingPlan**: Represents a subscription tier with name, priceINR, features list, storageLimit, galleryLimit, clientLimit, CTA text, isPopular flag.
- **Feature**: Represents a product feature with name, tagline, description, iconName, benefits array, demoImage.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Homepage loads and displays hero content within 2.5 seconds on 3G connection (LCP target).
- **SC-002**: Lighthouse SEO score achieves 100/100.
- **SC-003**: All pages pass WCAG 2.1 AA automated accessibility audit with zero critical violations.
- **SC-004**: First Contentful Paint occurs within 1.8 seconds on desktop.
- **SC-005**: Cumulative Layout Shift remains below 0.1 across all pages.
- **SC-006**: Theme switching completes visually within 200ms with no layout shift.
- **SC-007**: Pricing page displays correct INR values for all 5 plans matching specification.
- **SC-008**: All 6 feature descriptions render correctly on features page.
- **SC-009**: Blog posts render MDX content including code blocks, images, and formatting.
- **SC-010**: AI agents can successfully retrieve structured content from /llms.txt and JSON-LD schemas.

---

## Assumptions

1. **Existing Service**: The website service already exists at `services/website/` with basic Astro, Tailwind, React setup. This specification enhances rather than replaces.
2. **Port Configuration**: Port 8011 will be used per CLAUDE.md documentation (aligning with existing infrastructure).
3. **Content Source**: Blog and documentation content will be authored in MDX format within the service's content collections.
4. **Authentication**: Sign-up and sign-in flows redirect to app.vdrive.io (React app) - no auth implemented in website service.
5. **Payment**: Pricing CTAs link to app.vdrive.io checkout flow - no payment processing in website service.
6. **Analytics**: Google Analytics or similar to be configured via environment variable.
7. **Images**: Dashboard mockups and feature visuals will use placeholder images initially, to be replaced with production assets.
8. **Currency**: INR pricing is primary; multi-currency support is out of scope for initial implementation.
9. **Languages**: English only for initial implementation; i18n is out of scope.

---

## Dependencies

- **Backend API**: Required for auth redirect URLs (sign-in, sign-up endpoints).
- **Design System**: Uses vDrive design tokens from `docs/project-starter-kit/04-DESIGN-SYSTEM.md`.
- **Astro 5**: Static site generator with hybrid rendering capability.
- **MDX**: For blog and documentation content authoring.
- **Tailwind CSS**: For styling with design system tokens.
- **Existing Components**: Leverages existing components in `services/website/src/components/`.

---

## Out of Scope

- User authentication within website service
- Payment processing or checkout flows
- User dashboard or authenticated features
- Multi-language support (i18n)
- Multi-currency support beyond INR
- A/B testing infrastructure
- CMS integration for non-technical content editors
- Contact form backend processing
- Video hosting (embed from YouTube/Vimeo)

# Quickstart: RawDrive Public Website

**Feature**: 002-public-website
**Date**: 2026-01-13

## Prerequisites

- Node.js 20+
- npm 10+
- Git

## Setup

### 1. Navigate to Website Service

```bash
cd services/website
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Configure variables:

```env
# Site URLs
SITE_URL=http://localhost:4321
APP_URL=http://localhost:3000

# Optional: Analytics
# GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
```

### 4. Start Development Server

```bash
npm run dev
```

The website will be available at http://localhost:4321

## Project Structure

```
services/website/
├── astro.config.mjs      # Astro configuration
├── tailwind.config.mjs   # Tailwind CSS config
├── public/               # Static assets
│   ├── robots.txt        # SEO robots
│   └── favicon.svg       # Site favicon
├── src/
│   ├── components/       # Astro/React components
│   │   ├── layout/       # Page layouts
│   │   ├── shared/       # Header, Footer, etc.
│   │   ├── landing/      # Landing page sections
│   │   ├── blog/         # Blog components
│   │   ├── docs/         # Documentation components
│   │   └── seo/          # SEO/Schema components
│   ├── pages/            # Route pages
│   ├── content/          # MDX content collections
│   │   ├── blog/         # Blog posts
│   │   └── docs/         # Documentation
│   ├── data/             # Static data (pricing, features)
│   ├── styles/           # Global CSS
│   └── utils/            # Utility functions
└── tests/                # E2E tests
```

## Common Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server (port 4321) |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |
| `npm run format` | Format with Prettier |

## Adding Content

### Blog Post

1. Create file at `src/content/blog/your-post.mdx`
2. Add frontmatter:

```mdx
---
title: "Your Post Title"
description: "Brief description for SEO"
pubDate: 2026-01-13
author: "RawDrive Team"
image: "/blog/your-image.jpg"
tags: ["Photography", "Tips"]
---

Your content here...
```

### Documentation Page

1. Create file at `src/content/docs/your-doc.mdx`
2. Add frontmatter:

```mdx
---
title: "Documentation Title"
description: "Brief description"
section: "Getting Started"
order: 1
---

Documentation content...
```

## Modifying Pricing

Edit `src/data/pricing.ts`:

```typescript
export const pricingPlans: PricingPlan[] = [
  {
    id: 'starter',
    name: 'Starter',
    priceINR: 500,  // ₹500/month
    // ...
  },
];
```

## Modifying Features

Edit `src/data/features.ts`:

```typescript
export const features: Feature[] = [
  {
    id: 'ai-gallery',
    name: 'AI-Powered Gallery Management',
    icon: 'Images',  // Lucide icon name
    // ...
  },
];
```

## Theme Development

### Toggle Theme

The theme toggle component at `src/components/shared/ThemeToggle.astro` supports:
- Light mode
- Dark mode
- System preference

### Adding Dark Mode Styles

Use Tailwind's `dark:` variant:

```html
<div class="bg-white dark:bg-neutral-900">
  <p class="text-neutral-900 dark:text-white">
    Content
  </p>
</div>
```

## SEO Guidelines

### JSON-LD Schemas

Add schemas via the JsonLd component:

```astro
---
import JsonLd from '@/components/seo/JsonLd.astro';
import { generateOrganizationSchema } from '@/utils/schema';
---

<JsonLd schema={generateOrganizationSchema()} />
```

### Meta Tags

BaseLayout handles meta tags. Pass props:

```astro
<BaseLayout
  title="Page Title"
  description="Page description for SEO"
  image="/og-image.png"
/>
```

## Testing

### Run E2E Tests

```bash
npm run test:e2e
```

### Lighthouse Audit

```bash
npm run lighthouse
```

Or use Chrome DevTools > Lighthouse tab.

### Accessibility Testing

```bash
npm run test:a11y
```

## Deployment

### Build for Production

```bash
npm run build
```

Output is generated in `dist/`.

### Docker

```bash
docker build -t RawDrive-website .
docker run -p 8020:8020 RawDrive-website
```

## Troubleshooting

### Port Already in Use

Change port in `astro.config.mjs`:

```javascript
server: {
  port: 4322,  // or another available port
}
```

### MDX Not Rendering

Ensure:
1. File extension is `.mdx`
2. Frontmatter is valid YAML
3. Content collection is defined in `src/content/config.ts`

### Dark Mode Flash

The theme script in BaseLayout runs before render to prevent flash. If you see flash:
1. Ensure script is `is:inline`
2. Check localStorage key is 'theme'

## Resources

- [Astro Docs](https://docs.astro.build)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [MDX](https://mdxjs.com/docs)
- [Schema.org](https://schema.org)

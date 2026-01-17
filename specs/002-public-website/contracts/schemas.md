# JSON-LD Schemas: RawDrive Public Website

**Feature**: 002-public-website
**Date**: 2026-01-13

## Overview

This document defines the JSON-LD structured data schemas for SEO and AI agent optimization. Each schema follows Schema.org vocabulary and Google's structured data guidelines.

---

## 1. Organization Schema

**Used on**: All pages (via BaseLayout)
**Purpose**: Identify RawDrive as the organization behind the website

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://www.RawDrive.io/#organization",
  "name": "RawDrive",
  "url": "https://www.RawDrive.io",
  "logo": {
    "@type": "ImageObject",
    "url": "https://www.RawDrive.io/logo.png",
    "width": 512,
    "height": 512
  },
  "description": "AI-powered photography platform for professional photographers. Manage galleries, deliver photos, and grow your business.",
  "email": "info@RawDrive.in",
  "telephone": "+49-178-5220533",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "Heinrich Brauns str 17",
    "addressLocality": "Essen",
    "postalCode": "45355",
    "addressCountry": "DE"
  },
  "sameAs": [
    "https://instagram.com/RawDrive",
    "https://twitter.com/RawDrive",
    "https://linkedin.com/company/RawDrive",
    "https://youtube.com/RawDrive"
  ]
}
```

---

## 2. WebSite Schema

**Used on**: Homepage only
**Purpose**: Define site-level information and enable sitelinks search box

```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "@id": "https://www.RawDrive.io/#website",
  "name": "RawDrive",
  "url": "https://www.RawDrive.io",
  "description": "Professional Photography Client Galleries Made Simple",
  "publisher": {
    "@id": "https://www.RawDrive.io/#organization"
  },
  "potentialAction": {
    "@type": "SearchAction",
    "target": {
      "@type": "EntryPoint",
      "urlTemplate": "https://www.RawDrive.io/search?q={search_term_string}"
    },
    "query-input": "required name=search_term_string"
  }
}
```

---

## 3. Product Schemas (Pricing)

**Used on**: /pricing page
**Purpose**: Enable rich results with pricing information

### Free Plan
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "RawDrive Free",
  "description": "Get started with RawDrive - 1GB storage, 3 galleries, 5 clients",
  "brand": {
    "@id": "https://www.RawDrive.io/#organization"
  },
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "INR",
    "availability": "https://schema.org/InStock",
    "url": "https://app.RawDrive.io/sign-up?plan=free"
  }
}
```

### Starter Plan
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "RawDrive Starter",
  "description": "For photographers starting out - 10GB storage, 10 galleries, 20 clients, AI-powered tagging",
  "brand": {
    "@id": "https://www.RawDrive.io/#organization"
  },
  "offers": {
    "@type": "Offer",
    "price": "500",
    "priceCurrency": "INR",
    "priceValidUntil": "2026-12-31",
    "availability": "https://schema.org/InStock",
    "url": "https://app.RawDrive.io/sign-up?plan=starter"
  }
}
```

### Professional Plan (Popular)
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "RawDrive Professional",
  "description": "Most popular choice - 100GB storage, 50 galleries, 100 clients, print album designer, custom domain",
  "brand": {
    "@id": "https://www.RawDrive.io/#organization"
  },
  "offers": {
    "@type": "Offer",
    "price": "1500",
    "priceCurrency": "INR",
    "priceValidUntil": "2026-12-31",
    "availability": "https://schema.org/InStock",
    "url": "https://app.RawDrive.io/sign-up?plan=professional"
  }
}
```

### Business Plan
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "RawDrive Business",
  "description": "For agencies and studios - 1TB storage, 200 galleries, 500 clients, white-label branding, API access",
  "brand": {
    "@id": "https://www.RawDrive.io/#organization"
  },
  "offers": {
    "@type": "Offer",
    "price": "3000",
    "priceCurrency": "INR",
    "priceValidUntil": "2026-12-31",
    "availability": "https://schema.org/InStock",
    "url": "https://app.RawDrive.io/sign-up?plan=business"
  }
}
```

---

## 4. FAQPage Schema

**Used on**: Homepage (FAQ section), /pricing page
**Purpose**: Enable FAQ rich results in search

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "How do I get started with RawDrive?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Sign up for a free account, upload your photos, and create your first gallery. You can upgrade to a paid plan anytime to unlock more features."
      }
    },
    {
      "@type": "Question",
      "name": "Can I try RawDrive for free?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes! Our Free plan includes 1GB storage, 3 galleries, and 5 clients. No credit card required."
      }
    },
    {
      "@type": "Question",
      "name": "How does the AI photo tagging work?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Our AI analyzes your photos and automatically adds tags based on content, scene type, and colors. It also detects and groups faces for easy searching."
      }
    },
    {
      "@type": "Question",
      "name": "Can my clients download photos directly?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes, you control download permissions for each gallery. Clients can download individual photos or entire galleries in high resolution."
      }
    },
    {
      "@type": "Question",
      "name": "Is my data secure?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "We use enterprise-grade encryption, secure cloud infrastructure with automatic backups, and never share your data with third parties."
      }
    },
    {
      "@type": "Question",
      "name": "What payment methods do you accept?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "We accept all major credit and debit cards via Stripe. Enterprise customers can request invoice billing for annual plans."
      }
    }
  ]
}
```

---

## 5. BlogPosting Schema

**Used on**: /blog/[slug] pages
**Purpose**: Enable article rich results

```json
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "{{title}}",
  "description": "{{description}}",
  "image": "{{image}}",
  "datePublished": "{{pubDate}}",
  "dateModified": "{{updatedDate || pubDate}}",
  "author": {
    "@type": "Person",
    "name": "{{author}}"
  },
  "publisher": {
    "@id": "https://www.RawDrive.io/#organization"
  },
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "{{canonicalUrl}}"
  }
}
```

---

## 6. BreadcrumbList Schema

**Used on**: All pages except homepage
**Purpose**: Enable breadcrumb rich results

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "https://www.RawDrive.io"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "{{sectionName}}",
      "item": "https://www.RawDrive.io/{{section}}"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "{{pageTitle}}",
      "item": "{{canonicalUrl}}"
    }
  ]
}
```

---

## Implementation

### Schema Utility Functions

**Location**: `src/utils/schema.ts`

```typescript
export function generateOrganizationSchema() { /* ... */ }
export function generateWebSiteSchema() { /* ... */ }
export function generateProductSchema(plan: PricingPlan) { /* ... */ }
export function generateFAQSchema(faqs: FAQ[]) { /* ... */ }
export function generateBlogPostSchema(post: BlogPost) { /* ... */ }
export function generateBreadcrumbSchema(items: BreadcrumbItem[]) { /* ... */ }
```

### JsonLd Component

**Location**: `src/components/seo/JsonLd.astro`

```astro
---
interface Props {
  schema: object | object[];
}

const { schema } = Astro.props;
const schemas = Array.isArray(schema) ? schema : [schema];
---

{schemas.map((s) => (
  <script type="application/ld+json" set:html={JSON.stringify(s)} />
))}
```

### Usage in Pages

```astro
---
import JsonLd from '@/components/seo/JsonLd.astro';
import { generateOrganizationSchema, generateWebSiteSchema } from '@/utils/schema';
---

<JsonLd schema={[
  generateOrganizationSchema(),
  generateWebSiteSchema(),
]} />
```

---

## Validation

Use Google's Rich Results Test to validate:
- https://search.google.com/test/rich-results

Test each schema type:
1. Organization - verify logo, sameAs links
2. WebSite - verify search action
3. Product - verify price, currency (INR)
4. FAQPage - verify questions render
5. BlogPosting - verify article details
6. BreadcrumbList - verify hierarchy

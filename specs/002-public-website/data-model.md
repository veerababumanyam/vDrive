# Data Model: RawDrive Public Website

**Feature**: 002-public-website
**Date**: 2026-01-13

## Overview

The public website uses static content and TypeScript data files. No database is required. Content is managed through:
1. **MDX Content Collections**: Blog posts and documentation pages
2. **TypeScript Data Files**: Pricing, features, navigation configuration

---

## Content Collections (Astro)

### BlogPost Collection

**Location**: `src/content/blog/*.mdx`
**Schema**: `src/content/config.ts`

```typescript
const blogCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.date(),
    updatedDate: z.date().optional(),
    author: z.string().default('RawDrive Team'),
    authorImage: z.string().optional(),
    image: z.string().optional(),           // Featured image URL
    tags: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
    readingTime: z.number().optional(),     // Minutes (calculated)
  }),
});
```

**Example Frontmatter**:
```yaml
---
title: "Getting Started with AI Photo Tagging"
description: "Learn how RawDrive's AI automatically tags and organizes your photos"
pubDate: 2026-01-10
author: "RawDrive Team"
image: "/blog/ai-tagging-hero.jpg"
tags: ["AI", "Organization", "Tutorial"]
---
```

---

### DocsCollection

**Location**: `src/content/docs/*.mdx`
**Schema**: `src/content/config.ts`

```typescript
const docsCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    order: z.number().default(999),         // Sort order within section
    section: z.string().optional(),         // Grouping: "Getting Started", "Features", etc.
    draft: z.boolean().default(false),
    lastUpdated: z.date().optional(),
  }),
});
```

**Example Frontmatter**:
```yaml
---
title: "Introduction to RawDrive"
description: "Overview of the RawDrive photography platform"
order: 1
section: "Getting Started"
lastUpdated: 2026-01-13
---
```

---

## TypeScript Data Structures

### PricingPlan

**Location**: `src/data/pricing.ts`

```typescript
export interface PricingPlan {
  id: string;
  name: string;
  description: string;
  priceINR: number | null;  // null for Enterprise (Contact us)
  priceMonthly: number | null;
  priceYearly: number | null;

  // Limits
  storageGB: number | null;  // null = unlimited
  galleries: number | null;  // null = unlimited
  clients: number | null;    // null = unlimited

  // Features
  features: string[];
  highlighted: string[];     // Key differentiators to emphasize

  // UI
  isPopular: boolean;
  ctaText: string;
  ctaLink: string;
}

export const pricingPlans: PricingPlan[] = [
  {
    id: 'free',
    name: 'Free',
    description: 'Get started with RawDrive',
    priceINR: 0,
    priceMonthly: 0,
    priceYearly: 0,
    storageGB: 1,
    galleries: 3,
    clients: 5,
    features: [
      '1 GB storage',
      '3 galleries',
      '5 clients',
      'Basic client portal',
      'Email support',
    ],
    highlighted: ['1 GB storage'],
    isPopular: false,
    ctaText: 'Start Free',
    ctaLink: 'https://app.RawDrive.io/sign-up?plan=free',
  },
  {
    id: 'starter',
    name: 'Starter',
    description: 'For photographers starting out',
    priceINR: 500,
    priceMonthly: 500,
    priceYearly: 5000,
    storageGB: 10,
    galleries: 10,
    clients: 20,
    features: [
      '10 GB storage',
      '10 galleries',
      '20 clients',
      'AI-powered tagging',
      'Custom watermarks',
      'Email support',
    ],
    highlighted: ['10 GB storage', 'AI-powered tagging'],
    isPopular: false,
    ctaText: 'Get Started',
    ctaLink: 'https://app.RawDrive.io/sign-up?plan=starter',
  },
  {
    id: 'professional',
    name: 'Professional',
    description: 'Most popular choice',
    priceINR: 1500,
    priceMonthly: 1500,
    priceYearly: 15000,
    storageGB: 100,
    galleries: 50,
    clients: 100,
    features: [
      '100 GB storage',
      '50 galleries',
      '100 clients',
      'Print album designer',
      'Custom domain',
      'Video support',
      'Priority support',
    ],
    highlighted: ['100 GB storage', 'Print album designer', 'Custom domain'],
    isPopular: true,
    ctaText: 'Get Started',
    ctaLink: 'https://app.RawDrive.io/sign-up?plan=professional',
  },
  {
    id: 'business',
    name: 'Business',
    description: 'For agencies and studios',
    priceINR: 3000,
    priceMonthly: 3000,
    priceYearly: 30000,
    storageGB: 1000,
    galleries: 200,
    clients: 500,
    features: [
      '1 TB storage',
      '200 galleries',
      '500 clients',
      'White-label branding',
      'API access',
      '10 team members',
      'Priority support',
    ],
    highlighted: ['1 TB storage', 'White-label branding', 'API access'],
    isPopular: false,
    ctaText: 'Get Started',
    ctaLink: 'https://app.RawDrive.io/sign-up?plan=business',
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    description: 'Custom solutions',
    priceINR: null,
    priceMonthly: null,
    priceYearly: null,
    storageGB: null,
    galleries: null,
    clients: null,
    features: [
      'Custom storage',
      'Unlimited galleries',
      'Unlimited clients',
      'White-label branding',
      'API access',
      'Unlimited team members',
      'Dedicated support',
      'Custom integrations',
    ],
    highlighted: ['Custom storage', 'Dedicated support', 'Custom integrations'],
    isPopular: false,
    ctaText: 'Contact Sales',
    ctaLink: '/contact',
  },
];
```

---

### Feature

**Location**: `src/data/features.ts`

```typescript
export interface Feature {
  id: string;
  name: string;
  tagline: string;
  description: string;
  icon: string;           // Lucide icon name
  gradient: string;       // Tailwind gradient classes
  benefits: string[];
  stat: {
    value: string;
    label: string;
  };
}

export const features: Feature[] = [
  {
    id: 'ai-gallery',
    name: 'AI-Powered Gallery Management',
    tagline: 'Organize effortlessly',
    description: 'Organize thousands of photos effortlessly with intelligent tagging and smart search. Our AI understands your photos and makes them searchable.',
    icon: 'Images',
    gradient: 'from-violet-500 to-purple-600',
    benefits: [
      'Automatic photo tagging with AI',
      'Smart search by content, colors, faces',
      'Bulk organization & batch editing',
      'Custom collections & albums',
    ],
    stat: { value: '10x', label: 'Faster organization' },
  },
  {
    id: 'client-portal',
    name: 'Beautiful Client Portal',
    tagline: 'Premium experience',
    description: 'Give your clients a premium experience with branded galleries they can access anytime. Your brand, your style, your client\'s delight.',
    icon: 'Users',
    gradient: 'from-cyan-500 to-blue-600',
    benefits: [
      'Password-protected galleries',
      'Custom branding & colors',
      'Easy photo downloads',
      'Favorites & selection tools',
    ],
    stat: { value: '99%', label: 'Client satisfaction' },
  },
  {
    id: 'album-designer',
    name: 'Print Album Designer',
    tagline: 'Create stunning albums',
    description: 'Create stunning print-ready albums with our intuitive drag-and-drop designer. From concept to print in minutes, not hours.',
    icon: 'BookOpen',
    gradient: 'from-pink-500 to-rose-600',
    benefits: [
      'Intuitive drag-and-drop interface',
      '50+ pre-made templates',
      'AI auto-layout suggestions',
      'Print-ready PDF exports',
    ],
    stat: { value: '40%', label: 'More album sales' },
  },
  {
    id: 'face-tagging',
    name: 'Face Tagging & Search',
    tagline: 'Find anyone instantly',
    description: 'Automatically detect and tag faces, making it easy to find specific people across all your galleries. Perfect for events.',
    icon: 'Sparkles',
    gradient: 'from-amber-500 to-orange-600',
    benefits: [
      'Automatic face detection',
      'Person-based search',
      'Group similar faces together',
      'Privacy controls built-in',
    ],
    stat: { value: '1M+', label: 'Faces tagged' },
  },
  {
    id: 'client-management',
    name: 'Client Management',
    tagline: 'Stay organized',
    description: 'Keep track of all your clients, projects, and deliveries in one organized dashboard. Never lose track of a project again.',
    icon: 'UserCheck',
    gradient: 'from-emerald-500 to-teal-600',
    benefits: [
      'Detailed client profiles',
      'Project tracking & timelines',
      'Communication history',
      'Invoice & payment integration',
    ],
    stat: { value: '50%', label: 'Time saved' },
  },
  {
    id: 'cloud-storage',
    name: 'Secure Cloud Storage',
    tagline: 'Enterprise-grade security',
    description: 'Store and deliver your photos with enterprise-grade security and lightning-fast delivery via our global CDN.',
    icon: 'Cloud',
    gradient: 'from-blue-500 to-indigo-600',
    benefits: [
      'Unlimited bandwidth',
      'Global CDN delivery',
      'Automatic backups',
      '99.9% uptime guarantee',
    ],
    stat: { value: '99.9%', label: 'Uptime SLA' },
  },
];
```

---

### Navigation

**Location**: `src/data/navigation.ts`

```typescript
export interface NavItem {
  label: string;
  href: string;
  external?: boolean;
}

export interface FooterSection {
  title: string;
  links: NavItem[];
}

export const mainNav: NavItem[] = [
  { label: 'Features', href: '/features' },
  { label: 'Pricing', href: '/pricing' },
  { label: 'Blog', href: '/blog' },
  { label: 'Docs', href: '/docs' },
];

export const footerSections: FooterSection[] = [
  {
    title: 'Product',
    links: [
      { label: 'Features', href: '/features' },
      { label: 'Pricing', href: '/pricing' },
      { label: 'Gallery Examples', href: '/examples' },
      { label: 'Integrations', href: '/integrations' },
    ],
  },
  {
    title: 'Company',
    links: [
      { label: 'About Us', href: '/about' },
      { label: 'Blog', href: '/blog' },
      { label: 'Careers', href: '/careers' },
      { label: 'Contact', href: '/contact' },
    ],
  },
  {
    title: 'Resources',
    links: [
      { label: 'Documentation', href: '/docs' },
      { label: 'Help Center', href: '/help' },
      { label: 'Community', href: '/community' },
    ],
  },
  {
    title: 'Legal',
    links: [
      { label: 'Privacy Policy', href: '/privacy' },
      { label: 'Terms of Service', href: '/terms' },
      { label: 'Security', href: '/security' },
    ],
  },
];

export const socialLinks = [
  { label: 'Instagram', href: 'https://instagram.com/RawDrive', icon: 'Instagram' },
  { label: 'Twitter', href: 'https://twitter.com/RawDrive', icon: 'Twitter' },
  { label: 'LinkedIn', href: 'https://linkedin.com/company/RawDrive', icon: 'LinkedIn' },
  { label: 'YouTube', href: 'https://youtube.com/RawDrive', icon: 'Youtube' },
];
```

---

## Relationships

```
                    ┌─────────────┐
                    │   Website   │
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │    Pages    │ │   Content   │ │    Data     │
    │  (Astro)    │ │ Collections │ │   (TS)      │
    └─────────────┘ └─────────────┘ └─────────────┘
           │               │               │
           │        ┌──────┴──────┐        │
           │        ▼             ▼        │
           │  ┌──────────┐ ┌──────────┐    │
           │  │   Blog   │ │   Docs   │    │
           │  │  Posts   │ │  Pages   │    │
           │  └──────────┘ └──────────┘    │
           │                               │
           │     ┌─────────────────────────┤
           ▼     ▼                         ▼
    ┌─────────────────────────────────────────────┐
    │              Static HTML Output             │
    │         (Generated at build time)           │
    └─────────────────────────────────────────────┘
```

---

## State Transitions

Not applicable - static content, no user state.

---

## Validation Rules

1. **Blog Posts**:
   - title: Required, max 100 characters
   - description: Required, 50-160 characters (SEO meta)
   - pubDate: Required, valid date
   - image: If provided, must be valid URL or path

2. **Documentation**:
   - title: Required, max 100 characters
   - description: Required for SEO
   - section: If provided, must match predefined sections

3. **Pricing Plans**:
   - priceINR: Number >= 0 or null for Enterprise
   - features: At least 3 items
   - ctaLink: Valid URL or path

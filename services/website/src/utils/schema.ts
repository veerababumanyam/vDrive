/**
 * JSON-LD Schema builders for SEO
 * Following Schema.org specifications
 */

import type { PricingPlan } from '../data/pricing';

const SITE_URL = import.meta.env.SITE_URL || 'https://www.vdrive.io';
const APP_URL = import.meta.env.APP_URL || 'https://app.vdrive.io';

/**
 * Organization schema for the company
 */
export function generateOrganizationSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'vDrive',
    url: SITE_URL,
    logo: `${SITE_URL}/logo.svg`,
    description:
      'Professional photography client gallery platform with AI-powered organization, beautiful client portals, and secure cloud storage.',
    foundingDate: '2024',
    sameAs: [
      'https://twitter.com/vdriveio',
      'https://instagram.com/vdriveio',
      'https://linkedin.com/company/vdriveio',
      'https://youtube.com/@vdriveio',
    ],
    contactPoint: {
      '@type': 'ContactPoint',
      contactType: 'customer service',
      email: 'support@vdrive.io',
      availableLanguage: 'English',
    },
    address: {
      '@type': 'PostalAddress',
      addressCountry: 'IN',
    },
  };
}

/**
 * WebSite schema for search features
 */
export function generateWebSiteSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'vDrive',
    url: SITE_URL,
    description:
      'Professional Photography Client Galleries Made Simple. Share, deliver, and sell your photos with AI-powered galleries.',
    potentialAction: {
      '@type': 'SearchAction',
      target: {
        '@type': 'EntryPoint',
        urlTemplate: `${SITE_URL}/search?q={search_term_string}`,
      },
      'query-input': 'required name=search_term_string',
    },
  };
}

/**
 * SoftwareApplication schema for the product
 */
export function generateSoftwareApplicationSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'vDrive',
    applicationCategory: 'PhotographyApplication',
    operatingSystem: 'Web',
    url: SITE_URL,
    description:
      'AI-powered photography client gallery platform for professional photographers.',
    offers: {
      '@type': 'AggregateOffer',
      priceCurrency: 'INR',
      lowPrice: '0',
      highPrice: '3000',
      offerCount: '5',
    },
    aggregateRating: {
      '@type': 'AggregateRating',
      ratingValue: '4.9',
      ratingCount: '500',
      bestRating: '5',
      worstRating: '1',
    },
    featureList: [
      'AI-Powered Gallery Management',
      'Beautiful Client Portal',
      'Print Album Designer',
      'Face Tagging & Search',
      'Client Management',
      'Secure Cloud Storage',
    ],
  };
}

/**
 * Product schema for a pricing plan
 */
export function generateProductSchema(plan: PricingPlan) {
  return {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: `vDrive ${plan.name}`,
    description: plan.description,
    brand: {
      '@type': 'Brand',
      name: 'vDrive',
    },
    offers: {
      '@type': 'Offer',
      price: plan.priceINR ?? undefined,
      priceCurrency: 'INR',
      priceValidUntil: new Date(
        Date.now() + 365 * 24 * 60 * 60 * 1000
      ).toISOString(),
      availability: 'https://schema.org/InStock',
      url: `${APP_URL}${plan.ctaLink}`,
    },
  };
}

/**
 * FAQPage schema for FAQ sections
 */
export function generateFAQSchema(
  faqs: Array<{ question: string; answer: string }>
) {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqs.map((faq) => ({
      '@type': 'Question',
      name: faq.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: faq.answer,
      },
    })),
  };
}

/**
 * BlogPosting schema for blog posts
 */
export function generateBlogPostingSchema(post: {
  title: string;
  description: string;
  slug: string;
  pubDate: Date;
  updatedDate?: Date;
  author: string;
  image?: string;
  tags?: string[];
}) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: post.title,
    description: post.description,
    url: `${SITE_URL}/blog/${post.slug}`,
    datePublished: post.pubDate.toISOString(),
    dateModified: (post.updatedDate ?? post.pubDate).toISOString(),
    author: {
      '@type': 'Person',
      name: post.author,
    },
    publisher: {
      '@type': 'Organization',
      name: 'vDrive',
      logo: {
        '@type': 'ImageObject',
        url: `${SITE_URL}/logo.svg`,
      },
    },
    image: post.image ? `${SITE_URL}${post.image}` : undefined,
    keywords: post.tags?.join(', '),
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': `${SITE_URL}/blog/${post.slug}`,
    },
  };
}

/**
 * BreadcrumbList schema for navigation
 */
export function generateBreadcrumbSchema(
  items: Array<{ name: string; url?: string }>
) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: item.url ? `${SITE_URL}${item.url}` : undefined,
    })),
  };
}

/**
 * Article schema for documentation pages
 */
export function generateArticleSchema(doc: {
  title: string;
  description: string;
  slug: string;
  section: string;
  lastUpdated?: Date;
}) {
  return {
    '@context': 'https://schema.org',
    '@type': 'TechArticle',
    headline: doc.title,
    description: doc.description,
    url: `${SITE_URL}/docs/${doc.slug}`,
    dateModified: doc.lastUpdated?.toISOString(),
    author: {
      '@type': 'Organization',
      name: 'vDrive',
    },
    publisher: {
      '@type': 'Organization',
      name: 'vDrive',
      logo: {
        '@type': 'ImageObject',
        url: `${SITE_URL}/logo.svg`,
      },
    },
    articleSection: doc.section,
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': `${SITE_URL}/docs/${doc.slug}`,
    },
  };
}

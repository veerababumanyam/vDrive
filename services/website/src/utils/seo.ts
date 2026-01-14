/**
 * SEO utility functions for meta tags and Open Graph
 */

const SITE_URL = import.meta.env.SITE_URL || 'https://www.vdrive.io';
const SITE_NAME = 'vDrive';
const DEFAULT_DESCRIPTION =
  'Professional Photography Client Galleries Made Simple. Share, deliver, and sell your photos with AI-powered galleries. No technical skills needed.';
const DEFAULT_IMAGE = '/og-image.png';

export interface SEOProps {
  title?: string;
  description?: string;
  image?: string;
  url?: string;
  type?: 'website' | 'article';
  publishedTime?: Date;
  modifiedTime?: Date;
  author?: string;
  tags?: string[];
  noindex?: boolean;
}

/**
 * Generate page title with site name suffix
 */
export function generateTitle(title?: string): string {
  if (!title) {
    return `${SITE_NAME} - Professional Photography Client Galleries`;
  }
  return `${title} | ${SITE_NAME}`;
}

/**
 * Generate canonical URL
 */
export function generateCanonicalUrl(path: string): string {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${SITE_URL}${cleanPath}`;
}

/**
 * Generate absolute image URL
 */
export function generateImageUrl(image?: string): string {
  if (!image) {
    return `${SITE_URL}${DEFAULT_IMAGE}`;
  }
  if (image.startsWith('http')) {
    return image;
  }
  return `${SITE_URL}${image.startsWith('/') ? image : `/${image}`}`;
}

/**
 * Truncate description to optimal length (150-160 chars)
 */
export function truncateDescription(text: string, maxLength = 160): string {
  if (text.length <= maxLength) {
    return text;
  }
  const truncated = text.substring(0, maxLength - 3);
  const lastSpace = truncated.lastIndexOf(' ');
  return `${truncated.substring(0, lastSpace)}...`;
}

/**
 * Generate all meta tags for a page
 */
export function generateMetaTags(props: SEOProps): Record<string, string> {
  const {
    title,
    description = DEFAULT_DESCRIPTION,
    image,
    url = '/',
    type = 'website',
    publishedTime,
    modifiedTime,
    author,
    tags,
    noindex = false,
  } = props;

  const fullTitle = generateTitle(title);
  const canonicalUrl = generateCanonicalUrl(url);
  const imageUrl = generateImageUrl(image);
  const truncatedDescription = truncateDescription(description);

  const meta: Record<string, string> = {
    // Basic meta
    title: fullTitle,
    description: truncatedDescription,

    // Open Graph
    'og:title': fullTitle,
    'og:description': truncatedDescription,
    'og:image': imageUrl,
    'og:url': canonicalUrl,
    'og:type': type,
    'og:site_name': SITE_NAME,
    'og:locale': 'en_US',

    // Twitter Card
    'twitter:card': 'summary_large_image',
    'twitter:site': '@vdriveio',
    'twitter:creator': '@vdriveio',
    'twitter:title': fullTitle,
    'twitter:description': truncatedDescription,
    'twitter:image': imageUrl,

    // Canonical
    canonical: canonicalUrl,
  };

  // Article-specific tags
  if (type === 'article') {
    if (publishedTime) {
      meta['article:published_time'] = publishedTime.toISOString();
    }
    if (modifiedTime) {
      meta['article:modified_time'] = modifiedTime.toISOString();
    }
    if (author) {
      meta['article:author'] = author;
    }
    if (tags?.length) {
      meta['article:tag'] = tags.join(', ');
    }
  }

  // Robots
  if (noindex) {
    meta.robots = 'noindex, nofollow';
  } else {
    meta.robots = 'index, follow';
  }

  return meta;
}

/**
 * Generate structured data script tag content
 */
export function generateStructuredDataScript(schema: object): string {
  return JSON.stringify(schema);
}

/**
 * Calculate reading time for content
 */
export function calculateReadingTime(content: string): number {
  const wordsPerMinute = 200;
  const wordCount = content.split(/\s+/).length;
  const minutes = Math.ceil(wordCount / wordsPerMinute);
  return Math.max(1, minutes);
}

/**
 * Generate sitemap priority based on page type
 */
export function getSitemapPriority(path: string): number {
  if (path === '/') return 1.0;
  if (path === '/features' || path === '/pricing') return 0.9;
  if (path.startsWith('/blog/') || path.startsWith('/docs/')) return 0.7;
  if (path === '/blog' || path === '/docs') return 0.8;
  return 0.5;
}

/**
 * Generate sitemap changefreq based on page type
 */
export function getSitemapChangeFreq(
  path: string
): 'always' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'never' {
  if (path === '/') return 'daily';
  if (path === '/blog' || path === '/docs') return 'daily';
  if (path.startsWith('/blog/')) return 'weekly';
  if (path.startsWith('/docs/')) return 'weekly';
  return 'monthly';
}

/**
 * Default SEO values for common pages
 */
export const pageSEO = {
  home: {
    title: undefined, // Uses default
    description:
      'Professional Photography Client Galleries Made Simple. Share, deliver, and sell your photos with AI-powered galleries. Start free, upgrade when you grow.',
  },
  features: {
    title: 'Features',
    description:
      'Discover vDrive features: AI-powered gallery management, beautiful client portals, print album designer, face tagging, client management, and secure cloud storage.',
  },
  pricing: {
    title: 'Pricing',
    description:
      'Simple, transparent pricing for photographers. Start free, upgrade as you grow. Plans from Free to Enterprise with INR pricing for Indian photographers.',
  },
  blog: {
    title: 'Blog',
    description:
      'Photography tips, industry insights, and vDrive updates. Learn how to grow your photography business and deliver exceptional client experiences.',
  },
  docs: {
    title: 'Documentation',
    description:
      'Learn how to use vDrive with comprehensive guides, tutorials, and API documentation. Get started in minutes.',
  },
};

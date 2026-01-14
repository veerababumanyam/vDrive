/**
 * Dynamic llms.txt Endpoint
 *
 * Generates structured content for AI agents/LLMs to understand the vDrive platform.
 * This endpoint can be extended to include dynamic content like:
 * - Latest blog posts
 * - Current pricing (from data file)
 * - Feature updates
 *
 * @see https://llmstxt.org/ for specification
 */
import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { pricingPlans, type PricingPlan } from '../data/pricing';

export const GET: APIRoute = async () => {
  // Fetch latest blog posts for dynamic content
  const blogPosts = await getCollection('blog', ({ data }) => !data.draft);
  const recentPosts = blogPosts
    .sort((a, b) => b.data.pubDate.getTime() - a.data.pubDate.getTime())
    .slice(0, 5);

  // Fetch documentation for dynamic content
  const docs = await getCollection('docs', ({ data }) => !data.draft);
  const docSections = [...new Set(docs.map((d) => d.data.section || 'General'))];

  // Format storage amount for display
  const formatStorage = (gb: number | null): string => {
    if (gb === null) return 'Unlimited';
    if (gb >= 1000) return `${gb / 1000} TB`;
    return `${gb} GB`;
  };

  // Format pricing from data file
  const pricingSection = pricingPlans
    .map((plan: PricingPlan) => {
      const price =
        plan.priceINR === 0
          ? 'Free'
          : plan.priceINR === null
            ? 'Custom pricing'
            : `Rs.${plan.priceINR.toLocaleString('en-IN')}/month`;
      const storage = formatStorage(plan.storageGB);
      const galleries = plan.galleries === null ? 'Unlimited' : plan.galleries;
      const clients = plan.clients === null ? 'Unlimited' : plan.clients;
      return `- **${plan.name}** (${price}): ${storage} storage, ${galleries} galleries, ${clients} clients`;
    })
    .join('\n');

  // Format recent blog posts
  const blogSection = recentPosts
    .map((post) => `- [${post.data.title}](/blog/${post.slug}) - ${post.data.description}`)
    .join('\n');

  // Format documentation sections
  const docsSection = docSections.map((section) => `- ${section}`).join('\n');

  const content = `# vDrive - Professional Photography Client Galleries

> vDrive is an AI-powered photography platform that helps professional photographers manage, deliver, and sell their work. Built for wedding photographers, portrait studios, and event photographers.

## Product Overview

vDrive provides:
- **AI-Powered Gallery Management**: Automatically tag, sort, and organize thousands of photos
- **Beautiful Client Portals**: Branded galleries with magic links and password protection
- **Face Recognition**: Let clients find themselves in hundreds of photos instantly
- **Print Album Designer**: Create professional print-ready albums with AI-suggested layouts
- **Client Management**: CRM features for tracking shoots, contracts, and communication
- **Secure Cloud Storage**: Enterprise-grade encryption with Cloudflare R2

## Pricing (INR)

${pricingSection}

All paid plans include a 14-day free trial. Annual billing saves 17%.

## Key Features

### AI & Automation
- Smart photo tagging with scene, object, and color detection
- Face detection and grouping across all galleries
- Intelligent search across your entire library
- Batch operations with AI assistance

### Client Experience
- Customizable gallery themes matching your brand
- Magic links with optional password protection
- Client proofing with favorites and comments
- Download permissions (full-res, web-quality, or none)

### Business Tools
- Team collaboration with role-based access
- Analytics dashboard for gallery engagement
- Webhooks and REST API for integrations
- White-label branding for studios

## Target Users

1. **Wedding Photographers**: Managing 2000+ photos per event, delivering client galleries
2. **Portrait Studios**: Multiple sessions daily, client proofing and selection
3. **Event Photographers**: Corporate events, conferences, parties
4. **Photography Studios**: Teams needing collaboration and white-label features

## Documentation Sections

${docsSection}

## Recent Blog Posts

${blogSection}

## Technical Details

- **Platform**: Web-based (app.vdrive.io), mobile-responsive
- **Storage**: Cloudflare R2 with global CDN
- **Security**: AES-256 encryption, TLS 1.3, SOC 2 compliant
- **API**: REST API available on Business+ plans

## Links

- Website: https://www.vdrive.io
- Features: https://www.vdrive.io/features
- Pricing: https://www.vdrive.io/pricing
- Documentation: https://www.vdrive.io/docs
- Blog: https://www.vdrive.io/blog
- Sign Up: https://app.vdrive.io/sign-up
- Contact: support@vdrive.io

## Company

vDrive is headquartered in India and serves photographers worldwide. Founded in 2024, we're committed to helping photographers save time and impress their clients with beautiful, AI-powered galleries.

---
Last updated: ${new Date().toISOString().split('T')[0]}
`;

  return new Response(content, {
    status: 200,
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'public, max-age=3600', // Cache for 1 hour
    },
  });
};

/**
 * Navigation configuration for header and footer
 */

export interface NavItem {
  label: string;
  href: string;
  external?: boolean;
  highlight?: boolean;
}

export interface NavSection {
  title: string;
  items: NavItem[];
}

/**
 * Main header navigation items
 */
export const headerNav: NavItem[] = [
  { label: 'Features', href: '/features' },
  { label: 'Pricing', href: '/pricing' },
  { label: 'Blog', href: '/blog' },
  { label: 'Docs', href: '/docs' },
];

/**
 * Header CTA buttons
 */
export const headerCTAs = {
  signIn: {
    label: 'Sign In',
    href: '/sign-in',
    variant: 'ghost' as const,
  },
  signUp: {
    label: 'Start Free',
    href: '/sign-up',
    variant: 'primary' as const,
  },
};

/**
 * Footer navigation sections
 */
export const footerNav: NavSection[] = [
  {
    title: 'Product',
    items: [
      { label: 'Features', href: '/features' },
      { label: 'Pricing', href: '/pricing' },
      { label: 'Integrations', href: '/integrations' },
      { label: 'Changelog', href: '/changelog' },
    ],
  },
  {
    title: 'Resources',
    items: [
      { label: 'Documentation', href: '/docs' },
      { label: 'Blog', href: '/blog' },
      { label: 'Help Center', href: '/docs/help' },
      { label: 'API Reference', href: '/docs/api' },
    ],
  },
  {
    title: 'Company',
    items: [
      { label: 'About', href: '/about' },
      { label: 'Careers', href: '/careers' },
      { label: 'Press', href: '/press' },
      { label: 'Contact', href: '/contact' },
    ],
  },
  {
    title: 'Legal',
    items: [
      { label: 'Privacy Policy', href: '/privacy' },
      { label: 'Terms of Service', href: '/terms' },
      { label: 'Cookie Policy', href: '/cookies' },
      { label: 'GDPR', href: '/gdpr' },
    ],
  },
];

/**
 * Social media links
 */
export const socialLinks = [
  {
    name: 'Twitter',
    href: 'https://twitter.com/RawDriveio',
    icon: 'Twitter',
  },
  {
    name: 'Instagram',
    href: 'https://instagram.com/RawDriveio',
    icon: 'Instagram',
  },
  {
    name: 'LinkedIn',
    href: 'https://linkedin.com/company/RawDriveio',
    icon: 'Linkedin',
  },
  {
    name: 'YouTube',
    href: 'https://youtube.com/@RawDriveio',
    icon: 'Youtube',
  },
];

/**
 * Mobile navigation items (combines header nav with CTAs)
 */
export const mobileNav: NavItem[] = [
  ...headerNav,
  { label: 'Sign In', href: '/sign-in' },
  { label: 'Start Free', href: '/sign-up', highlight: true },
];

/**
 * Breadcrumb helpers
 */
export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export function generateBreadcrumbs(path: string): BreadcrumbItem[] {
  const segments = path.split('/').filter(Boolean);
  const breadcrumbs: BreadcrumbItem[] = [{ label: 'Home', href: '/' }];

  let currentPath = '';
  for (const segment of segments) {
    currentPath += `/${segment}`;
    const label = segment
      .split('-')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
    breadcrumbs.push({ label, href: currentPath });
  }

  // Remove href from last item (current page)
  if (breadcrumbs.length > 1) {
    delete breadcrumbs[breadcrumbs.length - 1].href;
  }

  return breadcrumbs;
}

/**
 * Pricing data for RawDrive subscription tiers
 * All prices in Indian Rupees (INR)
 */

export interface PricingPlan {
  id: string;
  name: string;
  description: string;
  priceINR: number | null; // null for Enterprise (Contact us)
  priceINRAnnual: number | null; // Annual price (if applicable)
  storageGB: number | null; // null for unlimited
  galleries: number | null; // null for unlimited
  clients: number | null; // null for unlimited
  features: string[];
  isPopular: boolean;
  ctaText: string;
  ctaLink: string;
}

export const pricingPlans: PricingPlan[] = [
  {
    id: 'free',
    name: 'Free',
    description: 'Perfect for getting started',
    priceINR: 0,
    priceINRAnnual: 0,
    storageGB: 1,
    galleries: 3,
    clients: 5,
    features: [
      'Up to 3 galleries',
      '1 GB storage',
      '5 client accounts',
      'Basic gallery sharing',
      'Mobile-friendly galleries',
      'Email support',
    ],
    isPopular: false,
    ctaText: 'Get Started Free',
    ctaLink: '/sign-up?plan=free',
  },
  {
    id: 'starter',
    name: 'Starter',
    description: 'For photographers just starting out',
    priceINR: 500,
    priceINRAnnual: 5000, // ~17% discount
    storageGB: 10,
    galleries: 10,
    clients: 20,
    features: [
      'Up to 10 galleries',
      '10 GB storage',
      '20 client accounts',
      'Custom branding',
      'Download tracking',
      'Basic AI tagging',
      'Priority email support',
    ],
    isPopular: false,
    ctaText: 'Start Free Trial',
    ctaLink: '/sign-up?plan=starter',
  },
  {
    id: 'professional',
    name: 'Professional',
    description: 'Most popular for growing photographers',
    priceINR: 1500,
    priceINRAnnual: 15000, // ~17% discount
    storageGB: 100,
    galleries: 50,
    clients: 100,
    features: [
      'Up to 50 galleries',
      '100 GB storage',
      '100 client accounts',
      'Advanced AI tagging & face detection',
      'Print album designer',
      'Custom domain support',
      'Client favorites & selections',
      'Advanced analytics',
      'Priority support',
    ],
    isPopular: true,
    ctaText: 'Start Free Trial',
    ctaLink: '/sign-up?plan=professional',
  },
  {
    id: 'business',
    name: 'Business',
    description: 'For established photography studios',
    priceINR: 3000,
    priceINRAnnual: 30000, // ~17% discount
    storageGB: 1000, // 1 TB
    galleries: 200,
    clients: 500,
    features: [
      'Up to 200 galleries',
      '1 TB storage',
      '500 client accounts',
      'Everything in Professional',
      'Team collaboration (up to 5 users)',
      'White-label client portal',
      'API access',
      'Advanced integrations',
      'Dedicated account manager',
    ],
    isPopular: false,
    ctaText: 'Start Free Trial',
    ctaLink: '/sign-up?plan=business',
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    description: 'For large studios and agencies',
    priceINR: null,
    priceINRAnnual: null,
    storageGB: null, // Unlimited
    galleries: null, // Unlimited
    clients: null, // Unlimited
    features: [
      'Unlimited galleries',
      'Unlimited storage',
      'Unlimited client accounts',
      'Everything in Business',
      'Unlimited team members',
      'Custom integrations',
      'SLA guarantee',
      'On-premise deployment option',
      'Dedicated success manager',
      '24/7 phone support',
    ],
    isPopular: false,
    ctaText: 'Contact Sales',
    ctaLink: '/contact?plan=enterprise',
  },
];

/**
 * Get a pricing plan by ID
 */
export function getPlanById(id: string): PricingPlan | undefined {
  return pricingPlans.find((plan) => plan.id === id);
}

/**
 * Get all paid plans (excluding free)
 */
export function getPaidPlans(): PricingPlan[] {
  return pricingPlans.filter((plan) => plan.priceINR !== 0);
}

/**
 * Get the popular/recommended plan
 */
export function getPopularPlan(): PricingPlan | undefined {
  return pricingPlans.find((plan) => plan.isPopular);
}

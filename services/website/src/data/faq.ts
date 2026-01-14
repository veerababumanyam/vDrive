/**
 * FAQ data for landing page and JSON-LD schema
 */

export interface FAQ {
  question: string;
  answer: string;
}

export const faqData: FAQ[] = [
  {
    question: 'How does the 14-day free trial work?',
    answer:
      'Start using vDrive immediately with full access to all features. No credit card required. At the end of your trial, choose a plan that fits your needs or your data will be safely stored for 30 days.',
  },
  {
    question: 'Can I upgrade or downgrade my plan?',
    answer:
      "Yes, you can change your plan at any time. When upgrading, you'll get immediate access to new features. When downgrading, changes take effect at the next billing cycle.",
  },
  {
    question: 'How secure are my photos?',
    answer:
      'We use enterprise-grade AES-256 encryption for all files at rest and TLS 1.3 for data in transit. Your photos are stored on Cloudflare R2 with automatic backups and 99.99% uptime.',
  },
  {
    question: 'Can my clients download full-resolution photos?',
    answer:
      'Absolutely! You control download permissions for each gallery. Enable full-resolution downloads, limit to web-quality, or disable downloads entirely. You can also require password protection.',
  },
  {
    question: 'How does face recognition work?',
    answer:
      'Our AI analyzes photos to detect and group faces. Clients can upload a selfie to find all photos of themselves across the entire gallery. It works on events with thousands of photos.',
  },
  {
    question: 'Do you offer a white-label option?',
    answer:
      'Yes! Business plan subscribers can fully customize their client galleries with their own branding, colors, and domain. Your clients will see your brand, not ours.',
  },
  {
    question: 'What happens to my photos if I cancel?',
    answer:
      "Your photos remain accessible for 30 days after cancellation. You can export everything before your account is closed. We'll never delete your data without notice.",
  },
  {
    question: 'Is there an API for developers?',
    answer:
      'Yes, Business and Enterprise plans include full API access for custom integrations. Build workflows with your existing tools, automate gallery creation, or integrate with your website.',
  },
  {
    question: 'What payment methods do you accept?',
    answer:
      'We accept all major credit cards, debit cards, UPI, and net banking for Indian customers. Enterprise customers can also pay via invoice with NET-30 terms.',
  },
  {
    question: 'Can I bring my own storage (BYOS)?',
    answer:
      'Yes! Enterprise customers can connect their own Cloudflare R2, AWS S3, or Google Cloud Storage buckets. This gives you full control over your data while using vDrive for management.',
  },
];

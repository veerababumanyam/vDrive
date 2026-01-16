/**
 * Features data for RawDrive product showcase
 * 6 core AI-powered capabilities
 */

export interface Feature {
  id: string;
  name: string;
  tagline: string;
  description: string;
  icon: string; // Lucide icon name
  gradient: string; // Tailwind gradient classes
  benefits: string[];
  useCases: string[];
}

export const features: Feature[] = [
  {
    id: 'ai-gallery',
    name: 'AI-Powered Gallery Management',
    tagline: 'Organize thousands of photos in seconds',
    description:
      'Let AI automatically sort, tag, and organize your photos. Our smart algorithms detect scenes, objects, and colors to create a perfectly organized library without manual effort.',
    icon: 'Sparkles',
    gradient: 'from-primary-500 to-accent-500',
    benefits: [
      'Auto-categorize photos by event, scene, and subject',
      'Smart duplicate detection saves storage',
      'Intelligent search across your entire library',
      'Batch operations with AI assistance',
    ],
    useCases: [
      'Wedding photographers with 2000+ photos per event',
      'Portrait studios managing multiple sessions daily',
      'Event photographers handling corporate shoots',
    ],
  },
  {
    id: 'client-portal',
    name: 'Beautiful Client Portal',
    tagline: 'Impress clients from the first click',
    description:
      'Deliver stunning, branded galleries that make your work shine. Clients can view, favorite, and download their photos through an elegant, mobile-friendly experience.',
    icon: 'Users',
    gradient: 'from-accent-500 to-primary-500',
    benefits: [
      'Custom branding with your logo and colors',
      'Password-protected private galleries',
      'Mobile-optimized viewing experience',
      'Client notifications and activity tracking',
    ],
    useCases: [
      'Wedding photographers sharing preview galleries',
      'Portrait studios delivering final images',
      'Commercial photographers with corporate clients',
    ],
  },
  {
    id: 'print-designer',
    name: 'Print Album Designer',
    tagline: 'Design beautiful albums in minutes',
    description:
      'Create professional print-ready albums with our intuitive drag-and-drop designer. AI suggests layouts based on your photos, or customize every detail to perfection.',
    icon: 'BookImage',
    gradient: 'from-success-500 to-primary-500',
    benefits: [
      'AI-powered layout suggestions',
      'Drag-and-drop photo arrangement',
      'Print-ready PDF export',
      'Integration with popular print labs',
    ],
    useCases: [
      'Wedding album creation and sales',
      'Baby and family photo books',
      'Corporate event commemorative albums',
    ],
  },
  {
    id: 'face-tagging',
    name: 'Face Tagging & Search',
    tagline: 'Find anyone in seconds',
    description:
      'Advanced facial recognition automatically identifies and groups people across all your galleries. Clients can easily find every photo of themselves or loved ones.',
    icon: 'ScanFace',
    gradient: 'from-warning-500 to-error-500',
    benefits: [
      'Automatic face detection and grouping',
      'Cross-gallery person search',
      'Privacy-focused on-device processing',
      'Manual tagging override for accuracy',
    ],
    useCases: [
      'Wedding guests finding their photos',
      'School photography with hundreds of students',
      'Corporate events with multiple attendees',
    ],
  },
  {
    id: 'client-management',
    name: 'Client Management',
    tagline: 'Your photography CRM',
    description:
      'Keep all client information, communication, and project history in one place. Track shoots, manage contracts, and maintain lasting client relationships.',
    icon: 'Contact',
    gradient: 'from-primary-600 to-primary-400',
    benefits: [
      'Centralized client database',
      'Project and shoot tracking',
      'Communication history',
      'Automated reminders and follow-ups',
    ],
    useCases: [
      'Tracking repeat wedding clients',
      'Managing corporate client accounts',
      'Building long-term client relationships',
    ],
  },
  {
    id: 'cloud-storage',
    name: 'Secure Cloud Storage',
    tagline: 'Your photos, protected forever',
    description:
      'Enterprise-grade cloud storage keeps your photos safe, backed up, and accessible from anywhere. Never worry about losing your work to hardware failures.',
    icon: 'CloudUpload',
    gradient: 'from-neutral-600 to-neutral-400',
    benefits: [
      'Automatic cloud backup',
      'End-to-end encryption',
      'Multi-region redundancy',
      'Bring your own storage (BYOS) option',
    ],
    useCases: [
      'Photographers transitioning from external drives',
      'Studios needing team access to files',
      'Backup solution for peace of mind',
    ],
  },
];

/**
 * Get a feature by ID
 */
export function getFeatureById(id: string): Feature | undefined {
  return features.find((feature) => feature.id === id);
}

/**
 * Get features grouped by category (for features page)
 */
export function getFeaturesByCategory(): Record<string, Feature[]> {
  return {
    'AI & Automation': features.filter((f) =>
      ['ai-gallery', 'face-tagging'].includes(f.id)
    ),
    'Client Experience': features.filter((f) =>
      ['client-portal', 'print-designer'].includes(f.id)
    ),
    'Business Tools': features.filter((f) =>
      ['client-management', 'cloud-storage'].includes(f.id)
    ),
  };
}

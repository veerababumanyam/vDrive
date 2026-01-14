/**
 * TypeScript type definitions for Schema.org structured data
 * Used with JSON-LD for SEO
 */

// Base types
export interface Thing {
  '@type': string;
  name?: string;
  description?: string;
  url?: string;
  image?: string | ImageObject;
}

export interface ImageObject {
  '@type': 'ImageObject';
  url: string;
  width?: number;
  height?: number;
}

// Organization
export interface Organization extends Thing {
  '@type': 'Organization';
  '@context'?: string;
  logo?: string | ImageObject;
  sameAs?: string[];
  contactPoint?: ContactPoint;
  address?: PostalAddress;
  foundingDate?: string;
}

export interface ContactPoint {
  '@type': 'ContactPoint';
  contactType: string;
  email?: string;
  telephone?: string;
  availableLanguage?: string | string[];
}

export interface PostalAddress {
  '@type': 'PostalAddress';
  streetAddress?: string;
  addressLocality?: string;
  addressRegion?: string;
  postalCode?: string;
  addressCountry?: string;
}

// WebSite
export interface WebSite extends Thing {
  '@type': 'WebSite';
  '@context'?: string;
  potentialAction?: SearchAction;
}

export interface SearchAction {
  '@type': 'SearchAction';
  target: EntryPoint;
  'query-input': string;
}

export interface EntryPoint {
  '@type': 'EntryPoint';
  urlTemplate: string;
}

// Product
export interface Product extends Thing {
  '@type': 'Product';
  '@context'?: string;
  brand?: Brand;
  offers?: Offer | AggregateOffer;
  aggregateRating?: AggregateRating;
}

export interface Brand {
  '@type': 'Brand';
  name: string;
}

export interface Offer {
  '@type': 'Offer';
  price?: number | string;
  priceCurrency?: string;
  priceValidUntil?: string;
  availability?: string;
  url?: string;
}

export interface AggregateOffer {
  '@type': 'AggregateOffer';
  priceCurrency: string;
  lowPrice: string;
  highPrice: string;
  offerCount: string;
}

export interface AggregateRating {
  '@type': 'AggregateRating';
  ratingValue: string;
  ratingCount: string;
  bestRating?: string;
  worstRating?: string;
}

// SoftwareApplication
export interface SoftwareApplication extends Thing {
  '@type': 'SoftwareApplication';
  '@context'?: string;
  applicationCategory?: string;
  operatingSystem?: string;
  offers?: Offer | AggregateOffer;
  aggregateRating?: AggregateRating;
  featureList?: string[];
}

// FAQPage
export interface FAQPage {
  '@type': 'FAQPage';
  '@context'?: string;
  mainEntity: Question[];
}

export interface Question {
  '@type': 'Question';
  name: string;
  acceptedAnswer: Answer;
}

export interface Answer {
  '@type': 'Answer';
  text: string;
}

// BlogPosting
export interface BlogPosting extends Thing {
  '@type': 'BlogPosting';
  '@context'?: string;
  headline: string;
  datePublished: string;
  dateModified?: string;
  author: Person | Organization;
  publisher?: Organization;
  keywords?: string;
  mainEntityOfPage?: WebPage;
}

export interface Person extends Thing {
  '@type': 'Person';
}

export interface WebPage {
  '@type': 'WebPage';
  '@id': string;
}

// Article (TechArticle for docs)
export interface TechArticle extends Thing {
  '@type': 'TechArticle';
  '@context'?: string;
  headline: string;
  dateModified?: string;
  author: Person | Organization;
  publisher?: Organization;
  articleSection?: string;
  mainEntityOfPage?: WebPage;
}

// BreadcrumbList
export interface BreadcrumbList {
  '@type': 'BreadcrumbList';
  '@context'?: string;
  itemListElement: ListItem[];
}

export interface ListItem {
  '@type': 'ListItem';
  position: number;
  name: string;
  item?: string;
}

// Type guards
export function isOrganization(thing: Thing): thing is Organization {
  return thing['@type'] === 'Organization';
}

export function isProduct(thing: Thing): thing is Product {
  return thing['@type'] === 'Product';
}

export function isBlogPosting(thing: Thing): thing is BlogPosting {
  return thing['@type'] === 'BlogPosting';
}

/**
 * Currency formatting utilities for INR
 */

/**
 * Format a number as Indian Rupees
 * Uses proper Indian number system (lakhs, crores)
 *
 * @param amount - The amount to format
 * @param options - Formatting options
 * @returns Formatted currency string (e.g., "₹1,500")
 */
export function formatINR(
  amount: number | null,
  options: {
    showSymbol?: boolean;
    showDecimals?: boolean;
    compact?: boolean;
  } = {}
): string {
  const { showSymbol = true, showDecimals = false, compact = false } = options;

  if (amount === null) {
    return showSymbol ? '₹Custom' : 'Custom';
  }

  if (amount === 0) {
    return showSymbol ? '₹0' : '0';
  }

  const formatter = new Intl.NumberFormat('en-IN', {
    style: showSymbol ? 'currency' : 'decimal',
    currency: 'INR',
    minimumFractionDigits: showDecimals ? 2 : 0,
    maximumFractionDigits: showDecimals ? 2 : 0,
    notation: compact ? 'compact' : 'standard',
  });

  return formatter.format(amount);
}

/**
 * Format price with period (monthly/annually)
 *
 * @param amount - The amount to format
 * @param period - 'month' or 'year'
 * @returns Formatted string (e.g., "₹1,500/mo")
 */
export function formatPriceWithPeriod(
  amount: number | null,
  period: 'month' | 'year'
): string {
  if (amount === null) {
    return 'Contact us';
  }

  const formatted = formatINR(amount);
  const suffix = period === 'month' ? '/mo' : '/yr';

  return `${formatted}${suffix}`;
}

/**
 * Calculate annual savings percentage
 *
 * @param monthly - Monthly price
 * @param annual - Annual price
 * @returns Savings percentage (e.g., 17)
 */
export function calculateAnnualSavings(
  monthly: number,
  annual: number
): number {
  if (monthly === 0 || annual === 0) return 0;
  const monthlyTotal = monthly * 12;
  const savings = ((monthlyTotal - annual) / monthlyTotal) * 100;
  return Math.round(savings);
}

/**
 * Format storage size
 *
 * @param gb - Size in gigabytes
 * @returns Formatted string (e.g., "100 GB", "1 TB", "Unlimited")
 */
export function formatStorage(gb: number | null): string {
  if (gb === null) {
    return 'Unlimited';
  }

  if (gb >= 1000) {
    return `${gb / 1000} TB`;
  }

  return `${gb} GB`;
}

/**
 * Format limit numbers
 *
 * @param count - Count to format
 * @returns Formatted string (e.g., "50", "Unlimited")
 */
export function formatLimit(count: number | null): string {
  if (count === null) {
    return 'Unlimited';
  }

  return count.toLocaleString('en-IN');
}

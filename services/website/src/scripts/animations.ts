/**
 * Mobile-First Scroll Animations
 * Intersection Observer for reveal animations
 * Respects prefers-reduced-motion
 */

export function initScrollAnimations() {
  // Respect user preference for reduced motion
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (prefersReducedMotion) {
    // Remove animation classes for users who prefer reduced motion
    document.querySelectorAll('.scroll-fade-up, .scroll-scale-in').forEach((el) => {
      el.classList.add('visible');
    });
    return;
  }

  // Intersection Observer options
  const observerOptions: IntersectionObserverInit = {
    root: null,
    rootMargin: '0px 0px -100px 0px', // Trigger 100px before element enters viewport
    threshold: 0.1, // Trigger when 10% of element is visible
  };

  // Create observer
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        // Unobserve after animation to improve performance
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  // Observe all elements with scroll animation classes
  document.querySelectorAll('.scroll-fade-up, .scroll-scale-in').forEach((el) => {
    observer.observe(el);
  });
}

/**
 * Initialize touch ripple effect for buttons
 * Mobile-optimized tap feedback
 */
export function initRippleEffect() {
  document.addEventListener('click', (e) => {
    const target = e.target as HTMLElement;
    const rippleElement = target.closest('.ripple');

    if (!rippleElement) return;

    // Create ripple element
    const ripple = document.createElement('span');
    const rect = rippleElement.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;

    ripple.style.cssText = `
      position: absolute;
      width: ${size}px;
      height: ${size}px;
      left: ${x}px;
      top: ${y}px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.6);
      pointer-events: none;
      transform: scale(0);
      animation: ripple 0.6s ease-out;
    `;

    rippleElement.appendChild(ripple);

    // Remove ripple after animation
    setTimeout(() => ripple.remove(), 600);
  });
}

/**
 * Initialize all animations
 */
export function initAnimations() {
  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      initScrollAnimations();
      initRippleEffect();
    });
  } else {
    initScrollAnimations();
    initRippleEffect();
  }
}

// Auto-initialize if script is loaded
if (typeof window !== 'undefined') {
  initAnimations();
}

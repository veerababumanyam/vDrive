/**
 * Professional-Grade Animation Controllers
 * Scroll animations, magnetic effects, parallax, and particle systems
 */

// ============================================
// Scroll Animation Controller
// ============================================
class ScrollAnimationController {
  constructor() {
    this.observerOptions = {
      root: null,
      rootMargin: '0px 0px -100px 0px',
      threshold: 0.1,
    };

    this.init();
  }

  init() {
    // Observe all elements with scroll animations
    const elements = document.querySelectorAll('.scroll-fade-up, .scroll-scale-in');

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');

          // Optional: unobserve after animation
          // observer.unobserve(entry.target);
        }
      });
    }, this.observerOptions);

    elements.forEach((el) => observer.observe(el));
  }
}

// ============================================
// Magnetic Cursor Controller
// ============================================
class MagneticCursorController {
  constructor() {
    this.magneticElements = document.querySelectorAll('.hover-magnetic-advanced');
    this.init();
  }

  init() {
    this.magneticElements.forEach((element) => {
      element.addEventListener('mousemove', (e) => {
        const rect = element.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        const deltaX = (e.clientX - centerX) * 0.2;
        const deltaY = (e.clientY - centerY) * 0.2;

        element.style.setProperty('--mouse-x', `${deltaX}px`);
        element.style.setProperty('--mouse-y', `${deltaY}px`);

        element.style.transform = `translate(${deltaX}px, ${deltaY}px) scale(1.02)`;
      });

      element.addEventListener('mouseleave', () => {
        element.style.transform = '';
        element.style.setProperty('--mouse-x', '0px');
        element.style.setProperty('--mouse-y', '0px');
      });
    });
  }
}

// ============================================
// Parallax Controller
// ============================================
class ParallaxController {
  constructor() {
    this.parallaxElements = document.querySelectorAll('[data-parallax]');
    this.init();
  }

  init() {
    if (this.parallaxElements.length === 0) return;

    window.addEventListener('scroll', () => {
      const scrolled = window.pageYOffset;

      this.parallaxElements.forEach((element) => {
        const speed = parseFloat(element.dataset.parallax) || 0.5;
        const yPos = -(scrolled * speed);
        element.style.transform = `translate3d(0, ${yPos}px, 0)`;
      });
    });
  }
}

// ============================================
// Initialize All Controllers
// ============================================
function initAnimationControllers() {
  // Check for reduced motion preference
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (prefersReducedMotion) {
    console.log('Reduced motion enabled - skipping complex animations');
    return;
  }

  // Initialize controllers
  new ScrollAnimationController();
  new MagneticCursorController();
  new ParallaxController();

  console.log('Animation controllers initialized');
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAnimationControllers);
} else {
  initAnimationControllers();
}

// Re-initialize on Astro view transitions
document.addEventListener('astro:after-swap', initAnimationControllers);

// Export for manual initialization if needed
export { ScrollAnimationController, MagneticCursorController, ParallaxController };

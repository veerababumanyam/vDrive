/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    // Mobile-first breakpoints
    screens: {
      'xs': '360px',   // Standard phones
      'sm': '480px',   // Large phones, small tablets
      'md': '768px',   // Tablets
      'lg': '1024px',  // Small laptops, tablets landscape
      'xl': '1280px',  // Desktops
      '2xl': '1536px', // Large desktops
    },
    extend: {
      colors: {
        // Primary - Sky Blue
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
          950: '#082f49',
        },
        // Accent - Apple Blue (clean, professional)
        accent: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          950: '#172554',
        },
        // Neutral - Slate Gray (kept for light mode)
        neutral: {
          50: '#fafafa',
          100: '#f5f5f5',
          200: '#e5e5e5',
          300: '#d4d4d4',
          400: '#a3a3a3',
          500: '#737373',
          600: '#525252',
          700: '#404040',
          800: '#262626',
          900: '#171717',
          950: '#0a0a0a',
        },
        // Warm - Custom warm neutrals for dark mode (espresso/taupe undertones)
        warm: {
          50: '#f7f6f5',
          100: '#eceae9',
          200: '#d9d5d3',
          300: '#b5afac',
          400: '#8a8380',
          500: '#6b6562',
          600: '#524d4a',
          700: '#3d3835',
          800: '#2a2523',
          900: '#1a1614',
          950: '#0f0d0c',
        },
        // Status Colors
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
        },
        error: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
        },
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
        },
        // Surface colors for glass effects
        surface: {
          dark: 'rgba(15, 13, 12, 0.8)',
          glass: 'rgba(255, 255, 255, 0.1)',
          'glass-strong': 'rgba(255, 255, 255, 0.15)',
          'glass-border': 'rgba(255, 255, 255, 0.2)',
          'glass-border-strong': 'rgba(255, 255, 255, 0.3)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Cal Sans', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.875rem' }],
        // Fluid typography (use with text-[length:var(--text-fluid-*)])
        'fluid-xs': 'var(--text-fluid-xs)',
        'fluid-sm': 'var(--text-fluid-sm)',
        'fluid-base': 'var(--text-fluid-base)',
        'fluid-lg': 'var(--text-fluid-lg)',
        'fluid-xl': 'var(--text-fluid-xl)',
        'fluid-2xl': 'var(--text-fluid-2xl)',
        'fluid-3xl': 'var(--text-fluid-3xl)',
        'fluid-4xl': 'var(--text-fluid-4xl)',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '112': '28rem',
        '128': '32rem',
        // Fluid spacing
        'fluid-1': 'clamp(0.25rem, 0.5vw, 0.5rem)',
        'fluid-2': 'clamp(0.5rem, 1vw, 1rem)',
        'fluid-4': 'clamp(1rem, 2vw, 2rem)',
        'fluid-8': 'clamp(2rem, 4vw, 4rem)',
        'fluid-16': 'clamp(4rem, 8vw, 8rem)',
        // Safe area (use with padding utilities)
        'safe-top': 'env(safe-area-inset-top)',
        'safe-bottom': 'env(safe-area-inset-bottom)',
        'safe-left': 'env(safe-area-inset-left)',
        'safe-right': 'env(safe-area-inset-right)',
      },
      height: {
        'screen-dynamic': '100dvh',
        'screen-small': '100svh',
        'screen-large': '100lvh',
      },
      minHeight: {
        'screen-dynamic': '100dvh',
        'touch': '44px',
      },
      minWidth: {
        'touch': '44px',
      },
      animation: {
        // Entrance animations
        'fade-in': 'fadeIn 0.5s ease-out',
        'fade-up': 'fadeUp 0.5s ease-out',
        'fade-in-up': 'fadeInUp 0.6s ease-out forwards',
        'fade-in-down': 'fadeInDown 0.6s ease-out forwards',
        'fade-in-scale': 'fadeInScale 0.5s ease-out forwards',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'slide-in-left': 'slideInLeft 0.3s ease-out',
        'slide-up-mobile': 'slideUpMobile 0.4s ease-out forwards',
        // Continuous animations
        'float': 'float 6s ease-in-out infinite',
        'pulse-glow': 'pulseGlow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-subtle': 'bounceSubtle 2s ease-in-out infinite',
        // Futuristic effects
        'aurora': 'aurora 15s ease-in-out infinite',
        'aurora-slow': 'aurora 25s ease-in-out infinite',
        'shimmer': 'shimmer 2s infinite',
        'morph': 'morph 15s ease-in-out infinite',
        'gradient-x': 'gradientX 3s ease infinite',
        'gradient-xy': 'gradientXY 5s ease infinite',
        'spin-slow': 'spin 8s linear infinite',
        'neon-pulse': 'neonPulse 2s ease-in-out infinite',
      },
      keyframes: {
        // Entrance keyframes
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeInDown: {
          '0%': { opacity: '0', transform: 'translateY(-20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeInScale: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        slideInLeft: {
          '0%': { opacity: '0', transform: 'translateX(-20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        slideUpMobile: {
          '0%': { opacity: '0', transform: 'translateY(100%)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        // Continuous keyframes
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        bounceSubtle: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-5px)' },
        },
        // Futuristic keyframes
        aurora: {
          '0%, 100%': { transform: 'translate(0, 0) rotate(0deg)' },
          '50%': { transform: 'translate(30px, -30px) rotate(180deg)' },
        },
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        morph: {
          '0%, 100%': { borderRadius: '60% 40% 30% 70% / 60% 30% 70% 40%' },
          '50%': { borderRadius: '30% 60% 70% 40% / 50% 60% 30% 60%' },
        },
        gradientX: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        gradientXY: {
          '0%, 100%': { backgroundPosition: '0% 0%' },
          '50%': { backgroundPosition: '100% 100%' },
        },
        neonPulse: {
          '0%, 100%': {
            opacity: '1',
            boxShadow: '0 0 20px var(--tw-shadow-color, rgba(59, 130, 246, 0.5)), 0 0 40px var(--tw-shadow-color, rgba(59, 130, 246, 0.3))'
          },
          '50%': {
            opacity: '0.8',
            boxShadow: '0 0 10px var(--tw-shadow-color, rgba(59, 130, 246, 0.3)), 0 0 20px var(--tw-shadow-color, rgba(59, 130, 246, 0.2))'
          },
        },
      },
      boxShadow: {
        // Glow effects
        'glow-sm': '0 0 10px rgba(59, 130, 246, 0.3)',
        'glow': '0 0 20px rgba(14, 165, 233, 0.3)',
        'glow-lg': '0 0 40px rgba(14, 165, 233, 0.4)',
        'glow-accent': '0 0 40px rgba(59, 130, 246, 0.4)',
        'glow-primary': '0 0 40px rgba(14, 165, 233, 0.4)',
        // Neon effects
        'neon-accent': '0 0 20px rgba(59, 130, 246, 0.6), 0 0 40px rgba(59, 130, 246, 0.3)',
        'neon-primary': '0 0 20px rgba(14, 165, 233, 0.6), 0 0 40px rgba(14, 165, 233, 0.3)',
        'neon-success': '0 0 20px rgba(34, 197, 94, 0.6), 0 0 40px rgba(34, 197, 94, 0.3)',
        'neon-error': '0 0 20px rgba(239, 68, 68, 0.6), 0 0 40px rgba(239, 68, 68, 0.3)',
        'neon-warning': '0 0 20px rgba(245, 158, 11, 0.6), 0 0 40px rgba(245, 158, 11, 0.3)',
        // Glass effects
        'glass': '0 8px 32px rgba(0, 0, 0, 0.12)',
        'glass-lg': '0 25px 80px rgba(0, 0, 0, 0.35)',
        // Elevation
        'float': '0 20px 60px -10px rgba(0, 0, 0, 0.3)',
        'float-lg': '0 30px 80px -15px rgba(0, 0, 0, 0.4)',
        // Inner effects
        'inner-glow': 'inset 0 1px 0 rgba(255, 255, 255, 0.1)',
        'inner-glow-strong': 'inset 0 1px 0 rgba(255, 255, 255, 0.2)',
      },
      backdropBlur: {
        xs: '2px',
        '3xl': '64px',
      },
      borderRadius: {
        '4xl': '2rem',
        '5xl': '2.5rem',
      },
      transitionTimingFunction: {
        'spring': 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
        'smooth': 'cubic-bezier(0.22, 1, 0.36, 1)',
        'bounce': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
      },
      transitionDuration: {
        '400': '400ms',
        '600': '600ms',
        '800': '800ms',
        '900': '900ms',
      },
      zIndex: {
        '60': '60',
        '70': '70',
        '80': '80',
        '90': '90',
        '100': '100',
      },
    },
  },
  plugins: [
    // Custom plugin for safe area utilities
    function({ addUtilities }) {
      addUtilities({
        '.pt-safe': {
          paddingTop: 'env(safe-area-inset-top)',
        },
        '.pb-safe': {
          paddingBottom: 'env(safe-area-inset-bottom)',
        },
        '.pl-safe': {
          paddingLeft: 'env(safe-area-inset-left)',
        },
        '.pr-safe': {
          paddingRight: 'env(safe-area-inset-right)',
        },
        '.p-safe': {
          paddingTop: 'env(safe-area-inset-top)',
          paddingBottom: 'env(safe-area-inset-bottom)',
          paddingLeft: 'env(safe-area-inset-left)',
          paddingRight: 'env(safe-area-inset-right)',
        },
        '.mt-safe': {
          marginTop: 'env(safe-area-inset-top)',
        },
        '.mb-safe': {
          marginBottom: 'env(safe-area-inset-bottom)',
        },
        // Touch target helpers
        '.touch-target': {
          minWidth: '44px',
          minHeight: '44px',
        },
        '.touch-target-lg': {
          minWidth: '48px',
          minHeight: '48px',
        },
        // Glass morphism shortcuts
        '.glass': {
          backgroundColor: 'rgba(255, 255, 255, 0.12)',
          backdropFilter: 'blur(16px)',
          border: '1px solid rgba(255, 255, 255, 0.25)',
        },
        '.glass-dark': {
          backgroundColor: 'rgba(26, 22, 20, 0.8)',
          backdropFilter: 'blur(16px)',
          border: '1px solid rgba(61, 56, 53, 0.5)',
        },
        // Animation delay utilities
        '.stagger-1': { animationDelay: '50ms' },
        '.stagger-2': { animationDelay: '100ms' },
        '.stagger-3': { animationDelay: '150ms' },
        '.stagger-4': { animationDelay: '200ms' },
        '.stagger-5': { animationDelay: '250ms' },
        '.stagger-6': { animationDelay: '300ms' },
        '.stagger-7': { animationDelay: '350ms' },
        '.stagger-8': { animationDelay: '400ms' },
      });
    },
  ],
}

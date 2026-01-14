/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
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
          500: '#22c55e',
          600: '#16a34a',
        },
        error: {
          50: '#fef2f2',
          500: '#ef4444',
          600: '#dc2626',
        },
        warning: {
          50: '#fffbeb',
          500: '#f59e0b',
          600: '#d97706',
        },
        // Surface colors for glass effects
        surface: {
          dark: 'rgba(15, 13, 12, 0.8)',  // warm-950 with opacity
          glass: 'rgba(255, 255, 255, 0.1)',
          'glass-border': 'rgba(255, 255, 255, 0.2)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Cal Sans', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.875rem' }],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '112': '28rem',
        '128': '32rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'fade-up': 'fadeUp 0.5s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'slide-in-left': 'slideInLeft 0.3s ease-out',
        'float': 'float 6s ease-in-out infinite',
        'pulse-glow': 'pulseGlow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'aurora': 'aurora 15s ease-in-out infinite',
        'shimmer': 'shimmer 2s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        slideInLeft: {
          '0%': { opacity: '0', transform: 'translateX(-20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        aurora: {
          '0%, 100%': { transform: 'translate(0, 0) rotate(0deg)' },
          '50%': { transform: 'translate(30px, -30px) rotate(180deg)' },
        },
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        },
      },
      boxShadow: {
        'glow': '0 0 20px rgba(14, 165, 233, 0.3)',
        'glow-lg': '0 0 40px rgba(14, 165, 233, 0.4)',
        'glow-accent': '0 0 40px rgba(59, 130, 246, 0.4)',
        'glass': '0 8px 32px rgba(0, 0, 0, 0.12)',
        'glass-lg': '0 25px 80px rgba(0, 0, 0, 0.35)',
        'float': '0 20px 60px -10px rgba(0, 0, 0, 0.3)',
        'inner-glow': 'inset 0 1px 0 rgba(255, 255, 255, 0.1)',
      },
      backdropBlur: {
        xs: '2px',
      },
      borderRadius: {
        '4xl': '2rem',
      },
    },
  },
  plugins: [],
}

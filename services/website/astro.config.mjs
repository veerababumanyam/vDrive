import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';
import react from '@astrojs/react';

// https://astro.build/config
export default defineConfig({
  site: 'https://www.RawDrive.io',
  output: 'static',

  integrations: [
    mdx(),
    tailwind({
      applyBaseStyles: false,
    }),
    sitemap(),
    react(),
  ],

  server: {
    port: 8011,
    host: true,
  },

  vite: {
    server: {
      port: 8011,
    },
  },

  prefetch: {
    prefetchAll: true,
    defaultStrategy: 'viewport',
  },

  markdown: {
    shikiConfig: {
      theme: 'github-dark',
      wrap: true,
    },
  },

  // Environment variables
  env: {
    schema: {
      SITE_URL: {
        type: 'string',
        context: 'client',
        access: 'public',
        default: 'https://www.RawDrive.io',
      },
      APP_URL: {
        type: 'string',
        context: 'client',
        access: 'public',
        default: 'https://app.RawDrive.io',
      },
    },
  },
});

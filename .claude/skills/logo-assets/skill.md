---
name: logo-assets
aliases: [logo, favicon, icon, branding, assets]
description: Logo and favicon asset guidelines for RawDrive. Use when referencing logos, updating branding, or implementing theme-aware images.
---

# Logo & Favicon Assets

## Asset Inventory

All logo assets are located in `frontend/public/`:

### Light Mode
- `logo-light-16x16.png` - Browser favicon (16px)
- `logo-light-32x32.png` - Browser favicon retina (32px)
- `logo-light-180x180.png` - Apple Touch Icon (iOS)
- `logo-light-192x192.png` - PWA icon (Android)
- `logo-light-512x512.png` - PWA splash screen

### Dark Mode
- `logo-dark-16x16.png` - Browser favicon (16px)
- `logo-dark-32x32.png` - Browser favicon retina (32px)
- `logo-dark-180x180.png` - Apple Touch Icon (iOS)
- `logo-dark-192x192.png` - PWA icon (Android)
- `logo-dark-512x512.png` - PWA splash screen

### Source Files
- `android-chrome-512x512.png` - Light mode source (1024x1024 JPEG)
- `logo-dark-512x512.png` - Dark mode source (1024x1024 JPEG)

## Usage Patterns

### Browser Favicons (Automatic Theme Switching)

Already configured in `frontend/index.html` using `prefers-color-scheme`:

```html
<!-- Light Mode -->
<link rel="icon" sizes="16x16" href="/logo-light-16x16.png" media="(prefers-color-scheme: light)">
<link rel="icon" sizes="32x32" href="/logo-light-32x32.png" media="(prefers-color-scheme: light)">

<!-- Dark Mode -->
<link rel="icon" sizes="16x16" href="/logo-dark-16x16.png" media="(prefers-color-scheme: dark)">
<link rel="icon" sizes="32x32" href="/logo-dark-32x32.png" media="(prefers-color-scheme: dark)">
```

### React Component Logo

Use the `AppLogo` component for theme-aware logo display:

```tsx
import { AppLogo } from '@/components/ui/AppLogo';

// Basic usage
<AppLogo size="md" />

// With custom styling
<AppLogo size="lg" className="mx-auto my-4" />

// Available sizes: 'sm' (32px), 'md' (48px), 'lg' (64px)
```

**Manual implementation** (if AppLogo component is not available):

```tsx
import { useTheme } from '@/hooks/useTheme';

function MyComponent() {
  const { theme } = useTheme();

  const logoSrc = theme === 'dark'
    ? '/logo-dark-192x192.png'
    : '/logo-light-192x192.png';

  return <img src={logoSrc} alt="RawDrive" width={48} height={48} />;
}
```

### PWA Configuration

Manifest file: `frontend/public/manifest.json`

Icons are defined for Android PWA installation and splash screens.

**Manifest structure:**
```json
{
  "name": "RawDrive",
  "short_name": "RawDrive",
  "icons": [
    {
      "src": "/logo-light-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/logo-light-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ]
}
```

## Size Guidelines

| Size | Use Case | Files |
|------|----------|-------|
| 16x16 | Browser tab, bookmark bar | `logo-{light\|dark}-16x16.png` |
| 32x32 | Browser tab (retina), Windows taskbar | `logo-{light\|dark}-32x32.png` |
| 180x180 | iOS home screen icon | `logo-{light\|dark}-180x180.png` |
| 192x192 | Android PWA icon | `logo-{light\|dark}-192x192.png` |
| 512x512 | PWA splash screen, high-res | `logo-{light\|dark}-512x512.png` |

## Rules

- ✅ **ALWAYS** use theme-appropriate logo variant (light/dark)
- ✅ **ALWAYS** use proper file extensions (`.png` for raster)
- ✅ **ALWAYS** specify `width` and `height` attributes for performance
- ✅ **ALWAYS** use `AppLogo` component in React for automatic theme switching
- ❌ **NEVER** reference `vite.svg` or default template assets
- ❌ **NEVER** hardcode light-mode logos in dark-theme contexts
- ❌ **NEVER** use JPEG files with `.png` extension

## Maintenance

### Updating Logos

When updating logos:
1. Replace source files in `frontend/public/`:
   - `android-chrome-512x512.png` (light mode source)
   - `logo-dark-512x512.png` (dark mode source)
2. Run regeneration script: `bash scripts/generate-logos.sh`
3. Verify theme switching in browser DevTools
4. Test PWA installation on Android/iOS
5. Clear browser cache to see changes

### Regenerating All Sizes

Run the logo generation script:

```bash
bash scripts/generate-logos.sh
```

This will:
- Check for ImageMagick installation
- Resize source logos to all required sizes
- Generate 10 logo files total (5 light + 5 dark)
- Create true PNG files with transparency

### Manual Regeneration (without script)

If the script is not available:

```bash
# Generate light mode logos
magick frontend/public/android-chrome-512x512.png -resize 16x16 frontend/public/logo-light-16x16.png
magick frontend/public/android-chrome-512x512.png -resize 32x32 frontend/public/logo-light-32x32.png
magick frontend/public/android-chrome-512x512.png -resize 180x180 frontend/public/logo-light-180x180.png
magick frontend/public/android-chrome-512x512.png -resize 192x192 frontend/public/logo-light-192x192.png
magick frontend/public/android-chrome-512x512.png -resize 512x512 frontend/public/logo-light-512x512.png

# Generate dark mode logos
magick frontend/public/logo-dark-512x512.png -resize 16x16 frontend/public/logo-dark-16x16.png
magick frontend/public/logo-dark-512x512.png -resize 32x32 frontend/public/logo-dark-32x32.png
magick frontend/public/logo-dark-512x512.png -resize 180x180 frontend/public/logo-dark-180x180.png
magick frontend/public/logo-dark-512x512.png -resize 192x192 frontend/public/logo-dark-192x192.png
```

## Testing

### Visual Verification
1. Open `http://localhost:3000` in browser
2. Check browser tab for favicon
3. Toggle OS theme (System Preferences > Appearance)
4. Verify favicon changes to match theme

### PWA Testing
1. Open Chrome DevTools (F12)
2. Go to Application > Manifest
3. Verify manifest loads without errors
4. Check Application > Icons for proper icon registration
5. Install PWA: Chrome menu > Install RawDrive
6. Verify installed app uses correct icon

### Network Testing
1. Open Chrome DevTools (F12)
2. Go to Network tab
3. Reload page (Cmd+R)
4. Filter by "logo-"
5. Verify no 404 errors for logo files
6. Check file sizes match expected values

## Website Service

The website service (`services/website/`) uses inline SVG logos in `src/components/shared/Header.astro`. This is independent of the frontend logo system and should not be modified.

Website favicon: `services/website/public/favicon.svg`

## Troubleshooting

### Favicon not updating
- Clear browser cache (Cmd+Shift+R or Ctrl+Shift+R)
- Check browser console for 404 errors
- Verify files exist: `ls -lh frontend/public/logo-*.png`
- Restart dev server

### Dark mode logo not showing
- Check OS theme setting (not browser theme)
- Verify `media="(prefers-color-scheme: dark)"` in HTML
- Test in incognito mode (no extensions)
- Check browser support for `prefers-color-scheme`

### PWA icon not correct
- Clear Service Worker cache in DevTools
- Uninstall PWA and reinstall
- Verify manifest.json is accessible at `/manifest.json`
- Check Console for manifest parsing errors

### AppLogo component not working
- Verify `useTheme` hook is properly configured
- Check React Context is provided at app root
- Ensure logo files are in `public/` directory (not `src/assets/`)
- Verify import path: `@/components/ui/AppLogo`

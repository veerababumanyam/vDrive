# RawDrive Branding & Assets

**Version:** 0.3.3 | **Last Updated:** January 2026

---

## Logo & Favicons

All brand assets are located in `frontend/public/`:

### Favicon Files

| File | Size | Usage |
|------|------|-------|
| `favicon.ico` | Multi-size | Browser tab icon (legacy) |
| `favicon-16x16.png` | 16x16 | Small favicon |
| `favicon-32x32.png` | 32x32 | Standard favicon |
| `apple-touch-icon.png` | 180x180 | iOS home screen |
| `android-chrome-192x192.png` | 192x192 | Android home screen |
| `android-chrome-512x512.png` | 512x512 | Android splash screen |

### Logo Location

```
frontend/public/android-chrome-192x192.png  # Primary logo
```

---

## Color Palette

### Brand Colors

| Color | Hex | Usage |
|-------|-----|-------|
| **Primary (Indigo)** | `#4f46e5` | Primary actions, branding |
| **Primary Dark** | `#4338ca` | Hover states |
| **Primary Light** | `#818cf8` | Highlights |

### Neutral Colors (Slate)

| Color | Hex | Usage |
|-------|-----|-------|
| **Slate 50** | `#f8fafc` | Lightest background |
| **Slate 100** | `#f1f5f9` | Muted backgrounds |
| **Slate 200** | `#e2e8f0` | Borders (light) |
| **Slate 400** | `#94a3b8` | Placeholder text |
| **Slate 500** | `#64748b` | Muted text |
| **Slate 700** | `#334155` | Secondary text |
| **Slate 800** | `#1e293b` | Dark backgrounds |
| **Slate 900** | `#0f172a` | Primary text |
| **Slate 950** | `#020617` | Darkest (dark mode bg) |

### Status Colors

| Status | Hex | Usage |
|--------|-----|-------|
| **Success** | `#059669` | Success states |
| **Error** | `#dc2626` | Error states |
| **Warning** | `#f59e0b` | Warning states |
| **Info** | `#2563eb` | Informational |

---

## Typography

### Primary Font: Inter

```css
font-family: 'Inter', system-ui, -apple-system, sans-serif;
```

**Google Fonts URL:**
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

### Font Weights
- 400: Regular (body text)
- 500: Medium (UI elements)
- 600: Semibold (subheadings)
- 700: Bold (headings)

---

## Marketing Images

### Hero Images
Location: `frontend/public/images/hero/`

| File | Purpose |
|------|---------|
| `wedding-hero-1.jpg` | Wedding photography hero |
| `wedding-hero-2.jpg` | Wedding photography alternate |
| `portrait-hero.jpg` | Portrait photography hero |

### Feature Images
Location: `frontend/public/images/features/`

| File | Purpose |
|------|---------|
| `feature-gallery.jpg` | Gallery management feature |
| `feature-ai.jpg` | AI features showcase |
| `feature-album.jpg` | Album designer feature |
| `feature-crm.jpg` | CRM feature |
| `feature-mobile.jpg` | Mobile experience |
| `feature-security.jpg` | Security features |

### Testimonial Images
Location: `frontend/public/images/testimonials/`

12 testimonial images (6 JPG + 6 PNG) for customer stories.

### Use Case Images
Location: `frontend/public/images/use-cases/`

| Category | Count | Location |
|----------|-------|----------|
| Wedding | 6 | `use-cases/wedding/` |
| Portrait | 6 | `use-cases/portrait/` |
| Event | 6 | `use-cases/event/` |
| Commercial | 6 | `use-cases/commercial/` |

---

## Gallery Gradient Themes

Pre-configured gradient themes for client galleries:

| Theme Name | Primary | Secondary | CSS |
|------------|---------|-----------|-----|
| Sunset | `#f97316` | `#ec4899` | `bg-gradient-to-r from-orange-500 to-pink-500` |
| Ocean | `#0ea5e9` | `#6366f1` | `bg-gradient-to-r from-sky-500 to-indigo-500` |
| Forest | `#22c55e` | `#14b8a6` | `bg-gradient-to-r from-green-500 to-teal-500` |
| Midnight | `#1e293b` | `#3b82f6` | `bg-gradient-to-r from-slate-800 to-blue-500` |
| Rose | `#f43f5e` | `#ec4899` | `bg-gradient-to-r from-rose-500 to-pink-500` |

---

## Profile Brand Themes

Background themes for Personal Profile Digital Visiting Cards:

| Theme | Description | Background |
|-------|-------------|------------|
| `dark` | Dark sophisticated | Deep slate gradients |
| `pastel` | Soft muted colors | Light pastels |
| `bold` | Vibrant high-contrast | Saturated colors |
| `cinematic` | Film-inspired | Dark with accent |
| `minimal` | Clean white-focused | White/off-white |

---

## Web Manifest

Location: `frontend/public/manifest.json`

```json
{
  "name": "RawDrive",
  "short_name": "RawDrive",
  "description": "Professional Photography Management Platform",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#4f46e5",
  "icons": [
    {
      "src": "/android-chrome-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/android-chrome-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

---

## SEO Assets

### Robots.txt
Location: `frontend/public/robots.txt`

```
User-agent: *
Allow: /
Sitemap: https://RawDrive.com/sitemap.xml
```

### Meta Tags Template

```html
<meta name="description" content="RawDrive - Enterprise SaaS Professional Photography Management Platform. AI-powered galleries, client proofing, and album design.">
<meta name="keywords" content="photography, galleries, client proofing, album design, AI, professional photography">
<meta property="og:title" content="RawDrive - Professional Photography Platform">
<meta property="og:description" content="Enterprise-grade photography management with AI-powered features.">
<meta property="og:image" content="/android-chrome-512x512.png">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
```

---

## ML Models (Face Detection)

Pre-loaded models in `frontend/public/models/`:

| Model | Purpose | Files |
|-------|---------|-------|
| Face Landmark | 68-point face landmarks | `face_landmark_68_model-*` |
| Face Recognition | Face embedding generation | `face_recognition_model-*` |
| Object Detection | SSD MobileNet V1 | `ssd_mobilenetv1_model-*` |

---

## Localization Files

Translation files in `frontend/public/locales/`:

### Supported Languages

| Code | Language | Files |
|------|----------|-------|
| `en` | English | auth, common, dashboard, errors, gallery, settings, album |
| `hi` | Hindi | common, dashboard, errors, settings |
| `te` | Telugu | auth, common, dashboard, gallery, settings |
| `ta` | Tamil | common |
| `es` | Spanish | common |
| `gu` | Gujarati | common, settings |
| `mr` | Marathi | common, settings |
| `kn` | Kannada | common, settings |
| `ml` | Malayalam | common, settings |
| `bn` | Bengali | common, settings |
| `as` | Assamese | common, settings |
| `or` | Odia | common, settings |
| `pa` | Punjabi | common, settings |
| `ur` | Urdu (RTL) | common |

---

## Asset Checklist for New Deployments

### Required Assets
- [ ] `favicon.ico` - Multi-size favicon
- [ ] `favicon-16x16.png` - Small favicon
- [ ] `favicon-32x32.png` - Standard favicon
- [ ] `apple-touch-icon.png` - iOS icon
- [ ] `android-chrome-192x192.png` - Android icon
- [ ] `android-chrome-512x512.png` - Android splash
- [ ] `manifest.json` - Web app manifest
- [ ] `robots.txt` - Search engine directives

### Optional Customization
- [ ] Hero images for landing page
- [ ] Feature showcase images
- [ ] Testimonial photos
- [ ] Use case images by category
- [ ] Custom gradient themes
- [ ] Additional language translations

---

## File Size Guidelines

| Asset Type | Max Size | Format |
|------------|----------|--------|
| Favicon | 10KB | ICO, PNG |
| App Icons | 50KB | PNG |
| Hero Images | 500KB | JPG, WebP |
| Feature Images | 200KB | JPG, WebP |
| Testimonials | 50KB | JPG, PNG |

**Optimization Tools:**
- TinyPNG for PNG compression
- ImageOptim for general optimization
- Squoosh for WebP conversion

---

## Related Documentation

- **Design System:** [04-DESIGN-SYSTEM.md](04-DESIGN-SYSTEM.md)
- **Features:** [03-FEATURES-CATALOG.md](03-FEATURES-CATALOG.md)

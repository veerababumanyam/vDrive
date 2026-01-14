#!/bin/bash
# Generate all logo sizes from source files
# Usage: bash scripts/generate-logos.sh

set -e  # Exit on error

LIGHT_SOURCE="frontend/public/android-chrome-512x512.png"
DARK_SOURCE="frontend/public/logo-dark-512x512.png"
OUTPUT_DIR="frontend/public"

echo "🎨 vDrive Logo Generator"
echo "========================"
echo ""

# Check if source files exist
if [ ! -f "$LIGHT_SOURCE" ]; then
    echo "❌ Error: Light mode source file not found: $LIGHT_SOURCE"
    exit 1
fi

if [ ! -f "$DARK_SOURCE" ]; then
    echo "❌ Error: Dark mode source file not found: $DARK_SOURCE"
    exit 1
fi

# Check ImageMagick installation
if ! command -v magick &> /dev/null; then
    echo "❌ Error: ImageMagick not found."
    echo ""
    echo "Install ImageMagick:"
    echo "  macOS: brew install imagemagick"
    echo "  Ubuntu/Debian: sudo apt-get install imagemagick"
    echo "  Windows: Download from https://imagemagick.org/script/download.php"
    exit 1
fi

echo "✓ ImageMagick found: $(magick -version | head -1)"
echo ""

# Generate light mode sizes
echo "🌞 Generating light mode logos..."
magick "$LIGHT_SOURCE" -resize 16x16 "$OUTPUT_DIR/logo-light-16x16.png"
echo "  ✓ logo-light-16x16.png"

magick "$LIGHT_SOURCE" -resize 32x32 "$OUTPUT_DIR/logo-light-32x32.png"
echo "  ✓ logo-light-32x32.png"

magick "$LIGHT_SOURCE" -resize 180x180 "$OUTPUT_DIR/logo-light-180x180.png"
echo "  ✓ logo-light-180x180.png"

magick "$LIGHT_SOURCE" -resize 192x192 "$OUTPUT_DIR/logo-light-192x192.png"
echo "  ✓ logo-light-192x192.png"

magick "$LIGHT_SOURCE" -resize 512x512 "$OUTPUT_DIR/logo-light-512x512.png"
echo "  ✓ logo-light-512x512.png"

echo ""

# Generate dark mode sizes
echo "🌙 Generating dark mode logos..."
magick "$DARK_SOURCE" -resize 16x16 "$OUTPUT_DIR/logo-dark-16x16.png"
echo "  ✓ logo-dark-16x16.png"

magick "$DARK_SOURCE" -resize 32x32 "$OUTPUT_DIR/logo-dark-32x32.png"
echo "  ✓ logo-dark-32x32.png"

magick "$DARK_SOURCE" -resize 180x180 "$OUTPUT_DIR/logo-dark-180x180.png"
echo "  ✓ logo-dark-180x180.png"

magick "$DARK_SOURCE" -resize 192x192 "$OUTPUT_DIR/logo-dark-192x192.png"
echo "  ✓ logo-dark-192x192.png"

# Note: Dark 512x512 already exists as source, but regenerate for consistency
magick "$DARK_SOURCE" -resize 512x512 "$OUTPUT_DIR/logo-dark-512x512.png"
echo "  ✓ logo-dark-512x512.png"

echo ""
echo "✅ Logo generation complete!"
echo ""
echo "Generated files:"
ls -lh "$OUTPUT_DIR"/logo-*.png | awk '{printf "  %s - %s\n", $9, $5}'
echo ""
echo "Next steps:"
echo "  1. Verify logos in browser: http://localhost:3000"
echo "  2. Test theme switching (System Preferences > Appearance)"
echo "  3. Check PWA manifest: http://localhost:3000/manifest.json"
echo "  4. Clear browser cache if logos don't update (Cmd+Shift+R)"

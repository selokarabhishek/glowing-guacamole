#!/bin/bash
# Generate placeholder icons (requires ImageMagick)
# If ImageMagick is not available, the extension will still work
# but you'll need to add proper icons manually

if command -v convert &> /dev/null; then
    convert -size 128x128 xc:'#667eea' -pointsize 80 -fill white -gravity center -annotate +0+0 "AI" icon128.png
    convert icon128.png -resize 48x48 icon48.png
    convert icon128.png -resize 16x16 icon16.png
    echo "Icons generated successfully!"
else
    echo "ImageMagick not found. Please add icons manually."
fi

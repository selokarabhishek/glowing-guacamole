ICON PLACEHOLDER

Add your extension icons here:
- icon16.png (16x16 pixels)
- icon48.png (48x48 pixels)
- icon128.png (128x128 pixels)

You can create simple icons using:
1. Online tools like favicon.io or canva.com
2. Design software like Figma or Photoshop
3. Or use a simple colored square as a placeholder

For a quick placeholder, you can use ImageMagick:
convert -size 128x128 xc:#667eea -pointsize 80 -fill white -gravity center -annotate +0+0 "AI" icon128.png
convert icon128.png -resize 48x48 icon48.png
convert icon128.png -resize 16x16 icon16.png

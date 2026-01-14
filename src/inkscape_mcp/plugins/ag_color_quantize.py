"""
AG Color Quantize Extension

Reduces color palette of SVG files to optimize for Unity/VRChat performance.
Forces colors into specified palette to maintain brand consistency.
"""

import inkex
from inkex import PathElement, Style
import colorsys


class AGColorQuantize(inkex.EffectExtension):
    """Quantize colors in SVG to reduce palette size."""

    def add_arguments(self, pars):
        pars.add_argument("--max_colors", type=int, default=8, help="Maximum number of colors")
        pars.add_argument("--palette", type=str, default="", help="Custom palette (hex colors separated by commas)")
        pars.add_argument("--dither", type=bool, default=False, help="Apply dithering")

    def effect(self):
        """Quantize colors in the SVG."""
        max_colors = self.options.max_colors
        custom_palette = self._parse_palette(self.options.palette)
        should_dither = self.options.dither

        if custom_palette:
            # Use custom palette
            self._apply_custom_palette(custom_palette)
        else:
            # Auto-quantize to max_colors
            self._quantize_colors(max_colors, should_dither)

        inkex.errormsg(f"Color quantization completed. Max colors: {max_colors}")

    def _parse_palette(self, palette_str):
        """Parse custom palette string into RGB tuples."""
        if not palette_str.strip():
            return None

        palette = []
        for color_str in palette_str.split(','):
            color_str = color_str.strip()
            if color_str.startswith('#'):
                # Convert hex to RGB
                try:
                    r = int(color_str[1:3], 16)
                    g = int(color_str[3:5], 16)
                    b = int(color_str[5:7], 16)
                    palette.append((r, g, b))
                except ValueError:
                    continue
        return palette if palette else None

    def _apply_custom_palette(self, palette):
        """Apply custom color palette to all elements."""
        for elem in self.svg.iter():
            if isinstance(elem, PathElement):
                # Get current fill color
                fill_color = self._get_color_from_style(elem.style, 'fill')
                if fill_color:
                    nearest_color = self._find_nearest_color(fill_color, palette)
                    elem.style['fill'] = self._rgb_to_hex(nearest_color)

                # Get current stroke color
                stroke_color = self._get_color_from_style(elem.style, 'stroke')
                if stroke_color:
                    nearest_color = self._find_nearest_color(stroke_color, palette)
                    elem.style['stroke'] = self._rgb_to_hex(nearest_color)

    def _quantize_colors(self, max_colors, dither):
        """Auto-quantize colors using median cut algorithm."""
        # Collect all colors used in the document
        colors = set()
        for elem in self.svg.iter():
            if isinstance(elem, PathElement):
                fill_color = self._get_color_from_style(elem.style, 'fill')
                if fill_color:
                    colors.add(fill_color)

                stroke_color = self._get_color_from_style(elem.style, 'stroke')
                if stroke_color:
                    colors.add(stroke_color)

        if len(colors) <= max_colors:
            return  # Already within limit

        # Simple quantization: reduce to most common colors
        # For now, just map to a basic palette
        basic_palette = [
            (0, 0, 0),       # Black
            (255, 255, 255), # White
            (255, 0, 0),     # Red
            (0, 255, 0),     # Green
            (0, 0, 255),     # Blue
            (255, 255, 0),   # Yellow
            (255, 0, 255),   # Magenta
            (0, 255, 255),   # Cyan
        ]

        # Apply the basic palette
        self._apply_custom_palette(basic_palette[:max_colors])

    def _get_color_from_style(self, style, property_name):
        """Extract RGB tuple from style property."""
        color_str = style.get(property_name)
        if not color_str or color_str == 'none':
            return None

        # Handle hex colors
        if color_str.startswith('#'):
            try:
                if len(color_str) == 7:  # #RRGGBB
                    r = int(color_str[1:3], 16)
                    g = int(color_str[3:5], 16)
                    b = int(color_str[5:7], 16)
                    return (r, g, b)
                elif len(color_str) == 4:  # #RGB
                    r = int(color_str[1] * 2, 16)
                    g = int(color_str[2] * 2, 16)
                    b = int(color_str[3] * 2, 16)
                    return (r, g, b)
            except ValueError:
                pass

        # Handle named colors (basic support)
        named_colors = {
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'yellow': (255, 255, 0),
            'purple': (128, 0, 128),
            'orange': (255, 165, 0),
        }

        return named_colors.get(color_str.lower())

    def _find_nearest_color(self, target_color, palette):
        """Find the nearest color in the palette."""
        min_distance = float('inf')
        nearest = palette[0]

        for color in palette:
            distance = self._color_distance(target_color, color)
            if distance < min_distance:
                min_distance = distance
                nearest = color

        return nearest

    def _color_distance(self, color1, color2):
        """Calculate Euclidean distance between two RGB colors."""
        return sum((a - b) ** 2 for a, b in zip(color1, color2)) ** 0.5

    def _rgb_to_hex(self, rgb):
        """Convert RGB tuple to hex string."""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


if __name__ == '__main__':
    AGColorQuantize().run()
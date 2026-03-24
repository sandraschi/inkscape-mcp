"""
AG Layer Animation Extension

Creates CSS-animated SVGs from layers. Each layer becomes a keyframe in the animation.
Perfect for Unity web UI elements and lightweight animations.
"""

import inkex
from inkex import StyleElement


class AGLayerAnimation(inkex.EffectExtension):
    """Create CSS-animated SVG from layers."""

    def add_arguments(self, pars):
        pars.add_argument("--duration", type=float, default=2.0, help="Animation duration in seconds")
        pars.add_argument("--loop", type=bool, default=True, help="Loop animation")
        pars.add_argument("--easing", type=str, default="ease-in-out", help="CSS easing function")

    def effect(self):
        """Create CSS animation from layers."""
        duration = self.options.duration
        should_loop = self.options.loop
        easing = self.options.easing

        # Find all layers
        layers = self._get_layers()
        if len(layers) < 2:
            inkex.errormsg("Need at least 2 layers to create animation.")
            return

        # Create CSS keyframes
        css_rules = self._create_keyframes(layers, duration, easing, should_loop)

        # Inject CSS into SVG
        self._inject_css(css_rules)

        inkex.errormsg(f"Created {len(layers)}-frame CSS animation (duration: {duration}s).")

    def _get_layers(self):
        """Get all Inkscape layers in order."""
        layers = []
        for elem in self.svg.xpath('//svg:g[@inkscape:groupmode="layer"]'):
            layers.append(elem)
        return layers

    def _create_keyframes(self, layers, duration, easing, loop):
        """Create CSS keyframes from layers."""
        css_rules = []
        num_frames = len(layers)

        # Calculate timing for each frame
        frame_duration = duration / num_frames if num_frames > 1 else duration

        for i, layer in enumerate(layers):
            layer_id = layer.get('id', f'layer_{i}')
            start_percent = (i / num_frames) * 100
            end_percent = ((i + 1) / num_frames) * 100

            # Hide all layers initially
            if i == 0:
                css_rules.append(f"""
                #{layer_id} {{
                    opacity: 1;
                    animation: ag_layer_anim {duration}s {easing} {'infinite' if loop else '1'};
                }}
                """.strip())
            else:
                css_rules.append(f"""
                #{layer_id} {{
                    opacity: 0;
                    animation: ag_layer_anim {duration}s {easing} {'infinite' if loop else '1'};
                }}
                """.strip())

        # Create the keyframe animation
        keyframe_rules = []
        for i in range(num_frames):
            percent = (i / num_frames) * 100
            keyframe_rules.append(f"""
            {percent:.1f}% {{
                opacity: {'1' if i == 0 else '0'};
            }}
            """.strip())

        # Add keyframes for each layer
        for i, layer in enumerate(layers):
            layer_id = layer.get('id', f'layer_{i}')
            start_percent = (i / num_frames) * 100
            end_percent = ((i + 1) / num_frames) * 100

            css_rules.append(f"""
            @keyframes ag_layer_anim_{layer_id} {{
                0%, {start_percent:.1f}% {{
                    opacity: 0;
                    display: none;
                }}
                {start_percent + 0.1:.1f}%, {end_percent - 0.1:.1f}% {{
                    opacity: 1;
                    display: inline;
                }}
                {end_percent:.1f}%, 100% {{
                    opacity: 0;
                    display: none;
                }}
            }}
            """.strip())

        # Main animation keyframes
        css_rules.insert(0, f"""
        @keyframes ag_layer_anim {{
            {"".join(keyframe_rules)}
        }}
        """.strip())

        return css_rules

    def _inject_css(self, css_rules):
        """Inject CSS rules into the SVG document."""
        # Create or find defs element
        defs = self.svg.defs
        if defs is None:
            defs = inkex.Defs()
            self.svg.insert(0, defs)

        # Create style element with CSS
        style_elem = StyleElement()
        style_elem.text = "\n".join(css_rules)
        defs.append(style_elem)


if __name__ == '__main__':
    AGLayerAnimation().run()

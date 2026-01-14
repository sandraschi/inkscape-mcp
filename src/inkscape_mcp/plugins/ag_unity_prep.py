"""
AG Unity Prep Extension

Prepares SVG files for Unity UI import by flattening groups, resetting coordinates,
and optimizing for game engine performance.
"""

import inkex
from inkex import Group, PathElement, Style


class AGUnityPrep(inkex.EffectExtension):
    """Prepare SVG for Unity UI import."""

    def add_arguments(self, pars):
        pars.add_argument("--flatten_groups", type=bool, default=True, help="Flatten all groups")
        pars.add_argument("--reset_coordinates", type=bool, default=True, help="Reset document coordinates")
        pars.add_argument("--optimize_paths", type=bool, default=True, help="Optimize path complexity")
        pars.add_argument("--remove_metadata", type=bool, default=True, help="Remove Inkscape metadata")

    def effect(self):
        """Prepare SVG for Unity import."""
        flatten_groups = self.options.flatten_groups
        reset_coords = self.options.reset_coordinates
        optimize_paths = self.options.optimize_paths
        remove_metadata = self.options.remove_metadata

        # Flatten all groups if requested
        if flatten_groups:
            self._flatten_all_groups()

        # Reset coordinates to origin if requested
        if reset_coords:
            self._reset_coordinates()

        # Optimize paths if requested
        if optimize_paths:
            self._optimize_paths()

        # Remove metadata if requested
        if remove_metadata:
            self._remove_metadata()

        inkex.errormsg("SVG prepared for Unity import.")

    def _flatten_all_groups(self):
        """Recursively flatten all groups in the document."""
        groups_to_process = []

        # Find all groups
        for elem in self.svg.iter():
            if isinstance(elem, Group):
                groups_to_process.append(elem)

        # Process groups (work backwards to avoid index issues)
        for group in reversed(groups_to_process):
            try:
                # Move all children up one level
                parent = group.getparent()
                if parent is not None:
                    index = parent.index(group)
                    for child in list(group):
                        parent.insert(index, child)
                        index += 1
                    parent.remove(group)
            except Exception as e:
                inkex.errormsg(f"Error flattening group: {e}")

    def _reset_coordinates(self):
        """Reset document coordinates to origin."""
        # Get current viewBox
        viewbox = self.svg.get('viewBox')
        if viewbox:
            # Parse viewBox values
            try:
                values = [float(x) for x in viewbox.split()]
                if len(values) >= 4:
                    x, y, width, height = values[:4]
                    # Reset to origin
                    self.svg.set('viewBox', f'0 0 {width} {height}')
            except ValueError:
                pass

        # Reset any transforms on root element
        if self.svg.get('transform'):
            self.svg.set('transform', None)

    def _optimize_paths(self):
        """Optimize path complexity for Unity."""
        for elem in self.svg.iter():
            if isinstance(elem, PathElement):
                # Remove unnecessary style attributes that Unity doesn't need
                style_attrs_to_remove = ['filter', 'marker', 'marker-start', 'marker-mid', 'marker-end']
                for attr in style_attrs_to_remove:
                    if attr in elem.style:
                        del elem.style[attr]

                # Ensure stroke-width is reasonable for UI
                if 'stroke-width' in elem.style:
                    try:
                        width = float(elem.style['stroke-width'])
                        if width > 5:  # Cap maximum stroke width
                            elem.style['stroke-width'] = '2px'
                        elif width < 0.5:  # Minimum visible stroke
                            elem.style['stroke-width'] = '1px'
                    except ValueError:
                        elem.style['stroke-width'] = '1px'

    def _remove_metadata(self):
        """Remove Inkscape-specific metadata."""
        # Remove Inkscape namespace declarations
        namespaces_to_remove = ['inkscape', 'sodipodi']

        # Remove metadata elements
        for elem in self.svg.iter():
            # Remove Inkscape-specific attributes
            attrs_to_remove = []
            for attr_name in elem.attrib:
                if any(ns in attr_name for ns in namespaces_to_remove):
                    attrs_to_remove.append(attr_name)

            for attr in attrs_to_remove:
                del elem.attrib[attr]

        # Remove defs that are Inkscape-specific
        defs = self.svg.defs
        if defs is not None:
            children_to_remove = []
            for child in defs:
                if child.tag.endswith('}metadata') or 'inkscape' in child.tag:
                    children_to_remove.append(child)

            for child in children_to_remove:
                defs.remove(child)


if __name__ == '__main__':
    AGUnityPrep().run()
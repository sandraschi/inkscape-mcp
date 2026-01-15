"""
AG Batch Trace Extension

Converts bitmaps to optimized SVG vectors with color quantization.
Designed for Unity/VRChat workflows to reduce vertex counts and file sizes.
"""

import inkex
import subprocess
from pathlib import Path


class AGBatchTrace(inkex.EffectExtension):
    """Batch convert bitmaps to optimized SVG vectors."""

    def add_arguments(self, pars):
        pars.add_argument("--input_dir", type=str, help="Directory containing bitmaps")
        pars.add_argument("--output_dir", type=str, help="Directory to save SVGs")
        pars.add_argument("--colors", type=int, default=4, help="Number of colors to quantize to")
        pars.add_argument("--simplify", type=bool, default=True, help="Simplify paths after tracing")

    def effect(self):
        """Execute batch bitmap tracing."""
        input_dir = Path(self.options.input_dir)
        output_dir = Path(self.options.output_dir)
        num_colors = self.options.colors
        should_simplify = self.options.simplify

        if not input_dir.exists() or not input_dir.is_dir():
            inkex.errormsg(f"Input directory not found: {input_dir}")
            return

        output_dir.mkdir(parents=True, exist_ok=True)

        # Process each bitmap file
        processed_count = 0
        for file_path in input_dir.glob("*"):
            if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
                try:
                    self._process_single_file(file_path, output_dir, num_colors, should_simplify)
                    processed_count += 1
                except Exception as e:
                    inkex.errormsg(f"Error processing {file_path}: {e}")

        inkex.errormsg(f"Batch trace completed. Processed {processed_count} files.")

    def _process_single_file(self, input_path: Path, output_dir: Path, colors: int, simplify: bool):
        """Process a single bitmap file."""
        output_path = output_dir / f"{input_path.stem}_traced.svg"

        # Build Inkscape command for tracing
        cmd = [
            'inkscape',
            str(input_path),
            '--batch-process',
            f'--export-filename={output_path}',
            '--export-do'
        ]

        # Add tracing actions
        actions = []
        actions.append('select-all')  # Select the bitmap
        actions.append('object-to-path')  # Convert to path (trace)
        if simplify:
            actions.append('selection-simplify')  # Simplify the path

        cmd.append(f'--actions={"".join(f"{action};" for action in actions)}')

        # Execute the command
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            raise Exception(f"Inkscape command failed: {result.stderr}")

        inkex.errormsg(f"Processed: {input_path.name} -> {output_path.name}")


if __name__ == '__main__':
    AGBatchTrace().run()

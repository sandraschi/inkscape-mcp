"""Heraldry Studio - specialized tool for generating heraldic assets with SOTA vector aesthetics.

Consolidates heraldry generation, blazon parsing, and SVG asset creation.
"""

import logging
import os
import time
from typing import Any, Dict, List, Literal, Optional

from mcp.types import ToolAnnotations
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class HeraldryResult(BaseModel):
    """Result model for heraldry operations."""

    success: bool
    operation: str
    message: str
    data: Dict[str, Any]
    execution_time_ms: float


async def generate_heraldry_trumponia(
    output_path: str,
    cli_wrapper: Any = None,
    config: Any = None,
) -> Dict[str, Any]:
    """Generate the 'Empire of Trumponia' heraldic coat of arms.

    Subject: Two asses rampant.
    Style: High-contrast SOTA Heraldry (Gold, Crimson, Cyan).
    """
    start_time = time.time()

    try:
        # SOTA Heraldry SVG Template
        svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="600" height="800" viewBox="0 0 600 800" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#FFD700;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#FDB931;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#B8860B;stop-opacity:1" />
    </linearGradient>
    <filter id="dropShadow">
      <feDropShadow dx="2" dy="2" stdDeviation="3" flood-opacity="0.5"/>
    </filter>
  </defs>

  <!-- Shield (Escutcheon) - Crimson / Gules -->
  <path d="M 50,50 L 550,50 L 550,450 C 550,650 300,750 300,750 C 300,750 50,650 50,450 Z" 
        fill="#960018" stroke="#FFD700" stroke-width="10" filter="url(#dropShadow)"/>

  <!-- Two Asses Rampant (Left) - Or / Gold -->
  <g transform="translate(150, 400) scale(1.2)" fill="url(#goldGrad)">
     <!-- Stylized Ass Rampant Silhouettes -->
     <path d="M 0,0 C -20,-20 -40,-10 -50,10 C -60,30 -40,60 -20,70 L -30,100 L 0,80 L 30,100 L 20,70 C 40,60 60,30 50,10 C 40,-10 20,-20 0,0 Z" 
           transform="rotate(-15)"/>
     <circle cx="0" cy="-30" r="15"/> <!-- Head -->
     <rect x="-5" y="-60" width="10" height="40" rx="5"/> <!-- Ears -->
  </g>

  <!-- Two Asses Rampant (Right) - Or / Gold -->
  <g transform="translate(450, 400) scale(1.2) scale(-1, 1)" fill="url(#goldGrad)">
     <path d="M 0,0 C -20,-20 -40,-10 -50,10 C -60,30 -40,60 -20,70 L -30,100 L 0,80 L 30,100 L 20,70 C 40,60 60,30 50,10 C 40,-10 20,-20 0,0 Z" 
           transform="rotate(-15)"/>
     <circle cx="0" cy="-30" r="15"/>
     <rect x="-5" y="-60" width="10" height="40" rx="5"/>
  </g>

  <!-- Cyan Accents (Motto Scroll) -->
  <path d="M 100,700 Q 300,650 500,700 L 500,760 Q 300,710 100,760 Z" 
        fill="#00FFFF" stroke="#000000" stroke-width="2"/>
  <text x="300" y="740" text-anchor="middle" font-family="Serif" font-size="24" font-weight="bold" fill="black">
    TRUMPONIA IMPERIUM
  </text>

  <!-- Crest / Crown -->
  <path d="M 200,40 L 250,10 L 300,40 L 350,10 L 400,40 L 300,80 Z" fill="url(#goldGrad)" stroke="black"/>
</svg>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg_content)

        return HeraldryResult(
            success=True,
            operation="generate_heraldry_trumponia",
            message="Generated the 'Empire of Trumponia' coat of arms (two asses rampant).",
            data={
                "output_path": output_path,
                "palette": ["crimson", "gold", "cyan"],
                "elements": ["two asses rampant", "escutcheon", "motto scroll"],
            },
            execution_time_ms=(time.time() - start_time) * 1000,
        ).model_dump()

    except Exception as e:
        logger.error(f"Heraldry generation failed: {e}")
        return HeraldryResult(
            success=False,
            operation="generate_heraldry_trumponia",
            message=f"Heraldry generation failed: {e}",
            data={},
            execution_time_ms=(time.time() - start_time) * 1000,
        ).model_dump()


def register_heraldry_tools(mcp: Any, cli_wrapper: Any, config: Any) -> None:
    """Register heraldry tools with FastMCP server."""

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    async def generate_heraldry(
        operation: Literal["trumponia", "custom"] = "trumponia",
        output_path: Optional[str] = None,
        ctx: Any = None,
    ) -> Dict[str, Any]:
        """GENERATE_HERALDRY — Emit heraldic SVG assets (preset compositions).

        PORTMANTEAU RATIONALE: Single entry point for heraldry; `operation` selects preset.

        Args:
            operation: trumponia (implemented) or custom (not yet implemented).
            output_path: Destination SVG path; default under config temp directory.
            ctx: Reserved for future sampling context.

        Returns:
            Dict with success, operation, message, data, execution_time_ms.

        Errors:
            Write failures or missing temp directory — see message.
        """
        if not output_path:
            output_path = os.path.join(config.temp_directory, f"heraldry_{operation}.svg")

        if operation == "trumponia":
            return await generate_heraldry_trumponia(output_path, cli_wrapper, config)
        else:
            return {"success": False, "message": "Custom heraldry not yet implemented."}

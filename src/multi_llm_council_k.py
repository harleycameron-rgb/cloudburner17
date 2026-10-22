"""In-memory compressed-description-length profiles for council outputs."""

from __future__ import annotations

import zlib
from typing import Any, Dict, Iterable


def compressed_length_profile(text: str) -> Dict[str, Any]:
    """Measure UTF-8 and zlib-compressed byte lengths for one string."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    encoded = text.encode("utf-8")
    compressed = zlib.compress(encoded, level=9)
    return {
        "raw_bytes": len(encoded),
        "compressed_bytes": len(compressed),
    }


def council_length_profile(
    rounds: Iterable[Any], final_synthesis: str
) -> Dict[str, Any]:
    """Build a stable length profile of model replies and the final synthesis."""
    items = []
    for round_result in rounds:
        for reply in round_result.replies:
            item = {
                "round_id": round_result.round_id,
                "model": reply.model,
                **compressed_length_profile(reply.content),
            }
            items.append(item)

    items.append(
        {
            "round_id": None,
            "model": "final_synthesis",
            **compressed_length_profile(final_synthesis),
        }
    )
    return {
        "method": "zlib-deflate-level-9",
        "units": "bytes",
        "items": items,
        "total_raw_bytes": sum(item["raw_bytes"] for item in items),
        "total_compressed_bytes": sum(
            item["compressed_bytes"] for item in items
        ),
    }

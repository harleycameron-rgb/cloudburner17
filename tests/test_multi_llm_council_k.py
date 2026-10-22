import unittest
import zlib

from src.multi_llm_council_k import (
    compressed_length_profile,
    council_length_profile,
)
from src.multi_llm_council import CouncilRound, ModelReply


class CouncilLengthProfileTests(unittest.TestCase):
    def test_profile_measures_utf8_and_compressed_bytes(self):
        text = "café"
        profile = compressed_length_profile(text)

        self.assertEqual(profile["raw_bytes"], len(text.encode("utf-8")))
        self.assertEqual(
            profile["compressed_bytes"],
            len(zlib.compress(text.encode("utf-8"), level=9)),
        )

    def test_profile_accepts_empty_text_and_rejects_non_strings(self):
        self.assertEqual(compressed_length_profile(""), {
            "raw_bytes": 0,
            "compressed_bytes": len(zlib.compress(b"", level=9)),
        })
        with self.assertRaisesRegex(TypeError, "text must be a string"):
            compressed_length_profile(None)

    def test_council_profile_includes_replies_and_synthesis(self):
        rounds = [
            CouncilRound(
                round_id=0,
                prompt="topic",
                replies=[
                    ModelReply("model-a", "reply a", 1.0),
                    ModelReply("model-b", "reply b", 1.0),
                ],
            )
        ]

        profile = council_length_profile(rounds, "synthesis")

        self.assertEqual(
            [item["model"] for item in profile["items"]],
            ["model-a", "model-b", "final_synthesis"],
        )
        self.assertEqual([item["round_id"] for item in profile["items"]], [0, 0, None])
        self.assertEqual(
            profile["total_raw_bytes"],
            sum(len(text.encode("utf-8")) for text in ("reply a", "reply b", "synthesis")),
        )
        self.assertEqual(
            profile["total_compressed_bytes"],
            sum(item["compressed_bytes"] for item in profile["items"]),
        )


if __name__ == "__main__":
    unittest.main()

# tests/test_multi_llm_council.py
"""Offline tests for the multi-LLM council. No inference calls."""

import copy
import hashlib
import json
import unittest
from unittest.mock import patch

from src import multi_llm_council as council


class MultiLLMCouncilTests(unittest.TestCase):
    @staticmethod
    def reply(model, content):
        return council.ModelReply(
            model=model,
            content=content,
            latency_ms=1.0,
        )

    def assert_sentinel_valid(self, result):
        payload = copy.deepcopy(result.to_dict())
        sentinel = payload["sentinel"]
        payload["sentinel"] = ""

        self.assertEqual(len(sentinel), 128)
        self.assertEqual(
            sentinel,
            council.make_sentinel(payload),
        )

    def test_sentinel_uses_canonical_json(self):
        payload = {"z": "trajectory", "a": [1, 2, 3]}
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        expected = hashlib.sha512(
            canonical.encode("utf-8")
        ).hexdigest()

        self.assertEqual(council.make_sentinel(payload), expected)

    def test_sentinel_ignores_dictionary_insertion_order(self):
        first = {"role": "TAP", "tick": 1}
        second = {"tick": 1, "role": "TAP"}

        self.assertEqual(
            council.make_sentinel(first),
            council.make_sentinel(second),
        )

    def test_sentinel_changes_when_payload_changes(self):
        first = {"topic": "trajectory", "tick": 1}
        second = {"topic": "trajectory", "tick": 2}

        self.assertNotEqual(
            council.make_sentinel(first),
            council.make_sentinel(second),
        )

    @patch.object(council, "call_model")
    def test_collects_replies_then_requests_synthesis(self, call):
        call.side_effect = [
            self.reply("model-a", "First analysis"),
            self.reply("model-b", "Second analysis"),
            self.reply("chair", "Combined analysis"),
        ]

        result = council.run_council(
            topic="Review trajectory consistency",
            models=["model-a", "model-b"],
            chairman="chair",
            api_key="offline-test-key",
        )

        self.assertEqual(call.call_count, 3)
        self.assertEqual(
            [entry.args[0] for entry in call.call_args_list],
            ["model-a", "model-b", "chair"],
        )
        self.assertEqual(len(result.rounds), 1)
        self.assertEqual(
            [reply.model for reply in result.rounds[0].replies],
            ["model-a", "model-b"],
        )
        self.assertEqual(result.final_synthesis, "Combined analysis")
        self.assertEqual(
            result.length_profile["method"],
            "zlib-deflate-level-9",
        )
        self.assertEqual(
            [item["model"] for item in result.length_profile["items"]],
            ["model-a", "model-b", "final_synthesis"],
        )

        chair_messages = call.call_args_list[-1].args[1]
        synthesis_prompt = chair_messages[-1]["content"]
        self.assertIn("First analysis", synthesis_prompt)
        self.assertIn("Second analysis", synthesis_prompt)
        self.assert_sentinel_valid(result)

    @patch.object(council, "call_model")
    def test_member_failure_is_recorded_and_collection_continues(
        self, call
    ):
        call.side_effect = [
            RuntimeError("member unavailable"),
            self.reply("model-b", "Available analysis"),
            self.reply("chair", "Qualified synthesis"),
        ]

        result = council.run_council(
            topic="Review",
            models=["model-a", "model-b"],
            chairman="chair",
        )

        replies = result.rounds[0].replies
        self.assertEqual(call.call_count, 3)
        self.assertEqual(
            replies[0].content,
            "[ERROR] member unavailable",
        )
        self.assertEqual(replies[0].latency_ms, 0.0)
        self.assertEqual(replies[1].content, "Available analysis")
        self.assert_sentinel_valid(result)

    @patch.object(council, "call_model")
    def test_chairman_failure_is_explicit(self, call):
        call.side_effect = [
            self.reply("model-a", "Analysis"),
            RuntimeError("chair unavailable"),
        ]

        result = council.run_council(
            topic="Review",
            models=["model-a"],
            chairman="chair",
        )

        self.assertEqual(
            result.final_synthesis,
            "[Chairman error] chair unavailable",
        )
        self.assert_sentinel_valid(result)

    @patch.object(council, "call_model")
    def test_public_entry_point_returns_serializable_dictionary(
        self, call
    ):
        call.side_effect = [
            self.reply("model-a", "Analysis"),
            self.reply("chair", "Synthesis"),
        ]

        result = council.autonomous_collaboration(
            topic="Review",
            models=["model-a"],
            chairman="chair",
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["final_synthesis"], "Synthesis")
        self.assertEqual(
            json.loads(json.dumps(result)),
            result,
        )

        payload = copy.deepcopy(result)
        sentinel = payload["sentinel"]
        payload["sentinel"] = ""
        self.assertEqual(sentinel, council.make_sentinel(payload))


if __name__ == "__main__":
    unittest.main()

# src/multi_llm_council.py
"""
Autonomous multi-model collaboration for CLOUDBURNER17.
Zero-data. Sentinel-producing. Constellation-compliant.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

if __package__:
    from .network_gateway import GatewayError, NetworkGateway
else:
    from network_gateway import GatewayError, NetworkGateway

DEFAULT_MODELS = [
    "openai/gpt-4o",
    "google/gemini-2.5-flash",
    "deepseek/deepseek-v4.1-flash",
    "moonshotai/kimi-k3",
    "perplexity/sonar-pro",
]

@dataclass
class ModelReply:
    model: str
    content: str
    latency_ms: float
    tokens: Optional[Dict[str, int]] = None


@dataclass
class CouncilRound:
    round_id: int
    prompt: str
    replies: List[ModelReply] = field(default_factory=list)
    rankings: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class CouncilResult:
    topic: str
    rounds: List[CouncilRound]
    final_synthesis: str
    chairman_model: str
    sentinel: str
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "rounds": [
                {
                    "round_id": r.round_id,
                    "prompt": r.prompt,
                    "replies": [
                        {
                            "model": rep.model,
                            "content": rep.content,
                            "latency_ms": rep.latency_ms,
                        }
                        for rep in r.replies
                    ],
                    "rankings": r.rankings,
                }
                for r in self.rounds
            ],
            "final_synthesis": self.final_synthesis,
            "chairman_model": self.chairman_model,
            "sentinel": self.sentinel,
            "created_at": self.created_at,
        }


def make_sentinel(payload: Dict[str, Any]) -> str:
    """Deterministic SHA-512 sentinel of the collaboration payload."""
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha512(canonical.encode("utf-8")).hexdigest()


def call_model(
    model: str,
    messages: List[Dict[str, str]],
    api_key: Optional[str] = None,
    temperature: float = 0.4,
    max_tokens: int = 1024,
    data_classification: Optional[str] = None,
) -> ModelReply:
    if api_key:
        raise RuntimeError("Pass outbound credentials through the network gateway only")
    if data_classification not in {"public", "synthetic"}:
        raise RuntimeError("Explicit public or synthetic data classification required")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/harleycameron-rgb/cloudburner17",
        "X-Title": "CLOUDBURNER17 Multi-LLM Council",
    }

    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    messages_digest = hashlib.sha512(
        json.dumps(
            messages, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    ).hexdigest()
    gateway_request = {
        "service": "openrouter",
        "operation": "chat_completions",
        "mode": "analysis",
        "data_classification": data_classification,
        "provenance": {
            "source": "caller-supplied-prompt",
            "revision": "unverified",
            "sha512": messages_digest,
        },
        "payload": body,
    }

    t0 = time.perf_counter()
    try:
        result = NetworkGateway.from_env().dispatch_internal(gateway_request)
    except GatewayError as error:
        raise RuntimeError(error.code) from None
    if result["upstream_status"] < 200 or result["upstream_status"] >= 300:
        raise RuntimeError(f"LLM service returned HTTP {result['upstream_status']}")
    data = result["response"]

    latency = (time.perf_counter() - t0) * 1000
    content = data["choices"][0]["message"]["content"]

    return ModelReply(
        model=model,
        content=content.strip(),
        latency_ms=round(latency, 1),
        tokens=data.get("usage"),
    )


def run_council(
    topic: str,
    models: Optional[Sequence[str]] = None,
    chairman: Optional[str] = None,
    rounds: int = 1,
    api_key: Optional[str] = None,
    data_classification: Optional[str] = None,
) -> CouncilResult:
    """
    Fully autonomous multi-model collaboration.
    1. Fan-out: every model answers the topic independently.
    2. Chairman synthesises final answer.
    Everything stays in memory. Returns a sentinel-hashed result.
    """
    models = list(models or DEFAULT_MODELS)
    chairman = chairman or models[0]

    all_rounds: List[CouncilRound] = []

    system = (
        "You are a rigorous, independent reasoning agent inside the "
        "CLOUDBURNER17 invariance system. Answer carefully and honestly. "
        "Do not mention other models."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": topic},
    ]

    first_round = CouncilRound(round_id=0, prompt=topic)
    for model in models:
        try:
            reply = call_model(
                model,
                messages,
                api_key=api_key,
                data_classification=data_classification,
            )
            first_round.replies.append(reply)
        except Exception as e:
            first_round.replies.append(
                ModelReply(model=model, content=f"[ERROR] {e}", latency_ms=0.0)
            )
    all_rounds.append(first_round)

    # Chairman synthesis
    synthesis_prompt = f"Topic: {topic}\n\nIndependent answers:\n\n"
    for i, rep in enumerate(first_round.replies, 1):
        synthesis_prompt += f"--- {rep.model} ---\n{rep.content}\n\n"
    synthesis_prompt += (
        "Synthesise the strongest possible final answer. "
        "Resolve contradictions. Be precise."
    )

    chair_messages = [
        {
            "role": "system",
            "content": "You are the Chairman of the LLM Council. Produce a clear final answer.",
        },
        {"role": "user", "content": synthesis_prompt},
    ]

    try:
        final = call_model(
            chairman,
            chair_messages,
            api_key=api_key,
            max_tokens=1500,
            data_classification=data_classification,
        )
        final_text = final.content
    except Exception as e:
        final_text = f"[Chairman error] {e}"

    result = CouncilResult(
        topic=topic,
        rounds=all_rounds,
        final_synthesis=final_text,
        chairman_model=chairman,
        sentinel="",
    )
    result.sentinel = make_sentinel(result.to_dict())
    return result


def autonomous_collaboration(
    topic: str,
    models: Optional[Sequence[str]] = None,
    chairman: Optional[str] = None,
    data_classification: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Public entry point. Returns a pure dict that can be sentinel-verified
    and never touches disk.
    """
    return run_council(
        topic=topic,
        models=models,
        chairman=chairman,
        data_classification=data_classification,
    ).to_dict()


if __name__ == "__main__":
    # Quick local test (requires the opt-in network gateway).
    out = autonomous_collaboration(
        "What is the most robust way to prevent context drift in multi-agent LLM systems?",
        data_classification="synthetic",
    )
    print(json.dumps(out, indent=2)[:2000])
    print("\nSentinel:", out["sentinel"][:32], "...")

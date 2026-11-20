# SCANDOC Zero controlled network boundary

Status: **implemented as an opt-in, single-process gateway; not configured or production-authorized.**
The owner authorizes SCANDOC Zero network capability, not access to any particular account, repository,
provider, data class, production deployment, or native action. This gateway is outside the deterministic
geometry runtime. Sentinel → Cube → Sphere, the six canonical commitments, geometry hashes and temporal
receipts remain separate and unchanged. Network connectivity never opens the native gate or permits writes.

## Boundary and permissions

`POST /scandoc/network/dispatch` in the full FastAPI application is a server-to-server interface. It is
disabled unless `SCANDOC_GATEWAY_ENABLED=true`, requires a server-side bearer value in
`SCANDOC_GATEWAY_INBOUND_TOKEN`, and must not be called from browser JavaScript or given browser-held
provider credentials. Outbound service credentials are read from server environment variables named in
the service configuration. The request cannot choose a URL, HTTP method, headers, or provider credential.
Only configured operation names, methods, fixed paths, service hosts, and (where applicable) exact
repository and model allowlists are usable. TLS certificate verification is provided by Python's
`HTTPSConnection`; redirects are not followed.

The JSON value of `SCANDOC_GATEWAY_SERVICES` configures services. For example, an administrator could
configure a GitHub App installation token restricted to selected repositories, an OpenRouter key and
specific models, and one approved research API:

```json
{
  "github": {
    "base_url": "https://api.github.com",
    "credential_env": "GITHUB_APP_INSTALLATION_TOKEN",
    "repositories": ["OWNER/PRIVATE-REPO"],
    "operations": {
      "contents": {
        "method": "GET",
        "path": "/repos/{repository}/contents",
        "modes": ["observation"]
      }
    },
    "rate_limit_per_minute": 30,
    "request_bytes": 65536,
    "response_bytes": 1048576,
    "timeout_seconds": 10
  },
  "openrouter": {
    "base_url": "https://openrouter.ai",
    "credential_env": "OPENROUTER_API_KEY",
    "models": ["openai/example-model"],
    "operations": {
      "chat_completions": {
        "method": "POST",
        "path": "/api/v1/chat/completions",
        "modes": ["analysis"]
      }
    },
    "rate_limit_per_minute": 10,
    "request_bytes": 65536,
    "response_bytes": 1048576,
    "timeout_seconds": 30
  },
  "research": {
    "base_url": "https://api.example.org",
    "credential_env": "RESEARCH_API_TOKEN",
    "operations": {
      "lookup": {
        "method": "GET",
        "path": "/v1/lookup",
        "modes": ["observation"]
      }
    },
    "rate_limit_per_minute": 20,
    "request_bytes": 32768,
    "response_bytes": 1048576,
    "timeout_seconds": 10
  }
}
```

These are illustrative settings, not live endpoints, credentials, endorsements, or proof of GitHub App
installation. The gateway consumes a pre-minted installation access token; token issuance/rotation,
GitHub App setup, deployment secrets, provider approvals and outbound firewall configuration must be
done by an authorized operator. Service hosts and operation paths come only from trusted server
configuration. Restrict deployment egress to those configured hosts as a separate network control.
Never add a broad token or private key to the repository.

Requests must declare `data_classification` as `public` or `synthetic`, and provide `provenance` with
`source`, `revision`, and a SHA-512 digest. The gateway does not perform PII detection or independently
authenticate declared provenance: only send data that has been reviewed and authorized for the
configured provider. `observation` is GET-only; `analysis` may invoke configured analysis operations.
The `authority` mode and all other classifications are rejected. The multi-LLM council now uses this
gateway and requires an explicit classification; caller-supplied credentials are rejected.

Successful requests and transport failures yield a bounded in-memory `scandoc-network-receipt/1`.
It binds the operation, declared source provenance, request digest, upstream status/response digest,
outcome and observed timestamp. It contains no request or response body or credentials. This is a
best-effort temporal audit receipt, not a trusted timestamp, source attestation, geometry commitment,
Sentinel, or authority token. Receipts are lost on process restart and only the most recent 512 are
retained per process. Rate limits are likewise per process; they are not a distributed quota.

## Deployment and validation boundary

The gateway is disabled by default, is not wired into the browser UI, and does not change GitHub
repository visibility, GitHub Pages, Vercel projects, DNS, production deployments, or native firing.
No provider credentials or repository allowlists are configured by this change. Before production use,
operators must provide shared rate limiting and durable protected audit retention if required, enforce
egress at the hosting network, establish provider/data approvals and PII controls, test short-lived
credential rotation, and review hosting access logs and retention. Never treat a successful network
response or receipt as qualification or permission to write.

Offline tests exercise the policy and receipt behavior with an injected transport. No live provider,
private repository, deployment, DNS change, merge, or native gate is exercised by the tests.

## Next MDL

ASSESS the actual hosting plan, exact repository allowlist, approved LLM/models, research API hosts,
data handling rules, and whether shared rate limiting and audit retention are required. ACT only after
those settings and the deployment egress boundary are approved. TEST against mocked endpoints first,
then separately approved read-only staging resources. RECORD the configuration owner, provider scopes,
credential rotation, test evidence, retention and remaining risks. Generate the next MDL only from that
reviewed evidence; do not infer production readiness from this local implementation.

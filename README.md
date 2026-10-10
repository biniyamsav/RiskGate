# RiskGate API

RiskGate is an asynchronous FastAPI service that accepts transaction and
account context, asks a configured LLM to assess fraud risk, and returns a
validated decision with a score and explanations.

> **Current status:** This project is an early-stage API scaffold, not a
production fraud-prevention system. Risk evaluation is model-generated and is
not independently verified against payment outcomes or a trained fraud model.
Do not use the response as the sole basis for high-impact financial decisions.

## Contents

- [What it does](#what-it-does)
- [How a prediction works](#how-a-prediction-works)
- [Requirements](#requirements)
- [Configure](#configure)
- [Run locally](#run-locally)
- [API reference](#api-reference)
- [Errors and troubleshooting](#errors-and-troubleshooting)
- [Tests](#tests)
- [Docker](#docker)
- [Project layout](#project-layout)
- [Security and production readiness](#security-and-production-readiness)

## What it does

- Validates nested transaction, account, device, and location input with
  Pydantic.
- Uses an OpenAI-compatible asynchronous chat-completions client. The current
  dependency setup supports Groq or OpenAI.
- Requests a JSON assessment and validates it against the response schema.
- Exposes a health endpoint and generated OpenAPI documentation.

The evaluator currently asks the LLM to apply these score bands:

| Score | Action |
| --- | --- |
| 0–29 | `ALLOW` |
| 30–69 | `REVIEW` |
| 70–100 | `DENY` |

These are instructions in the model prompt, not deterministic rules enforced
by the application. The API validates that the score is between 0 and 100 and
the action is one of the allowed values; it does not verify that the action
matches the score band.

## How a prediction works

1. FastAPI validates the request against `TransactionAssessmentRequest`.
2. A dependency constructs an `AsyncOpenAI` client for Groq or OpenAI.
3. `RiskEvaluatorService` sends the configured model a system prompt and the
   serialized transaction, requesting JSON mode.
4. The response content is parsed as JSON and validated as a
   `TransactionAssessmentResponse`.
5. An upstream request or parsing failure is reported as HTTP 503.

The API does not persist requests or assessment results. It does send all
submitted request fields to the configured LLM provider. Do not send payment
card numbers, credentials, or other sensitive information unless you have
reviewed the provider's data-handling terms and have an appropriate legal basis.

## Requirements

- Python 3.11 or newer (the Docker image uses Python 3.11)
- pip
- A Groq or OpenAI API key for live prediction requests

## Configure

Settings are read by Pydantic Settings from process environment variables and
from `.env` in the process working directory. Create a `.env` file in the
`riskgate-api` project directory. There is currently no checked-in
`.env.example` file.

Example for Groq:

```dotenv
APP_NAME="RiskGate API"
DEBUG=false
API_V1_STR="/api/v1"

LLM_PROVIDER="groq"
LLM_MODEL="openai/gpt-oss-20b"
GROQ_API_KEY="replace-with-your-groq-api-key"
```

Example for OpenAI:

```dotenv
APP_NAME="RiskGate API"
DEBUG=false
API_V1_STR="/api/v1"

LLM_PROVIDER="openai"
LLM_MODEL="replace-with-an-available-openai-model"
OPENAI_API_KEY="replace-with-your-openai-api-key"
```

Use a model ID that is currently available to your provider account and
supports the chat-completions JSON response format used by this application.
Provider model catalogs and availability change; check the provider's current
model list rather than assuming an older model ID still works. The Groq
example is a starting point, not a guarantee of account access.

Configuration details:

| Variable | Purpose | Default |
| --- | --- | --- |
| `APP_NAME` | FastAPI application title and health response name | `RiskGate API` |
| `DEBUG` | FastAPI debug mode; keep disabled outside local development | `true` in code |
| `API_V1_STR` | Prefix for versioned API routes | `/api/v1` |
| `LLM_PROVIDER` | Use `groq` or `openai` | `groq` |
| `LLM_MODEL` | Model ID sent to chat completions | `llama-3.3-70b-versatile` |
| `GROQ_API_KEY` | API key used when `LLM_PROVIDER=groq` | Empty |
| `OPENAI_API_KEY` | API key used for any non-`groq` provider setting | Empty |
| `OLLAMA_BASE_URL` | Defined in settings, but not currently used by the client dependency | `http://localhost:11434` |
| `OLLAMA_MODEL` | Defined in settings, but not currently used by the evaluator | `llama3` |

The current dependency code selects Groq only when `LLM_PROVIDER` is exactly
`groq`; every other value falls through to the OpenAI client. Setting
`LLM_PROVIDER=ollama` does **not** currently configure an Ollama connection.
The evaluator always sends `LLM_MODEL` as its model ID.

Never commit `.env` or put real API keys in source control, screenshots, issue
reports, or logs. `.gitignore` excludes `.env` and virtual environments; verify
your staged changes before pushing.

## Run locally

Run these commands from the project root directory.

### Windows PowerShell

```powershell
py -3 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Before starting the server, create `.env` manually using one of the examples
in [Configure](#configure).

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

By default, Uvicorn serves the API at `http://127.0.0.1:8000`.

## API reference

Interactive API docs are generated by FastAPI:

- Deployed Swagger UI: https://riskgate-9hys.onrender.com/docs
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI schema: `http://127.0.0.1:8000/openapi.json`

### `GET /health`

Returns application and configured model metadata. This is a basic liveness
check; it does not contact the LLM provider or prove that prediction requests
will succeed.

Example:

```json
{
  "status": "ok",
  "app_name": "RiskGate API",
  "provider": "groq",
  "model": "openai/gpt-oss-20b"
}
```

### `POST /api/v1/predictions`

Submit a transaction for model-based risk assessment.

Example request:

```json
{
  "transaction_id": "txn_2026_000123",
  "order": {
    "amount": 249.99,
    "currency": "USD",
    "item_category": "Electronics"
  },
  "user_account": {
    "account_age_days": 12,
    "failed_login_attempts_24h": 1,
    "past_chargebacks_count": 0
  },
  "device_context": {
    "ip_address": "203.0.113.10",
    "is_vpn_or_proxy": false,
    "device_fingerprint_hash": "device-hash-123456"
  },
  "location": {
    "billing_country": "US",
    "shipping_country": "US"
  }
}
```

Example success response:

```json
{
  "transaction_id": "txn_2026_000123",
  "risk_score": 12,
  "action": "ALLOW",
  "risk_factors": [],
  "summary_reasoning": "No significant risk signals were identified."
}
```

The response is model-generated; the example is illustrative and does not
represent a guaranteed decision.

Request validation currently requires:

- `transaction_id`: non-empty string.
- `order.amount`: number greater than zero.
- `order.currency`: exactly three characters.
- `order.item_category`: non-empty string.
- `user_account.account_age_days`, `failed_login_attempts_24h`, and
  `past_chargebacks_count`: non-negative integers.
- `device_context.ip_address`: string; `is_vpn_or_proxy`: boolean;
  `device_fingerprint_hash`: string of at least eight characters.
- `location.billing_country` and `shipping_country`: two-character strings.

### `GET /api/v1/model/info`

This route is **not currently implemented**. The endpoint mentioned in older
scaffold documentation will return 404 until a route is added.

### PowerShell example

```powershell
$body = Get-Content .\transaction.json -Raw
Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/api/v1/predictions `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

Save the request JSON example above as `transaction.json` before running this
command.

## Errors and troubleshooting

| HTTP status | Meaning |
| --- | --- |
| `200` | Health check or prediction succeeded. |
| `422` | The request body is missing required fields or violates schema validation. |
| `503` | LLM request failed, the provider returned unusable/empty content, or the response did not match the expected schema. |
| `500` | An unexpected server-side failure occurred, including possible client setup failures. |

For a 503, inspect the JSON response's `detail` field and the server logs. Check
the API key, provider account/model access, model ID, provider availability,
quota, and whether the model supports JSON mode. Confirm that the server is
started from the project directory so `.env` is found, and restart it after
changing configuration.

For a 422, use `/docs` to compare the submitted JSON to the nested request
schema. The API's response schema also constrains risk scores to 0–100 and
actions to `ALLOW`, `REVIEW`, or `DENY`.

## Tests

Install the requirements, then run:

```bash
pytest
```

The current test suite covers health response behavior and selected request
schema validation. It does not call the live LLM provider or verify real
provider credentials, model availability, quotas, or the evaluator's end-to-end
success path.

## Docker

Build and run from the project root directory:

```bash
docker build -t riskgate-api .
docker run --rm -p 8000:8000 --env-file .env riskgate-api
```

The image uses Python 3.11 and starts Uvicorn on `0.0.0.0:8000`. Provide a
locally-created `.env` file to Docker; do not copy secrets into the image or
build context. Ensure `.env` remains excluded by `.dockerignore` or another
build-context control before using Docker with credentials (this project does
not currently include a `.dockerignore`).

## Project layout

```text
RiskGate/
├── app/
│   ├── api/             # Health and prediction routes
│   ├── core/            # Provider dependency and error handling
│   ├── schemas/         # Pydantic request and response contracts
│   ├── services/        # LLM prompt and transaction evaluator
│   ├── config.py        # Environment-backed application settings
│   └── main.py          # FastAPI application factory and app instance
├── tests/               # Schema and API tests
├── Dockerfile
├── requirements.txt
└── README.md
```

## Security and production readiness

Before exposing this service to real traffic, address at least the following:

- Add authentication, authorization, rate limiting, and abuse controls.
- Set `DEBUG=false` and configure TLS and trusted proxy/network boundaries.
- Add request size limits, provider timeouts/retry policy, and operational
  metrics/alerting.
- Define a privacy and retention policy for transaction data sent to the LLM.
- Avoid returning raw upstream provider errors to callers in production.
- Add deterministic validation for score/action consistency and test with
  representative fraud scenarios and known outcomes.
- Evaluate the system for false positives, false negatives, model drift,
  prompt injection, and provider outages; provide human review/override paths.
- Add integration tests using mocked provider responses and keep live-provider
  tests separate from the default test suite.
- Add `.dockerignore` and verify that `.env`, virtual environments, test
  artifacts, and other local files cannot enter container images.

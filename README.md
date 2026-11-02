# Supplier Offer & Installation Compatibility Advisor

A working, candidate-built, independent Plancraft growth experiment for German plumbing/heating (SHK) businesses. **Not an official Plancraft product.** It uses the supplied dashboard layout as a visual reference but does not copy the reference's hypothetical green compatibility verdict or invented costs.

## What it actually does

1. Takes details of an existing domestic heating-circulation-pump installation, including connection, installed length, voltage and optional hydraulic/site information. An exact existing pump model can be matched to a manufacturer catalogue for reference (the installer must still verify site measurements). Optional photographed equipment label reading uses the server-side OpenAI API.
2. Accepts **two real supplier quotes**, each as pasted text, a selectable-text PDF (up to eight pages), or PNG/JPG/WEBP images. AI extracts model, article number, quote price, VAT basis, quantities, stated delivery/accessories, actual evidence excerpts and unknowns. Image input relies on OpenAI's vision capability.
3. Shows editable extracted values before analysis and preserves the original pasted/PDF quotation text and AI evidence. The model and article number are **never silently replaced** by the catalogue dropdown. A mismatch against original quotation evidence blocks the comparison (HTTP 422) until corrected; unknown models remain clearly unverified. Manual entry works without an AI key but does not count as completed AI extraction.
4. Matches exact product/article numbers against **nine documented pump variants**, sourced from Wilo and Grundfos. A mismatch or unrecognised variant is never approved.
5. Separately checks connection thread, length, voltage, fluid, system pressure/temperature, control features, hydraulic design limits and on-site follow-up. Each field is `verified_match`, `verified_conflict`, or `unknown` with a source. Max head and max flow are NOT an operating-point performance curve and never justify a hydraulic pass by themselves.
6. Calculates **gross installed cost** from quoted pump price, quantity, delivery, installer-entered extra parts and labour hours × installer-entered gross hourly rate. Excludes unconfirmed components from the known subtotal and withholds a total/winner when price components, VAT basis or quantities are unresolved. Never invents adapter, labour or supplier prices.
7. Explains lower known costs independently from technical suitability. Lists other documented **mechanically matching candidates** without pricing or declaring they are valid replacements.
8. Generates an actual two-page-or-longer **PDF comparison report** on the server, including offer totals, manufacturer checks, open questions, citations and alternatives. The previous JSON browser download is removed.
9. Includes an AI **Ask the Advisor** chat below each report, with short conversation history and suggested questions. The server recomputes the comparison for each request and shares a limited verified technical/cost context with the model; it does not send raw quotations to chat or allow chat to invent compatibility/parts/prices. A configured OpenAI key is required to answer.
10. Offers an outbound link to Plancraft's project-folder features, with anonymous analytics events recorded to SQLite.

## Run locally

You need Python 3.11+ (3.12 recommended). No JavaScript build step is required.

```bash
cd supplier-advisor
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY for live AI document extraction.
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000**. Both endpoints and the frontend are served from the same app. Add the AI key to `.env` **on the server** (never in HTML, JavaScript, or a Git repository). `OPENAI_MODEL` defaults to `gpt-4.1-mini` for newcomers; the user may keep `gpt-6.1-sol` in their existing `.env`. If you have no key, select **Or enter the offer details yourself** to exercise the deterministic checks and cost calculator. Real AI extraction is not verified until a key has been configured and a real request succeeds.

For a service health check, visit `http://localhost:8000/health`. It reports AI key configuration (not provider balance or live model connectivity).

## Deploy

`Dockerfile` is included for Render, Railway, Fly.io or any Docker-compatible host. Create a web service with the repository and Dockerfile, set `OPENAI_API_KEY` and optionally `OPENAI_MODEL` as **secret server environment variables**, then configure a persistent directory for `EVENTS_DB_PATH` (e.g., `/data/events.sqlite3`) if you intend to measure real visitors across restarts. Optionally set a strong `METRICS_TOKEN` for the private `/api/admin/metrics` endpoint. Without a persistent volume, analytics will be lost when the filesystem resets. Serve with HTTPS through the host. Test the actual public URL on mobile and desktop after deployment, including an authenticated real AI request, before claiming a fully operational live experiment. File content is handled in memory, but the user's quotes/images are sent to the AI provider for extraction; explain this in public trial privacy information.

**No public URL has been deployed or verified in this supplied code bundle.** Deployment requires a hosting account and a valid OpenAI API key.

## API routes

- `GET /health`: application readiness and AI-key-present flag.
- `GET /api/catalogue`: official-source records and exact model variants.
- `POST /api/installation/extract-label`: optional pump-label PNG/JPG/WEBP image; live OpenAI vision API required.
- `POST /api/supplier/extract`: multipart `offer_a`, `offer_b` text + optional `file_a`, `file_b`; live OpenAI API required. Always review extracted results.
- `POST /api/supplier/analyze`: JSON containing `installation`, exactly two `offers`, and `vat_rate_percent`; deterministic manufacturer-based preliminary fit and cost assessment. Hard-blocks incompatible original quote versus selected product identity.
- `POST /api/supplier/report.pdf`: accepts the same JSON, validates and recalculates it, returns a genuine downloadable PDF.
- `POST /api/supplier/chat`: JSON with `comparison` (same input), `question`, optional `history`; an evidence-grounded conversational explanation (not an installation approval). Live OpenAI API is required.
- `GET /api/admin/metrics`: authenticated real unique-session event counts and post-comparison CTA rate; set `METRICS_TOKEN` and send header `X-Metrics-Key`. Disabled without a token.
- `POST /api/events`: validates and persists an anonymous measured UI event (`landing_view`, `tool_started`, `ai_result_generated`, `comparison_completed`, `result_used`, `plancraft_cta_clicked`). An outbound click does not prove a lead or a Plancraft signup.

## Source/evidence handling

See `data/pumps.json` and `SOURCE_REGISTER.md`. Records identify **exact article numbers**, mechanical dimensions, 230 V supply and only selected supported operating data. Some manufacturer fields are intentionally null. There are **no product retail prices** in the catalogue: prices come from the user's actual supplier quotations, not manufacturer list prices. Grundfos variants are from the **Germany/Austria/Switzerland Model E** listing in the manufacturer's booklet; country and exact product article number matter.

### Engineering and safety boundaries

- The status is **“Checks pending”** even if length and connections match. Real hydraulic suitability requires a flow-versus-head design point checked against the actual manufacturer pump curve. Manufacturer approval, electrical protection, pressure drop, mounting, union fit, clearance and site conditions must be checked professionally.
- If the model/article or installation details are insufficient, return **cannot verify / unknown**, not a safe verdict. Conflicting dimensions or voltage are clearly flagged.
- Supplier quote extraction may fail or be inaccurate; no default fake offers or prices are shown. A manually selected catalogue product is evidence for published specs, not evidence that the supplier actually quoted that product.
- Only text-based PDFs are parsed; scanned PDF pages must be uploaded as images or transcribed. No OCR is silently claimed. A document must be <= 8 MB and PDFs <= 8 pages. Other limits are in the code.
- There is deliberately no automatic adapter-selection engine. Extra parts are costs entered or confirmed by the installer, not made-up AI estimates; a mismatched pump is not approved merely because extra cost was entered.
- The budget field can be displayed, but unquoted catalogue alternatives cannot be truthfully compared against a budget.
- No external electrical control wiring or glycol compatibility is guaranteed from matching labels alone.
- Only anonymous session/event names are stored in the local SQLite event database; the tool does not store raw supplier documents or quotes. Production deployment still requires an appropriate privacy policy, access controls and a data-retention decision.
- The app checks and tracks clicks on an official Plancraft feature page. It does **not** integrate with Plancraft's APIs or claim endorsement.

## Tests

```bash
python -m pytest -q
# Run uvicorn on port 8765 in another terminal for browser interaction tests:
uvicorn app.main:app --host 127.0.0.1 --port 8765
python tests/browser_flow.py
python tests/browser_revision.py
```

The browser script uses Playwright/Chromium and a transport bridge because sandbox browser navigation to localhost is blocked. It executes the real frontend in Chromium against the real local FastAPI calculation endpoint, with **clearly synthetic** supplier quote fixtures. It is not a test of AI-provider availability. The screenshots `preview-*.png` show synthetic testing results; the actual page loads empty without sample values.

## What is not verified / not yet done

- Live OpenAI model calls and new chat answers: **not tested in this development container** (no user API key provided). The user previously confirmed that supplier extraction worked in their own localhost session; this upgraded bundle still requires a fresh live test with their key.
- The new PDF endpoint has been generated, text-checked and visually rendered with synthetic test fixtures; this is not evidence of real supplier pricing.
- The review flow now blocks the exact article/model mismatch reported on 2 Nov 2026 (original 4215516/4215515 versus erroneously selected 4215513/4215514).
- Public deployment: **not done** (no hosting account supplied).
- Real SHK professional validation, market traffic, qualified leads: **not measured**.
- Accessory-part pricing sourced from suppliers or manufacturer compatibility notices: **not implemented**. Instead, the user enters confirmed extra costs and the result shows uncertainty honestly.
- Dynamic supplier catalogue / universal plumbing compatibility: **outside this experiment**.

See `EXPERIMENT_PLAN.md` for the hypothesis, metrics and testing method. Do not present planned success criteria or synthetic QA results as observed acquisition or user feedback.

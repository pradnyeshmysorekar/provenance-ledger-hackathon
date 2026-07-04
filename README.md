# Provenance-Native Media Asset Ledger

Built for the **Backblaze Generative Media Hackathon** (Genblaze + B2).

## What this is

A generative-media pipeline that treats **Backblaze B2 as a governed data
asset, not a dumb bucket.** Every generated image or audio asset is stored in
B2 alongside a SHA-256–verified provenance manifest (provider, model, prompt,
parameters, timestamp), and every manifest is indexed into a queryable
**DuckDB ledger** — so "what did we generate, with what model, when, and can
we prove it hasn't been tampered with" becomes a SQL query, not a manual
bucket crawl.

This directly targets the hackathon's **"B2 Storage + Data Orchestration"**
judging criterion, which most generation-novelty submissions will treat as an
afterthought.

## Architecture

```
 prompt --> Genblaze Pipeline --> NVIDIA NIM (image/audio) --> asset + manifest
                                          |
                                          v
                              Backblaze B2 (ObjectStorageSink,
                              HIERARCHICAL key layout)
                                          |
                                          v
                         DuckDB ledger (asset_ledger table)
                         queryable by provider / model / date / verified
```

- **Generation + storage:** `src/pipeline.py` — wraps Genblaze's `Pipeline`
  API with an NVIDIA NIM image or audio provider and a B2-backed
  `ObjectStorageSink`.
- **Ledger:** `src/ledger.py` — DuckDB table that indexes every run's
  manifest fields for querying.
- **CLI:** `src/cli.py` — ties the two together (`generate`, `list`,
  `stats`, `query`).

### Why image + audio, not video

NVIDIA NIM's video models (Cosmos, Edify) are enterprise-gated as of 2026 and
return an auth failure on free-tier keys. This project targets **image**
(Stable Diffusion 3.5) and **audio** (Riva TTS) — both confirmed accessible
on the free tier — to keep the entire build at **zero cost**, per project
ground rules. This is a scope decision, not a limitation of the
architecture: a video provider adapter can be added later with one new
`.step()` call once/if enterprise access is available.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in .env with your real B2 and NVIDIA NIM credentials
```

**Credentials you need (both free tier, zero cost):**
1. Backblaze B2 — Application Key (`B2_KEY_ID`, `B2_APP_KEY`) for the
   `provenance-ledger-hackathon` bucket.
2. NVIDIA NIM — API key from build.nvidia.com (`NVIDIA_API_KEY` /
   `NVAPI_KEY` — check the installed `genblaze-nvidia` package's own README
   for the exact variable name it expects; both are set in `.env.example`
   as a safe default).

## Usage

```bash
# Generate an image and record its provenance
python -m src.cli generate --modality image --prompt "a studio photo of a brass teapot"

# Generate a short TTS audio clip
python -m src.cli generate --modality audio --prompt "Hello, world."

# See what's in the ledger
python -m src.cli list

# Summary stats
python -m src.cli stats

# Arbitrary SQL over the ledger
python -m src.cli query --sql "SELECT provider, model, verified FROM asset_ledger"
```

## Judging-criteria mapping (for submission write-up)

| Criterion | How this project addresses it |
|---|---|
| Real-World Utility | Any team or individual producing AI media at volume needs an audit trail — proving what was generated, by which model, and that the asset hasn't been altered since. This is that audit trail as a product. |
| Production Readiness | Structured schema, credential-gated, error-checked (`require_credentials`), queryable via SQL rather than ad-hoc file inspection. |
| B2 Storage + Data Orchestration | Core thesis of the project — B2 objects are indexed, hierarchically keyed, and made queryable, not just stored. |
| Use of Genblaze | Uses `Pipeline`, `Step`/provider invocation, `ObjectStorageSink`, `KeyStrategy`, and the manifest/verification API directly. |

## Submission checklist (Devpost)

- [ ] Public GitHub repo with this code + setup instructions
- [ ] List of AI providers/models used (NVIDIA NIM: Stable Diffusion 3.5, Riva TTS)
- [ ] Explanation of B2 + Genblaze usage (use the table above as a starting point)
- [ ] ~3-minute demo video showing `generate` → `list` → `query` end to end
- [ ] Submit before Aug 3, 2026, 5pm ET
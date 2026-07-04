"""
Core generation pipeline for the Provenance-Native Media Asset Ledger.

Runs a single Genblaze step against an NVIDIA NIM model, persists the
resulting asset (and its provenance manifest) to Backblaze B2, and
returns the full result object so the caller (CLI) can hand it to the
ledger for indexing.

NOTE on modalities: NVIDIA's Cosmos/Edify VIDEO models are enterprise
-gated as of 2026 and return AUTH_FAILURE on free-tier keys. This
project intentionally targets IMAGE and AUDIO modalities, which are
confirmed accessible on the free tier — keeping the whole build at
zero cost, per project ground rules.
"""
from genblaze_core import Modality, ObjectStorageSink, KeyStrategy, Pipeline
from genblaze_s3 import S3StorageBackend
from genblaze_google import ImagenProvider
from genblaze_nvidia import NvidiaAudioProvider

from . import config

# Google Imagen — confirmed current model as of this hackathon (per Google's
# own live API documentation, not a stale training-data reference).
DEFAULT_IMAGE_MODEL = "imagen-4.0-generate-001"
DEFAULT_AUDIO_MODEL = "nvidia/magpie-tts-multilingual"  # kept for later extension; not part of MVP scope


def _storage_sink() -> ObjectStorageSink:
    backend = S3StorageBackend.for_backblaze(
        config.B2_BUCKET_NAME,
        key_id=config.B2_KEY_ID,
        app_key=config.B2_APP_KEY,
        region=config.B2_REGION,
    )
    # HIERARCHICAL key strategy keeps assets organized as
    # provider/model/date/run-id in the bucket, which is what
    # the ledger's directory-scan fallback relies on.
    return ObjectStorageSink(backend, key_strategy=KeyStrategy.HIERARCHICAL)


def run_image_generation(prompt: str, model: str = DEFAULT_IMAGE_MODEL, **params):
    """Generate a single image asset and persist it + its manifest to B2."""
    config.require_credentials()
    storage = _storage_sink()

    result = (
        Pipeline("provenance-ledger-image")
        .step(
            ImagenProvider(),
            model=model,
            prompt=prompt,
            modality=Modality.IMAGE,
            params=params,
        )
        .run(sink=storage, timeout=600)
    )
    return result


def run_audio_generation(prompt: str, model: str = DEFAULT_AUDIO_MODEL, **params):
    """Generate a single audio asset and persist it + its manifest to B2."""
    config.require_credentials()
    storage = _storage_sink()

    result = (
        Pipeline("provenance-ledger-audio")
        .step(
            NvidiaAudioProvider(),
            model=model,
            prompt=prompt,
            modality=Modality.AUDIO,
            params=params,
        )
        .run(sink=storage, timeout=600)
    )
    return result


def summarize_result(result) -> dict:
    """Flatten a Genblaze run result into the fields the ledger stores."""
    step = result.run.steps[0]
    if not getattr(step, "assets", None):
        error_detail = getattr(step, "error", None) or "no assets returned — see Genblaze's own step-failure output above for the exact reason (auth, model access, or rate limit)."
        raise RuntimeError(f"Generation step produced no asset: {error_detail}")
    asset = step.assets[0]
    return {
        "run_id": result.run.id if hasattr(result.run, "id") else None,
        "provider": step.provider if hasattr(step, "provider") else None,
        "model": step.model if hasattr(step, "model") else None,
        "prompt": step.prompt if hasattr(step, "prompt") else None,
        "asset_url": asset.url,
        "sha256": asset.sha256,
        "manifest_uri": result.manifest.manifest_uri,
        "canonical_hash": result.manifest.canonical_hash,
        "verified": result.manifest.verify(),
    }

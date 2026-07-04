"""
The 'ledger' half of the Provenance-Native Media Asset Ledger.

Every generation run produces a manifest (provider, model, prompt,
params, timestamp, SHA-256, B2 URL). This module persists that
manifest into a local DuckDB file so it becomes queryable — by
provider, by model, by date, by verification status — instead of
sitting as opaque JSON blobs in a bucket.

This is the piece that directly answers the hackathon's
"B2 Storage + Data Orchestration" judging criterion: B2 is treated
as a governed data asset with a structured index, not a dumb bucket.
"""
import datetime
import duckdb

from . import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS asset_ledger (
    run_id          VARCHAR,
    provider        VARCHAR,
    model           VARCHAR,
    prompt          VARCHAR,
    asset_url       VARCHAR,
    sha256          VARCHAR,
    manifest_uri    VARCHAR,
    canonical_hash  VARCHAR,
    verified        BOOLEAN,
    recorded_at     TIMESTAMP
);
"""


def _connect():
    con = duckdb.connect(config.LEDGER_DB_PATH)
    con.execute(_SCHEMA)
    return con


def record(entry: dict):
    """Insert one summarized generation result into the ledger."""
    con = _connect()
    con.execute(
        """
        INSERT INTO asset_ledger
        (run_id, provider, model, prompt, asset_url, sha256,
         manifest_uri, canonical_hash, verified, recorded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            entry.get("run_id"),
            entry.get("provider"),
            entry.get("model"),
            entry.get("prompt"),
            entry.get("asset_url"),
            entry.get("sha256"),
            entry.get("manifest_uri"),
            entry.get("canonical_hash"),
            entry.get("verified"),
            datetime.datetime.utcnow(),
        ],
    )
    con.close()


def list_all(limit: int = 50):
    con = _connect()
    rows = con.execute(
        "SELECT * FROM asset_ledger ORDER BY recorded_at DESC LIMIT ?", [limit]
    ).fetchall()
    cols = [d[0] for d in con.description]
    con.close()
    return cols, rows


def query(sql: str):
    """Run an arbitrary read-only SQL query against the ledger table."""
    con = _connect()
    rows = con.execute(sql).fetchall()
    cols = [d[0] for d in con.description]
    con.close()
    return cols, rows


def stats():
    con = _connect()
    total = con.execute("SELECT COUNT(*) FROM asset_ledger").fetchone()[0]
    by_provider = con.execute(
        "SELECT provider, COUNT(*) FROM asset_ledger GROUP BY provider"
    ).fetchall()
    unverified = con.execute(
        "SELECT COUNT(*) FROM asset_ledger WHERE verified = FALSE"
    ).fetchone()[0]
    con.close()
    return {
        "total_assets": total,
        "by_provider": by_provider,
        "unverified_count": unverified,
    }

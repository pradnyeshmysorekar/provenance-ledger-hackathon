"""
CLI for the Provenance-Native Media Asset Ledger.

Usage:
    python -m src.cli generate --modality image --prompt "a brass teapot"
    python -m src.cli generate --modality audio --prompt "Hello, world."
    python -m src.cli list
    python -m src.cli stats
    python -m src.cli query --sql "SELECT provider, COUNT(*) FROM asset_ledger GROUP BY provider"
"""
import argparse
import sys

from . import pipeline, ledger


def cmd_generate(args):
    if args.modality == "image":
        result = pipeline.run_image_generation(args.prompt, model=args.model or pipeline.DEFAULT_IMAGE_MODEL)
    elif args.modality == "audio":
        result = pipeline.run_audio_generation(args.prompt, model=args.model or pipeline.DEFAULT_AUDIO_MODEL)
    else:
        print(f"Unsupported modality: {args.modality}", file=sys.stderr)
        sys.exit(1)

    entry = pipeline.summarize_result(result)
    ledger.record(entry)

    print("Generation complete and recorded in ledger:")
    for k, v in entry.items():
        print(f"  {k}: {v}")


def cmd_list(args):
    cols, rows = ledger.list_all(limit=args.limit)
    print(" | ".join(cols))
    for row in rows:
        print(" | ".join(str(c) for c in row))


def cmd_stats(args):
    s = ledger.stats()
    print(f"Total assets recorded : {s['total_assets']}")
    print(f"Unverified assets     : {s['unverified_count']}")
    print("By provider:")
    for provider, count in s["by_provider"]:
        print(f"  {provider}: {count}")


def cmd_query(args):
    cols, rows = ledger.query(args.sql)
    print(" | ".join(cols))
    for row in rows:
        print(" | ".join(str(c) for c in row))


def main():
    parser = argparse.ArgumentParser(description="Provenance-Native Media Asset Ledger CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_gen = sub.add_parser("generate", help="Generate a media asset and record its provenance")
    p_gen.add_argument("--modality", choices=["image", "audio"], required=True)
    p_gen.add_argument("--prompt", required=True)
    p_gen.add_argument("--model", default=None, help="Override default model for the modality")
    p_gen.set_defaults(func=cmd_generate)

    p_list = sub.add_parser("list", help="List recent ledger entries")
    p_list.add_argument("--limit", type=int, default=20)
    p_list.set_defaults(func=cmd_list)

    p_stats = sub.add_parser("stats", help="Show summary stats over the ledger")
    p_stats.set_defaults(func=cmd_stats)

    p_query = sub.add_parser("query", help="Run a raw SQL query against the ledger")
    p_query.add_argument("--sql", required=True)
    p_query.set_defaults(func=cmd_query)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

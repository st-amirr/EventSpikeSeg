#!/usr/bin/env python3
"""Generate the technology-independent actor-local SRAM manifest."""

from __future__ import annotations

import argparse

from eventspikeseg.asic.sram_manifest import write_sram_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", required=True, help="ASIC export directory")
    parser.add_argument("--output", help="Output JSON path (default: EXPORT/sram_manifest.json)")
    parser.add_argument("--maximum-bank-depth", type=int, default=65_536)
    args = parser.parse_args()
    output = write_sram_manifest(
        args.export,
        args.output,
        maximum_bank_depth=args.maximum_bank_depth,
    )
    print(output)


if __name__ == "__main__":
    main()

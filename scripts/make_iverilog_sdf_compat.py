#!/usr/bin/env python3
"""Create simulation-only ASAP7/SDF copies compatible with Icarus.

Icarus 12 does not parse OpenSTA's conditional ``COND`` timing arcs and does
not drive the delayed-input arguments of timing-check system tasks.  The
functional cell equations use those delayed inputs, so alias them to the real
ports. Unconditional cell IOPATH delays remain SDF annotated; OpenSTA remains
authoritative for full interconnect timing.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

DIRECT_DELAYED_PORTS = ("CLK", "D", "ENA", "RESETN", "SE", "SETN", "SI")


def strip_unsupported_sdf_blocks(text: str) -> tuple[str, dict[str, int]]:
    lines = text.splitlines(keepends=True)
    output: list[str] = []
    skipped = {"conditional_arcs": 0, "interconnect_arcs": 0, "timingcheck_blocks": 0}
    index = 0
    while index < len(lines):
        line = lines[index]
        kind = None
        if re.match(r"^\s*\(COND(?:ELSE)?(?:\s|\()", line):
            kind = "conditional_arcs"
        elif re.match(r"^\s*\(INTERCONNECT\s", line):
            kind = "interconnect_arcs"
        elif re.match(r"^\s*\(TIMINGCHECK(?:\s|\()", line):
            kind = "timingcheck_blocks"
        if kind is not None:
            skipped[kind] += 1
            balance = line.count("(") - line.count(")")
            index += 1
            while balance > 0 and index < len(lines):
                balance += lines[index].count("(") - lines[index].count(")")
                index += 1
            if balance != 0:
                raise ValueError("unbalanced conditional SDF timing arc")
            continue
        output.append(line)
        index += 1
    return "".join(output), skipped


def strip_unsupported_cells(
    text: str, *, max_cells: int | None = None
) -> tuple[str, int, int]:
    """Remove empty cells and escaped instance names rejected by Icarus."""

    lines = text.splitlines(keepends=True)
    output: list[str] = []
    empty_removed = 0
    escaped_removed = 0
    kept = 0
    index = 0
    while index < len(lines):
        if not re.match(r"^\s*\(CELL\s*$", lines[index]):
            output.append(lines[index])
            index += 1
            continue
        block: list[str] = []
        balance = 0
        while index < len(lines):
            block.append(lines[index])
            balance += lines[index].count("(") - lines[index].count(")")
            index += 1
            if balance == 0:
                break
        if balance != 0:
            raise ValueError("unbalanced SDF CELL block")
        joined = "".join(block)
        instance = re.search(r"(?m)^\s*\(INSTANCE\s+([^)]*)\)", joined)
        if "(IOPATH " not in joined:
            empty_removed += 1
        elif instance is not None and "\\" in instance.group(1):
            escaped_removed += 1
        else:
            output.extend(block)
            kept += 1
            if max_cells is not None and kept >= max_cells:
                output.extend(")\n")
                break
    return "".join(output), empty_removed, escaped_removed


def normalize_header_for_iverilog(text: str) -> str:
    """Fill header fields and typ values required by Icarus's strict parser."""

    text = text.replace('(SDFVERSION "3.0")', '(SDFVERSION "2.1")', 1)
    text = text.replace(
        ' (DESIGN "resident_actor_tile_pnr_top")\n',
        ' (DESIGN "resident_actor_tile_pnr_top")\n (DATE "")\n',
        1,
    )
    text = text.replace(' (PROGRAM "STA")\n', ' (PROGRAM "STA")\n (VERSION "")\n', 1)
    text = re.sub(
        r'(?m)^( \(PROCESS ")([-+]?\d+(?:\.\d+)?)::'
        r'([-+]?\d+(?:\.\d+)?)("\))$',
        lambda match: f"{match.group(1)}{match.group(2)}{match.group(4)}",
        text,
    )
    return re.sub(
        r"(?m)^( \((?:VOLTAGE|PROCESS|TEMPERATURE) )"
        r"([-+]?\d+(?:\.\d+)?)::([-+]?\d+(?:\.\d+)?)(\))$",
        lambda match: (
            f"{match.group(1)}{match.group(2)}:{match.group(2)}:"
            f"{match.group(3)}{match.group(4)}"
        ),
        text,
    )


def patch_timing_models(text: str) -> tuple[str, int, int]:
    aliases = 0
    timing_checks = 0
    output: list[str] = []
    declaration = re.compile(r"^(\s*)wire\s+([^;]*\bdelayed_[^;]*);\s*$")
    for line in text.splitlines(keepends=True):
        if re.match(
            r"^\s*\$(?:setuphold|width|recrem|hold|setup|recovery|removal)\b",
            line,
        ):
            timing_checks += 1
            continue
        output.append(line)
        if re.match(r"^\s*reg\s+notifier;\s*$", line.rstrip("\r\n")):
            output.append("\tinitial notifier = 1'b0;\n")
        match = declaration.match(line.rstrip("\r\n"))
        if not match:
            continue
        names = [part.strip() for part in match.group(2).split(",")]
        for port in DIRECT_DELAYED_PORTS:
            delayed = f"delayed_{port}"
            if delayed in names:
                output.append(f"{match.group(1)}assign {delayed} = {port};\n")
                aliases += 1
    return "".join(output), aliases, timing_checks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdf", type=Path, required=True)
    parser.add_argument("--stdcells", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-cells", type=int)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    sdf_text, removed = strip_unsupported_sdf_blocks(
        args.sdf.read_text(encoding="utf-8", errors="strict")
    )
    sdf_text, empty_cells, escaped_cells = strip_unsupported_cells(
        sdf_text, max_cells=args.max_cells
    )
    sdf_text = normalize_header_for_iverilog(sdf_text)
    sdf_out = args.output_dir / "enc1_depthwise_beta48_iverilog.sdf"
    # Icarus's SDF lexer rejects CRLF even though its Verilog lexer accepts it.
    sdf_out.write_bytes(sdf_text.replace("\r\n", "\n").encode("utf-8"))

    cell_dir = args.output_dir / "stdcells"
    if cell_dir.exists():
        shutil.rmtree(cell_dir)
    cell_dir.mkdir()
    aliases = 0
    model_timing_checks = 0
    files = 0
    for source in sorted(args.stdcells.glob("*.v")):
        patched, count, check_count = patch_timing_models(
            source.read_text(encoding="utf-8", errors="strict")
        )
        (cell_dir / source.name).write_text(patched, encoding="utf-8")
        aliases += count
        model_timing_checks += check_count
        files += 1
    if (files == 0 or aliases == 0 or model_timing_checks == 0
            or empty_cells == 0 or not all(removed.values())):
        raise ValueError(
            f"unexpected compatibility transform: files={files}, "
            f"aliases={aliases}, timing_checks={model_timing_checks}, "
            f"empty_cells={empty_cells}, escaped_cells={escaped_cells}, "
            f"removed={removed}"
        )
    summary = {
        "simulation_only": True,
        "conditional_sdf_arcs_removed": removed["conditional_arcs"],
        "interconnect_sdf_arcs_removed": removed["interconnect_arcs"],
        "timingcheck_blocks_removed": removed["timingcheck_blocks"],
        "empty_cell_blocks_removed": empty_cells,
        "escaped_instance_cell_blocks_removed": escaped_cells,
        "unconditional_iopath_delays_preserved": True,
        "delayed_input_aliases_added": aliases,
        "unsupported_model_timing_checks_removed": model_timing_checks,
        "stdcell_files": files,
        "limitation": (
            "Icarus cannot parse OpenSTA INTERCONNECT/conditional arcs or implement "
            "timing checks; extracted OpenSTA reports remain authoritative for full "
            "path setup/hold timing, while this replay annotates unconditional cell IOPATHs"
        ),
    }
    (args.output_dir / "iverilog_compat_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()

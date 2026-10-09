#!/usr/bin/env python3
"""Build an extracted source/drain-parallel bank from qualified SKY130 TG cells.

Each gate and body terminal remains an explicit macro pin so the first bank
can be physically qualified without inventing a gate-routing topology.
"""
from __future__ import annotations
import argparse, json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE = "eventspikeseg:analog-layout"
RC = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc"
SRC = ROOT / "artifacts/analog_asic/layout/sky130_transmission_gate/sky130_transmission_gate_raw.mag"

def docker(ep: str, args: list[str], stdin: str, out: Path) -> str:
    p = subprocess.run(["docker", "run", "--rm", "-i", "-v", f"{ROOT}:/workspace",
        "-e", "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root",
        "-w", f"/workspace/{out.relative_to(ROOT).as_posix()}", "--entrypoint", ep,
        IMAGE, *args], input=stdin, text=True, capture_output=True, timeout=240, cwd=ROOT)
    log = p.stdout + p.stderr
    if p.returncode:
        raise RuntimeError(f"{ep} failed ({p.returncode}):\n{log[-4000:]}")
    return log

def parse_mag(path: Path):
    sections: dict[str, list[tuple[int,int,int,int]]] = {}
    sec = None
    for line in path.read_text(encoding="ascii").splitlines():
        if line.startswith("<< ") and line.endswith(" >>"):
            sec = line[3:-3]
            if sec in {"end", "properties", "checkpaint", "labels"}: sec = None
        elif sec and line.startswith("rect "):
            a = tuple(map(int, line.split()[1:]))
            sections.setdefault(sec, []).append(a)
    return sections

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=4)
    n = ap.parse_args().count
    if not 1 <= n <= 256: raise ValueError("bank count must be 1..256")
    if not SRC.exists(): raise FileNotFoundError(SRC)
    out = ROOT / f"artifacts/analog_asic/layout/sky130_parallel_tg_bank_{n}"
    out.mkdir(parents=True, exist_ok=True)
    src = parse_mag(SRC)
    stride = 600
    # Buses run beyond the cell's active geometry. Individual TG pins attach
    # through short same-layer M1 stems at their qualified A/B metal rails.
    xlo, xhi = -44, (n-1)*stride + 44
    wires = [(xlo-20,-220,xhi+20,-180), (xlo-20,1300,xhi+20,1340)] # A/B buses
    for i in range(n):
        dx = i*stride
        wires += [(dx-54,-200,dx-34,340), (dx+34,500,dx+54,1320)]
    src.setdefault("metal1", []).extend(wires)
    data = ["magic", "tech sky130A", "magscale 1 2", "timestamp 0"]
    for layer, rects in src.items():
        data.append(f"<< {layer} >>")
        for i in range(n):
            dx = i * stride
            data.extend("rect " + " ".join(map(str, (x1+dx,y1,x2+dx,y2))) for x1,y1,x2,y2 in rects)
    data.append("<< labels >>")
    port=1
    def label(name: str, x: int, y: int, layer: str = "metal1", is_port: bool = True):
        nonlocal port
        if layer == "psubdiff": bounds=(x-10,y-8,x+10,y+8)
        elif layer == "nsubdiff": bounds=(x-10,y-8,x+10,y+8)
        else: bounds=(x-20,y-20,x+20,y+20)
        data.append(f"rlabel {layer} s {bounds[0]} {bounds[1]} {bounds[2]} {bounds[3]} 4 {name}")
        if is_port:
            data.append(f"port {port} nsew"); port += 1
    label("A", -44, -200)
    label("B", (n-1)*stride+44, 1320)
    for i in range(n):
        dx=i*stride
        label(f"EN{i}", dx, 280); label(f"ENB{i}", dx, 1180)
    for i in range(n):
        dx=i*stride
        label("BULKP", dx-110, 1163, "nsubdiff", is_port=(i==0))
        label("BULKN", dx-110, 258, "psubdiff", is_port=(i==0))
    data += ["<< end >>", ""]
    top=f"sky130_parallel_tg_bank_{n}_raw"; cell=f"sky130_parallel_tg_bank_{n}"
    (out/f"{top}.mag").write_text("\n".join(data),encoding="ascii")
    tcl="\n".join([f"load {top}","drc check","drc count","extract all","ext2spice lvs","ext2spice scale off",
        f"ext2spice -o {cell}.spice","ext2spice cthresh 0","ext2spice rthresh infinite",f"ext2spice -o {cell}_pex.spice",
        f"gds write {cell}.gds","save","quit -noprompt",""])
    args=["magic","-dnull","-noconsole","-rcfile",RC]
    log=docker("magic",args[1:],tcl,out); (out/"magic_extract.log").write_text(log,encoding="utf-8")
    m=re.search(r"Total DRC errors found: (\d+)",log)
    if not m or m.group(1)!="0": raise RuntimeError("Magic DRC failed:\n"+log[-4000:])
    spice=(out/f"{cell}.spice").read_text(encoding="ascii")
    topmatch=re.search(r"(?im)^\.subckt\s+(\S+)(.*)$",spice)
    if not topmatch: raise RuntimeError("No extracted subckt")
    ports=topmatch.group(2).split()
    lines=spice.splitlines()
    subline=next(i for i,line in enumerate(lines) if re.match(r"(?i)^\.subckt\s+"+re.escape(top)+r"\b",line))
    while subline+1 < len(lines) and lines[subline+1].lstrip().startswith("+"):
        ports.extend(lines[subline+1].lstrip()[1:].split()); subline += 1
    expected=["A","B"]+[z+str(i) for i in range(n) for z in ("EN","ENB")]+["BULKP","BULKN"]
    if ports != expected: raise RuntimeError(f"Unexpected ports {ports}; expected {expected}")
    # Independent pins make all connections explicit in LVS; each switch has
    # its own controls and body terminals while A/B are physically common.
    refs=[f".subckt {top} "+" ".join(expected)]
    for i in range(n):
        refs += [f"Xn{i} B EN{i} A BULKN sky130_fd_pr__nfet_01v8 w=1 l=0.15",
                 f"Xp{i} B ENB{i} A BULKP sky130_fd_pr__pfet_01v8 w=2 l=0.15"]
    refs += [f".ends {top}",""]
    (out/"reference.spice").write_text("\n".join(refs),encoding="ascii")
    setup="/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/netgen/sky130A_setup.tcl"
    lv=docker("netgen-lvs",["-batch","lvs",f"{cell}.spice {top}",f"reference.spice {top}",setup,"lvs.out"],"",out)
    (out/"netgen_lvs.log").write_text(lv,encoding="utf-8")
    unique="Circuits match uniquely" in lv
    if not unique: raise RuntimeError("Netgen LVS failed:\n"+lv[-4000:])
    report={"cell":top,"count":n,"magic_drc_zero":True,"netgen_lvs_unique":unique,
        "gds_written":(out/f"{cell}.gds").exists(),"pex_capacitors":len(re.findall(r"(?im)^C\S+\s",(out/f"{cell}_pex.spice").read_text(encoding="ascii"))),
        "common_source_drain_buses":"physically routed metal1 A/B buses", "control_and_body":"explicit individual pins per TG; not yet shared or buffered",
        "scope":"Parallel source/drain bank of qualified 1um/2um SKY130 TG cells. No shared gate-driver layout, no rail/settling simulation, no mismatch/noise.","gds":str((out/f"{cell}.gds").relative_to(ROOT))}
    (out/"qualification.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())

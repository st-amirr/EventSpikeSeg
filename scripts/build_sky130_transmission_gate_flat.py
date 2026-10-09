"""Flatten SKY130 TG PCells into a routed, extractable switch macro."""
from __future__ import annotations
import json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"artifacts/analog_asic/layout/sky130_transmission_gate"
IMAGE="eventspikeseg:analog-layout"; RC="/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc"
CELL="sky130_transmission_gate"; TOP=CELL+"_raw"; NF="sky130_fd_pr__nfet_01v8_648S5X"; PF="sky130_fd_pr__pfet_01v8_XGAKDL"
def run(ep,args,stdin=None,timeout=180):
 p=subprocess.run(["docker","run","--rm","-i","-v",f"{ROOT}:/workspace","-e","PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root","-w","/workspace/artifacts/analog_asic/layout/sky130_transmission_gate","--entrypoint",ep,IMAGE,*args],input=stdin,text=True,capture_output=True,timeout=timeout,cwd=ROOT)
 s=p.stdout+p.stderr
 if p.returncode: raise RuntimeError(f"{ep} failed ({p.returncode}):\n{s[-4000:]}")
 return s
def parse(path,dy):
 sections={}; key=None
 for line in path.read_text(encoding="ascii").splitlines():
  if line.startswith("<< ") and line.endswith(" >>"):
   key=line[3:-3]
   if key in ("end","properties","checkpaint"): key=None
   else: sections.setdefault(key,[])
  elif key and line.startswith("rect "):
   v=list(map(int,line.split()[1:])); sections[key].append((v[0],v[1]+dy,v[2],v[3]+dy))
 return sections
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 pdir=ROOT/"artifacts/analog_asic/layout/sky130_tg_pcell"
 paths=[]
 for n in (NF,PF):
  p=pdir/(n+".mag"); (OUT/p.name).write_bytes(p.read_bytes()); paths.append(p)
 # NF occupies y~+-257; shift PF to +800 so wells have clearance.
 lay=parse(paths[0],0); pl=parse(paths[1],800)
 for layer,rects in pl.items(): lay.setdefault(layer,[]).extend(rects)
 # A connects NF upper diffusion to PF lower diffusion. B takes the other
 # pair around the cell perimeter. EN/ENB are isolated centerline gate straps.
 lay.setdefault("metal1",[]).extend([
  (-54,88,-34,712),        # A: left diffusion rails of NFET and PFET
  (34,-100,54,1012),       # B: right diffusion rails of NFET and PFET
  (-15,172,15,300),        # EN gate strap
  (-15,1081,15,1200),      # ENB gate strap
 ])
 mag=["magic","tech sky130A","magscale 1 2","timestamp 0"]
 for layer,rects in lay.items():
  mag.append(f"<< {layer} >>")
  mag.extend("rect "+" ".join(map(str,r)) for r in rects)
 mag += ["<< labels >>",
  "rlabel metal1 s -54 340 -34 370 4 A","port 1 nsew",
  "rlabel metal1 s 34 340 54 370 4 B","port 2 nsew",
  "rlabel metal1 s -15 280 15 310 4 EN","port 3 nsew",
  "rlabel metal1 s -15 1180 15 1210 4 ENB","port 4 nsew",
  "rlabel psubdiff s -120 250 -100 265 4 BULKN","port 5 nsew",
  "rlabel nsubdiff s -120 1155 -100 1170 4 BULKP","port 6 nsew","<< end >>",""]
 (OUT/(TOP+".mag")).write_text("\n".join(mag),encoding="ascii")
 tcl="\n".join((f"load {TOP}","drc check","drc count","extract all","ext2spice lvs","ext2spice scale off",f"ext2spice -o {CELL}.spice",f"gds write {CELL}.gds","save","quit -noprompt",""))
 args=["magic","-dnull","-noconsole","-rcfile",RC]; log=run(args[0],args[1:],tcl)
 (OUT/"magic_extract.log").write_text(log,encoding="utf-8")
 m=re.search(r"Total DRC errors found: (\d+)",log)
 if not m or m.group(1)!="0": raise RuntimeError("Magic DRC: "+log[-5000:])
 sp=(OUT/(CELL+".spice")).read_text(encoding="ascii"); (OUT/(CELL+".magic.spice")).write_text(sp,encoding="ascii")
 pextcl="\n".join((f"load {TOP}","extract all","ext2spice lvs","ext2spice scale off","ext2spice cthresh 0","ext2spice rthresh infinite",f"ext2spice -o {CELL}_pex.spice","quit -noprompt",""))
 pexlog=run(args[0],args[1:],pextcl)
 (OUT/"magic_pex.log").write_text(pexlog,encoding="utf-8")
 pex=(OUT/(CELL+"_pex.spice")).read_text(encoding="ascii")
 if len(re.findall(r"(?im)^C\S+\s",pex)) < 5: raise RuntimeError("Expected extracted interconnect/device coupling capacitances in PEX netlist")
 sub=re.search(r"(?im)^\.subckt\s+(\S+)(.*)$",sp)
 if not sub: raise RuntimeError("No extracted subckt: "+sp[:2000])
 ports=sub.group(2).split()
 if ports != ["A","B","EN","ENB","BULKP","BULKN"]: raise RuntimeError(f"Unexpected extracted TG pin order: {ports}")
 ref=OUT/"tg_reference.spice"
 ref.write_text(".subckt sky130_transmission_gate_raw A B EN ENB BULKP BULKN\nXn B EN A BULKN sky130_fd_pr__nfet_01v8 w=1 l=0.15\nXp B ENB A BULKP sky130_fd_pr__pfet_01v8 w=2 l=0.15\n.ends sky130_transmission_gate_raw\n",encoding="ascii")
 setup="/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/netgen/sky130A_setup.tcl"
 l=run("netgen-lvs",["-batch","lvs",f"{CELL}.spice {TOP}",f"{ref.name} {TOP}",setup,"tg_lvs.out"])
 (OUT/"netgen_lvs.log").write_text(l,encoding="utf-8")
 unique="Circuits match uniquely" in l
 if not unique: raise RuntimeError("TG LVS failed: "+l[-4000:])
 inspect=OUT/"inspect_tg.rb"
 inspect.write_text("\n".join(("include RBA","layout=Layout.new",f"layout.read('/workspace/{(OUT/(CELL+'.gds')).relative_to(ROOT).as_posix()}')",f"cell=layout.cell('{TOP}')","box=cell.bbox",'puts "bbox_um=#{(box.width*layout.dbu).round(4)}x#{(box.height*layout.dbu).round(4)}"',"")),encoding="ascii")
 kl=run("klayout",["-b","-r",f"/workspace/{inspect.relative_to(ROOT).as_posix()}"])
 bm=re.search(r"bbox_um=([0-9.]+)x([0-9.]+)",kl)
 if not bm: raise RuntimeError("KLayout did not report TG footprint: "+kl[-2000:])
 report={"cell":TOP,"magic_drc_zero":True,"lvs_unique":unique,"subckt":sub.group(1),"ports":ports,"devices":{"nfet":"1um/0.15um physical PCell","pfet":"2um/0.15um physical PCell"},"gds_bbox_um":[float(bm.group(1)),float(bm.group(2))],"parasitic_capacitors_extracted":len(re.findall(r"(?im)^C\S+\s",pex)),"parasitic_resistance_extraction":"not available through installed Magic 8.3.306 flow; wire RC not included","gds":str((OUT/(CELL+".gds")).relative_to(ROOT)),"scope":"flattened physical TG PCell pair; LVS-checked body pins, extracted capacitances and extracted-switch simulation"}
 (OUT/"qualification.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(report,indent=2))
if __name__=="__main__": main()

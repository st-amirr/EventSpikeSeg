"""Isolate long-bin state drift in the extracted weighted MIM array."""
from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"artifacts/analog_asic"
CELL="sky130_cap_trim_weighted_array"
LAYOUT=OUT/"layout"/CELL
IMAGE="eventspikeseg:analog-ngspice47" if "--ngspice47" in sys.argv[1:] else "eventspikeseg:analog-ngspice36"

def main()->int:
    standard_only="--standard-only" in sys.argv[1:]
    ideal_caps="--ideal-caps" in sys.argv[1:]
    flat_devices="--flat-devices" in sys.argv[1:]
    clamp_state="--clamp-state" in sys.argv[1:]
    op_start="--op-start" in sys.argv[1:]
    tight="--tight" in sys.argv[1:]
    small_gmin="--small-gmin" in sys.argv[1:]
    no_gauss="--no-gauss" in sys.argv[1:]
    ideal_internal="--ideal-internal" in sys.argv[1:]
    no_rs1="--no-rs1" in sys.argv[1:]
    no_rs2="--no-rs2" in sys.argv[1:]
    device_limit=next((int(sys.argv[i+1]) for i,a in enumerate(sys.argv[:-1]) if a=="--device-limit"),1020)
    bank_filter=next((sys.argv[i+1].upper() for i,a in enumerate(sys.argv[:-1]) if a=="--bank"),None)
    common_plate="--common-plate" in sys.argv[1:]
    common_state="--common-state" in sys.argv[1:]
    newer_sim="--ngspice47" in sys.argv[1:]
    leak_value=next((sys.argv[i+1] for i,a in enumerate(sys.argv[:-1]) if a=="--leak-ohms"),None)
    native_mim="--native-mim" in sys.argv[1:]
    init_internals="--init-internals" in sys.argv[1:]
    init_hold_us=float(next((sys.argv[i+1] for i,a in enumerate(sys.argv[:-1]) if a=="--init-hold-us"),"0.1"))
    if native_mim and not flat_devices:
        raise ValueError("--native-mim requires --flat-devices")
    RES=OUT/"results"; BENCH=OUT/"benches"; RES.mkdir(parents=True,exist_ok=True); BENCH.mkdir(parents=True,exist_ok=True)
    spice=(LAYOUT/f"{CELL}_pex.spice").read_text(encoding="ascii")
    m=re.search(rf"(?im)^\.subckt\s+{CELL}([^\n]*(?:\n\+[^\n]*)*)",spice)
    if not m: raise RuntimeError("Missing extracted weighted-cap array")
    pins=m.group(1).replace("+"," ").split(); nodes=[]; plate_nodes=set()
    for pin in pins:
        if pin.startswith("STATE_"):
            nodes.append("sa" if "COARSE_P" in pin or "FINE_P" in pin else "sb")
        elif pin.startswith("PLATE_"):
            name=pin.lower(); nodes.append(name); plate_nodes.add(name)
        else: raise RuntimeError(f"Unexpected array pin {pin}")
    suffix=("icmim_" if init_internals else "")+(f"hold{init_hold_us:g}us_" if init_hold_us != 0.1 else "")+("nativemim_" if native_mim else "")+(f"leak{leak_value}_" if leak_value else "")+("ng47_" if newer_sim else "")+("commonplate_" if common_plate else "")+("commonstate_" if common_state else "")+(f"{bank_filter.lower()}_" if bank_filter else "")+(f"n{device_limit}_" if device_limit != 1020 else "")+("idealinternal" if ideal_internal else ("nors1" if no_rs1 else ("nors2" if no_rs2 else ("nogauss" if no_gauss else ("gmin" if small_gmin else ("tight" if tight else ("op" if op_start else ("clamp" if clamp_state else ("ideal" if ideal_caps else ("flat" if flat_devices else ("standard" if standard_only else "pex")))))))))))
    array_netlist="reference.spice" if standard_only or ideal_caps else f"{CELL}_pex.spice"
    deck=BENCH/f"sky130_trim_array_state_drift_diag_{suffix}.cir"
    if ideal_caps:
        standard=(LAYOUT/"reference.spice").read_text(encoding="ascii").replace("sky130_fd_pr__cap_mim_m3_2","ideal_trim_cap")
        (BENCH/"trim_array_ideal_cap.spice").write_text(standard+"\n.subckt ideal_trim_cap c0 c1 w=1 l=1 mf=1\nCunit c0 c1 9.52f\n.ends ideal_trim_cap\n",encoding="ascii")
        array_netlist="../../benches/trim_array_ideal_cap.spice"
    variant_model = no_gauss or ideal_internal or no_rs1 or no_rs2 or leak_value is not None
    model_include='cap_mim_model_variant.spice' if variant_model else '../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice'
    if no_gauss or ideal_internal or no_rs1 or no_rs2 or leak_value is not None:
        model=(ROOT/'artifacts/analog_asic/pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice').read_text(encoding='ascii')
        if no_gauss:
            model=model.replace(" dev/gauss='0.01*2.8*(carea + cperim)/sqrt(wc*lc*mf)'", "")
        if ideal_internal:
            model=model.replace("c1 c0       a 'czero' tc1 = 0 tc2 = 0.0\nrs1 a        b1 'r1' tc1 = {tc1rm4} tc2 = {tc2rm4}\nrs2 b1        c1 'r2' tc1 = {tc1rvia4} tc2 = {tc2rvia4}", "c1 c0       c1 'czero' tc1 = 0 tc2 = 0.0")
        if no_rs1:
            model=model.replace("rs1 a        b1 'r1' tc1 = {tc1rm4} tc2 = {tc2rm4}", "rs1 a        b1 0")
        if no_rs2:
            model=model.replace("rs2 b1        c1 'r2' tc1 = {tc1rvia4} tc2 = {tc2rvia4}", "rs2 b1        c1 0")
        if leak_value is not None:
            model=model.replace(".ends sky130_fd_pr__cap_mim_m3_2", f"rleak c0 a {leak_value}\n.ends sky130_fd_pr__cap_mim_m3_2")
        (BENCH/model_include).write_text(model,encoding='ascii')
    flat_lines=[]; device_count=0
    if flat_devices:
        for line in (LAYOUT/"reference.spice").read_text(encoding="ascii").splitlines():
            if not line.startswith("XU"): continue
            if bank_filter and f"STATE_{bank_filter}_" not in line: continue
            if device_count >= device_limit: break
            match=re.match(r"(X\S+)\s+(\S+)\s+(\S+)\s+sky130_fd_pr__cap_mim_m3_2(.*)$",line)
            if not match: raise RuntimeError(f"Bad MIM instance line {line}")
            inst,plate,state,params=match.groups()
            node="sa" if common_state or "COARSE_P" in state or "FINE_P" in state else "sb"
            plate_node="plate_common" if common_plate else plate.lower(); plate_nodes.add(plate_node)
            if native_mim:
                cap_f = 2.0e-15 * 2.0 * 2.0 + 0.19e-15 * (2.0 + 2.0) * 2.0
                r1 = 0.047 * 2.0 / 2.0
                r2 = 0.38 / (2.0 * 2.0 / ((0.28 + 0.31 + 0.14) ** 2))
                flat_lines.extend([f"C{inst} {plate_node} a_{inst.lower()} {cap_f:.12g}",
                                   f"R1{inst} a_{inst.lower()} b_{inst.lower()} {r1:.12g}",
                                   f"R2{inst} b_{inst.lower()} {node} {r2:.12g}"])
            else:
                flat_lines.append(f"{inst} {plate_node} {node} sky130_fd_pr__cap_mim_m3_2{params}")
            device_count += 1
    wrdata="v(sa) v(sb) v(vcm)" + (" i(Vclampa) i(Vclampb)" if clamp_state else "")
    if flat_devices and not native_mim and not ideal_internal and device_count == 1020:
        wrdata += " v(xu0.a) v(xu0.b1) v(xu1019.a) v(xu1019.b1)"
    if native_mim and device_count == 1020:
        wrdata += " v(a_xu0) v(b_xu0) v(a_xu1019) v(b_xu1019)"
    precharge_edge=max(0.0,init_hold_us-0.01)
    init_source=f"Vinit_mem init_mem 0 PWL(0 1.8 {precharge_edge:g}u 1.8 {init_hold_us:g}u 0 5.1m 0)"
    ic_lines=[]
    if init_internals:
        if native_mim or not flat_devices:
            raise ValueError("--init-internals requires flat PDK subcircuit instances")
        ic_nodes=[f"v(xu{i}.{node})=0.9" for i in range(device_count) for node in ("a","b1")]
        for offset in range(0,len(ic_nodes),40):
            ic_lines.append((".ic " if offset==0 else "+ ")+" ".join(ic_nodes[offset:offset+40]))
    deck.write_text("\n".join([
        "* Isolated weighted MIM array: all 64 plates clamped at VCM",
        (".option scale=1u reltol=1e-9 abstol=1e-19 vntol=1e-12 method=gear maxord=2 gmin=1e-15" if small_gmin else (".option scale=1u reltol=1e-9 abstol=1e-19 vntol=1e-12 method=gear maxord=2" if tight else ".option scale=1u reltol=1e-6 abstol=1e-16 vntol=1e-10 method=gear maxord=2")),
        '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
        '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
        '.include "../pdk/sky130_fd_pr/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"',
        ".param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0",
        ".param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11",
        ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
        *([] if ideal_caps or native_mim else [f'.include "{model_include}"']),
        *([] if flat_devices else [f'.include "../layout/{CELL}/{array_netlist}"']),
        *ic_lines,
        "Vcm vcm 0 0.9", *[f"Vplate{index} {node} 0 0.9" for index,node in enumerate(sorted(plate_nodes))],
        "Csa sa vcm 21.84p", "Csb sb vcm 21.84p",
        *(["Vclampa sa vcm 0", "Vclampb sb vcm 0"] if clamp_state else ["Rsa sa vcm 1e12", "Rsb sb vcm 1e12"] + ([] if op_start else [
          ".model init_sw sw ron=1 roff=1e30 vt=0.9 vh=0.1", "Vinita inita 0 0.9", "Vinitb initb 0 0.9",
          init_source,
          "Sinit_a sa inita init_mem 0 init_sw", "Sinit_b sb initb init_mem 0 init_sw"])),
        *flat_lines, *([] if flat_devices else [f"Xarray {' '.join(nodes)} {CELL}"]), ".control", "set wr_singlescale", "set wr_vecnames",
        "tran 1u 5.1m 0 1u" + ("" if op_start else " uic"), f"wrdata ../results/sky130_trim_array_state_drift_diag_{suffix}.dat {wrdata}",
        "quit", ".endc", ".end",""]),encoding="ascii")
    cmd=["docker","run","--rm","--memory","4g","--cpus","2","-v",f"{ROOT}:/workspace:ro","-v",f"{OUT}:/workspace/artifacts/analog_asic",
         "-w","/workspace/artifacts/analog_asic/benches","--entrypoint","timeout",IMAGE,"180","ngspice","-b",deck.name]
    r=subprocess.run(cmd,text=True,capture_output=True,timeout=195,cwd=ROOT); log=r.stdout+r.stderr
    (RES/f"sky130_trim_array_state_drift_diag_{suffix}.log").write_text(log,encoding="utf-8")
    dat=RES/f"sky130_trim_array_state_drift_diag_{suffix}.dat"; rows=[]
    if dat.exists():
        for line in dat.read_text(encoding="utf-8").splitlines()[1:]:
            try: rows.append([float(x) for x in line.split()])
            except ValueError: pass
    if r.returncode or len(rows)<100 or not re.search(r"ngspice-\d+ done",log,re.I):
        raise RuntimeError(f"Array-only drift test failed rc={r.returncode}, rows={len(rows)}\n{log[-3000:]}")
    def near(t): return min(rows,key=lambda q:abs(q[0]-t*1e-6))
    report={"test":"isolated_weighted_mim_array_state_drift","completed":True,"simulator":"ngspice-47" if newer_sim else "ngspice-36","standard_cap_model_only":standard_only,"ideal_caps":ideal_caps,"flat_devices":flat_devices,"native_mim_element_expansion":native_mim,"device_limit":device_limit,"simulated_mim_devices":device_count if flat_devices else None,"explicit_mim_internal_initial_conditions":init_internals,"initial_state_precharge_hold_us":init_hold_us,"diagnostic_dielectric_bleed_ohms":leak_value,"state_held_by_ideal_source":clamp_state,"common_plate_net":common_plate,"all_states_mapped_to_sa":common_state,"operating_point_initialized":op_start,"tight_solver_tolerances":tight,"small_gmin":small_gmin,"no_dev_gauss":no_gauss,"ideal_internal_cap_model":ideal_internal,"series_rs1_bypassed":no_rs1,"series_rs2_bypassed":no_rs2,"all_plates_clamped_to_vcm":True,
        "state_at_0p9us_v":near(.9)[1:3],"state_at_4p9ms_v":near(4900)[1:3],
        "vcm_at_4p9ms_v":near(4900)[3],**({"state_clamp_current_at_4p9ms_a":near(4900)[4:6]} if clamp_state else {}),
        **({"mim_internal_nodes_at_4p9ms_v":near(4900)[6:10]} if flat_devices and not native_mim and not ideal_internal and device_count == 1020 else {}),
        **({"mim_internal_nodes_at_4p9ms_v":near(4900)[4:8]} if native_mim and device_count == 1020 and not clamp_state else {}),
        "scope":f"{device_count if flat_devices else 1020}-cap array {'native explicit C-R-R expansion of the PDK nominal values' if native_mim else ('flat SKY130 MIM instances' if flat_devices else ('ideal 9.52fF devices' if ideal_caps else ('reference netlist' if standard_only else 'PEX')))} only; selector MOS/plate switches omitted; plate nodes {'tied together' if common_plate else 'independently clamped'} at0.9V; state nodes {'tied together' if common_state else 'kept as separate P/N rails'} and {'held at VCM by ideal sources' if clamp_state else 'initialized to VCM and held by21.84pF loads with1TOhm returns'}."}
    (RES/f"sky130_trim_array_state_drift_diag_{suffix}.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2)); return 0

if __name__=="__main__": raise SystemExit(main())

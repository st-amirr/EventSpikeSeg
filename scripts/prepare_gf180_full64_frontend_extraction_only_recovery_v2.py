"""Reuse the completed full flat DRC, preserve truncated EXT, repeat only extraction."""
from pathlib import Path
import hashlib,json,re
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';d=B/'layout/gf180_full64_rms_frontend_v1'
old=R/'scripts/extract_gf180_full64_frontend_flat_exact_graph_v1.py'
new=R/'scripts/extract_gf180_full64_frontend_extraction_only_v2.py';assert not new.exists()
log=d/'flat_native_runtime_observation.log';raw=log.read_text();assert re.search(r'Total DRC errors found:\s*0\b',raw)
assert not (d/'flat_cap_qualification.json').exists()
ext=d/'gf180_full64_rms_frontend_v1_flat.ext';saved=d/'flat_initial_timeout_partial.ext';assert not saved.exists();saved.write_bytes(ext.read_bytes())
review=B/'results/gf180_full64_frontend_flat_runtime_stage_review_v1.json';assert not review.exists()
review.write_text(json.dumps({'runtime_stage_review_completed':True,'initial_native_timeout_seconds':1800,
 'full_flat_DRC_count':0,'extraction_complete':False,'partial_EXT_last_line':saved.read_text().splitlines()[-1],
 'finding':'Native full flat DRC completed successfully near the end of the bound. Extraction was then cut while writing its device list; the unterminated final record proves this EXT is incomplete and must not be exported as a qualified result.',
 'selected_repair':'Preserve truncated EXT, original Tcl and log. Recreate exactly the same flattened geometry from hash-checked immutable source MAG hierarchy. Reuse the completed flat DRC; run only capacitance/device extraction and exports with a new120s native bound, then exact native primitive graph comparison. No geometry, model, solver or analog-netlist repair.',
 'full_chip_layout_complete':False,'sha256':{p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [old,saved,log,d/'flat_single_pass.tcl']}},indent=2)+'\n')
s=old.read_text().replace("'1800',*args","'120',*args").replace('timeout=1815','timeout=135')
s=s.replace("'flat_native_runtime_observation.log'","'flat_native_extraction_only_runtime.log'")
s=s.replace("drc on\\ndrc style drc(full)\\ndrc check\\ndrc catchup\\ndrc count total\\n",'drc off\\n',1)
s=s.replace("'flat_single_pass.tcl'","'flat_extraction_only_reuse_DRC.tcl'").replace("'flat_cap_extraction.log'","'flat_cap_extraction_only_reuse_DRC.log'")
s=s.replace("assert re.search(r'Total DRC errors found:\\s*0\\b',log);cs=", "assert re.search(r'Total DRC errors found:\\s*0\\b',(d/'flat_native_runtime_observation.log').read_text());cs=")
s=s.replace("files={Path(__file__),qp,", "files={Path(__file__),qp,ROOT/'artifacts/analog_asic/results/gf180_full64_frontend_flat_runtime_stage_review_v1.json',d/'flat_native_runtime_observation.log',d/'flat_single_pass.tcl',d/'flat_initial_timeout_partial.ext',")
s=s.replace("'runtime_basis':'Previous actual2304MOS full64 flat extraction completed in approximately22minutes; this2397MOS parent adds93MOS frontend. One1800s native bound, same2CPU/2GB, single extraction, no geometry/solver sweep.'", "'runtime_basis':'Original1800s native pass completed full flat DRC0 then was cut during EXT device output. Preserve truncated file. One120s extraction-only recovery on the exact same hash-checked source geometry; completed native flat DRC result is reused explicitly, not rerun or fabricated.'")
s=s.replace("'scope':'Single full flat", "'flat_DRC_reused_from_completed_original_pass':True,'scope':'Extraction-only recovery with completed original full flat DRC0 reused for identical source geometry. Full flat")
new.write_text(s);print(new)

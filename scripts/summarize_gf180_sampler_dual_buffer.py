"""Audit nominal extracted dual-buffer loading evidence without accepting storage."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic/results'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    cases=[]; validated=[]
    for p in sorted(BASE.glob('gf180_sampler_dual_buffer*.json')):
        if p.name=='gf180_sampler_dual_buffer_boundary.json':continue
        report=json.loads(p.read_text())
        for name,expected in report['sha256'].items():
            if digest(ROOT/name)!=expected:raise ValueError('Changed evidence: '+name)
        validated.append((p,report))
        cases.append({'report':p.relative_to(ROOT).as_posix(),'report_sha256':digest(p),'simulation_completed':report['simulation_completed'],'settings':report.get('settings',{}),'held_measurement_time_s':report.get('held_measurement_time_s',5.001e-3),'five_ms_hold_completed':report.get('five_ms_hold_completed',report['simulation_completed']),'cases':report['cases']})
    fine=[(p,v) for p,v in validated if v.get('settings',{}).get('max_step_ns')==20 and v['simulation_completed']]
    comparisons=[]
    for p,v in fine:
        settings={k:x for k,x in v['settings'].items() if k!='max_step_ns'}
        coarse=[(q,w) for q,w in validated if w['simulation_completed'] and {k:x for k,x in w.get('settings',{}).items() if k!='max_step_ns'}==settings and w.get('settings',{}).get('max_step_ns',100)==100]
        for q,w in coarse:
            def deck(rep):
                paths=[ROOT/n for n in rep['sha256'] if n.endswith('.spice') and '/benches/' in n]
                assert len(paths)==1
                return re.sub(r'(?m)^tran .*$', 'TRAN_NORMALIZED',paths[0].read_text())
            if deck(v)!=deck(w):raise ValueError('Convergence decks differ beyond time step')
            comparisons.append({'fine':p.name,'coarse':q.name,'exact_deck_match_except_tran':True,'max_endpoint_difference_uv':max(abs(x['measurements_v'][key]-y['measurements_v'][key])*1e6 for x,y in zip(v['cases'],w['cases']) for key in x['measurements_v'])})
    output={'cases':cases,'convergence':comparisons,'read_restore_accepted':False,'full_chip_accepted':False,'scope':'Nominal schematic assembly of qualified cap-extracted sampler/OTA views; physical combined routing, noise, mismatch/PVT, RPEX, actual switched access, complete neuron and population service remain unqualified.'}
    p=BASE/'gf180_sampler_dual_buffer_boundary.json';p.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'report':str(p),'cases':len(cases),'convergence':comparisons},indent=2))
if __name__=='__main__':main()

"""Remove only byte-identical unreferenced intermediate copies of saved views."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'operations/storage_cleanup_20261013'
PAIRS={'6_1_merged.gds':'6_final.gds','6_1_fill.odb':'6_final.odb','5_2_route.odb':'5_route.odb',
       '5_3_fillcell.odb':'5_route.odb','4_1_cts.odb':'4_cts.odb','3_5_place_dp.odb':'3_place.odb',
       '3_4_place_resized.odb':'3_place.odb','3_3_place_gp.odb':'3_place.odb',
       '3_1_place_gp_skip_io.odb':'2_floorplan.odb','2_4_floorplan_pdn.odb':'2_floorplan.odb'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);plan_path=OUT/'duplicate_output_plan.json'
    results=(BASE/'orfs/results').resolve();assert results.is_relative_to(ROOT.resolve())
    live=subprocess.check_output(['docker','ps','--filter','name=ess-','--format','{{.ID}}'],text=True).strip()
    assert not live,'Do not clean intermediates while an ASIC job is live.'
    if args.apply:
        plan=json.loads(plan_path.read_text());removed=[]
        for entry in plan['candidates']:
            target=(ROOT/entry['remove']).resolve();keep=(ROOT/entry['keep']).resolve()
            assert target.is_relative_to(results) and keep.is_relative_to(results) and target!=keep
            assert target.is_file() and keep.is_file() and not target.is_symlink() and not keep.is_symlink()
            assert sha(target)==sha(keep)==entry['sha256']
            target.unlink();removed.append(entry)
        report=dict(removed_files=len(removed),reclaimed_bytes=sum(e['bytes'] for e in removed),
                    removed=removed,completed_utc=datetime.now(timezone.utc).isoformat(),
                    scope='Only byte-identical intermediate copies from completed physical macros; canonical views,hash-referenced artifacts,failed-job checkpoints,source layouts/netlists/logs retained.')
        (OUT/'duplicate_output_cleanup.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:report[k] for k in ['removed_files','reclaimed_bytes']},indent=2));return
    assert not plan_path.exists()
    pattern='|'.join(re.escape(n) for n in PAIRS)
    matched=subprocess.run(['rg','-l','-g','*.json',pattern,str(BASE/'assembly'),str(BASE/'results')],capture_output=True,text=True)
    assert matched.returncode in [0,1]
    protected=set();protected_basenames=set()
    def inspect(value):
        if isinstance(value,dict):
            for key,item in value.items():
                if isinstance(item,str) and re.fullmatch('[a-fA-F0-9]{64}',item):
                    key=key.replace('\\','/').removeprefix('/workspace/')
                    if key.rsplit('/',1)[-1] in PAIRS:
                        if '/' not in key:protected_basenames.add(key)
                        else:protected.add(key)
                inspect(item)
        elif isinstance(value,list):
            for item in value:inspect(item)
    for filename in matched.stdout.splitlines():inspect(json.loads(Path(filename).read_text(encoding='utf-8')))
    folders=set()
    for p in (BASE/'assembly').glob('*/physical_macro.json'):
        m=json.loads(p.read_text())
        if m.get('physical_implementation_completed'):folders.add(BASE/'orfs/results/gf180'/m['design']/m['variant'])
    cache={};candidates=[];skipped=[]
    def digest(p):
        if p not in cache:cache[p]=sha(p)
        return cache[p]
    for folder in sorted(folders):
        assert folder.resolve().is_relative_to(results)
        if not (folder/'6_final.gds').exists():continue
        for intermediate,canonical in PAIRS.items():
            p=folder/intermediate;q=folder/canonical
            if not p.is_file() or not q.is_file():continue
            relative=p.relative_to(ROOT).as_posix()
            if relative in protected or p.name in protected_basenames:
                skipped.append(dict(path=relative,reason='hash-referenced evidence'));continue
            if p.stat().st_size==q.stat().st_size and digest(p)==digest(q):
                candidates.append(dict(remove=relative,keep=q.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=digest(p)))
    plan=dict(candidates=candidates,protected=skipped,reclaimable_bytes=sum(e['bytes'] for e in candidates),
              scope='Explicit file paths inside resolved ORFS results root. Only completed macro intermediates identical to a retained canonical view. Hash-referenced intermediates and all failed-job folders excluded.')
    plan_path.write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(dict(candidate_files=len(candidates),reclaimable_bytes=plan['reclaimable_bytes'],protected_files=len(skipped)),indent=2))

if __name__=='__main__':main()

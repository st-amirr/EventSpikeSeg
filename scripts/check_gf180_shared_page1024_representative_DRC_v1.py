"""Three remaining exact geometry groups, native source GDS DRC only."""
from pathlib import Path
import hashlib,json,re,subprocess
from assemble_gf180_external_bank_service_full25_v5 import cells_read
from assemble_gf180_full_capacity_storage_gds_v2 import records,rec
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';D=B/'assembly/full25_shared_page1024_v8'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    mf=D/'physical_assembly.json';m=json.loads(mf.read_text());g=D/'eventspikeseg140k_shared_page1024_v7.gds';prefix,cells=cells_read(g.read_bytes());pd=B/'pdk/gf180_open_pdks_source/gf180mcu/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc';reports=[]
    for ix in [2,6,12]:
        q=D/'verification'/f'actor_{ix:02d}_DRC_only_v1';assert not q.exists();q.mkdir(parents=True);a=m['actor_regions'][ix];root=a['gds_cell'];needed=set()
        def visit(n):
            if n in needed:return
            needed.add(n)
            for t,d,v,b in records(cells[n]):
                if t==18:visit(v.rstrip(b'\0').decode())
        visit(root);sub=q/'actor_native_geometry.gds';sub.write_bytes(prefix+b''.join(cells[n] for n in sorted(needed))+rec(4,0))
        t='drc off\ngds read /workspace/'+sub.relative_to(R).as_posix()+'\nload '+root+'\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nputs "PHASE source DRC complete"\nquit -noprompt\n';tp=q/'native_check.tcl';tp.write_text(t)
        r=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','-i','--volume',f'{R}:/workspace','--workdir','/workspace/'+q.relative_to(R).as_posix(),'--entrypoint','timeout','eventspikeseg:analog-gf180-layout','120','magic','-dnull','-noconsole','-rcfile','/workspace/'+pd.relative_to(R).as_posix()],input=t,capture_output=True,text=True,timeout=135);log=r.stdout+r.stderr;lp=q/'native_check.log';lp.write_text(log);dc=re.search(r'Total DRC errors found:\s*(\d+)',log)
        o={'actor_index':ix,'actor':a['actor'],'native_command_returncode':r.returncode,'native_DRC_completed':r.returncode==0 and 'PHASE source DRC complete' in log,'full_parent_drc_count':int(dc[1]) if dc else None,'native_connectivity_proved':False,'scope':'ActualV8 representative sourceGDS fullDRC only;no flatten/extraction/wholechip claim. ExactnonTEXTrootgeometry groups justify actorcoverage.','sha256':{p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),mf,g,sub,tp,lp]}}
        (q/'qualification_attempt.json').write_text(json.dumps(o,indent=2)+'\n');reports.append(o);print(json.dumps({k:v for k,v in o.items() if k!='sha256'}),flush=True)
    (D/'representative_DRC_summary_v1.json').write_text(json.dumps(reports,indent=2)+'\n')
if __name__=='__main__':main()

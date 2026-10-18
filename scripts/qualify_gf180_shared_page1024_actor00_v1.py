"""Qualify new page-to-compute parent from actual emitted actor GDS."""
from pathlib import Path
import hashlib,json,re,subprocess
from assemble_gf180_external_bank_service_full25_v5 import cells_read
from assemble_gf180_full25_shared_page1024_v7 import labels
from assemble_gf180_full_capacity_storage_gds_v2 import records,rec
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';D=B/'assembly/full25_shared_page1024_v7';Q=D/'verification/actor_00_native_parent_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not Q.exists();Q.mkdir(parents=True);mf=D/'physical_assembly.json';m=json.loads(mf.read_text());a=m['actor_regions'][0];root=a['gds_cell'];flat=root+'_flat';g=D/'eventspikeseg140k_shared_page1024_v7.gds';prefix,cells=cells_read(g.read_bytes());needed=set()
    def visit(n):
        if n in needed:return
        needed.add(n)
        for t,d,v,b in records(cells[n]):
            if t==18:visit(v.rstrip(b'\0').decode())
    visit(root);subset=Q/'actor_native_geometry.gds';subset.write_bytes(prefix+b''.join(cells[n] for n in sorted(needed))+rec(4,0));ports=list(labels(cells[root]));defs={};inputs=[Path(__file__),mf,g,subset]
    def add(text,topname=None):
        for block in re.findall(r'(?mis)^\.subckt\s+.*?^\.ends[^\r\n]*',text):
            name=re.match(r'(?i)\.subckt\s+(\S+)',block)[1]
            if name=='reference':assert topname;block=re.sub(r'(?i)^(\.subckt\s+)reference',lambda m:m[1]+topname,block);name=topname
            if name in defs:assert defs[name].strip()==block.strip(),name
            else:defs[name]=block
    old=B/'assembly/full25_external_bank_service_v5/verification/actor_00_external_service_v5/reference.spice';page=B/'assembly/shared_reader_page1024_v1/verification/native_parent_v1/reference.spice';add(old.read_text(),'V6BASE');add(page.read_text(),'PAGE1024');inputs += [old,page]
    for c in ['gf180_candidate_penalty_subtractor_v2','gf180_fixed_body_tg_quarter_shorttracks']:
        d=B/'layout'/c;sp=d/(c+'.spice');cg=d/(c+'.gds');text=sp.read_text();ns={v.rstrip(b'\0').decode():'N'+sha(cg)[:8]+'_'+hashlib.sha256(v.rstrip(b'\0')).hexdigest()[:16] for t,dt,v,b in records(cg.read_bytes()) if t==6}
        for oldn in sorted(ns,key=len,reverse=True):text=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(oldn)+r'(?![A-Za-z0-9_])',ns[oldn],text)
        add(text);inputs += [sp,cg]
    pinmap={(s.split('.',1)[0],s.split('.',1)[1]):n['net'] for n in m['local_pin_nets'] if n['actor']==a['actor'] for s in n['endpoint_pins']}
    oldports=re.match(r'(?i)\.subckt\s+\S+\s+([^\r\n]+)',defs['V6BASE'])[1].split();pageports=re.match(r'(?i)\.subckt\s+\S+\s+([^\r\n]+)',defs['PAGE1024'])[1].split()
    ref='\n'.join(defs.values())+'\n.subckt reference '+' '.join(ports)+'\nXold '+' '.join(oldports)+' V6BASE\n'
    nodes=[('page_service__'+p if '__B' in p and '_STATE' in p else pinmap['page_service',p]) for p in pageports];ref+='Xpage '+' '.join(nodes)+' PAGE1024\n'
    for p in a['modules']:
        if p['instance'] not in ['page_up','page_restore']:continue
        c=p['cell'];d=B/'layout'/c;q=json.loads((d/'qualification.json').read_text());cg=d/(c+'.gds');cn='N'+sha(cg)[:8]+'_'+hashlib.sha256(c.encode()).hexdigest()[:16];ref+='X'+p['instance']+' '+' '.join(pinmap[p['instance'],n] for n in q['ports'])+' '+cn+'\n'
    ref+='.ends\n';rp=Q/'reference.spice';rp.write_text(ref);inputs.append(rp)
    t='drc off\ngds read /workspace/'+subset.relative_to(R).as_posix()+'\nload '+root+'\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nputs "PHASE source DRC complete"\ndrc off\nflatten -dotoplabels '+flat+'\nload '+flat+'\nsave '+flat+'\nextract no capacitance\nextract no coupling\nextract no adjust\nextract no resistance\nextract all\nfeedback save parent.feedback\next2spice lvs\next2spice hierarchy off\next2spice subcircuit top on\next2spice scale off\next2spice -o parent.spice\nputs "PHASE SPICE complete"\nquit -noprompt\n';tp=Q/'native_check.tcl';tp.write_text(t);inputs.append(tp);pd=B/'pdk/gf180_open_pdks_source/gf180mcu/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc'
    r=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','-i','--volume',f'{R}:/workspace','--workdir','/workspace/'+Q.relative_to(R).as_posix(),'--entrypoint','timeout','eventspikeseg:analog-gf180-layout','120','magic','-dnull','-noconsole','-rcfile','/workspace/'+pd.relative_to(R).as_posix()],input=t,capture_output=True,text=True,timeout=135);log=r.stdout+r.stderr;lp=Q/'native_parent_check.log';lp.write_text(log);inputs.append(lp);dc=re.search(r'Total DRC errors found:\s*(\d+)',log)
    o={'actor':a['actor'],'top_cell':flat,'parent_native_command_returncode':r.returncode,'parent_native_command_completed':r.returncode==0 and 'PHASE SPICE complete' in log,'full_parent_drc_count':int(dc[1]) if dc else None,'parent_native_extraction_written':(Q/'parent.spice').exists(),'independent_connectivity_accepted':False,'parent_nominal_simulation_completed':False,'full_chip_complete':False,'scope':'New emitted firstactor including native1024page,levelshift/gatedrestore,sharedDATA and unchanged V6BASE. SourcefullDRC thenfastflatconnectivity; no repeatedflatDRC orcapextraction. Reference independently composes original native source netlists, not extractedparent. Parentexactgraph stillrequired.','sha256':{p.relative_to(R).as_posix():sha(p) for p in inputs}}
    (Q/'qualification_attempt.json').write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({k:v for k,v in o.items() if k!='sha256'},indent=2))
if __name__=='__main__':main()

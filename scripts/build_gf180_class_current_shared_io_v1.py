"""Native analog restore and eight-column AGE/AMP row capture interface.

AGE and AMPLITUDE remain native adaptation voltage nodes, no membrane-domain
0.45V translation. AMP_BUFFERED comes from the existing resident AMP_BUF.
"""
from pathlib import Path
import collections,hashlib,json,re
from assemble_gf180_full25_physical_candidate_v5 import Library,pinlist,rect,label
from assemble_gf180_external_bank_service_full25_v5 import via
from assemble_gf180_full_capacity_storage_gds_v2 import begin,reference,rec
from gf180_compact_lvs_v2 import compact
import probe_gf180_mos_gate_cap as f
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';C='gf180_class_current_shared_io_v1';D=B/'layout'/C
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not D.exists();D.mkdir();f.OUT=D;lib=Library();children={};groups=collections.OrderedDict();body=[];mods=[];definitions=[];inputs=[]
 tg='gf180_fixed_body_tg_quarter_shorttracks';buf='gf180_candidate_penalty_subtractor_v2';hold='gf180_analog_commit_hold_buffer_v2'
 ports=['RECOV','STORAGE_REFERENCE','COMPUTE_REFERENCE','UP_BIAS','DOWN_BIAS','IO_BIAS','VDD','VSS']+[f'STATE{k}' for k in range(6)]+[f'OUTPUT{k}' for k in range(6)]+[f'DATA{k}' for k in range(8)]+[f'{kind}{k}{suffix}' for kind in ('RESTORE','SELECT') for k in range(6) for suffix in ('','B')]+[f'CAP{k}{suffix}' for k in range(8) for suffix in ('','B')]
 for c in (tg,buf,hold):
  d=B/'layout'/c;qf=d/'qualification.json';q=json.loads(qf.read_text());g=d/(c+'.gds');assert q['lvs_unique'] and q['magic_drc_count']==0 and sha(g)==q['sha256'][g.name];children[c]=(lib.load(g)[c],q,pinlist(d,c));definitions.append((d/(c+'.spice')).read_text());inputs.extend([qf,g,d/(c+'.spice')])
 row_y=0
 def place(tag,c,mapping):
  nonlocal row_y
  native,q,pins=children[c];bb=[round(v*1000) for v in q['bbox_um']];left=500000;ox=left-bb[0];oy=row_y-bb[1];top=row_y+bb[3]-bb[1];body.append(reference(native,ox,oy));assert set(mapping)==set(q['ports']);mods.append({'instance':tag,'cell':c,'gds_cell':native,'origin_dbu':[ox,oy],'bbox_dbu':[left,row_y,left+bb[2]-bb[0],top],'mapping':mapping})
  for pi,pin in enumerate(q['ports']):
   layer,x,y=pins[pin];x=round(x+ox);y=round(y+oy)
   if layer=='metal3':
    sx=left-2000-pi*2000;ey=top+10000+pi*3200;body.extend([rect(42,(min(sx,x)-200,y-200,max(sx,x)+200,y+200)),via(42,46,40,sx,y),rect(46,(sx-200,min(y,ey)-200,sx+200,max(y,ey)+200)),via(46,81,41,sx,ey)]);x,y=sx,ey
   else:assert layer=='metal5'
   groups.setdefault(mapping[pin],[]).append((tag,pin,x,y))
  row_y=top+10000+len(q['ports'])*3200+100000

 place('UP',buf,{'CANDIDATE':'RECOV','PENALTY':'STORAGE_REFERENCE','VCOM':'COMPUTE_REFERENCE','ADJUSTED':'SHIFTED','BIAS':'UP_BIAS','VDD':'VDD','VSS':'VSS'})
 for k in range(6):place(f'RESTORE{k}',tg,{'A':'SHIFTED','B':f'STATE{k}','EN':f'RESTORE{k}','ENB':f'RESTORE{k}B','VDD':'VDD','VSS':'VSS'})
 for k in range(6):place(f'SELECT{k}',tg,{'A':f'OUTPUT{k}','B':'SELECTED','EN':f'SELECT{k}','ENB':f'SELECT{k}B','VDD':'VDD','VSS':'VSS'})
 place('DOWN',buf,{'CANDIDATE':'SELECTED','PENALTY':'COMPUTE_REFERENCE','VCOM':'STORAGE_REFERENCE','ADJUSTED':'COMMIT_DATA','BIAS':'DOWN_BIAS','VDD':'VDD','VSS':'VSS'})
 for k in range(8):place(f'HOLD{k}',hold,{'DATA':'COMMIT_DATA','WRITE':f'CAP{k}','WRITEB':f'CAP{k}B','OUT':f'DATA{k}','BIAS':'IO_BIAS','VDD':'VDD','VSS':'VSS'})

 endpoint=0;track=row_y+100000;netrows=[];ground_attach=None
 for ni,(net,ends) in enumerate(groups.items()):
  ty=(max(p['bbox_dbu'][3]+10000+len(children[p['cell']][1]['ports'])*3200+20000 for p in mods if p['instance'] in {e[0] for e in ends})) if net in ('AGE','AMPLITUDE') else track+ni*3200;xs=[]
  for tag,pin,x,y in ends:
   ex=-20000-endpoint*6000;endpoint+=1;xs.append(ex);body.extend([rect(81,(min(x,ex)-220,y-220,max(x,ex)+220,y+220)),via(81,46,41,ex,y),rect(46,(ex-200,min(y,ty)-220,ex+200,max(y,ty)+220)),via(46,81,41,ex,ty)])
  body.append(rect(81,(min(xs)-1200,ty-220,max(xs)+1200,ty+220)))
  if net in ports:body.append(label(net,min(xs)-1000,ty))
  netrows.append({'net':net,'endpoint_pins':[tag+'.'+pin for tag,pin,*_ in ends]})
  if net=='VSS':ground_attach=(xs[0],ty)
 # Grounded M4 guards break the long lateral control-to-state coupling measured
 # in V1. Their M5 ground rail is above every signal track; no signal crossing via.
 gy=track+len(groups)*3200+10000;gx,gty=ground_attach;guards=[-20000-i*6000+3000 for i in range(endpoint+1)]
 for x in guards:body.extend([rect(46,(x-200,0,x+200,gy+220)),via(46,81,41,x,gy)])
 body.extend([rect(46,(gx-200,gty-220,gx+200,gy+220)),via(46,81,41,gx,gy),rect(81,(min(guards+[gx])-220,gy-220,max(guards+[gx])+220,gy+220))])
 # M4 shields do not intercept lateral coupling between the horizontal M5
 # endpoint escapes. Ground an M5 guard between each pair of local pin tracks.
 # Stop outside the native child bbox; connect only at a separate outer M4 rail.
 hx=-1400000;horizontal_guards=[]
 for p in mods:
  ys=sorted({e[3] for ends in groups.values() for e in ends if e[0]==p['instance']})
  for a,b in zip(ys,ys[1:]):
   assert b-a>=3200
   yy=(a+b)//2;horizontal_guards.append(yy);body.extend([rect(81,(hx-220,yy-220,p['bbox_dbu'][0]-500,yy+220)),via(81,46,41,hx,yy)])
 body.extend([rect(46,(hx-200,0,hx+200,gy+220)),via(46,81,41,hx,gy),rect(81,(hx-220,gy-220,min(guards)-220,gy+220))])
 root=C+'_parent';source=D/'source_parent.gds';source.write_bytes(lib.prefix+b''.join(lib.cells)+begin(root)+b''.join(body)+rec(7,0)+rec(4,0));ref='\n'.join(definitions)+'\n.subckt reference '+' '.join(ports)+'\n'
 for p in mods:ref+='X'+p['instance']+' '+' '.join(p['mapping'][pin] for pin in children[p['cell']][1]['ports'])+' '+p['cell']+'\n'
 ref+='.ends\n';rp=D/'reference.spice';rp.write_text(ref);(D/'placement_and_binding.json').write_text(json.dumps({'modules':mods,'nets':netrows},indent=2)+'\n')
 t='drc off\ngds read /workspace/'+source.relative_to(R).as_posix()+'\nload '+root+'\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\ndrc off\nflatten -dotoplabels '+C+'\nload '+C+'\nsave '+C+'\nextract no capacitance\nextract no coupling\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice hierarchy off\next2spice subcircuit top on\next2spice scale off\next2spice -o '+C+'.spice\ngds write '+C+'.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n';log=f.magic(t);(D/'extraction.log').write_text(log);dc=re.search(r'Total DRC errors found:\s*(\d+)',log);assert dc
 actual=(D/(C+'.spice')).read_text();src,si=compact(actual,C);rr,ri=compact(ref,'reference');(D/'source_compact.spice').write_text(src);(D/'reference_compact.spice').write_text(rr);assert si['primitive_devices']==ri['primitive_devices']
 setup='/workspace/'+f.PDK.relative_to(R).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl';nl=f.run(['netgen-lvs','-batch','lvs','source_compact.spice '+C,'reference_compact.spice reference',setup,'lvs.out']);(D/'netgen.log').write_text(nl);(D/'build_source.py').write_bytes(Path(__file__).read_bytes());xl=[l.split() for l in actual.replace('\n+',' ').splitlines() if l.startswith('X')];mos=sum(any(t in ['nfet_03v3','pfet_03v3'] for t in l) for l in xl);mim=sum(any(t.startswith('cap_mim_') for t in l) for l in xl)
 paths=[Path(__file__),source,rp,D/'extraction.log',D/'netgen.log',D/'source_compact.spice',D/'reference_compact.spice']+[D/(C+s) for s in ('.mag','.spice','.gds')]+inputs
 q={'cell':C,'ports':ports,'bbox_um':[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],'mos_count':mos,'native_mim_count':mim,'native_resistor_count':8,'compact_source_inventory':si,'magic_drc_count':int(dc[1]),'lvs_unique':'Circuits match uniquely' in nl,'source_layout_completed':True,'scope':'Native class-current IO: one shared upshift, six restore TGs to existing readout STATE0..5, six onehot OUTPUT mux TGs, shared downshift, eight analog row hold/output buffers. Numeric values remain analog. Existing class working caps/readout are separate and must be joined; trained synapse injection, forest, categorical sequencer, timing and model accuracy unqualified.','sha256':{p.relative_to(R).as_posix():sha(p) for p in paths}}
 (D/'initial_physical_result.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({k:v for k,v in q.items() if k not in ('ports','sha256')},indent=2));assert q['magic_drc_count']==0 # Independent exact graph required if native Netgen is ambiguous.
if __name__=='__main__':main()

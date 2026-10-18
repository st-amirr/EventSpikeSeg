"""Generate a new native class-score IO implementation from proven guarded routing.

Preserves the consumed adaptation implementation unchanged. Numeric state remains
analog; categorical restore/mux/capture phases are externally sequenced.
"""
from pathlib import Path
R=Path(__file__).resolve().parents[1]

def main():
 src=(R/'scripts/build_gf180_adaptation_shared_state_io_v6.py').read_text()
 src=src.replace('gf180_adaptation_shared_state_io_v6','gf180_class_current_shared_io_v1')
 src=src.replace("buf='gf180_amplitude_buffer_v2'", "buf='gf180_candidate_penalty_subtractor_v2'")
 a=src.index(' ports=[');b=src.index('\n for c in (tg,buf,hold):',a)
 src=src[:a]+" ports=['RECOV','STORAGE_REFERENCE','COMPUTE_REFERENCE','UP_BIAS','DOWN_BIAS','IO_BIAS','VDD','VSS']+[f'STATE{k}' for k in range(6)]+[f'OUTPUT{k}' for k in range(6)]+[f'DATA{k}' for k in range(8)]+[f'{kind}{k}{suffix}' for kind in ('RESTORE','SELECT') for k in range(6) for suffix in ('','B')]+[f'CAP{k}{suffix}' for k in range(8) for suffix in ('','B')]"+src[b:]
 a=src.index(" for kind,node in [('AGE','AGE')");b=src.index('\n endpoint=0;',a)
 src=src[:a]+"""
 place('UP',buf,{'CANDIDATE':'RECOV','PENALTY':'STORAGE_REFERENCE','VCOM':'COMPUTE_REFERENCE','ADJUSTED':'SHIFTED','BIAS':'UP_BIAS','VDD':'VDD','VSS':'VSS'})
 for k in range(6):place(f'RESTORE{k}',tg,{'A':'SHIFTED','B':f'STATE{k}','EN':f'RESTORE{k}','ENB':f'RESTORE{k}B','VDD':'VDD','VSS':'VSS'})
 for k in range(6):place(f'SELECT{k}',tg,{'A':f'OUTPUT{k}','B':'SELECTED','EN':f'SELECT{k}','ENB':f'SELECT{k}B','VDD':'VDD','VSS':'VSS'})
 place('DOWN',buf,{'CANDIDATE':'SELECTED','PENALTY':'COMPUTE_REFERENCE','VCOM':'STORAGE_REFERENCE','ADJUSTED':'COMMIT_DATA','BIAS':'DOWN_BIAS','VDD':'VDD','VSS':'VSS'})
 for k in range(8):place(f'HOLD{k}',hold,{'DATA':'COMMIT_DATA','WRITE':f'CAP{k}','WRITEB':f'CAP{k}B','OUT':f'DATA{k}','BIAS':'IO_BIAS','VDD':'VDD','VSS':'VSS'})
"""+src[b:]
 src=src.replace("'native_resistor_count':0", "'native_resistor_count':8")
 a=src.index("'scope':'Sharednativeanalogadaptationaccess:");b=src.index(",'sha256':",a)
 src=src[:a]+"'scope':'Native class-current IO: one shared upshift, six restore TGs to existing readout STATE0..5, six onehot OUTPUT mux TGs, shared downshift, eight analog row hold/output buffers. Numeric values remain analog. Existing class working caps/readout are separate and must be joined; trained synapse injection, forest, categorical sequencer, timing and model accuracy unqualified.'"+src[b:]
 src=src.replace("assert q['magic_drc_count']==0 and q['lvs_unique']", "assert q['magic_drc_count']==0 # Independent exact graph required if native Netgen is ambiguous.")
 p=R/'scripts/build_gf180_class_current_shared_io_v1.py';assert not p.exists();p.write_text(src)
 print(str(p))
if __name__=='__main__':main()

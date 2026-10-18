"""Construct one64-state shared-bus sequence from the completed2x2 baseline."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def main():
 p=R/'scripts/screen_gf180_compact_bank2x2_v4_native_sequence.py';s=p.read_text().replace('gf180_compact_memory_bank2x2_v4','gf180_compact_memory_bank8x8_v1')
 s=s.replace("[(0,1e-6),(1,20e-6)]","[(r,20e-6 if r==7 else 1e-6) for r in range(8)]").replace("[(0,5.03e-3),(1,5.13e-3)]","[(r,5.13e-3 if r==7 else 5.03e-3) for r in range(8)]")
 s=s.replace("for row,start in [(r,5.13e-3 if r==7 else 5.03e-3) for r in range(8)]:lines +=[", "for row,start in [(r,5.13e-3 if r==7 else 5.03e-3) for r in range(8)]:\n  if row not in [0,7]:lines +=[f'Vr{row} READ{row} 0 0'];continue\n  lines +=[")
 s=s.replace("[(0,1.,1.2),(1,1.4,1.3)]","[(c,1.+.05*c,1.4-.03*c) for c in range(8)]")
 s=s.replace("nodes=['STATE00','STATE01','STATE10','STATE11','READOUT0','READOUT1']","nodes=[f'STATE{r}{c}' for r in range(8) for c in range(8)]+[f'READOUT{c}' for c in range(8)]")
 s=s.replace('w.shape[1]==8','w.shape[1]==74')
 start=s.index('   for j,target in enumerate(');end=s.index("   r['VDD_supply_energy",start)
 s=s[:start]+'''   for j in range(64):
    row=j//8;col=j%8;target=1.4-.03*col if row==7 else 1.+.05*col
    release=22e-6 if row==7 else 3e-6;hold=5.021e-3 if row==7 else 5.001e-3;read=5.15e-3 if row==7 else 5.05e-3;base=sample(j+1,release);held=sample(j+1,hold);mask=(t>=release)&(t<=hold)
    record=dict(state=nodes[j],target_v=target,after_write_release_v=base,write_error_v=base-target,after5ms_v=held,max_hold_excursion_v=float(np.max(np.abs(w[mask,j+1]-base))),total_final_state_change_v=sample(j+1,5.19e-3)-held)
    if row in [0,7]:record.update(readout_v=sample(65+col,read),state_on_read_v=sample(j+1,read))
    states.append(record)
   r['states']=states;r['cases']=[{'sequence':'64states; overwrite row7, hold others, read rows0and7'}]
   r['max_write_error_v']=max(abs(x['write_error_v']) for x in states)
   r['max_hold_excursion_v']=max(x['max_hold_excursion_v'] for x in states)
   r['max_read_disturbance_v']=max(abs(x['total_final_state_change_v']) for x in states)
   increasing=all(states[c]['readout_v']<states[c+1]['readout_v'] for c in range(7));decreasing=all(states[56+c]['readout_v']>states[57+c]['readout_v'] for c in range(7))
   r['native_shared_bank_sequence_observed']=bool(r['max_write_error_v']<.02 and r['max_hold_excursion_v']<.02 and r['max_read_disturbance_v']<.02 and increasing and decreasing)
''' + s[end:]
 s=s.replace('One actual16MOS/4MIM2x2 shared-row/shared-column bank with all155 nonnegative routing-cap branches. Both rows initialized via real TG; row0 held while row1 is overwritten on shared DATA columns, then each held at least5ms with DATA rail stress before sequential native source-follower reads.', 'One actual256MOS/64MIM8x8 shared-row/shared-column bank with all2226 nonnegative routing-cap branches. All64 states initialized through real TGs; rows0-6 held while row7 is overwritten on shared DATA columns, then each state held at least5ms with DATA rail stress. Sequential native source-follower reads of rows0and7; six middle rows remain unselected. All64 analog states and8 read columns recorded; no ideal output buffer.')
 d=p.with_name('screen_gf180_compact_bank8x8_v1_native_sequence.py');assert not d.exists();d.write_text(s)
if __name__=='__main__':main()

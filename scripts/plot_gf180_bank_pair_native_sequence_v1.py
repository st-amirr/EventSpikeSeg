"""Article figure from the completed native transient; no fitted corrections."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';D=B/'assembly/full25_locally_decoded_storage_v1'
def main():
 s=B/'results/gf180_independent_bank_pair_v4_access_summary_v1.json';summary=json.loads(s.read_text());p=R/summary['report'];r=json.loads(p.read_text());data=p.with_suffix('.dat');w=np.loadtxt(data,skiprows=1);t=w[:,0]*1e6;states=[f'B{b}_STATE{y}{x}' for b in range(2) for y in range(8) for x in range(8)];at=lambda n:w[:,1+states.index(n)]
 plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False});fig,ax=plt.subplots(3,1,figsize=(10,9),sharex=True,layout='constrained')
 for n,c in [('B0_STATE00','#1769aa'),('B0_STATE07','#6fa8dc'),('B1_STATE70','#c55a11'),('B1_STATE77','#ed9d58')]:ax[0].plot(t,at(n),color=c,label=n)
 ax[0].hlines([1.4,1.33],2,50,colors=['#1769aa','#6fa8dc'],linestyles=':',linewidth=1);ax[0].hlines([.95,1.02],12,50,colors=['#c55a11','#ed9d58'],linestyles=':',linewidth=1);ax[0].set(ylabel='Stored voltage (V)',title='Native bank selection: separate analog identities, common write-data trunks');ax[0].legend(ncol=2,fontsize=9,loc='center right')
 selected={f'B0_STATE0{x}' for x in range(8)}|{f'B1_STATE7{x}' for x in range(8)};ii=[i for i,n in enumerate(states) if n not in selected];v=w[:,np.array(ii)+1];base=np.array([np.interp(1,t,w[:,i+1]) for i in ii]);delta=(v-base)*1e3;mask=t>=1;ax[1].fill_between(t[mask],delta[mask].min(1),delta[mask].max(1),color='#17845c',alpha=.3,label='Range of all112untargeted states');ax[1].axhline(0,color='#555',lw=.6);ax[1].set(ylabel='State change (mV)');ax[1].legend(loc='upper left')
 for bi,color in [(0,'#1769aa'),(1,'#c55a11')]:
  for c in range(8):ax[2].plot(t,w[:,129+bi*8+c],color=color,alpha=.45,linewidth=.8,label=f'Bank{bi}:8raw source-follower outputs' if c==0 else None)
 ax[2].set(xlabel='Time (microseconds)',ylabel='Raw read voltage (V)',xlim=(0,50));ax[2].legend(loc='upper left',fontsize=9)
 for a in ax:
  a.axvspan(2,6,color='#1769aa',alpha=.09);a.axvspan(12,16,color='#c55a11',alpha=.09);a.grid(alpha=.2)
 fig.suptitle('770MOS +128MIM;7,310verified native capacitance branches\n50us completed;write error23.56mV;untargeted-state change0.615mV',fontsize=12);fig.text(.01,.001,'Typical27C;startup states seeded by.ic. Dotted lines:commanded write targets. Read voltages are uncalibrated raw outputs.\nNo native initialization,5ms parent retention,trained precision or full-population service claim.',fontsize=8)
 for ext in ['png','svg','pdf']:fig.savefig(D/('bank_pair_native_sequence.'+ext),dpi=180,bbox_inches='tight')
 files=[Path(__file__),s,p,data]+[D/('bank_pair_native_sequence.'+ext) for ext in ['png','svg','pdf']];(D/'bank_pair_native_sequence_figure.json').write_text(json.dumps({'scope':'Existing completed native transient only;no rerun or corrections.','sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}},indent=2)+'\n')
if __name__=='__main__':main()

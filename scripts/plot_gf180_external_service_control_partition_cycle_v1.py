"""Article figure from completed layout-derived analog state cycle; no fitted values."""
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'

def main():
    stem='gf180_external_service_control_partition_cycle_v1';p=B/'results'/(stem+'.json');q=json.loads(p.read_text())
    assert q['completed'] and q['complete_analog_state_cycle_observed']
    z=np.load(p.with_suffix('.npz'));w=z['waveforms'];names=z['variables'].tolist();t=w[:,0]*1e6
    get=lambda n:w[:,names.index('v('+n.lower()+')')]
    fig,axs=plt.subplots(3,1,figsize=(10.4,7.3),sharex=True,layout='constrained',gridspec_kw={'height_ratios':[1,1.35,1.35]})
    colors=['#1976a3','#ce781b','#954097']
    for i,(name,label,color) in enumerate(zip(['BETA_PHASE','POSITIVE_INJECTION','SUBTRACTIVE_RESET_PHASE'],['Beta','Weighted injection','Reset'],colors)):
        axs[0].plot(t,i+get(name)/3.3*.75,color=color,lw=1.2)
    axs[0].set(yticks=[.35,1.35,2.35],yticklabels=['Beta','Weighted injection','Reset'],ylim=(-.15,3))
    axs[0].set_title('Selected analog state cycle through shared external storage',loc='left',fontweight='bold')
    axs[1].plot(t,get('xactor.'+q['compute_native_state_node']),color='#1976a3',lw=1.5,label='Compute membrane')
    axs[1].axhline(1.65,color='#78838e',lw=.8,ls=':',label='Compute reference')
    axs[1].set(ylabel='Compute voltage (V)',ylim=(1.62,1.94));axs[1].legend(loc='upper left',ncol=2,fontsize=9)
    axs[2].plot(t,get('bank_service__B0_STATE70'),color='#1976a3',lw=1.5,label='Selected resident membrane')
    axs[2].plot(t,get('SHARED_WRITE_DATA0'),color='#ce781b',lw=1.1,label='Write column')
    axs[2].plot(t,get('bank_service__B1_STATE70'),color='#78838e',lw=.9,ls='--',label='Opposite bank')
    axs[2].set(ylabel='Storage voltage (V)',xlabel='Time (µs)',ylim=(1.13,1.47));axs[2].legend(loc='upper left',ncol=3,fontsize=8)
    for ax in axs:
        ax.set_xlim(60,180);ax.grid(axis='x',alpha=.18);ax.spines[['top','right']].set_visible(False)
        for x in [70,85.2,95.2,115.2,155]:ax.axvline(x,lw=.65,color='#9ca7b1',ls=':',alpha=.6)
    axs[2].annotate('Writeback error −20.34 mV',xy=(176,q['final_resident_v']),xytext=(127,1.20),fontsize=9,arrowprops={'arrowstyle':'->','lw':.8})
    fig.supxlabel('1,832 native primitives · 14,365 routing C branches · external categorical phase fixtures\nTypical 27°C; noise/mismatch off. Precision and full-ASIC acceptance remain unproven.',fontsize=9)
    folder=B/'assembly/external_service_control_partition_v1';png=folder/'analog_state_cycle.png';svg=folder/'analog_state_cycle.svg'
    assert not png.exists() and not svg.exists();fig.savefig(png,dpi=200);fig.savefig(svg);plt.close(fig)
    print(str(png))

if __name__=='__main__':main()

from __future__ import annotations
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/analog_asic/layout/sky130_r2r_wide_resistor_probe'
IMAGE='eventspikeseg:analog-layout'
RC='/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc'

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/'wide_probe_raw.mag').write_text('magic\ntech sky130A\nmagscale 1 2\ntimestamp 0\n<< checkpaint >>\n<< end >>\n',encoding='ascii')
 tcl='\n'.join(['load wide_probe_raw','magic::gencell sky130::sky130_fd_pr__res_xhigh_po_5p73 resistor -spice w 5.73 l 6.0','save','writeall force','quit -noprompt',''])
 cmd=['docker','run','--rm','-i','-v',f'{ROOT}:/workspace','-e','PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root','-w','/workspace/artifacts/analog_asic/layout/sky130_r2r_wide_resistor_probe','--entrypoint','magic',IMAGE,'-dnull','-noconsole','-rcfile',RC]
 p=subprocess.run(cmd,input=tcl,text=True,capture_output=True,timeout=180,cwd=ROOT); log=p.stdout+p.stderr
 (OUT/'magic_wide_pcell.log').write_text(log,encoding='utf-8')
 print('return',p.returncode);print(log[-2500:]);print('mag files',[f.name for f in OUT.glob('*.mag')])
 if p.returncode:return 1
 return 0
if __name__=='__main__':raise SystemExit(main())

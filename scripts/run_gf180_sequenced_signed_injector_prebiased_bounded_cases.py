from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
for i in range(3):
 print('Starting prebiased complete-event case '+str(i),flush=True)
 subprocess.run([sys.executable,str(ROOT/'scripts/screen_gf180_sequenced_signed_injector_prebiased_complete_bounded.py'),str(i)],cwd=ROOT,check=True)

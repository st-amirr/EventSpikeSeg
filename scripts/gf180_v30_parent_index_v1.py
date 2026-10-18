"""Exact parent-wire index through verified V30."""
import json
from pathlib import Path
from gf180_v26_parent_index_v1 import build_index as previous
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'

def build_index():
    index,inp,paths=previous()
    for folder in ('full25_control_supplies_v27','full25_class_infrastructure_v30'):
        p=BASE/f'assembly/{folder}/route_plan.json';paths.append(p)
        for n in json.loads(p.read_text())['routes']:
            for l,b in n['shapes']:index.add(l,b,n['net'])
    ep=BASE/'assembly/full25_class_interfaces_v28/escape_plan.json';paths.append(ep)
    for e in json.loads(ep.read_text())['escapes']:
        owner=e['native_pin'] if e['native_pin'] in ('VDD','VSS','STORAGE_REFERENCE','COMPUTE_REFERENCE') else e['escape_label']
        index.add(81,e['rectangle_top_dbu'],owner)
    index.rebuild();return index,inp,paths

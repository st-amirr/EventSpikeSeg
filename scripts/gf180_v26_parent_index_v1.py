"""Exact retained parent-geometry index through V26 (no native device flattening)."""
import json
from pathlib import Path
from route_gf180_native_addresses_v23 import initial_index
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'

def build_index():
    ip=BASE/'assembly/native_address_route_inputs_v1/routing_inputs.json';inp=json.loads(ip.read_text());index,paths=initial_index(inp)
    for folder in ('full25_native_address_routes_v23','full25_analog_supplies_v25','full25_analog_references_v26'):
        p=BASE/f'assembly/{folder}/route_plan.json';paths.append(p)
        for n in json.loads(p.read_text())['routes']:
            for l,b in n['shapes']:index.add(l,b,n['net'])
    ep=BASE/'assembly/full25_analog_interfaces_v24/escape_plan.json';paths.append(ep)
    em=json.loads((ep.parent/'physical_assembly.json').read_text());paths.append(ep.parent/'physical_assembly.json')
    for e in json.loads(ep.read_text())['escapes']:
        ox,oy=em['actors'][e['actor_index']]['origin_top_dbu'];b=e['rectangle_local_dbu']
        owner=e['native_pin'] if e['native_pin'] in ('VDD','VSS','STORAGE_REFERENCE','COMPUTE_REFERENCE') else f"EXT_{e['actor_index']}_{e['endpoint_kind']}_{e['native_pin']}"
        index.add(81,(b[0]+ox,b[1]+oy,b[2]+ox,b[3]+oy),owner)
    index.rebuild();return index,inp,paths

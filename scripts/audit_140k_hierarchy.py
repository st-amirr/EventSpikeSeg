import csv, hashlib, json
from collections import Counter
from pathlib import Path

root=Path('/workspace')
out=root/'artifacts/ASIC/hard_hierarchy'
spec=json.loads((root/'artifacts/ASIC/model_spec.yaml').read_text())
catalog=json.loads((out/'hard_macro_catalog.json').read_text())
layers={x['name']:x for x in spec['layers']}
masters={x['module']:x for x in catalog['masters']}
seen=Counter();used=Counter();plifs=0;pixels=0
with (out/'hard_macro_instances.tsv').open() as f:
    for row in csv.DictReader(f,delimiter='\t'):
        actor=row['actor']; layer=layers[actor]; master=masters[row['master']]
        h,w=map(int,layer['output_hw']); index=seen[actor]
        y,x=divmod(index,w)
        assert (int(row['output_y']),int(row['output_x']))==(y,x)
        assert int(row['output_height'])==int(row['output_width'])==1
        assert master['variant']==row['variant']
        seen[actor]+=1; used[row['master']]+=1
        if row['kind']=='actor_tile':
            plifs+=int(layer['out_channels'])
        else:
            assert master['class_width']==3 and master['input_bits']==16
            pixels+=1
for actor,n in seen.items():
    h,w=layers[actor]['output_hw']; assert n==h*w
for name,count in used.items():assert count==masters[name]['instances']
assert plifs==30_976_000 and pixels==281600 and len(used)==160
assert len(spec['graph']['actor_topological_order'])==25 and len(spec['graph']['edges'])==54
assert catalog['model_spec_sha256']==hashlib.sha256((root/'artifacts/ASIC/model_spec.yaml').read_bytes()).hexdigest()
result={'status':'inventory_conservation_passed','model':'EventSpikeSeg140k',
        'actors':25,'graph_edges_in_source':54,'plif_identities':plifs,'readout_pixels':pixels,
        'physical_instances':sum(seen.values()),'unique_masters':len(used),
        'master_instance_counts_match':True,'every_output_coordinate_present_once':True,
        'full_chip_layout_complete':False,'macroized_assembly_generated':False,
        'physical_views_staged':0,'physical_views_required':480,
        'meaning':'structural inventory only; not executable assembly or physical signoff'}
(out/'inventory_preflight.json').write_text(json.dumps(result,indent=2)+'\n')
(out/'README.md').write_text('''# Exact 140k physical hierarchy inventory

Inventory conservation passed: 25 actors, 54 source graph edges, 30,976,000 PLIF identities and all 281,600 output pixels. There are 1,298,000 actor leaves plus 281,600 one-pixel readout leaves, requiring 160 unique masters and 480 LEF/GDS/Liberty views.

This directory contains the exact instance map, logical blackboxes, generation commands and view requirements. It is not a full-chip layout. No catalog views are staged yet; existing isolated primitive layouts are preserved elsewhere and are not automatically interchangeable with complete actor masters. The macroized assembly and graph wiring remain to be generated and verified after the implementation direction is chosen.

Each actor uses 1x1 physical leaves; the 8x8 logical grouping is retained. This partition policy is inherited from earlier XL host-capacity experiments, not proof that all 140k masters have been physically implemented. XL artifacts were not regenerated or modified.

The measured ordinary-PLIF footprint scaled over all resident identities is approximately 46,647 mm² of isolated die footprint (13,621 mm² of standard cells), before synapses and mechanisms. This is a capacity proxy rather than a floorplan. A full native direct-state layout therefore requires a substantially larger implementation campaign; choosing a smaller block demonstrator or changing resident-state/compute mapping is a design-scope decision.
''')
print(json.dumps(result,indent=2))

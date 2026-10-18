## Journal target and manuscript format - 2026-10-18

Target Microelectronics Journal as an Original paper, emphasizing GF180 circuit mapping, shared analog service, physical hierarchy and representative module characterization. Use the publisher's `elsarticle` template; two-column LaTeX is allowed. Retain the user-approved title and detailed model sections. Replace the 1,619-pixel-wide conceptual image with a deterministic vector redraw using the same graph/color organization; retain the original raster. Preserve native GDS visibility policies and source geometry. Report nominal simulation evidence without claiming measured silicon, calibrated segmentation or a compact die. Add mixed-signal circuit context, but avoid incompatible energy rankings. Publication or data deposition has not been authorized by this formatting request.

## Publication figure and evidence decisions - 2026-10-15

Use the corrected original illustration as main Figure 1 and omit the duplicate historical image from the PDFs while retaining its source. Use darker layer colors and a white background for GDS-derived publication variants; preserve geometry and mark hierarchy simplification explicitly. Local PLIF/injector images hide interconnect only; the native 64-state bank retains all wiring. Add results only from existing source data: waveform plots, state inventory, nominal operating conditions and geometric area arithmetic. No new circuit simulation or inferred full-chip performance is required for this editorial revision.

## Article layout delivered — user scope clarification2026-10-14

V31 is the completed full hierarchical research-layout deliverable under the user's instruction to avoid strict operational acceptance. See `artifacts/analog_asic/assembly/full25_native_controls_v31/article_layout_delivery_v1.json` and ACTIVE_TASKS. All original analog states and implemented modules are included; verified address/event/supply/reference wiring and explicit external research interfaces are documented. Native numerical errors, incomplete full1024-state transient and unproven global5ms timing are reported limitations, not blockers to this layout delivery. Module evidence covers18 completed nominal families plus the page-reader frontend partition. Connected signed-update/commit/5ms-hold evidence is in `results/selected_accumulation_retention_v2/simulation.json`. Further behavioral optimization is optional. Earlier strict flags below are historical; do not infer that the full GDS has not been exported.


## Article methods: restored technology and design rationale

Restored from the [committed Markdown snapshot](documentation_history/article_markdown_HEAD_4fd2e5e93257_20261014T155300Z.zip), commit `4fd2e5e93257`, on 2026-10-14. Historical experiments below retain their original scope; the current delivery is specified by `article_final_implementation` in [project_spec.yaml](project_spec.yaml).

### ASAP7 tool and model boundary — historical 2026-09-23 evaluation

The inspected ASAP7 umbrella revision was `d24f8b857ff74cf5b21ab18a7e1b11a3954c449b`; the device PDK revision was `58d72c9d291e186a77468586ab0c43d8a21eda6a`. Its unmodified TT card declared HSPICE level 72 and BSIM-CMG version 107. The initial inverter probe failed in the then-installed ngspice 36 with an unsupported model level. The inspected alternative VA-Models implementation used BSIM-CMG 111.2.1, so substituting it without validated parameter mapping would not establish equivalence to the original model card.

The checked Calibre DRC/LVS/PEX directories contained download instructions rather than usable rule decks. At that stage, native analog macro layout, qualified storage and complete extraction evidence were also missing. These were concrete limitations of the evaluated tool/model setup, not proof that 7 nm cannot support analog circuits. Subsequent MOSCAP diagnostics remain separate experiments with their own retention/acceptance results; they do not retroactively validate this initial probe or establish a usable full ASAP7 analog flow.

The final article implementation uses GF180MCU and native GF180 physical modules. Earlier SKY130 and ASAP7 work supports the development rationale but is not a controlled cross-process PPA comparison. Digital cell libraries and ORFS alone do not turn a behavioral analog circuit into a physically qualified macro.

Source: the corresponding historical section in the committed Markdown snapshot linked above.

### Preserve analog semantics without prescribing fixed-point precision

Use the original epoch58 float checkpoint for model topology and semantics. Quantized export ranges and provisional ASAP7 voltage scales were early experiment settings and are not requirements for the final analog implementation. Required analog precision depends on scaling, sampled error, retention, mismatch and model sensitivity. Report software accuracy separately from circuit evidence.

A presynaptic event contributes signed charge; pulse duration was reused first to limit redesign. Switched-capacitor injection remained an alternative and later circuit records document its development. Compare approaches through charge delivery, state dependence and timing under explicit operating conditions. Do not infer that one encoding is inherently more faithful solely from the fact that the network spikes.

### Share expensive peripherals while preserving resident states

The architecture must retain separately addressable membrane/state identities even when a physical read/compute/write lane is reused. This motivated shared readers, references, injection and feedback circuitry. The historical area and service estimates in RESULTS explain the tradeoff: less replicated peripheral area increases service scheduling and settling demands. They are neither final die-area measurements nor demonstrated population throughput.

### Keep development evidence distinct from article delivery

The useful historical experiments have been restored to ARCHITECTURE and RESULTS; obsolete live-session instructions, unfinished-stage task lists and provisional calibration settings remain in the snapshot. The V31 article layout and representative module-consumption deliverables remain complete under the agreed research scope. Unproven global 5 ms performance, full-chip power and calibrated accuracy remain explicit limitations rather than being inferred from local measurements.

## Control and class infrastructure — 2026-10-14

Latest qualified full-population GDS is V30 (`assembly/full25_class_infrastructure_v30/integration_readback_v1.json` under artifacts/analog_asic). All three categorical macro upper VDD/VSS grids are connected to existing rails; actual native M4/M5/VIA4 proofs cover all power-port rectangles. The class-current/readout wrapper has 118 verified boundary escapes and four verified supply/reference joins. V29 failed branch conflict is preserved; V30 moves the conflicting ground via. All source state geometry and existing graphs are preserved. Remaining work is native event/commit boundary controls, driven/observation terminal classification, retained module interfaces and connected per-module accumulation/retention/timing. No jobs live; full layout completion and 5 ms remain unproven. Earlier handoffs below are historical.

## Infrastructure progress — 2026-10-14

V26 is the latest incrementally readback-qualified full-population GDS. V24 added and verified 1,750 boundary terminals; V25 connected 100 analog supply endpoints; V26 connected 100 storage/compute-reference endpoints. Existing V23 address graph and all native state geometry are preserved. Evidence: `artifacts/analog_asic/assembly/full25_analog_references_v26/integration_readback_v1.json`. Remaining categorical/class-current infrastructure, operation interfaces and connected module simulations are listed in ACTIVE_TASKS. No global RC/IR/EM, full layout completion or 5 ms pass is claimed; no jobs are live. Prior handoffs below are historical.

## Current layout handoff — qualified address binding V23, 2026-10-13

Latest readback-qualified full-population GDS: `artifacts/analog_asic/assembly/full25_native_address_routes_v23/eventspikeseg140k_native_address_routes_v23.gds` (536,631,368 bytes), top `ESS140K_NATIVE_ADDRESS_ROUTES_V23`. All 947 controller address nets now physically reach all 1,622 native membrane address/select endpoints. Actual parent-metal graph and native dispatcher-edge checks pass: no opens, aliases, floating pieces, unlanded cuts, foreign/unknown native contacts or native-core intrusions within the checked scope. Complete V19 child geometry, all state identities, 25 spike paths and 3,050 control links are preserved. Combined evidence: `assembly/full25_native_address_routes_v23/independent_readback_v1.json` under `artifacts/analog_asic/`.

Next: finalize supply/reference and external analog contribution/phase interfaces, then connected per-module accumulation/retention/timing simulation coverage. Do not repeat address routing. Full layout completion and 5 ms accumulation are still unproven; no global-wire RC or whole-chip DRC/timing claim. No host or Docker jobs remain live. V20/V21/V22 failed plans are retained. Read the active scope clarification below: only supplied input-event delivery/accumulation has the 5 ms deadline; trained-weight transfer, output completion and hardware mIoU are excluded.

## Current physical stage — destination-controller integration, 2026-10-13

Latest qualified full-population research GDS is V19: `artifacts/analog_asic/assembly/full25_accumulation_dispatch_v19/eventspikeseg140k_accumulation_dispatch_v19.gds` (532,403,802 bytes), top `ESS140K_ACCUMULATION_DISPATCH_V19`. Actual GDS integration readback passes: all source state geometry and top placements preserved, all 25 native spike-to-fabric connections retained, 1,475 fabric-to-ingress routes and 1,575 ingress-to-destination-controller routes present, and shared clock/reset connected across those three control macros. All 1,622 native membrane address/select escapes are preserved. These escapes are NOT yet wired to the controller's 947 grouped address-output nets. Full layout completion and 5 ms accumulation remain unproven.

Destination controller is now physically complete: 1,842.61 um square, 4,729 pins, nominal GF180 3.3 V/25 C at 40 MHz setup +9.27429 ns and hold +0.837844 ns, Fmax 63.5901 MHz, routed DRC0. Retain 8 antenna nets/pins and 501 slew violations. These are macro results, not whole-chip timing. All 25 actual actor configurations passed 1,425 categorical groups / 4,358 service requests / 125 invalid-input cases, including every local-bank exception, bank9 gap, edge coordinates, duplicate destinations, backpressure and fresh-done qualification. Analog completion in that test is a fixture; it is not charge/timing evidence.

Native access escapes V18: actual GDS readback verifies 1,622 M5 connections beyond the enclosing native wrappers, no opens or same-layer aliases, unchanged native source elements, and preserved earlier spike/event routes. Same-layer corridor screening includes the enclosing native hierarchy and a 460 nm guard. It is not full-style DRC or native RC/analog timing. Controller-to-ingress link V2 verifies all 3,050 inherited/new event routes plus shared clock/reset in the actual metal graph, with zero opens, aliases, floating metal/cuts, foreign or unknown contacts within the checked 2 um native macro perimeter bands, and no intrusion beyond those bands. Earlier V1 route plan is retained: its oversized .60 um pads triggered conservative clearance failures; V2 uses .46 um pads with .26 um cuts and .10 um enclosure, retaining the clearance check.

Next executable stage: route the 947 controller address-output nets to the 1,622 native local/forest membrane terminals, using the exact physical driver/sink coordinates and obstacle bounds in `artifacts/analog_asic/assembly/native_address_route_inputs_v1/routing_inputs.json`. Preserve the existing three-macro graph and 25 spike paths. Analog signed contribution and operation phases remain explicit external research interfaces under the user's scope; correct selected-service read/restore/inject/capture/commit and row preservation are required. Finish global supply/reference/clock/reset distribution, export the final architecture views/boundary manifest, then finish per-module connected accumulation/retention/timing simulations. Trained-weight transfer, useful segmentation output and hardware mIoU remain excluded gates.

All Docker jobs are terminal and collected. The destination-controller container was archived and removed automatically after final physical views/logs were saved; no new image was built. No host assembly/readback process remains live. Preserve the existing final views and failed attempts. The layout remains a spacious research atlas; no compact die area, loaded global-wire timing, autonomous inference or 5 ms throughput claim.

Evidence: `assembly/full25_accumulation_dispatch_v19/independent_readback_v1.json`, `assembly/accumulation_dispatch_link_v2/independent_readback_v1.json`, `assembly/full25_membrane_address_breakouts_v18/independent_readback_v1.json`, `assembly/full25_accumulation_dispatch_v1/physical_macro.json`, and `results/accumulation_dispatch_v1/simulation.json`, all under `artifacts/analog_asic/`.

## Physical accumulation architecture integration — 2026-10-13

New full-population V17 GDS: `artifacts/analog_asic/assembly/full25_accumulation_architecture_v17/eventspikeseg140k_accumulation_architecture_v17.gds` (427,483,212 bytes), top `ESS140K_ACCUMULATION_ARCHITECTURE_V17`. It preserves all source analog state geometry, integrates the actual routed fabric/ingress pair, and retains all 25 native SPIKE outputs connected to that fabric. The 1,475 previously RTL-only fabric-to-ingress event/ready/payload/completion/tag connections are now physical metal; two shared clock/reset routes connect those two macros. Existing global clock/reset/power distribution remains incomplete.

Actual pair GDS readback passes all 1,477 new paths with no opens, aliases or floating additions. Its native contact check covers the 2 um macro perimeter band and verifies that new parent metal does not intrude beyond that band; original child cells are preserved (ingress names systematically prefixed). This is an incremental connection check, not full device extraction or full-style DRC. Evidence: `assembly/accumulation_fabric_ingress_v1/independent_readback_v1.json`.

Actual V17 GDS readback proves both source libraries byte-identical, all 25 rerouted spike paths connected, zero opens/aliases/floating metal or cuts, zero screened route spacing/cross-contact conflicts, and no unrelated macro intrusion. Outer spike channels now use M1/M2 while retaining their native M5 source and M3/M4 destination approaches, separating them from new ingress M3/M4/M5 routing. Evidence: `assembly/full25_accumulation_architecture_v17/independent_readback_v1.json`.

Current stage: destination-to-membrane integration. Ingress produces x/y/channel-group destinations, but conversion/dispatch to native local/forest page addressing and required read/restore/inject/capture/commit controls still need binding. Analog magnitude/sign and phases can be external research interfaces under the clarified scope. Global supplies/references and clock/reset distribution remain required. The full architecture layout is not yet complete and 5 ms accumulation is not verified. Trained-weight loading, useful inference output and hardware mIoU remain excluded completion gates. Parent RC/loading and per-module connected-event timing remain to be measured. This remains a spacious research atlas, with no compact die area claim. No Docker jobs were launched for these GDS assembly/readback steps.


## Active scope clarification — 2026-10-13

The user defines this deliverable as an article-suitable analog/mixed-signal implementation of the EventSpikeSeg140k architecture: full physical layout with membrane storage and event-to-membrane accumulation, followed by per-module simulations. The original epoch58 float model defines topology and state identities; QAT is unnecessary.

The 5 ms real-time requirement applies to delivery and accumulation of supplied input events onto their destination membranes. It does not require threshold/output generation, a full layer-to-layer inference pass, or final segmentation within 5 ms. For module timing, state exactly which input event workload and destinations were exercised; do not infer a full-model deadline pass from a small example. Later-layer workloads may be supplied externally for module characterization; this is not autonomous end-to-end inference.

Trained-weight loading, transfer, programming and exact checkpoint weight reproduction are outside the required completion gates. Retain the synaptic contribution/weight-control interfaces and existing physical synapse circuitry: an externally applied analog magnitude/sign is an explicit research interface, not a claim of loaded trained weights. Events must still have physical paths to selected membrane capacitors; removing weight transfer does not remove event fanout, charge injection or membrane access time.

A useful segmentation output, hardware mIoU, PyTorch-equivalent accuracy, calibration optimization and manufacture-ready signoff are not required. Preserve existing threshold/reset/adaptation/readout modules as architecture components and report their connectivity and simulation coverage, without requiring output completion for the accumulation deadline.

Completion requires a real hierarchical full-architecture GDS, inventory and connection/boundary manifest, and per-module simulation results including selected-event membrane accumulation/retention and measured timing. Explicit external interfaces are allowed. Opens/shorts in paths claimed connected remain vital defects. Never call an unconnected placement a functioning full ASIC or claim 5 ms compliance without corresponding evidence.

Next work: integrate the existing packet fabric and ingress/address macros with the membrane-access/injection architecture, expose analog contribution and phase controls, export the full architecture layout, then finish per-module simulations. Do not start trained-weight programming or output-accuracy campaigns. The old 68-decision-service lower bound is not an active completion gate. Existing packet/group lower bounds remain conditional on their supplied workload and assumed delivery architecture; they are not automatically waived or proven satisfied.

This scope supersedes conflicting older requirements below. Existing results and failures remain unchanged. No physical Docker jobs are live.

# Current decisions





Updated 2026-10-13. Run status belongs in [ACTIVE_TASKS](ACTIVE_TASKS.md); measurements belong in [RESULTS](RESULTS.md). Exact earlier decisions are archived through [PROGRESS](PROGRESS.md).





| Choice | Reason and boundary |


| --- | --- |


| Original epoch58 float model, analog state | Preserve trained SNN semantics; no QAT, silent retraining or digital membrane fallback |


| Continue GF180 prototype | Reuse native physical modules and measured evidence; process/organization can change after a measured feasibility failure |


| Signed charge per presynaptic event | Preserves weighted contribution and bin accumulation; weight does not control firing frequency |


| Tracking parking and four-bank injection autozero | Selected packet/state dependence improved; larger fan-in, total noise and service remain open |


| Map each guarded original-float local interval onto the capacitor voltage swing | The manifest defines Vstored=1.65+0.9*state/range across 0.75–2.55V, shared by each 8x8 channel/tile bank. This is the chosen analog state encoding, not a quantized representation. Every update and threshold term must use the same scale; recurrence accuracy remains open. |


| Reuse the physically held 9-MIM current cell with a routed long-channel PFET as a per-bank scale-source candidate | Parent macro v6 passes DRC, unique LVS and GDS readback. Extracted parent+reader transient after5ms measures min/median zero-subtracted current at0.988x/0.972x targets, with about7–8mV held-gate movement. Nominal only; no scale-weight multiplication, membrane recurrence, PVT/noise or population service. Parent bbox780.3x414.2um makes area replication a major open gate; evaluate sharing/compact implementation before accepting this cell for all490,240 banks. |


| Preserve one categorical full25 graph boundary around analog actors | Reuse qualified fork/join/OR/upsample blocks to connect original graph semantics while leaving PLIF state, weights and class currents analog; bounded Verilator smoke is not full graph or physical acceptance |


| Repaired minimum MIM and isolated write bus | Actual GDS connectivity and disturbance evidence support these separate views; legacy failed/guarded views preserved |


| Preserve sample-isolated native charge restore as comparison | Common correction checked independently; cumulative drift and shared cost prevent acceptance |


| Reject uncalibrated current reader as mismatch robust | Native variation causes large error and saturation; ideal amplifier controls alone do not resolve it |


| Review state/update organization before more capacitor growth | Shared access scenarios require excessive lanes/plates; local updates may remove that round trip at a different per-state cost |


| Do not rely on exact background sharing to solve density | Two unchanged float records retain most state exceptions/history allocations; no compact hardware acceptance |


| Develop settled NF-only local sharing | Complete-cycle correction includes auxiliary recharge; repeated 5 ms cadence checks support physical-parent integration. Learned-beta ratios, noise and service remain open |


| Accept approximately 1,215 mm2 bare state+auxiliary plates | User acceptance on 2026-10-10 removes this estimate as a decision blocker. Keep adaptation/peripheral/routing area separate; the two-slope ratio fit is conditional |


| Develop coarse MIM plus fine intermetal auxiliary sizing | Physical nominal endpoints bracket trained beta; 0.403/4.088 fF overlap increments checked. Actual channel sizing, error tolerance, reference generation and service remain open |


| Reject direct gated-bias resident threshold sensing | Measured4.64mV state disturbance plus uncorrected9.5/27.5mV trip offsets. Keep failed evidence |


| Develop shielded startup-autozero threshold sensing | MinimumNF dummy cancels release injection; slow-ramp nominal/seed29 trip errors sub-mV. Bias/service, retention, settling and physical parent remain open |


| Explore64xbase-threshold state bound; reject tighter16x/4x for now | Two exploratory records improve IoU atK64 but12-13%pixels change. Fresh three-record small-proxy results are encouraging, but actual-threshold native error is larger; larger-error check shows sign-sensitive accuracy. Freeze range sweep and integrate resident sensing/reset before another fit. No accepted model/representation change or retraining |


| Freeze targeted parent secant reference; integrate threshold/reset next | Limited float replay exposes switching offset sensitivity. Fresh native checks and two nominal heldouts support continued integration, not full accuracy acceptance; further isolated tuning waits for combined loading |


| Commit state after auxiliary recharge | Release-only measurement omits later backaction. Freeze complete-cycle physical correction before independent checks; recalibrate changed parent geometry |


| Reject direct short-pulse TG beta programming | Native gate filtering and intermediate voltage-dependent transfer produce multi-mV nonlinearity; stop the duration sweep |


| Reject directly attached pulsed cascode sink | Short reset response fails independent startup/5ms hold; preserve native evidence |


| Latch spike and steer continuously settled reset current | Prevent self-truncation and source internal-node tail; single phase/spike-selected output path replaces floating intermediate connection. Shared tracking/reference overhead and combined loading remain unqualified |


| Include physically routed reset selection before further calibration | Selector layout/abstract passes; routing changes switching offset. Integrate full parent before another isolated width/reference fit |


| Carry combined v6 state/detector into complete-neuron checks | Physical checks pass and fresh loaded-beta residual <=0.352 mV; keep common frozen settings. Reset voltage dependence needs diagnosis before repeated-cycle acceptance; no further isolated beta sweep |


| Finish layout/module simulations before further precision refinement | User clarification: retain measured errors, continue reusable physical modules and full assembly; no repeated precision sweeps unless needed to make a module operate. System accuracy/service remain reported, not inferred |


| Article-suitable implementation | Representative layout/simulation and explicit system limits; manufacture-ready signoff is outside scope |





## Delivery priority correction after user escalation - 2026-10-11





Three usage windows have elapsed without the requested full layout and module-simulation deliverable. Stop expansion of isolated qualification/precision variants as a prerequisite to article assembly. Assemble the actual25actor physical hierarchy from existing real module and storage layouts first, with explicit abstracted/missing interface and simulation coverage. Preserve measured failures and avoid false fullchip/accuracy/5ms claims. Module count alone is not progress toward the requested deliverable. Full128 source/GDS fullDRC0 and exact source/GDS primitive connectivity passed; native GDS Netgen failed and is retained. Fresh128 flat extraction timed out360s with a truncated final device record and must not be consumed. No runtime sweep or repeat extraction is authorized by this correction.





## Full-width verification method review - 2026-10-11





Full64 source hierarchy and independently reimported GDS pass full DRC and native Netgen. The redundant fresh flat fullDRC observation expired120s and was stopped207.85s after the180s review boundary; it is incomplete. Flat native extraction is retained independently. Both general VF2 and focused VF2++ exact comparisons exceeded120s. Diagnosis found all979net colors unique. Use colors only to propose a net bijection, then explicitly check every native primitive/dimension/pin, a complete bijective graph mapping and every edge; reject ambiguous net colors. This exact proof completed8.66s,12122graph nodes. No further general graph/runtime sweep. Full128 reuses this method; source/GDS fullDRC remain required and fresh flatDRC is explicitly outside this local article characterization.





## Corrected-C beta module characterization complete - 2026-10-11





Three10us native-driver phase trials completed at1.8/1.65/1.5V initialization,with frozen auxiliary reference and complete3941branch substrate/coupling extraction. Trained-beta residuals:-20.763/-13.311/-5.829mV. Autozero held; these are beta-phase results,not corrected fullcycle or full-model acceptance. Measured offset/gain retained; no circuit fit. Close this bounded characterization package and continue connected RMS/adaptation/inhibition/control and dense layout. [Three-state report](../artifacts/analog_asic/results/gf180_tile_v3_fullcap_three_state_beta_summary_v1.json). No jobs running.





## Use complete flat substrate export and bounded phase isolation - 2026-10-11





GF180 joined tile v3 keeps413MOS8R172MIM and passes source/flat/GDS full DRC0 plus exact primitive connectivity proofs; native Netgen is not claimed. Ground shield reduces STATE-to-buffer coupling291.53fF to25.84fF. Hierarchy-on export of the geometrically flat tile omitted185 substrate pairs and altered98 existing ground pairs. Native hierarchy-off/top-on export yields3941 nonnegative branches,593identical device tokens and per-node substrate agreement; C_STATE-to-VSS1.70294pF and C_AUX-to-VSS0.35526pF. Earlier hierarchical-PCAP joined cycles are underloaded diagnostics and cannot establish full extracted precision. Preserve them; no blanket invalidation of unreviewed child modules.





Corrected full-cycle trials remain incomplete. Ideal controls stop at switching corners; finite AZ driver crosses the first failure,all-phase resistive drivers reach beta1.0649ms,with partial read/restore error-5.163mV. Native two-inverter control drivers reuse a prior successful sequencer method but the full trial timed out120s; no restart/runtime/tolerance sweep. A10us beta-only native-driver probe is active. Native driver composition is not an integrated driver layout or autonomous scheduler. Catalog91 retains20module sets/71completed characterization entries and adds v3 as physical-qualified,in progress. Full analog functionality,dense layout,original-float accuracy and5ms service remain open. Evidence: `artifacts/analog_asic/results/gf180_shared_tile_v3_export_and_phase_review_v1.json`.





## Connected analog tile interfaces - 2026-10-11





Keep separate storage1.2V and compute1.65V common-mode domains,with native resistor/OTA up/down shifts and compute-output isolation. Eight analog output holds allow serial compute followed by one8column row commit. Direct cascade lacked output-current headroom; native isolation repairs that interface. Joined source/flat/GDS connectivity uses complete primitive graph bijections where conventional Netgen fails; retain its failed logs and one verified intentional dummy terminal warning. First closed-loop cycle establishes physical path operation; large beta residual prevents trained-model accuracy acceptance. Diagnose connected loading/phase behavior before one focused repair; do not silently change learned beta or replace analog state.





## Shared analog membrane access - 2026-10-11





Continue native3T storage with shared row decoding and a TG column mux feeding one matched-replica analog feedback reader. Actual64-state parent now has physical and nominal sampled-read evidence. Preserve analog numerical state and external categorical control boundary. One-reader-per64states is provisional: cold recovery and within-row recovery differ; qualify transition extremes and combined update timing before fixing reader replication. Do not multiply spaced characterization geometry into whole-chip area. No new user decision is needed for continued compute-tile integration.





## Storage control and article evidence milestone - 2026-10-11





Close RMS settling refinement for this milestone after the completed native100ns-input-edge run. Preserve initial180s timeout,660s first-edge abort, successful focused slew diagnostic and failed geometric-flat extraction; no tolerance or further precision sweep. Preserve independent5ms/50ms storage evidence and explicit loaded decoder status. Native hierarchy algebraic expansion requires formal-port scoping; the first erroneous global VSUBS expansion was rejected by independent device comparison and remains preserved. The corrected device graph passes, but capacitance matrices are not flat-equivalent. Do not use spacious decoder/RMS fixture footprints as dense replicated chip area.





Evidence: `artifacts/analog_asic/assembly/article_module_catalog_v70.json`, `artifacts/analog_asic/results/gf180_parameter_and_retention_supplement_v1.json`, `artifacts/analog_asic/results/gf180_addressed_memory_bank8x8_v2_native_decoded_sequence_src45c652b55f16.json`.





## Dense analog storage and assembly milestone - 2026-10-11





Reuse the completed8x8 storage geometry for a capacity-only layout assembly; do not replicate spacious characterization fixtures as dense neuron area. The GDS atlas contains866,080 native bank instances,55,429,120 slots including798,720 inactive boundary slots, covering every54,630,400 active identity. Bank geometry totals14,545.65mm2 before global routing/compute and is not the earlier1,215mm2 bare-plate estimate. This atlas is not a chosen manufacturable die/stack/chiplet architecture. Do not label it full-chip completion or infer model acceptance. Preserve the unsuccessful native atlas read and geometric full64 extraction; no blind runtime/precision sweep.





Evidence: `artifacts/analog_asic/assembly/article_module_catalog_v67.json`, `artifacts/analog_asic/assembly/full_capacity_storage_gds_v1/capacity_assembly.json`, `artifacts/analog_asic/results/gf180_full64_flat_and_storage_atlas_method_review_v1.json`.





## Assembly priority and startup branch review - 2026-10-11





After direct-clock abort, qualified clock-driver timeout and matched UIC-startup timeout, close the native connected controller/writer startup branch for this milestone. Preserve all physical views and incomplete runs; use completed independent native module evidence with the joined-sequencing gap visible. Prioritize actual full64 RMS-to-clip/strength physical integration. No solver-tolerance sweep or accuracy claim.





## Exact compositional LVS and RMS-aware physical sequencing - 2026-10-11





Resolve full-parent Netgen ambiguity using an independent ordered-interface graph proof, not relaxed tolerances or removed devices. Source parent nets map bijectively onto an independently built qualified-child reference; each embedded source child definition is identical to its qualified original. Every source/GDS subcircuit then passes exact graph isomorphism with fixed named ports and native W/L/passive dimensions. Full flat RC remains a separate requirement. Native fixed-period controller now explicitly captures RMS before reset; the handshake RTL is a distinct control reference, and its passed simulation does not establish native timing.





## Usage-window priority and capture branch review - 2026-10-11





User requests completion before the next five-hour usage limit. Prioritize finishing layout/module coverage and assembly; do not repeat precision sweeps or claim completion from artifact counts. Usage observed69% consumed at this checkpoint; no guaranteed completion time. Preserve completed sampling revision2 with its measured error after larger-capacitor revision3 aborts. Source hierarchy connectivity can be proved by exact ordered-pin/net-bijection equivalence plus identical qualified child definitions; this does not replace GDS or flatRC checks.





## Keep high-impedance capture nodes local - 2026-10-11





Do not run held analog voltages along20mm diagnostic buses beside capture clocks. Failed pre-reset sampling has500.33fF routing coupling from AMP_CAPTURE toCAPTUREB and500.08fF toRMS_CAPTURE. Local shielded capture/buffer layout lowers corresponding clock coupling to5.43fF in its independent extraction; actual loaded parent behavior remains to be measured. Preserve failed native transient and use one focused local-routing repair, then method review if unsuccessful. Do not infer calibrated precision from reduced coupling.





## Finish integration within current usage window - 2026-10-11





User requests completion before the next5h usage limit. Prioritize layout and per-module simulation deliverables, preserve measured imperfections, and avoid precision sweeps. No promise of completion or accuracy from remaining usage capacity. Global control uses explicit logical composition evidence after native timeout and failed switch startup methods; no transistor timing claim. Netgen hierarchy-name overflow is addressed with topology-preserving comparison copies; native geometry/netlists remain unchanged. Continue initialization/expiry, connected RMS/write, dense tile and full executed-graph assembly. No QAT/digital numerical-state fallback.





## Retain physical compensation for loaded feedback loops - 2026-10-10





The frozen diagnostic and new routed product give the same settled ratio6.003956 versus ideal6; the connected resident sequence now completes within120s with triangle error0.118mV. Retain original minimum capacitors and add native22um MIM in parallel, two per affected OTA. These are peripheral compensation capacitors, not enlarged resident state plates. Carry the measured write-release error and unequal age steps forward; do not launch precision sweeps before remaining module/assembly coverage. Shared-buffer compensation is the next focused connected-readout change. Supplemental exact-dimension comparisons are required when old Netgen ambiguously pairs mixed-size parallel MIMs; preserve original warnings and comparisons.





## Native triangle implementation and physical interface checks - 2026-10-10





Use real unity reflection (matched native high-poly feedback), comparator/TG branch selection and zero-floor clamp for the adaptation triangle. Add native unity buffering before resident-age storage so reflection resistors cannot directly discharge its MIM. Connected51MOS parent now characterized; age/AMP calibration remains unaccepted. Physical diode bias reference repairs preservePF20/2 and external1uA. Discard fullroute-referencev1 for reuse: a blank line in MAG label serialization hid pins despite device-only LVS match. Fullroute-referencev2 and reflectionv4 explicitly verify actual source and GDS port lists in addition to DRC/LVS. Earlier failed geometry/decks retained.





## Continue analog support after nominal storage/energy errors - 2026-10-10





Follow the users layout-first article workflow: preserve measured age-increment nonlinearity, amplitude write-release offset and RMS-ratio error, finish missing analog functions and connected layout before further precision tuning. Module artifact completion is separate from functional/model accuracy acceptance; neither failed storage check nor nominal monotonic energy response accepts the full adaptation/RMS rule. No digital membrane, QAT or trained-model clipping substitution.





## Fix event initialization before changing injector - 2026-10-10





Retain joined circuit and fixed analog biases after1ms prebias restores small-weight cutoff. Use common initialization for all subsequent signed cases; no weight-specific timing correction. Complete full-event verification before declaring the joined autonomous path usable. Startup remains an explicit external reset/clock requirement. Do not infer population5ms service from the local clock or a single event.





## Use actual-output interlock for local analog phases - 2026-10-10





Retain the native18MOS cross-interlock after three nominal native fanout cases show primary-phase logic nonoverlap. Feed back actual outputs through separate inverters; NAND precursor complements can release the opposite branch before the primary output falls. Keep local switch timing separate from autonomous event/bin control. Preserve TG/MIM passive charge-sharing measurements without calling them unity-gain state transfer. Physical placement must reserve pin-escape envelopes; use the qualified minimumMIM pin-specific route pattern.





## Retain physically guarded pulse duration - 2026-10-10





Routing revision2 restores weight-dependent pulse duration after revision1 collapsed it. Continue this native analog path and its real signed-gate/injector connection. Require pulse-count and delivered-charge/range evidence; strict monotonicity alone can label an almost constant pulse as passing. No switched-capacitor fallback or digital membrane change is needed at this nominal mechanism gate. Accuracy and full-population throughput remain unaccepted.





## Module assembly completion policy — 2026-10-10





Continue the original-float GF180 analog path. Five checked physical modules now form a real routed characterization parent; layout and nominal simulation completion are separate from functional/model acceptance. Preserve routing-induced beta/reset errors and failed revisions, complete the remaining physical functions and dense/full hierarchy, then refine transfer. Large fixture routing must not be replicated as dense storage area. Analog source bias may be changed once to correct a wrong-sign injection event; unequal signed magnitudes remain explicit rather than being silently corrected in measured outputs.





## Open engineering choices





1. Physically realizable learned-beta ratios and extracted-parent transfer; retain shared access as a comparison.


2. Storage, references, fan-in and adaptation organization that can serve the full inventory in 5 ms.


3. Representative mismatch/noise/retention and task accuracy tolerance for the selected complete neuron.





No critical user decision is currently recorded. Continue reversible engineering work within scope. Escalate only an unclear consequential tradeoff or proposed model/scope change.





Experiment budgets and method-review triggers are defined once in ACTIVE_TASKS. Retain failed controls and freeze calibration before independent comparisons; changed hierarchies require new provenance checks.








Shared storage optimization -2026-10-11: actual3T/50fF bank with transistors below MIM, shared row/column buses and9MOS column mirror. Bank core8517.056um2 vs16794.808um2 (-49.3%); with native bias10017.972um2 (-40.3% against old bank excluding bias). Source/GDS fullDRC0, independentLVS, realLEF and2103 nonnegative native cap branches.5ms and50ms64-state sequences complete; maxwrite17.31mV,hold6.88mV,finalreadchange2.67/2.35mV. Source-follower offset uncalibrated. Single-NFET write range1.0-1.4V; do not assume arbitrary analog voltage range. Full state-capacity atlasv2 projects8676.37mm2 storage plus native bias, excluding decoder/write drivers/global compute/wiring; fullchip incomplete. Local buffered reads remain to preserve independent analog charge. See `artifacts/analog_asic/results/gf180_shared_storage_area_milestone_v1.json`. Next:dense shared row/write circuitry, read calibration and connected compute tile.





## Integration delivery correction after elapsed-usage complaint - 2026-10-11





Keep full-assembly delivery ahead of additional isolated precision variants. A partial capacity atlas is not a functional full layout. The first integrated actor is accepted only for native geometry/connectivity after the supply-escape repair; preserve original nominal failures and all missing functions. Use independent electrical comparison in addition to DRC because same-layer shorts can satisfy width/spacing rules. Next work must close remaining bank access/global binding and missing connected simulations, with article-level approximations explicitly labeled. No new user decision required and no completion-time promise.





## Independent bank write access and honest transient metrics - 2026-10-11





Use independently gated bank commands for random bank writes; earlier two-bank lockstep decoder remains valid only for coordinated full-row writes with independent data. New native pair shares row-address polarity and analog DATA while preserving separate wordline enables. Global capacity upgrade uses qualified real local decoders,not a claim that global selection or compute service exists. Carry23.56mV write error and UIC startup issue into connected work; do not spend another isolated tuning campaign. Separate final state shift from maximum transient:full trace reports8.340mV peak versus.615mV final. Spacious full-decoder footprint34,801mm2 is an integration reference,not selected compact die area; next area work must share row/column periphery at larger array granularity while preserving all state identities.








## Decoded shared read/write/compute integration - 2026-10-11





Catalog99:20module sets/81characterization assemblies. Decoded64-state reader100us native sequence complete;recovery21.43uVagainstactualstoredstate,writeerror21.58mV,read-phasepeakstatechange11.33mV/final.822mV;noUICseed. Source/GDS fullDRC0 and independent exact480primitive connectivity/dimensions;nativeNetgen propertywarnings retained,not cleanLVS. Sharedread/write service499MOS113MIM and compute tile579MOS8R172MIM now physicallyconnected;source/flat/GDS DRC0/exact612and759primitive proofs. FullC4416and5337branches. New tile230us cycleaborted25usonautozero release;notnominalpass. All25actorclusters now use decodedtile;full25_locally_decoded_storage_v2 preservesall54,630,400states. Globalbankservice/graph/operatorbinding and fullASIC remainincomplete. Report:artifacts/analog_asic/assembly/full25_locally_decoded_storage_v2/delivery_report_v3.html.








## Measured loaded reset repair - 2026-10-11





Observed in the measured repair case. The adjusted reset pulse lasts 23.614 microseconds. Measured reset: -6.722 mV; requested: -6.875 mV. Writeback error: -20.345 mV. This is one donor-derived pulse-duration repair, not independent reset precision acceptance. The complete native reset path turns on correctly; prior pulse was too short under actual loading. No geometry/bias or beta-reference change; post-reset capture/commit delayed30us. Full functional assembly, global bank service, graph/operator binding and missing module simulations remain unfinished. Updated delivery report: artifacts/analog_asic/assembly/full25_locally_decoded_storage_v3/delivery_report_v2.html.








## Nominal native simulation runtime - 2026-10-12





Use compiled-in KLU for GF180 nominal MOS transient cases;verify selection in native log. Same equations,devices,capacitances,commands andtolerances as SPARSE1.3;measured fullactorprogress2.40times at120s. One240s case approved bymeasured201.1s projection,completed202.58s. No noise qualification implied. Existing SPARSE evidence retained. Officialsolverreference:https://ngspice.sourceforge.io/docs/ngspice-manual.pdf. Carry measured circuiterrors forward;finish integration beforeadditionalprecision tuning.








## Article delivery priority and current revision - 2026-10-12





User accepts imperfect results: finish connected layout and per-module simulations first; retain measured errors and defer precision optimization. V5 service escapes moved to a clear left gutter after V4 larger-actor supply/signal shorts were found. All54,630,400 state identities preserved. Four recursively audited geometry groups cover25actors;24 actor geometries inherit representative DRC0,stem retains oneM5 spacing violation. Firstactor exact2362 primitive graph and fresh17268 routingC pass; larger-parent exact extraction incomplete and partialEXT rejected. Latest180us native neuron case: Incomplete: reached 105.209us of180us; retained as partial evidence. Full global bank service,graph/operator/parameter bindings and remaining module functions are still missing. Current delivery report: artifacts/analog_asic/assembly/full25_external_bank_service_v5/delivery_report_v1.html.








## Complete integration before precision refinement - 2026-10-12





Use physical characterization partitions at categorical controller interfaces when fullnativecontroller transient stalls;verify the actual remaining device graph andfresh completeC before analogsimulation. Keep physicalcontrollers in fullASIC andretain separate failed fullparent results. This changes modeling scope,not analog numerical storage or network semantics. For missing full128 SUM nominal,qualified complete native primitive topology/MIM/resistors provides an initial simulation with routingC explicitly excluded; do not relabel it completeRC. Reuse existing current-summing ROOT networks for128channels:128kernels and128receivers shareROOT;no buffered RMS-voltage averaging or new sqrt block. Exact graph validation permits a symmetry-aware deterministic mapping only after everyprimitive,pin,node andedge is checked;failed unique-net method retained. Continue physicalbank/globalbindings instead of precision sweeps.








## Article results before precision tuning - 2026-10-12





User confirms imperfect results are acceptable; completing layout and per-module simulations is the priority. Preserve measured errors and failed runs. Distinguish missing implementation from imperfect precision. Continue physicalintegration using completed scoped module evidence; do not require wholepage/fullchip SPICE or signoff before article assembly. Qualified physicalpartitions are valid module evidence with explicit boundaryfixtures; they do not establish fullcoupled behavior.








## Nativechild andactualboundarymetal composition - 2026-10-12





Use frozen nativechild LVS/exactproofs plusindependent actualmetal/via boundary connectivity forlargeparent integration whenflat/hierarchical extractionstalls. VerifyallchildGDSbytes,everyterminal,allnewpaintcontacts,nounintendedaliases/opens,andgeometry/TEXT/sourcebinding equivalence beforeextendingrepresentativecoverage. GF180MIM41cuts requireCAPM/CAPDEFclassification;rejectpartialmaskcases. Knownbadnative-extractionshort servespositivecontrol. KeepnativeflatLVS/RC flagsfalse untilthose specificrunsfinish. This qualifiedcomposition replaces repeatedlargeextractioncampaigns forarticle connectivitywork.








## Globalanalogaccess tree contract - 2026-10-12





Reuse230MOS8way READ/WRITE/ENABLE/RECOVselector above native1024pages. Isolate8analogDATA lines perchild withnativeTG controlledbythat WRITE output;broadcastingDATA intoeverypage wouldadd needlesscapacitance. Keepuniformlogicaltree depth even inpartiallypopulatedtails soeveryaddressbit decoded;unusedRECOV inputs tieVCM andno logicalstateassigned. Canonicalbankrank excludesexistingcompute/page exceptions beforebase8pageaddressing. Physicalparentrouting mustescapeeachchildinto dedicatedrowchannels beforecrossingotherchildcolumns,thenjoinexternalM4spines;avoidM5branches throughotherchildinteriors. Loadedtree timing/lanereplication stillrequired;onecompute/actor doesnot establish5ms.








## Adaptation shared access V12 - 2026-10-12





UseactualM4andM5groundshieldsandlocalfloating-stateports;carryrepaired4-6mVerrors forwardforarticleassembly. NativeNetgen mismatchmustremainexplicit;independentcompleteprimitive/terminal/edge/dimensionproofs provideconnectivitybasis,notnativeNetgenpass.








## Class-score access V13 - 2026-10-12





Carry completed class-score restore7.97mV/roundtrip22.32mV errors forward for research article completion. Reuse existing readout and shared voltage bridges/holds; no precision sweep or digital numeric fallback. Finish global functional bindings before refinement. Native Netgen mismatch remains explicit; independent exact primitive/edge/dimension proof is connectivity evidence.








## Reuse lossless two-way event fork for fixed graph fanout - 2026-10-12





Selected the existing `event_fork2` protocol primitive as the first physically qualified GF180 graph operator. Retain independent per-branch pending state so a stalled destination cannot drop or duplicate categorical packets. Keep the macro boundary separate from analog state and weights. Continue to qualify the remaining operators before claiming graph or full-chip integration. Evidence: `artifacts/analog_asic/results/gf180_analog_event_fork2_v1.json`.








## Reuse nearest-neighbor event fanout for 2x graph expansion - 2026-10-12





Selected the existing categorical `event_upsample2x` operator as the fixed GF180 implementation for the two 2x expansion paths. Keep event copies serialized with ready/valid backpressure and preserve the single completion token. Evidence: `artifacts/analog_asic/results/gf180_analog_event_upsample2x_v1.json`. Full graph timing still depends on all actors and operators together.








## Keep lossless join separate from residual deduplication - 2026-10-12





Selected the existing two-input event join for concatenation and the project2+x1 multiplicity-preserving skip. Its contract forwards coincident input events separately. Do not use it as a residual OR; qualify a distinct deduplication implementation. Evidence: `artifacts/analog_asic/results/gf180_analog_event_join2_v1.json`.








## Use sorted-stream merge for analog residual OR, conditional on actor ordering - 2026-10-12





Selected the one-head-per-input sorted merge instead of the legacy `MAX_EVENTS` exact-search SRAM design for the analog residual operator. It handles arbitrary event counts with constant local storage and preserves binary OR semantics. This choice requires unique, monotonically increasing per-actor event addresses; the physical actor scanner must be bound and checked before the residual operator can be claimed as fully integrated. Evidence: `artifacts/analog_asic/results/gf180_analog_binary_event_merge_sorted2_v1.json`.








## Pipeline the offset-64 concat leg - 2026-10-12





Selected a one-entry registered channel remap to provide a physical GF180 timing boundary while retaining one-packet-per-cycle flow and backpressure. The extra cycle is part of graph latency and will be included when actor routes are assembled. Evidence: `artifacts/analog_asic/results/gf180_analog_event_channel_offset64_v1.json`.





## Partition actor spike serialization into 32-lane banks - 2026-10-12





The 128-lane priority/scan block did not complete detailed routing within bounded runs. Selected four contiguous 32-lane shift-register scanners operating in parallel, followed by the existing sorted merge tree. This keeps analog neuron state and thresholding unchanged and supplies the strict ascending event order required for residual OR. One 32-lane bank has routed views and Magic flat DRC zero; two OpenROAD Metal2 spacing report entries at a shared location remain documented. The 128-neuron parent is now separately routed and Magic DRC zero, but its final ORFS report contains 120 max-slew violations and it is not yet bound to analog comparator outputs.


## Physically route the four-bank 128-neuron output page - 2026-10-12





The four-bank 32-lane scan and sorted merge tree now passes end-to-end simulation and has a routed parent GDS/SPEF/LEF/Liberty. OpenROAD DRT and Magic full-style flat GDS DRC report zero errors; the final ORFS report still has 120 max-slew violations. Keep the architecture and carry the slew issue forward as a known limitation while binding the output page to the original analog comparators and graph. Evidence: `artifacts/analog_asic/results/gf180_analog_spike_event_page128_v1.json`.





Signed weight event update - 2026-10-13: retain one analog signed charge packet per presynaptic event. Correct the nominal shared NPROGRAM source to0.613V and ramp reset reference to1.0V for the tested continuous1.0-1.4V magnitude range. Extracted GF180 events show a quiet zero, a monotone quarter-scale point and +/-full-scale delivery within0.15% at1.4V. This supersedes the earlier statement that unequal signed magnitudes remained uncorrected at the nominal point. Do not mark the weight path accepted: the 143,824-value original-float inventory has a substantial short-pulse tail, loaded analog memory/readout is not connected, and network accuracy/5ms service are untested. Keep the original-float network as the reference; no QAT/quantized or digital-state fallback.





## Reject the linear low-end weight map pending correction - 2026-10-13





Keep the signed one-event-per-presynaptic-spike interface and original continuous float weights. Do not use the current linear MAG_DATA=1.0+0.4*abs(w)/max_abs(weight_tensor) map as an accepted implementation: the extracted nominal parent produces no pulse at5% or10%, and under-delivers at15% and20%. Next, tune the physical magnitude-to-duration transfer while preserving a quiet zero and5ms completion; if this ramp path cannot represent the low end, compare a fixed-duration amplitude injector and the switched-capacitor alternative. Replay the original-float model against the measured transfer before accepting any weight encoding. No QAT or digital numerical state.








Weight magnitude encoding update - 2026-10-13: use continuous voltage stored on the physical native MIM weight bank to control current amplitude during one fixed-width analog event. Calibrate the nonlinear gate-voltage-to-charge transfer and invert it for original-float weight magnitude; the cell voltage range does not imply a linear current transfer. A nominal extracted composition delivers nonzero charge at0.1% of full scale and matches sampled q0.1%, q1%, q5%, q10%, and full-scale targets within16.5%,2.2%,0.02%,1.4%, and0%, respectively. Keep this as a candidate only: rerun with sampled gate hold at the final settings, establish a noise/mismatch/PVT floor, connect addressed reads, then replay original-float inference and measure5ms service. Do not quantize or claim model accuracy from these transfer screens.








Original-float range update - 2026-10-13: retain every epoch58 float coefficient. The verified 143,824-weight inventory has a minimum per-tensor-normalized magnitude of1.68e-7 and about2% of values below0.1%; do not infer that those values can be removed from nominal cell simulations. The single fixed-duration current range does not distinguish q1e-5 and smaller from zero at the current report precision. Next measure inference sensitivity with a continuous analog transfer model and improve analog current sensitivity/range if needed; keep QAT and digital numerical state out of the design.








Analog range contract update - 2026-10-13: map each original float magnitude continuously into the safe analog programming range through a measured nonlinear inverse transfer; do not treat the capacitor voltage range alone as proof of weighted-current range. The native weight capacitor successfully stores the q0.1-to-full calibrated values, while the extracted source/readout resolves only to about normalized q1e-4 at TT27 in the current diagnostic. Keep all float weights and investigate a lower-current/gain-range analog read path; model sensitivity over four records is informative but not validation acceptance. No QAT, quantized reference or digital numerical state.








Continuous float-to-capacitor range - 2026-10-13: define the analog weight encoding over the measured usable capacitor/gate-voltage interval and retain every original float value; choose the endpoints from physical headroom and calibrate the nonlinear voltage-to-charge transfer. Do not infer precision from voltage fit alone: the present GF180 path resolves settled current only down to about normalized1e-4 at TT27, while the minimum normalized float magnitude is1.68e-7. Four-record residual sensitivity is modest for the tested +/-1.5e-5 full-scale model, but does not prove noise/PVT/accuracy. Continue analog low-current range and offset work; no QAT or coefficient cutoff.








Low-tail inverse-map qualification - 2026-10-13: set the zero and magnitude gate voltages using an extracted nonlinear inverse transfer, not an affine mapping of raw float extrema. The transparent-writer source/read bench supports q1e-5 near3.1194V within about10% at TT27. Do not claim q1e-6 or minimum-weight accuracy: those results move with bench composition, and the low-tail sampled-MIM/readout transient does not converge. Keep continuous weights; require stable physically held read and offset/reference cancellation before accepting the extended voltage range.








Held low-tail weight transfer - 2026-10-13: a physically sampled nine-MIM weight cell needs a1us writer ramp for convergent low-tail read simulation. Even then, q1e-5 and q1e-4 current/charge read fractions are roughly44x and6.3x above target, while full scale is correct and held gate is about0.8mV below command. Source-only inverse transfer is insufficient; continue with physical baseline cancellation and gate correction. Preserve all float weights and leave analog accuracy unaccepted until held read is characterized.








Held-cell transfer supersession - 2026-10-13: the earlier 44x/6.3x low-tail error applies to the transparent-writer-derived commands, not the recalibrated held-cell operating point. v17 shows negligible gate movement during READ. The four-case v23 extracted held-cell run measures q1e-5/q1e-4 charge at1.1767x target each with full-scale unity. Use this as a nominal continuous nonlinear map starting point only; independently confirm composition repeatability, characterize through the checkpoint minimum, and complete inference/5ms validation. Do not infer analog precision from capacitor voltage fit alone; preserve all float coefficients and numerical state.








Held-cell map repeatability - 2026-10-13: independent three-branch extracted TT27 checks confirm the v23 q1e-5 and q1e-4 held-gate calibration within about5% relative across tested branch compositions; full-scale remains unity. Proceed with this nominal map for range expansion and addressed integration. It does not resolve the checkpoint minimum or establish mismatch/noise/PVT, inference accuracy, or5ms service. Preserve all float weights.








Original-float membrane-to-capacitor range - 2026-10-13: map each8x8 membrane tile's measured continuous float range onto the usable physical capacitor voltage span using a local scale/reference. The eight-record checkpoint replay covers all30,976,000 states; observed guarded ranges vary1.57-19,100 model units. A single global scale is inappropriate for this spread. Keep numerical state analog and continuous; apply the same scale consistently to every recurrence term and threshold. Physical per-tile gain/reference and full-model accuracy remain open. No QAT or coefficient clipping.








Bank-local continuous float state scaling - 2026-10-13: bind one continuous scale to each existing8x8 spatial/channel membrane bank, serving up to64 analog state capacitors. Keep the scale value equal to usable signed capacitor half-swing divided by the calibrated float range. The bank-addressed range manifest covers all30,976,000 membranes with490,240 scales and adds no numerical quantization. Leave voltage endpoints unset until measured on the actual storage/restore path; the existing16x event-duration gain remains a candidate update mechanism, not yet integrated.








Measured voltage span for bank-local membrane mapping - 2026-10-13: use differential storage from-0.9V to+0.9V around1.65V, based on the native extracted sampler/read/restore screen over input0.75-2.55V with maximum tested round-trip error8.238mV. For each calibrated bank range Rtile, set the continuous state scale to0.9V/Rtile. This supersedes the earlier unset voltage endpoints. Keep PVT/noise/headroom and physical per-bank scale application open; the mapping alone does not accept the full PLIF.




| Keep 8x8 bank ranges as the fidelity baseline pending coarsened-state replay | Range-only analysis gives 16x16 banks 3.88x fewer scale values but a 5%+ roundtrip-error proxy in 1.466% of states; 32x32 raises this to 3.264%. These are not model accuracy results. Do not adopt coarser banks until original-float replay measures their impact. Evidence: `artifacts/analog_asic/results/gf180_membrane_scale_bank_coarsening_v2.json`. |


| Preserve8x8 bank ranges after the coarsening stress replay | Across eight calibration records, one-sided/alternating injection of the full measured8.238mV bound each update gives16x16 mean-IoU loss0.0206-0.0495. The surrogate is deliberately conservative and not a measured distribution, but it does not support coarsening; retain8x8 until state-transfer error is physically characterized at the intended recurrence. Evidence: `artifacts/analog_asic/results/gf180_membrane_scale_coarsening_replay_summary_v1.json`. |


## Compact per-bank scale parent baseline — 2026-10-13

Use `gf180_membrane_scale_compact_v16` as the current extracted prototype. Earlier v4/v5 shorts disappeared after increasing TG/PFET placement spacing; retain that spacing in future revisions. v16 passes DRC/LVS/GDS readback, and a nominal 5ms write/hold simulation passes at three voltage points. Keep the original 8x8 float-bank range policy. Do not infer a linear float-to-current relationship: the 19-point PFET transfer is strongly nonlinear and must be inverted/calibrated against original-float bank values before recurrence integration. The 0.1273mm2 parent bbox is not yet acceptable as a dense replicated layout; area reduction follows functional calibration.


## Compact scale parent area baseline — 2026-10-13

Prefer `gf180_membrane_scale_compact_v23` over v16 for continued work: it preserves the proven 100000/200000 internal-unit TG/PFET placement offsets and shortens the global rails, retaining DRC/LVS/readback and simulation results while reducing bbox area to 0.02708mm2. Keep 8x8 original-float ranges. Before recurrence integration, invert/calibrate the measured nonlinear current transfer to the float ranges and verify model behavior; do not treat monotonicity alone as sufficient.

## Routed signed update and membrane state parent v8 — 2026-10-13

The v7 composed GF180 parent passed full-style DRC, hierarchical LVS and GDS round-trip. v8 tightens top-level metal5 track pitch from50um to10um and moves the state/update child to a clear adjacent location. Full-style Magic DRC remains0, Netgen LVS remains unique, and GDS readback DRC/LVS both pass. Bbox is4550.6x1365.45um (6.21mm2), down57% from v7's14.44mm2; it remains a spacious characterization fixture because the signed injector child itself spans3725um.

Corrected the extracted transient ordering to apply beta to the prior state before the current event, matching the PLIF equation. At TT27, magnitude command1.5, PPROGRAM=2.7V, NPROGRAM=0.455V, and the extracted v8 parent: positive event step is+13.15mV; negative is-12.66mV (3.8% magnitude mismatch). Beta changes the centered initial state by-0.49mV before either event. Stored state drift from post-event through5ms is0.00mV positive and+0.01mV negative at report precision. The correct-order test avoids the earlier event-then-beta measurement, which was not model-faithful. v15 also used an incorrect DATA hookup; v21 failed at a sharp beta edge; all failures are retained as bench diagnostics.

Evidence: `artifacts/analog_asic/layout/gf180_signed_state_update_composed_v8/qualification.json`; `artifacts/analog_asic/results/gf180_signed_charge_state_update_v24.json` and `v25.json`; bench generators `scripts/simulate_gf180_integrated_signed_charge_state_update_v24.py` and `v25.py`. These are two nominal fixed-magnitude TT27 cases, not full transfer curves, calibrated original-float recurrence, PVT/noise/mismatch, 64-state bank service or full-chip acceptance. The v8 geometry is not dense macro area.

## Original-float storage endpoint check and signed-charge boundary — 2026-10-13

The current continuous state map uses Vstored=1.65V+0.9V*state/range, spanning0.75-2.55V for each local8x8 float interval. Re-ran the actual routed3T/50fF under-MIM storage cell at those endpoints and center with VCM=1.65V, 3.3V write wordline, extracted31 nonnegative capacitance branches per cell, 5ms hold, then selected read and release. Write-release errors are-4.57/-6.12/-5.51mV; maximum held excursions2.90/6.59/13.47mV; read-release state changes-4.03/-2.01/+0.21mV. The three-point storage transfer is monotonic. The prior1.0-1.4V screen was limited coverage, not a demonstrated hard range. The selected storage cell therefore supports testing the full mapped span at nominal TT27. Source-follower offsets are large and uncalibrated (about0.797/1.023/1.213V); read mapping remains to calibrate. This is a one-cell screen with ideal external wordline/data/reference/current drivers, not full-bank or model acceptance.

The center-calibrated pulse injector is not range independent: at a post-beta low state, the nominal negative event moves+44.65mV; at a post-beta high state, nominal positive moves-54.18mV. Raising NPROGRAM to0.60V restores a negative step but produces-360mV; lowering PPROGRAM to2.60V produces+41.76mV. The routed v8 parent remains electrically qualified and its centered +/-13mV tests pass, but this does not establish signed updates over0.75-2.55V.

Switched-cap packet diagnostics are still inconclusive. Early versions had a top-plate common-mode mismatch and large state disturbance. In the later extracted TG/MIM sequence, both packet plates track STATE through beta, the bottom is then connected to an ideal state-matched driver and stepped, and the top stays connected through the step. The bottom-source integral is-0.544fC over a26mV step; the state node is unchanged to 6-digit report precision during the packet. Opening the top TG then shifts STATE by-40.37mV; a zero-step control gives-39.995mV. The packet signal is therefore buried by the switch edge and not yet shown to update membrane state. Do not treat the earlier nominal endpoint deltas as acceptance. Next establish a non-disturbing state-tracked packet sample or a state-independent current injector, then bind it to the qualified shared bank and replay the original-float recurrence.

Evidence: `scripts/simulate_gf180_shared_analog_memory_3t_v2_range5ms_v2.py`, report `artifacts/analog_asic/results/gf180_shared_analog_memory_3t_v2_three_native_5ms_srce94a1c303383.json`; endpoint pulse reports `gf180_signed_charge_state_update_v27.json`, `v28.json`, `v29.json`, `v30.json`, `v31.json`, `v32.json`; switched-cap reports `gf180_sc_membrane_packet_lo_p_r3_9fccb3e4cb.json`, `gf180_sc_membrane_packet_hi_n_r3_9fccb3e4cb.json`, `gf180_sc_membrane_packet_lo_p_r4_9fccb3e4cb.json`. Failed/incorrect packet and pulse benches remain preserved and are not acceptance evidence.

## Switched-cap packet loading probe — 2026-10-13

The PDK model gives the 5x5um MIM packet about49.75fF area capacitance plus4.77fF perimeter capacitance (about54.5fF total);0.51842fF in the extracted netlist is a parasitic term, not the MIM value. A shortened transient measured before and after the bottom-plate edge and before top-switch release. At the low endpoint setup, a26mV bottom step produces+9.631mV while connected, then the top TG release produces-40.371mV; a135mV bottom step produces+50.003mV while connected, then-41.932mV on release, leaving a net+8.072mV. The 5ms result for the latter is0.378mV above its post-release value. At the center setup, no packet step gives-31.000mV net;80mV gives-2.400mV and110mV gives+8.330mV. At the high endpoint setup, the no-step release kick is-20.000mV; a60mV step gives+22.100mV connected movement and+1.450mV net, while140mV gives+51.570mV connected movement and+30.050mV net. Sparse interpolation puts local zero-update packet steps near112.3mV low,86.7mV center and55.9mV high. The trend is roughly affine in the three sampled states and supports a state-conditioned offset map as the next candidate for signed updates. It remains a hypothesis: data are sparse, one-polarity, nominal TT27 samples. The prior3.03fC integral spans the switch release and is not a packet-only measurement. A no-beta-pulse case retains a roughly-40.6mV release kick, so the beta pulse is not its cause. The TG output contributes6.02807fF to VSS. The packet transfers successfully while connected; the remaining problem is state-dependent top-switch release error and its calibration/cancellation.

Next characterize the complete packet step-to-net-state transfer densely across stored state, polarity, pulse order and representative weights; then fit a state-dependent zero-update correction and replay it against the original-float PLIF update. Keep feedthrough cancellation as a parallel option if the required offset accuracy is too tight. These are nominal TT27 schematic compositions using extracted child netlists and ideal external packet/common-mode drivers; they are not a routed full cell, PVT/noise result, model replay, or5ms service acceptance except for the one low-state 135mV point.

Evidence: `artifacts/analog_asic/results/gf180_sc_packet_signed_transfer_curve_v1.json`, `artifacts/analog_asic/benches/gf180_sc_membrane_packet_lo_p_fastedge_v1.spice`, `artifacts/analog_asic/results/gf180_sc_membrane_packet_lo_p_fastedge_v1.log`, `artifacts/analog_asic/benches/gf180_sc_membrane_packet_lo_p_compkick5ms_v1.spice`, `artifacts/analog_asic/results/gf180_sc_membrane_packet_lo_p_compkick5ms_v1.log`, and the exploratory switched-cap benches/reports cited above.

## Packet precharge handoff correction — 2026-10-13

The same low-state bench showed a second error before the event: after beta, STATE is0.837547V; opening the sample TG drops it to0.802955V, then connecting the bottom driver at0.837545V raises it only to0.814432V. The combined handoff leaves a-23.113mV pre-event error. Turning on the bottom driver before opening the sample TG does not remove this error. Raising the driver baseline by62mV, from0.837545V to0.899545V, makes the post-handoff state0.837400V, within0.15mV of the post-beta value. Under that baseline, a110mV packet step leaves-0.725mV net after top-TG release; a135mV step leaves+8.179mV and changes by+0.348mV over the remaining nominal5ms. This is an encouraging single-state compensation screen, not a qualified design: only the low endpoint was exercised, the drivers are ideal, the baseline/packet mappings are not physically implemented, and negative/full-float updates, mismatch, PVT, noise, layout and model replay remain open.

Evidence: `artifacts/analog_asic/results/gf180_sc_packet_handoff_compensation_v1.json` and its hashed benches/logs.

## Signed packet update and 5ms hold at three state levels — 2026-10-13

Applied the fitted baseline and per-state zero-update offset at low, center and high storage levels. One positive event at each level yields+8.179mV,+7.380mV,+7.660mV; one negative event yields-8.560mV,-8.350mV,-8.080mV. Positive 5ms post-release drift is+0.348mV,+0.070mV,+0.010mV; negative drift is+0.367mV,+0.070mV,+0.020mV. The compensated sample/drive handoff remains within0.27mV of the post-beta state at all three tested points. This is the first nominal extracted-cell demonstration of both signed packet updates over the mapped voltage span with a 5ms hold on all six cases. The amplitudes and baselines are hand-chosen from sparse calibration, and their voltage-generation circuit is idealized. No checkpoint-derived weight transfer, accumulated multi-event sequence, dense range coverage, mismatch/PVT/noise, model inference, physical parent layout or full-chip service has passed.

Evidence: `artifacts/analog_asic/results/gf180_sc_packet_signed_state_compensation_v1.json` and its hashed benches/logs.

## Full-frame original-float range diagnostic — 2026-10-13

Ran the original epoch58 float checkpoint on one full 440x640 training frame, all ten5ms updates and all25 PLIF actors, recording both pre-threshold candidates and post-reset states. The existing per-8x8 range map came from eight other calibration records and can under-cover this frame: sizing each bank to include its largest candidate and the existing four-times-threshold floor requires a median0.91x expansion, p90 1.44x, p99 22.3x, p99.9 205x and max605x. About5.82% of banks need over2x,1.58% over10x and0.409% over100x. The widened-range estimate drives the smallest analog threshold to16uV, while the median threshold remains5.68mV. This shows that simply widening every affected bank risks losing usable threshold margin; the 8x8 scale allocation needs refinement or a precision-preserving range strategy before full-float packet mapping can be accepted.

This is exact original-float software on one complete real frame, not QAT or analog inference. The analog voltage mapping is applied as a range diagnostic only. The data do not establish whole-dataset state bounds, acceptable hardware noise/mismatch, or model accuracy. Evidence: `artifacts/analog_asic/results/gf180_train_record_state_range_diagnostic_v1.json` and the unchanged checkpoint/model/calibration hashes recorded there.

## Stored-state versus candidate range follow-up — 2026-10-13

Separated the pre-threshold candidate from the post-reset state that the membrane capacitor must store. The expansion problem remains in post-reset state: candidate and stored-state range factors are close. Repeated the full-float diagnostic on eight contiguous frames from `zurich_city_00_a`, using the same epoch58 checkpoint and eight-record validation scale map. Across frames, about1.90-2.11% of state sites require over2x the mapped range,0.697-0.770% require over10x, and0.099-0.117% require over100x. The p99 stored-state expansion is5.16-6.09x, p99.9 is100.69-107.23x, and the minimum threshold under full expansion is15.55-16.10uV. This shows repeatability within one sequence, not coverage across independent scenes or the full training set. It supports the voltage-range mapping but does not qualify analog accuracy or noise margin.

Evidence: `artifacts/analog_asic/results/gf180_train_record_state_range_diagnostic_v3_record0_store_vs_candidate.json` through `...record7_store_vs_candidate.json`; source `scripts/diagnose_gf180_train_record_state_range_v3_store_vs_candidate.py`.

## Provisional capacitor-range choice — 2026-10-13

Keep the existing per-8x8 float-to-voltage map at its safe capacitor rails and permit saturation on rare outliers, rather than expanding every affected bank. An ideal replay on eight contiguous frames from `zurich_city_00_a` compared clipping the pre-threshold candidate with clipping only the stored post-reset state. Candidate clipping changed1.41-1.62% of predicted pixels and reduced mean present-class mIoU by0.000364 (worst frame0.000902); stored-state clipping changed1.12-1.40% of pixels and reduced mean mIoU by0.000349. Full-range expansion lowers the smallest threshold to about16uV. The observed accuracy cost is small enough to proceed with this map for the article prototype, while keeping the choice provisional until the physical packet saturates and the complete update path is replayed. Coverage is eight adjacent frames from one sequence; this is not independent-scene accuracy or circuit evidence.

Evidence: `artifacts/analog_asic/results/gf180_train_record_voltage_range_saturation_v1_summary.json`; individual frame reports `gf180_train_record_voltage_range_saturation_v1_record0.json` through `...record7.json`; source `scripts/replay_gf180_train_record_voltage_range_saturation_v1.py`.

## Always-connected diode rail clamp rejected — 2026-10-13

Tested native GF180 diode-connected NMOS/PMOS clamps around the 5x5um MIM state capacitor with shared1.35V/2.20V references. The bench initializes VCM and rails explicitly under UIC, then injects approximately±0.44fC at the low/high rail. By5ms the low state rises from0.7503V pre-event to0.7573V after a requested negative update; the high state falls from2.5498V to2.5475V after a requested positive update. Matching unclamped controls retain the expected signs at0.7425V and2.5575V. The always-connected clamp therefore erases/reverses the boundary update and is unsuitable. Proceed only with a phase-gated clamp or another limiter that disconnects during state hold.

Evidence: `artifacts/analog_asic/results/gf180_state_diode_clamp_screen_v1.json` and preserved benches/logs.

## Phase-gated capacitor rail limiting demonstrated — 2026-10-13

Replace the rejected always-connected diode clamp with an extracted quarter-size transmission gate that connects the state capacitor to a shared rail only during the commit window. In a nominal TT27 54.5fF state screen, outward updates at0.75V and2.55V were returned to within17uV and10uV of their rails after5ms. Inward updates remained unclamped and were held at+7.499mV and-7.500mV after5ms; the1.65V control held unchanged. Small static rail offsets compensate nominal TG turn-off kick. This supports rail saturation as the working range policy. The gate phases are ideal external commands; no comparator, physical sequencer, PVT/noise/mismatch or combined packet parent has been qualified.

Evidence: `artifacts/analog_asic/results/gf180_state_phase_gated_clamp_screen_v8.json`; bench `artifacts/analog_asic/benches/gf180_state_phase_gated_clamp_screen_v8.spice`.


## Continue with routed switched-cap packet; recalibrate at each state range — 2026-10-13

The center-state packet method remains the selected next implementation because the compact parent now passes DRC/LVS/GDS readback and delivers matched signed8mV-class updates with less than0.05mV drift over5ms. Use parent v12 while calibrating; the center packet steps must not be reused at endpoints without measurement. The endpoint transient shows beta/handoff errors up to13.9mV and wrong/small updates for some old packet settings. Continue with state-conditioned beta/baseline and positive/negative packet transfer calibration, then exercise the original-float recurrence. This is a provisional article implementation, not an acceptance claim. The first long-bus parent is rejected functionally because routed control coupling dominated the update; compact reroutes remain experiments until extracted simulation passes.

Evidence: `artifacts/analog_asic/layout/gf180_sc_state_packet_compact_v12/qualification.json`, center and endpoint reports cited in RESULTS.md.


## Physical switched-capacitor voltage mapping - 2026-10-13

The physically routed auxmetal_v1 switched-capacitor parent adds 5.52fF by enlarging existing M4/M5 plates from 100 to 240um2, with no bounding-box growth (0.04925mm2). DRC/LVS/GDS readback pass. Extracted calibrated low/high packets deliver +7.987/-7.935mV and +7.960/-8.000mV; endpoint hold drift <=0.191mV over 5ms. Seven initial states and -8/0/+8mV commands (21 cases, 130us) yield <=0.330mV packet error under interpolation of external calibration anchors. Handoff displacement improves to <=7.50mV but learned beta is not qualified. Prior MOS-cap screens are diagnostic only; body-at-VCM variants do not establish a standard substrate implementation. Actual linear metal plates are the carried-forward design. External ideal references/phases, UIC startup, original-float precision, PVT/noise, physical producer bindings and full-population 5ms remain open. Evidence: `artifacts/analog_asic/layout/gf180_sc_state_packet_auxmetal_v1/qualification.json`, `artifacts/analog_asic/results/gf180_sc_state_packet_auxmetal_v1_beta_noaux_calibrated_packet_map_v1.json`, `artifacts/analog_asic/results/gf180_sc_state_packet_auxmetal_v1_state_map21_v1.json`.

Documentation archive: `artifacts/analog_asic/documentation_history/project_docs_before_auxmetal_packet_map_20261013T063506Z.zip`.


## Integrated trained beta and shared auxiliary reference - 2026-10-13

GF180 integrated original-channel beta and physical shared-reference qualification. The detail_stem channel3 v4 SC parent passes DRC/LVS/GDS readback in0.04925mm2; actual386.4um2 auxiliary metal plates give measured beta0.88298 versus trained0.88189. Nominal21cases across0.75-2.55V have <=1.89mV combined beta/packet error with external calibrated reference. Two original-float heldout replays reproduce baseline hashes and change1.60/1.83% pixels with IoU+0.00175/+0.00123 for this channel only. Native three-resistor/MIM-decoupled reference v2 also passes physical checks; one extracted reference drives21 extracted parents with1us stagger and10ns beta edges, <=3.54mV candidate error. Inter-macro wiring remains bench-only. Next physically route reference and compute together, qualify actual weight/VCM producers and learned-beta channel coverage, then shared-service/full-chip integration. Full-model accuracy and5ms population service remain unqualified. Evidence and rejected attempts: `artifacts/analog_asic/results/gf180_sc_packet_beta_reference_stage_v1.json`. Archive: `artifacts/analog_asic/documentation_history/project_docs_before_sc_beta_reference_20261013T071254Z.zip`.


## Layout-first delivery order - 2026-10-13

Full-chip research layout completion first, then per-module simulation, per explicit user direction2026-10-13. Carry current measured imperfections forward. Start from V13 full-population numeric-state access assembly and existing physical module library; physically implement and connect the25-actor event graph, actor/event boundaries, parameter delivery and phase/address controls. Fix only missing connections, shorts/opens, absent required functions or faults preventing operation. Defer calibration refinements, behavior optimization and repeated accuracy screens until the full layout is assembled. Analog state and original epoch58 float parameters remain the architecture. Full layout and population5ms/accuracy validation are incomplete; do not claim placement/capacity alone completes functional layout. Archive: `artifacts/analog_asic/documentation_history/project_docs_before_layout_first_20261013T072922Z.zip`.


## Required state-service parallelism - 2026-10-13

One scalar service lane per entireactor is insufficient for real-time5ms. The generated address/result controller establishes a three-cycle per-neuron ideal lower bound; largestactor0.33792s at40MHz, at least68independent services before realanalog timing/traffic. Do not qualify currentserial fullpopulation service. Preserve originalfloat state/SNN semantics; partition analog state-access trees and replicate analog service/result lanes using measured loaded timing. The actual lane count and storage partition must still be selected and physically verified. New V2categorical address logic uses eachactor's exact19local exceptions;11actors leavebank9inforest whilebank19islocal. Numerical state/weights remain analog. Full layout/control/parameter completion remains the delivery priority.


## 2026-10-13 — Fixed-kernel ingress and confirmed real-time parallelism

- User explicitly retained5ms real-time execution. Slower execution is not an accepted replacement.
- Generated all25 actor ingress services from original epoch58 float convolution/input shapes;143728 PLIF synaptic addresses, plus96separate head weights. Preserve event multiplicity; each group completion requires all connected output channels' signed analog charge.
- First ingress physical attempt exhausted4GB during Yosys arithmetic mapping. Preserved failed status/log. V2 uses bounded fixed-kernel categorical arithmetic and omits redundant per-output address arithmetic. Ingress protocol passes; all25 actual configurations pass150000 clock comparisons against prior valid-address behavior, including padding/stride/groups/backpressure. First comparison incorrectly compared coordinates when valid was false; retained failure and corrected protocol-qualified comparison in scatter_fixed_kernel_v2b.
- Physical ingress V2 running: ess-gf180-full25-actor-ingress-v2; assembly/full25_actor_ingress_v2/status.json. Native analog weight read/injection remains unbound.
- Decision-control V2 first attempt timed out after30min; saved5_1_grt.odb and prior status/log retained. Resumed routing/final export in ess-gf180-full25-decision-control-resume-v3 with repeated post-route antenna repair disabled; carry remaining antenna findings. Final timing/layout acceptance awaits terminal reports.
- Reused two existing verified epoch58 float activity records; no new full-model simulation.11actors exceed ideal single40MHz packet capacity;19 exceed ideal single group issue capacity. final_fuse.standard needs >=35packet paths, >=309group issue paths, >=68three-cycle decision services before analog delay/contention/DAG overhead. Bounds are necessary minima under optimistic40MHz, not chosen hardware parallelism or timing closure.
- Next architecture must partition shared storage roots, provide independent native services and parallel weight/event dispatch, then preserve completion barriers and result ordering. Serial macro completion does not establish a5ms ASIC. Latest assembled GDS remains V16; functional full layout, loaded module service, original-float accuracy and5ms are incomplete.

Evidence: artifacts/analog_asic/results/actor_ingress_v2/simulation.json; results/scatter_fixed_kernel_v2b/simulation.json; assembly/full25_actor_ingress_v2/status.json; assembly/full25_actor_ingress_v2/measured_parallel_service_requirements_v1.json; assembly/full25_decision_control_v2/status.json (all relative to artifacts/analog_asic except where shown).


## Active remaining task: consumption per element type — 2026-10-14

The user clarified that per-module simulation means power/energy consumption for one representative instance of each implemented model element: one PLIF core, one membrane storage cell, one signed synaptic injector, beta/threshold/reset, adaptation, inhibition, normalization and class readout, plus their shared access/bias/control circuits. The full article layout is already delivered. Characterize element types once with explicit nominal operating point, activity/load, operation duration, idle/hold power and energy per operation. Do not simulate every replicated instance or restart behavior/calibration/layout improvements as completion gates.

Keep one resident storage cell separate from the shared PLIF update core and shared bank/page reader. Never divide a whole shared module's supply energy by its state capacity and label that a measured single-cell value. Account for driver/reference/programming ports explicitly; VDD alone may exclude energy supplied through other ports. Reuse saved current traces and existing supply results first, then run only missing bounded small-module measurements. Evidence/status: `artifacts/analog_asic/results/module_consumption_v1/consumption_inventory.json`; per-element consumption is not yet complete.



## Representative per-element consumption delivered — 2026-10-14

The article layout and representative consumption characterization are complete under the user's clarified scope. `artifacts/analog_asic/results/module_consumption_v1/consumption_summary.json` covers all22 required element/module families, plus native capacitor, sampled decision, bias/normalization kernels and the three shared categorical macro estimates. One physical PLIF core, one3T+MIM resident cell, signed injector, adaptation, inhibition, normalization, readout, access and controls are distinguished. Each transient row states its window and supply energy/power; detailed reports retain input-port accounting. Core beta/decision/reset windows are measurements of the whole core during those phases, not standalone leaf powers.

Coverage combines newly completed native transients, reused complete rail-current traces, native RMS DC/settled samples and explicitly labeled routed-library digital power estimates. Shared1024-state reader power is partition/leaf characterization, not a completed full connected-page power simulation. Bias/reference/phase-generator overhead outside the measured boundary remains excluded unless stated. No measured full-chip power, calibrated behavior or5ms full-population deadline is claimed. Do not sum overlapping modules or replicate shared-core cost per logical membrane. Further circuit optimization is optional.



## ASIC artifact reorganization — 2026-10-14

Canonical article package: `artifacts/analog_asic/` (start at index.html). Final GDS is `layout/EventSpikeSeg140k_GF180_Analog.gds`; PNG/SVG figures are together in images/; current consumption data is consumption/summary.json. Original manifests/source/results are preserved unchanged under evidence/, components/, model_reference/support locations. The current path locator is `artifacts/asic_artifact_index.json`.

Digital documentation-only snapshots are `artifacts/ASIC/final/` and `artifacts/ASIC_XL/final/`; neither claims a completed digital full-chip layout. Last exports, hierarchy inventory, completed block views and final reports are retained; digital jobs remain paused.

All superseded attempts and build environments moved to `bin/asic_cleanup_2026-10-14_20261014T145109Z/`, including related digital OpenROAD history. No files deleted. cleanup_plan.json inventories every original file; integrity_audit.json accounts for all64,814 originals and verifies SHA256 of all2,779 retained files. restore_artifacts.ps1 can restore original artifact trees; pre-cleanup docs and .gitignore are backed up in the same bin. User review of this bin is pending; do not delete it without explicit instruction. Historical report/script paths are original provenance; resolve with the locator or restore dependencies before replay. New experiments belong outside final/.

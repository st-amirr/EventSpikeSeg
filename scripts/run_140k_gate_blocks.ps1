param([string[]]$Blocks=@())
$ErrorActionPreference='Stop'
$taskRoot='C:\Users\stamir\Desktop\EventSpikeSeg'
$taskBase=Join-Path $taskRoot 'artifacts\ASIC\primitive_characterization'
$taskInventory=Join-Path $taskBase 'base_140k_inventory'
$taskCases=Get-Content -LiteralPath (Join-Path $taskInventory 'mechanism_gate_manifest.json') -Raw | ConvertFrom-Json
$taskStatus=[System.Collections.Generic.List[object]]::new()
if($Blocks.Count) { $oldStatus=Get-Content -LiteralPath (Join-Path $taskInventory 'mechanism_gate_status.json') -Raw | ConvertFrom-Json; foreach($item in $oldStatus) {if($item.block -notin $Blocks){$taskStatus.Add($item)}}; $taskCases=@($taskCases | Where-Object {$_.block -in $Blocks}) }; foreach($case in $taskCases) {
  $label=$case.block
  $local=Join-Path $taskRoot $case.result_directory
  $linux='/workspace/'+$case.result_directory
  $entry=[ordered]@{block=$label;status='running';stage=$case.physical_stage}
  $watch=[Diagnostics.Stopwatch]::StartNew()
  Write-Output "START $label ($($case.physical_stage))"
  if($case.physical_stage -ne 'detailed_route') {
    docker run --rm --name "eventspikeseg-140k-gate-$label-export" --network none --memory 8g --cpus 2 --ulimit core=0 --volume "${taskRoot}:/workspace:ro" --volume "${taskBase}:/workspace/artifacts/ASIC/primitive_characterization" openroad/orfs:latest timeout 120 /OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad -no_init -exit "${linux}/${label}_export.tcl" *> (Join-Path $local "${label}_export.log")
    if($LASTEXITCODE -ne 0) {$entry.status='export_failed'}
  }
  if($entry.status -eq 'running') {
    $command='set -euo pipefail; iverilog -g2012 -gno-specify -s '+$label+'_tb -o /tmp/gate.vvp /workspace/artifacts/ASIC_XL/activity/enc1_depthwise_1x1_beta48_gate/sim_models/stdcells/*.v /workspace/'+$case.netlist+' '+$label+'_tb.sv >'+$label+'_compile.log 2>&1; vvp -N /tmp/gate.vvp | tee '+$label+'_simulation.log'
    docker run --rm --name "eventspikeseg-140k-gate-$label-sim" --network none --memory 8g --cpus 2 --ulimit core=0 --ulimit fsize=536870912 --workdir $linux --volume "${taskRoot}:/workspace:ro" --volume "${taskBase}:/workspace/artifacts/ASIC/primitive_characterization" eventspikeseg:torch2.2.2-cpu-verification-guarded timeout 120 bash -lc $command *> (Join-Path $local "${label}_run.log")
    if($LASTEXITCODE -ne 0) {$entry.status='simulation_failed_or_bounded_timeout'}
  }
  if($entry.status -eq 'running') {
    docker run --rm --name "eventspikeseg-140k-gate-$label-power" --network none --memory 8g --cpus 2 --ulimit core=0 --volume "${taskRoot}:/workspace:ro" --volume "${taskBase}:/workspace/artifacts/ASIC/primitive_characterization" openroad/orfs:latest timeout 120 /OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad -no_init -exit "${linux}/${label}_power.tcl" *> (Join-Path $local "${label}_power.log")
    $entry.status=if($LASTEXITCODE -eq 0){'power_complete_pending_audit'}else{'power_failed_or_bounded_timeout'}
  }
  $entry.seconds=[math]::Round($watch.Elapsed.TotalSeconds,1)
  $taskStatus.Add([pscustomobject]$entry)
  $taskStatus | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $taskInventory 'mechanism_gate_status.json')
  Write-Output "$label : $($entry.status) ($($entry.seconds)s)"
}


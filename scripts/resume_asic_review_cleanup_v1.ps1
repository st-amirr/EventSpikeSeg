# Resume partial Windows directory moves using exact inventoried files; never overwrite or delete.
$ErrorActionPreference = 'Stop'
$TaskRoot = [IO.Path]::GetFullPath('C:\Users\stamir\Desktop\EventSpikeSeg')
$Pending = Get-Content -LiteralPath (Join-Path $TaskRoot 'artifacts\asic_cleanup_pending.json') -Raw | ConvertFrom-Json
$Plan = Get-Content -LiteralPath $Pending.plan -Raw | ConvertFrom-Json
$TaskBin = [IO.Path]::GetFullPath($Plan.bin)
function Checked([string]$p,[string]$parent){$f=[IO.Path]::GetFullPath($p);if(-not $f.StartsWith($parent.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)){throw "Outside expected root: $f"};return $f}
Checked $TaskBin (Join-Path $TaskRoot 'bin')|Out-Null
$Journal=Join-Path $TaskBin 'move_journal.jsonl'
$Count=0;$Already=0
# Existing original and partial-bin files are all checked before resuming.
foreach($e in $Plan.original_files){$src=Checked (Join-Path $TaskRoot $e.original) $TaskRoot;$dst=Checked (Join-Path $TaskBin $e.original) $TaskBin;$available=if(Test-Path -LiteralPath $src -PathType Leaf){$src}elseif(Test-Path -LiteralPath $dst -PathType Leaf){$dst}else{throw "Original missing from both locations: $src"};if((Get-Item -LiteralPath $available -Force).Length -ne $e.bytes){throw "Original size changed: $available"}}
foreach($e in $Plan.original_files){
 $src=Checked (Join-Path $TaskRoot $e.original) $TaskRoot;$dst=Checked (Join-Path $TaskBin $e.original) $TaskBin
 if(Test-Path -LiteralPath $src -PathType Leaf){
  if(Test-Path -LiteralPath $dst){
   if((Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash){throw "Conflicting copies: $src"}
   $extra=Checked (Join-Path (Join-Path $TaskBin 'duplicate_original_copies') $e.original) $TaskBin;New-Item -ItemType Directory -Path (Split-Path -Parent $extra) -Force|Out-Null;Move-Item -LiteralPath $src -Destination $extra -Force
  }else{New-Item -ItemType Directory -Path (Split-Path -Parent $dst) -Force|Out-Null;Move-Item -LiteralPath $src -Destination $dst -Force}
  @{type='original_to_bin';original=$e.original;target=$dst;bytes=$e.bytes}|ConvertTo-Json -Compress|Add-Content -LiteralPath $Journal -Encoding utf8;$Count++
 }else{$Already++}
 if(($Count+$Already)%5000 -eq 0){Write-Output ('Original files accounted in bin: '+($Count+$Already))}
}
foreach($entry in $Plan.roots){
 $src=Checked $entry.source $TaskRoot
 if(Test-Path -LiteralPath $src){
  $unknown=Get-ChildItem -LiteralPath $src -Recurse -File -Force | Select-Object -First 1
  if($null -ne $unknown){throw "Unexpected new file in original tree: $($unknown.FullName)"}
  $relative=[IO.Path]::GetRelativePath($TaskRoot,$src);$empty=Checked (Join-Path (Join-Path $TaskBin 'empty_original_folders') $relative) $TaskBin
  New-Item -ItemType Directory -Path (Split-Path -Parent $empty) -Force|Out-Null;Move-Item -LiteralPath $src -Destination $empty -Force
 }
}
Write-Output ('All original files safely archived: '+($Count+$Already))
$Count=0
foreach($entry in $Plan.retained_files){
 $src=Checked (Join-Path $TaskBin $entry.original) $TaskBin;$dst=Checked (Join-Path $TaskRoot $entry.current) $TaskRoot
 if(Test-Path -LiteralPath $dst){throw "Retained destination already exists: $dst"}
 New-Item -ItemType Directory -Path (Split-Path -Parent $dst) -Force|Out-Null;Move-Item -LiteralPath $src -Destination $dst -Force
 @{type='retained_final';original=$entry.original;source=$src;target=$dst;bytes=$entry.bytes}|ConvertTo-Json -Compress|Add-Content -LiteralPath $Journal -Encoding utf8;$Count++
 if($Count%500 -eq 0){Write-Output ('Retained final files moved: '+$Count)}
}
@{status='moves_completed_pending_hash_and_accounting';retained_files=$Count;bin=$TaskBin;completed_utc=[DateTime]::UtcNow.ToString('o')}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $TaskBin 'move_status.json') -Encoding utf8
Write-Output 'Move phase completed. No files deleted.'

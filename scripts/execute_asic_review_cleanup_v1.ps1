# Move-only ASIC cleanup. All filesystem mutations stay in native PowerShell.
$ErrorActionPreference = 'Stop'
$TaskRoot = [IO.Path]::GetFullPath('C:\Users\stamir\Desktop\EventSpikeSeg')
$Pending = Get-Content -LiteralPath (Join-Path $TaskRoot 'artifacts\asic_cleanup_pending.json') -Raw | ConvertFrom-Json
$PlanPath = [IO.Path]::GetFullPath($Pending.plan)
$Plan = Get-Content -LiteralPath $PlanPath -Raw | ConvertFrom-Json
$TaskBin = [IO.Path]::GetFullPath($Plan.bin)
function Assert-Contained([string]$Path, [string]$Parent) {
 $Full = [IO.Path]::GetFullPath($Path)
 $Base = [IO.Path]::GetFullPath($Parent).TrimEnd('\') + '\'
 if (-not $Full.StartsWith($Base, [StringComparison]::OrdinalIgnoreCase)) { throw "Path outside expected directory: $Full" }
 return $Full
}
Assert-Contained $TaskBin (Join-Path $TaskRoot 'bin') | Out-Null
$Journal = Join-Path $TaskBin 'move_journal.jsonl'
# Verify every resolved source/destination before performing any directory move.
foreach ($Entry in $Plan.roots) {
 $Source = Assert-Contained $Entry.source $TaskRoot
 $Archive = Assert-Contained $Entry.archive $TaskBin
 if (Test-Path -LiteralPath $Archive) { throw "Archive destination already exists: $Archive" }
 $Item = Get-Item -LiteralPath $Source -Force
 if (($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Artifact root is a reparse point: $Source" }
}
foreach ($Entry in $Plan.retained_files) {
 $Source = Assert-Contained (Join-Path $TaskRoot $Entry.original) $TaskRoot
 $Target = Assert-Contained (Join-Path $TaskRoot $Entry.current) $TaskRoot
 $ArchiveSource = Assert-Contained (Join-Path $TaskBin $Entry.original) $TaskBin
 if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) { throw "Missing original file: $Source" }
 if (Test-Path -LiteralPath $Target) { throw "Retained destination already exists: $Target" }
 if ((Get-Item -LiteralPath $Source -Force).Length -ne $Entry.bytes) { throw "Source size changed: $Source" }
}
# Preserve the exact project instructions/documents and ignore file before edits.
$DocZip = Join-Path $TaskBin 'project_docs_before_cleanup.zip'
$Docs = @('ACTIVE_TASKS.md','AGENTS.md','ARCHITECTURE.md','DECISIONS.md','PROGRESS.md','RESULTS.md','project_spec.yaml') | ForEach-Object { Join-Path $TaskRoot ('docs\' + $_) }
Compress-Archive -LiteralPath $Docs -DestinationPath $DocZip
Copy-Item -LiteralPath (Join-Path $TaskRoot '.gitignore') -Destination (Join-Path $TaskBin 'gitignore_before_cleanup.txt')
foreach ($Entry in $Plan.roots) {
 $Parent = Split-Path -Parent $Entry.archive
 New-Item -ItemType Directory -Path $Parent -Force | Out-Null
 Move-Item -LiteralPath $Entry.source -Destination $Entry.archive
 @{type='root_to_bin';source=$Entry.source;target=$Entry.archive;utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Compress | Add-Content -LiteralPath $Journal -Encoding utf8
 Write-Output ('Archived original tree: ' + $Entry.source)
}
$Count = 0
foreach ($Entry in $Plan.retained_files) {
 $Source = Assert-Contained (Join-Path $TaskBin $Entry.original) $TaskBin
 $Target = Assert-Contained (Join-Path $TaskRoot $Entry.current) $TaskRoot
 $Parent = Split-Path -Parent $Target
 if (-not (Test-Path -LiteralPath $Parent)) { New-Item -ItemType Directory -Path $Parent -Force | Out-Null }
 Move-Item -LiteralPath $Source -Destination $Target
 @{type='retained_final';original=$Entry.original;source=$Source;target=$Target;bytes=$Entry.bytes} | ConvertTo-Json -Compress | Add-Content -LiteralPath $Journal -Encoding utf8
 $Count++
 if ($Count % 500 -eq 0) { Write-Output ('Retained final files moved: ' + $Count) }
}
@{status='moves_completed_pending_hash_and_accounting';retained_files=$Count;bin=$TaskBin;completed_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $TaskBin 'move_status.json') -Encoding utf8
Write-Output ('Move phase complete: ' + $Count + ' retained files. No deletions performed.')

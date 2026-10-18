# Restore archived sources; preflight all paths and hashes before any move.
$ErrorActionPreference = 'Stop'
$plan = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'plan.json') -Raw | ConvertFrom-Json
$root = [IO.Path]::GetFullPath($plan.root)
$archiveRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$sourceRoot = [IO.Path]::GetFullPath((Join-Path $root 'asic'))
if ($archiveRoot -ne [IO.Path]::GetFullPath($plan.bin)) { throw 'Archive directory does not match plan' }
$rows = @($plan.files | Where-Object action -eq 'archive')
foreach ($entry in $rows) {
 $src = [IO.Path]::GetFullPath((Join-Path $root $entry.target))
 $dst = [IO.Path]::GetFullPath((Join-Path $root $entry.original))
 if (-not $src.StartsWith($archiveRoot + '\',[StringComparison]::OrdinalIgnoreCase) -or -not $dst.StartsWith($sourceRoot + '\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Path outside restoration bounds' }
 if (Test-Path -LiteralPath $dst) {
  if ((Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash.ToLower() -ne $entry.sha256) { throw "Existing file differs: $dst" }
 } elseif (-not (Test-Path -LiteralPath $src) -or (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash.ToLower() -ne $entry.sha256) { throw "Missing or altered archived source: $src" }
}
foreach ($entry in $rows) {
 $src = [IO.Path]::GetFullPath((Join-Path $root $entry.target))
 $dst = [IO.Path]::GetFullPath((Join-Path $root $entry.original))
 if (-not (Test-Path -LiteralPath $dst)) {
  New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($dst)) -Force | Out-Null
  Move-Item -LiteralPath $src -Destination $dst
 }
}
Write-Output 'Archived sources restored. Documentation backups remain in before_changes.zip.'

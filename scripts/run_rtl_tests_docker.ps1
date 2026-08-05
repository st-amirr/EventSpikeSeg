Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
Push-Location $repositoryRoot
try {
    & docker compose run --build --rm rtl-test
} finally {
    Pop-Location
}
exit $LASTEXITCODE

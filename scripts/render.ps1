#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Thin PowerShell wrapper over scripts/build.py — Windows muscle memory only.

.DESCRIPTION
    Activates .venv if present, then forwards all arguments verbatim to build.py. There is
    exactly one build implementation (scripts/build.py); this wrapper must never grow logic of
    its own — see .claude/knowledge/architecture.md §9 "Command shapes".

.EXAMPLE
    scripts\render.ps1 doctor
.EXAMPLE
    scripts\render.ps1 render coupons/neutrik-tile
.EXAMPLE
    scripts\render.ps1 all --release
#>

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (Test-Path $venvPython) {
    $python = $venvPython
} else {
    Write-Warning ".venv not found at $venvPython — falling back to 'py -3' on PATH. Run the venv setup in README.md first."
    $python = 'py'
    $pyArgs = @('-3')
}

$buildScript = Join-Path $repoRoot 'scripts\build.py'

if ($python -eq 'py') {
    & $python -3 $buildScript @Args
} else {
    & $python $buildScript @Args
}

exit $LASTEXITCODE

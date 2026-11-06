[CmdletBinding()]
param([switch]$SkipSubmodules)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $ProjectRoot
try {
    if (!$SkipSubmodules) {
        & git submodule update --init --recursive
        if ($LASTEXITCODE -ne 0) { throw 'Submodule initialization failed.' }
    }
    $Patches = @(
        @('psxrecomp', 'lle-irq-thread-switch.patch'),
        @('psxrecomp', 'audio-cd-media.patch'),
        @('psxrecomp', 'pc-volume-settings.patch'),
        @('recomp-ui', 'recomp-ui-pt-br.patch')
    )
    foreach ($Entry in $Patches) {
        $PatchPath = Join-Path $ProjectRoot "patches/$($Entry[1])"
        & git -C $Entry[0] apply --reverse --check $PatchPath 2>$null
        if ($LASTEXITCODE -eq 0) { Write-Host "Already applied: $($Entry[1])"; continue }
        & git -C $Entry[0] apply --check $PatchPath
        if ($LASTEXITCODE -ne 0) { throw "Patch conflicts: $($Entry[1]). Local changes were preserved." }
        & git -C $Entry[0] apply $PatchPath
        if ($LASTEXITCODE -ne 0) { throw "Patch failed: $($Entry[1])" }
        Write-Host "Applied: $($Entry[1])"
    }
} finally { Pop-Location }

[CmdletBinding()]
param([string]$Python = '', [string]$Disc = '', [switch]$SkipGenerate, [switch]$Diagnostics,
      [switch]$NativeUI)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $ProjectRoot
$OldTemp = $env:TEMP
$OldTmp = $env:TMP
$OldIsolated = $env:PSX_STATIC_NO_ISOLATED
$RuntimeBuildDir = if ($NativeUI) { 'build-native-ui' } elseif ($Diagnostics) { 'build-diagnostics' } else { 'build-runtime' }
function Invoke-Checked([string]$Exe, [string[]]$Arguments) {
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Exe failed with exit code $LASTEXITCODE" }
}
try {
    if (!$Python) {
        $PythonCandidates = @()
        if (Get-Command py -ErrorAction SilentlyContinue) {
            $LaunchedPython = & py -3 -c 'import sys; print(sys.executable)' 2>$null
            if ($LASTEXITCODE -eq 0) { $PythonCandidates += "$LaunchedPython".Trim() }
        }
        foreach ($Base in @($env:LOCALAPPDATA, (Join-Path $env:USERPROFILE 'AppData/Local'))) {
            $PythonCandidates += Get-ChildItem -Path (Join-Path $Base 'Programs/Python/Python*/python.exe') -ErrorAction SilentlyContinue |
                Sort-Object FullName -Descending | Select-Object -ExpandProperty FullName
        }
        $OnPath = Get-Command python -ErrorAction SilentlyContinue
        if ($OnPath -and $OnPath.Source -notlike '*WindowsApps*') { $PythonCandidates += $OnPath.Source }
        foreach ($Candidate in ($PythonCandidates | Select-Object -Unique)) {
            & $Candidate -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>$null
            if ($LASTEXITCODE -eq 0) { $Python = $Candidate; break }
        }
        if (!$Python) { throw 'Python 3.11+ not found. Install it or pass -Python <path-to-python.exe>.' }
    }
    Invoke-Checked $Python @('-c', 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ required"')
    & (Join-Path $PSScriptRoot 'setup.ps1') -SkipSubmodules
    if ($Disc) { Invoke-Checked $Python @('tools/configure_disc.py', $Disc) }
    $ConfigPath = if (Test-Path -LiteralPath 'game.local.toml') { 'game.local.toml' } else { 'game.toml' }
    if (!(Test-Path -LiteralPath 'disc/SCES_028.73')) {
        throw 'Configure your disc first: ./scripts/build.ps1 -NativeUI -Disc <path-to-cue>'
    }
    New-Item -ItemType Directory -Force '.cache/tmp' | Out-Null
    $env:TEMP = (Resolve-Path '.cache/tmp').Path
    $env:TMP = $env:TEMP
    # Optional isolated fragments currently fail original-byte guard audit.
    # Keep the audited base variants and interpreter coverage for these gaps.
    $env:PSX_STATIC_NO_ISOLATED = '1'
    Invoke-Checked 'cmake' @('-S','psxrecomp/recompiler','-B','build-recompiler','-G','MinGW Makefiles',
        '-DCMAKE_BUILD_TYPE=Release','-DCMAKE_C_COMPILER=clang','-DCMAKE_CXX_COMPILER=clang++',
        '-DPSXRECOMP_STATIC_CLI=ON')
    Invoke-Checked 'cmake' @('--build','build-recompiler','--target','psxrecomp-game','psxrecomp-bios','--parallel','2')
    if (!$SkipGenerate) {
        Invoke-Checked 'build-recompiler/psxrecomp-game.exe' @('--config',$ConfigPath)
        Push-Location 'psxrecomp'
        try {
            Invoke-Checked '../build-recompiler/psxrecomp-bios.exe' @('--config','bios/OpenBIOS.toml')
            $Stamp = & cmake "-DROOT=$ProjectRoot/psxrecomp" '-DPROFILE=bios/OpenBIOS.toml' '-P' 'tools/bios_emitter_fingerprint.cmake'
            if ($LASTEXITCODE -ne 0) { throw 'BIOS fingerprint failed' }
            [IO.File]::WriteAllText((Join-Path (Get-Location).Path 'generated/OpenBIOS.emitter.sha'), ($Stamp -join "`n") + "`n")
        } finally { Pop-Location }
        Invoke-Checked $Python @('psxrecomp/tools/aot_overlay_pipeline.py','static','--profile','aot/overlays.json',
            '--game-toml',$ConfigPath,'--recompiler','build-recompiler/psxrecomp-game.exe',
            '--work-dir','.cache/aot-static','--gcc','gcc','--workers','2','--cps')
    }
    $RuntimeArgs = @('-S','.','-B',$RuntimeBuildDir,'-G','MinGW Makefiles',
        '-DCMAKE_BUILD_TYPE=Release','-DCMAKE_C_COMPILER=clang','-DCMAKE_CXX_COMPILER=clang++',
        '-DPSXRECOMP_REQUIRE_GAME_C=ON')
    $RuntimeArgs += if ($Diagnostics) { '-DPSX_DEBUG_TOOLS=ON' } else { '-DPSX_DEBUG_TOOLS=OFF' }
    if ($Diagnostics -or $NativeUI) {
        foreach ($Dependency in @('SDL3','PSX_LIBWEBP','PSX_ZLIB','PSX_LIBCHDR')) {
            $DepName = $Dependency.ToLower() + '-src'
            $DepSource = Join-Path $ProjectRoot "build-runtime/_deps/$DepName"
            if (Test-Path -LiteralPath $DepSource) { $RuntimeArgs += "-DFETCHCONTENT_SOURCE_DIR_${Dependency}=$DepSource" }
        }
    }
    Invoke-Checked 'cmake' $RuntimeArgs
    Invoke-Checked 'cmake' @('--build',$RuntimeBuildDir,'--target','psx-runtime','--parallel','2')
    Invoke-Checked $Python @('tools/stage_overlay_toolchain.py','--runtime-dir',$RuntimeBuildDir)
} finally {
    $env:TEMP = $OldTemp
    $env:TMP = $OldTmp
    $env:PSX_STATIC_NO_ISOLATED = $OldIsolated
    Pop-Location
}

[CmdletBinding()]
param([switch]$Headless, [int]$DebugPort = 4370, [switch]$Diagnostics,
      [switch]$NativeUI)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RuntimeBuildDir = if ($NativeUI) { 'build-native-ui' } elseif ($Diagnostics) { 'build-diagnostics' } else { 'build-runtime' }
$Exe = Join-Path $ProjectRoot "$RuntimeBuildDir/VibRibbon_Recompiled.exe"
if (!(Test-Path -LiteralPath $Exe)) { throw 'Build the runtime first: ./scripts/build.ps1' }
$OldDebug = $env:PSX_DEBUG_SERVER
$env:PSX_DEBUG_SERVER = '1'
Push-Location $ProjectRoot
try {
    $ConfigPath = if (Test-Path -LiteralPath (Join-Path $ProjectRoot 'game.local.toml')) { 'game.local.toml' } else { 'game.toml' }
    $RunArgs = @('--game', (Join-Path $ProjectRoot $ConfigPath), '--debug-port', "$DebugPort")
    if (!$NativeUI -or $Headless) { $RunArgs += '--no-launcher' }
    if ($Headless) { $RunArgs += '--headless' }
    & $Exe @RunArgs
    if ($LASTEXITCODE -ne 0) { throw "Runtime exited with code $LASTEXITCODE" }
} finally {
    $env:PSX_DEBUG_SERVER = $OldDebug
    Pop-Location
}

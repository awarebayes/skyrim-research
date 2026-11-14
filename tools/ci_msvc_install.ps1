# Official installers only. No compiler packages, objects or diagnostics are cached/uploaded.
param([ValidateSet('v141', 'vs2017')][string]$Source = 'v141')
$ErrorActionPreference = 'Stop'
$timer = [Diagnostics.Stopwatch]::StartNew()
$installerRoot = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer'
if ($Source -eq 'v141') {
    $installPath = & (Join-Path $installerRoot 'vswhere.exe') -latest -products * -version '[17.0,18.0)' -property installationPath
    if (-not $installPath) { throw 'VS2022 instance not found' }
    $installer = Join-Path $installerRoot 'setup.exe'
    $arguments = @('modify', '--installPath', "`"$installPath`"", '--quiet', '--norestart',
        '--add', 'Microsoft.VisualStudio.Component.VC.v141.x86.x64',
        '--add', 'Microsoft.VisualStudio.Component.Windows10SDK.19041')
} else {
    $installPath = Join-Path $env:RUNNER_TEMP 'vs2017'
    $installer = Join-Path $env:RUNNER_TEMP 'vs_buildtools.exe'
    Invoke-WebRequest 'https://aka.ms/vs/15/release/vs_buildtools.exe' -OutFile $installer
    $signature = Get-AuthenticodeSignature $installer
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation') {
        throw 'Build Tools bootstrapper does not have a valid Microsoft signature'
    }
    # Use the project's existing fixed official catalog; never silently substitute a new pin.
    $pins = python -c "import sys; sys.path.insert(0, 'tools/verifier'); import recipe_pins, json; from pathlib import Path; print(json.dumps(recipe_pins.read_pins(Path.cwd())))" | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0) { throw 'Cannot read pinned installer catalog' }
    $catalog = Join-Path $env:RUNNER_TEMP 'VisualStudio.vsman'
    Invoke-WebRequest $pins.VSMAN_URL -OutFile $catalog
    if ((Get-FileHash $catalog -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pins.VSMAN_SHA256) {
        throw 'Official catalog hash differs from recipe pin'
    }
    $arguments = @('--installPath', "`"$installPath`"", '--quiet', '--wait', '--norestart',
        '--installCatalogUri', "`"$catalog`"", '--add', 'Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
        '--add', 'Microsoft.VisualStudio.Component.Windows10SDK.19041')
}
$process = Start-Process -FilePath $installer -ArgumentList $arguments -Wait -PassThru
if ($process.ExitCode -notin @(0, 3010)) { throw "Official installer exited $($process.ExitCode)" }
$bins = @(Get-ChildItem (Join-Path $installPath 'VC\Tools\MSVC\14.16.*\bin\Hostx64\x64\cl.exe'))
if ($bins.Count -ne 1) { throw "Expected one 14.16 x64 compiler, found $($bins.Count)" }
$seconds = [Math]::Round($timer.Elapsed.TotalSeconds, 2)
"bin=$($bins[0].DirectoryName)" >> $env:GITHUB_OUTPUT
"install_seconds=$seconds" >> $env:GITHUB_OUTPUT
Write-Output "Official $Source install: $seconds seconds; installer exit $($process.ExitCode); cache disabled"
"Official $Source install without cache: $seconds seconds. With cache: not measured (disabled)." >> $env:GITHUB_STEP_SUMMARY

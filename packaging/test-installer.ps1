$ErrorActionPreference = 'Stop'

$setup = Join-Path $PSScriptRoot '..\dist\PDF-Watermark-Setup.exe'
$programs = [Environment]::GetFolderPath('Programs')
$installDir = Join-Path $env:LOCALAPPDATA 'Programs\FZ-Labz\PDF Watermark'
$exe = Join-Path $installDir 'PDF Watermark.exe'
$shortcut = Join-Path $programs 'FZ-Labz\PDF Watermark.lnk'
$uninstallKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{C7937D91-C29F-4BD3-B1AB-F225A4F51DEB}_is1'
$portable = Join-Path $env:LOCALAPPDATA 'Programs\PDF Watermark\PDF-Watermark-Windows.exe'
$portableShortcut = Join-Path $programs 'PDF Watermark.lnk'
$settings = Join-Path $env:APPDATA 'PDF Watermark\settings.json'
$output = Join-Path $installDir 'user-export.pdf'
$silent = '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART'

foreach ($path in @($exe, $shortcut, $uninstallKey, $portable, $portableShortcut, $settings, $output)) {
    if (Test-Path -LiteralPath $path) { throw "Smoke test requires a fresh Windows runner: $path" }
}

# Use fixtures to detect any installer changes to pre-existing user files.
foreach ($path in @($exe, $portable, $portableShortcut, $settings, $output)) {
    [IO.Directory]::CreateDirectory((Split-Path -Parent $path)) | Out-Null
    Set-Content -LiteralPath $path -Value 'existing user file'
}

$blocked = Start-Process -FilePath $setup -ArgumentList $silent -Wait -PassThru
if ($blocked.ExitCode -ne 7 -or (Test-Path -LiteralPath $uninstallKey) -or
    (Get-Content -LiteralPath $exe) -ne 'existing user file') {
    throw 'Setup should stop before overwriting an unmanaged executable.'
}
Remove-Item -LiteralPath $exe

# Installing twice checks that the collision guard permits a managed upgrade.
foreach ($install in 1..2) {
    $process = Start-Process -FilePath $setup -ArgumentList $silent -Wait -PassThru
    if ($process.ExitCode -ne 0) { throw "Setup run $install exited with code $($process.ExitCode)." }
}

$entry = Get-ItemProperty -LiteralPath $uninstallKey
if ($entry.DisplayName -ne 'PDF Watermark' -or $entry.Publisher -ne 'FZ-Labz') {
    throw 'The per-user uninstall entry should display PDF Watermark published by FZ-Labz.'
}
$version = (Get-Content -LiteralPath (Join-Path $PSScriptRoot '..\VERSION') -Raw).Trim()
if ($entry.DisplayVersion -ne $version) { throw 'The uninstall entry should display the release version.' }
$target = (New-Object -ComObject WScript.Shell).CreateShortcut($shortcut).TargetPath
if ($target -ne $exe -or !(Test-Path -LiteralPath $exe -PathType Leaf)) {
    throw 'The Start menu shortcut should point to the installed application.'
}

$uninstaller = $entry.UninstallString.Trim('"')
if (!(Test-Path -LiteralPath $uninstaller -PathType Leaf)) { throw 'The uninstall entry should point to a real uninstaller.' }
$process = Start-Process -FilePath $uninstaller -ArgumentList $silent -Wait -PassThru
if ($process.ExitCode -ne 0) { throw "Uninstaller exited with code $($process.ExitCode)." }

foreach ($path in @($exe, $shortcut, $uninstallKey, $uninstaller)) {
    if (Test-Path -LiteralPath $path) { throw "Uninstall left behind $path." }
}
foreach ($path in @($portable, $portableShortcut, $settings, $output)) {
    if ((Get-Content -LiteralPath $path) -ne 'existing user file') { throw "Uninstall changed $path." }
}

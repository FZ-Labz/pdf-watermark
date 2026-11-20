#define AppName "PDF Watermark"
#define AppExe "PDF Watermark.exe"

[Setup]
AppId={{C7937D91-C29F-4BD3-B1AB-F225A4F51DEB}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=FZ-Labz
AppPublisherURL=https://github.com/FZ-Labz/pdf-watermark
AppSupportURL=https://github.com/FZ-Labz/pdf-watermark/issues
AppUpdatesURL=https://github.com/FZ-Labz/pdf-watermark/releases
DefaultDirName={localappdata}\Programs\FZ-Labz\{#AppName}
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
MinVersion=10.0
ArchitecturesAllowed=x64compatible
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExe}
SetupIconFile=icon.ico
OutputDir=..\dist
OutputBaseFilename=PDF-Watermark-Setup

[Files]
Source: "..\dist\{#AppExe}"; DestDir: "{app}"

[Icons]
Name: "{userprograms}\FZ-Labz\{#AppName}"; Filename: "{app}\{#AppExe}"

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  InstallDir: String;
begin
  InstallDir := ExpandConstant('{app}');
  Result := '';
  if CompareText(InstallDir, ExpandConstant('{localappdata}\Programs\FZ-Labz\{#AppName}')) <> 0 then
    Result := 'Use the default installation folder for PDF Watermark.'
  else if (CompareText(GetPreviousData('InstallDir', ''), InstallDir) <> 0) and
    (FileExists(InstallDir + '\{#AppExe}') or
      FileExists(ExpandConstant('{userprograms}\FZ-Labz\{#AppName}.lnk'))) then
    Result := 'Setup found an existing executable or shortcut it does not manage. Move it before installing PDF Watermark.';
end;

procedure RegisterPreviousData(PreviousDataKey: Integer);
begin
  SetPreviousData(PreviousDataKey, 'InstallDir', ExpandConstant('{app}'));
end;

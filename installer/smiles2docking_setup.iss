#ifndef AppVersion
  #error AppVersion must be passed from the project __version__ with /DAppVersion=x.y.z
#endif

#define AppName "SMILES2DOCKING"
#define AppExeName "smiles2docking.exe"

[Setup]
AppId={{9F6C1B97-6E92-4D9E-9D97-0CE1D36D85F4}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=[AUTHOR PLACEHOLDER]
AppPublisherURL=https://github.com/[REPO PLACEHOLDER]/smiles2docking
AppSupportURL=https://github.com/[REPO PLACEHOLDER]/smiles2docking
AppUpdatesURL=https://github.com/[REPO PLACEHOLDER]/smiles2docking
DefaultDirName={autopf}\SMILES2DOCKING
DefaultGroupName=SMILES2DOCKING
OutputDir=output
OutputBaseFilename=SMILES2DOCKING_Setup_v{#AppVersion}_win64
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0
PrivilegesRequired=lowest
LicenseFile=..\LICENSE
SetupIconFile=..\assets\caffeine_icon.ico
UninstallDisplayName=SMILES2DOCKING
UninstallDisplayIcon={app}\{#AppExeName}
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "..\dist\smiles2docking\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SMILES2DOCKING"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\SMILES2DOCKING"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,SMILES2DOCKING}"; Flags: nowait postinstall skipifsilent

[Code]
var
  MopacNoticePage: TOutputMsgWizardPage;

procedure InitializeWizard;
begin
  MopacNoticePage := CreateOutputMsgPage(
    wpLicense,
    'Bundled third-party software',
    'MOPAC 23.2.4 is bundled with SMILES2DOCKING.',
    'This installer includes MOPAC 23.2.4 in the application folder. MOPAC is licensed under the Apache License 2.0.' + #13#10 + #13#10 +
    'MOPAC license URL:' + #13#10 +
    'https://github.com/openmopac/mopac/blob/main/LICENSE' + #13#10 + #13#10 +
    'No separate MOPAC installer is run, no system PATH changes are made, and installation does not require internet access.'
  );
end;

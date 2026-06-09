#ifndef AppVersion
  #error AppVersion must be passed from the project __version__ with /DAppVersion=x.y.z
#endif

#define AppName "SMILES2DOCKING"
#define AppExeName "SMILES2DockingDesktop.exe"

[Setup]
AppId={{9F6C1B97-6E92-4D9E-9D97-0CE1D36D85F4}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Adriano Marques Goncalves; Daniel Grajales Ruiz; Nailton Monteiro do Nascimento Júnior
AppPublisherURL=https://github.com/amgoncalvesusp/Smiles2Docking
AppSupportURL=https://github.com/amgoncalvesusp/Smiles2Docking/issues
AppUpdatesURL=https://github.com/amgoncalvesusp/Smiles2Docking/releases
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
Source: "..\dist\SMILES2DockingDesktop\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
Type: filesandordirs; Name: "{app}\*"

[Icons]
Name: "{group}\SMILES2DOCKING"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\SMILES2DOCKING"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,SMILES2DOCKING}"; Flags: nowait postinstall skipifsilent

[Code]
var
  AuthorsNoticePage: TOutputMsgWizardPage;
  MopacNoticePage: TOutputMsgWizardPage;

procedure InitializeWizard;
begin
  AuthorsNoticePage := CreateOutputMsgPage(
    wpWelcome,
    'Authors',
    'SMILES2DOCKING was created by Adriano Marques Goncalves, Daniel Grajales Ruiz, and Nailton Monteiro do Nascimento Júnior.',
    'Authors:' + #13#10 +
    'Adriano Marques Goncalves - Universidade de Araraquara - UNIARA' + #13#10 +
    'Daniel Grajales Ruiz - IQ/UNESP' + #13#10 +
    'Nailton Monteiro do Nascimento Júnior - IQ/UNESP' + #13#10 + #13#10 +
    'Contact:' + #13#10 +
    'amgoncalves@uniara.edu.br'
  );

  MopacNoticePage := CreateOutputMsgPage(
    AuthorsNoticePage.ID,
    'Bundled third-party software',
    'MOPAC 23.2.4 is bundled with SMILES2DOCKING.',
    'This installer includes MOPAC 23.2.4 in the application folder. MOPAC is licensed under the Apache License 2.0.' + #13#10 + #13#10 +
    'MOPAC license URL:' + #13#10 +
    'https://github.com/openmopac/mopac/blob/main/LICENSE' + #13#10 + #13#10 +
    'No separate MOPAC installer is run, no system PATH changes are made, and installation does not require internet access.'
  );
end;

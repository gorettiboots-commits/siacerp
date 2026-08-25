; ============================================================
; SIAC ERP — Inno Setup Script
; Genera el instalador (.exe) con configuración de empresa
; ============================================================

#define MyAppName "SIAC ERP"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "Mario Felipe Luevano"
#define MyAppExeName "SIAC_ERP.exe"
#define MySourceDir "dist\SIAC_ERP"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=SIAC_ERP_Instalador_{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=src\views\assets\siac_icono.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "{#MySourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Pre-configuración se ejecuta en CurStepChanged

[Code]
var
  EditNombreEmpresa: TNewEdit;
  EditRazonSocial: TNewEdit;
  EditRFC: TNewEdit;
  EditDomicilio: TNewMemo;
  EditTelefono: TNewEdit;
  EditEmail: TNewEdit;
  PaginaEmpresaID: Integer;

procedure CrearPaginaEmpresa;
var
  Pagina: TWizardPage;
  L1, L2, L3: TLabel;
begin
  Pagina := CreateCustomPage(wpSelectDir, 'Configuración de la Empresa',
    'Ingrese los datos de la empresa que utilizará el sistema.');
  PaginaEmpresaID := Pagina.ID;

  L1 := TLabel.Create(Pagina);
  L1.Parent := Pagina.Surface;
  L1.Caption := 'Nombre de empresa:';
  L1.Left := ScaleX(16);
  L1.Top := ScaleY(16);

  EditNombreEmpresa := TNewEdit.Create(Pagina);
  EditNombreEmpresa.Parent := Pagina.Surface;
  EditNombreEmpresa.Left := ScaleX(16);
  EditNombreEmpresa.Top := ScaleY(36);
  EditNombreEmpresa.Width := ScaleX(360);

  L2 := TLabel.Create(Pagina);
  L2.Parent := Pagina.Surface;
  L2.Caption := 'Razón social (opcional):';
  L2.Left := ScaleX(16);
  L2.Top := ScaleY(76);

  EditRazonSocial := TNewEdit.Create(Pagina);
  EditRazonSocial.Parent := Pagina.Surface;
  EditRazonSocial.Left := ScaleX(16);
  EditRazonSocial.Top := ScaleY(96);
  EditRazonSocial.Width := ScaleX(360);

  L3 := TLabel.Create(Pagina);
  L3.Parent := Pagina.Surface;
  L3.Caption := 'RFC (opcional):';
  L3.Left := ScaleX(16);
  L3.Top := ScaleY(136);

  EditRFC := TNewEdit.Create(Pagina);
  EditRFC.Parent := Pagina.Surface;
  EditRFC.Left := ScaleX(16);
  EditRFC.Top := ScaleY(156);
  EditRFC.Width := ScaleX(360);
end;

procedure CrearPaginaContacto;
var
  Pagina: TWizardPage;
  L1, L2, L3: TLabel;
begin
  Pagina := CreateCustomPage(wpSelectDir, 'Datos de Contacto',
    'Información de contacto y domicilio de la empresa.');

  L1 := TLabel.Create(Pagina);
  L1.Parent := Pagina.Surface;
  L1.Caption := 'Domicilio:';
  L1.Left := ScaleX(16);
  L1.Top := ScaleY(16);

  EditDomicilio := TNewMemo.Create(Pagina);
  EditDomicilio.Parent := Pagina.Surface;
  EditDomicilio.Left := ScaleX(16);
  EditDomicilio.Top := ScaleY(36);
  EditDomicilio.Width := ScaleX(360);
  EditDomicilio.Height := ScaleY(60);

  L2 := TLabel.Create(Pagina);
  L2.Parent := Pagina.Surface;
  L2.Caption := 'Teléfono:';
  L2.Left := ScaleX(16);
  L2.Top := ScaleY(110);

  EditTelefono := TNewEdit.Create(Pagina);
  EditTelefono.Parent := Pagina.Surface;
  EditTelefono.Left := ScaleX(16);
  EditTelefono.Top := ScaleY(130);
  EditTelefono.Width := ScaleX(360);

  L3 := TLabel.Create(Pagina);
  L3.Parent := Pagina.Surface;
  L3.Caption := 'Email:';
  L3.Left := ScaleX(16);
  L3.Top := ScaleY(170);

  EditEmail := TNewEdit.Create(Pagina);
  EditEmail.Parent := Pagina.Surface;
  EditEmail.Left := ScaleX(16);
  EditEmail.Top := ScaleY(190);
  EditEmail.Width := ScaleX(360);
end;

procedure InitializeWizard;
begin
  CrearPaginaEmpresa;
  CrearPaginaContacto;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = PaginaEmpresaID then
  begin
    if Trim(EditNombreEmpresa.Text) = '' then
    begin
      MsgBox('Debe ingresar el nombre de la empresa.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  ExePath: String;
  Params: String;
begin
  if CurStep = ssPostInstall then
  begin
    ExePath := ExpandConstant('{app}\{#MyAppExeName}');
    Params := '--pre-configurar --nombre "' + EditNombreEmpresa.Text + '" ';
    if Trim(EditRazonSocial.Text) <> '' then
      Params := Params + '--razon "' + EditRazonSocial.Text + '" ';
    if Trim(EditRFC.Text) <> '' then
      Params := Params + '--rfc "' + EditRFC.Text + '" ';
    if Trim(EditDomicilio.Text) <> '' then
      Params := Params + '--domicilio "' + EditDomicilio.Text + '" ';
    if Trim(EditTelefono.Text) <> '' then
      Params := Params + '--telefono "' + EditTelefono.Text + '" ';
    if Trim(EditEmail.Text) <> '' then
      Params := Params + '--email "' + EditEmail.Text + '" ';
    Exec(ExePath, Params, '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;

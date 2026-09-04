; ============================================================
; SIAC ERP — Inno Setup Script
; Genera el instalador (.exe) con configuración de empresa
; NO ejecuta SIAC_ERP.exe durante la instalación (evita AV)
; Guarda datos en onboarding.json para que la app lea al abrir
; ============================================================

#define MyAppName "SIAC ERP"
#define MyAppVersion "1.2.1"
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
Compression=lzma2
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
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
var
  EditNombreEmpresa: TNewEdit;
  EditRazonSocial: TNewEdit;
  EditRFC: TNewEdit;
  EditDomicilio: TNewMemo;
  EditTelefono: TNewEdit;
  EditEmail: TNewEdit;
  EditAdminUser: TNewEdit;
  EditAdminPassword: TNewEdit;
  EditAdminPassword2: TNewEdit;
  EditAdminNombre: TNewEdit;
  PaginaEmpresaID: Integer;
  PaginaAdminID: Integer;

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

procedure CrearPaginaAdmin;
var
  Pagina: TWizardPage;
  L1, L2, L3, L4: TLabel;
begin
  Pagina := CreateCustomPage(wpSelectDir, 'Usuario Administrador',
    'Configure las credenciales del usuario administrador del sistema.');
  PaginaAdminID := Pagina.ID;

  L1 := TLabel.Create(Pagina);
  L1.Parent := Pagina.Surface;
  L1.Caption := 'Nombre de usuario:';
  L1.Left := ScaleX(16);
  L1.Top := ScaleY(16);

  EditAdminUser := TNewEdit.Create(Pagina);
  EditAdminUser.Parent := Pagina.Surface;
  EditAdminUser.Left := ScaleX(16);
  EditAdminUser.Top := ScaleY(36);
  EditAdminUser.Width := ScaleX(360);
  EditAdminUser.Text := 'admin';

  L2 := TLabel.Create(Pagina);
  L2.Parent := Pagina.Surface;
  L2.Caption := 'Contrasena:';
  L2.Left := ScaleX(16);
  L2.Top := ScaleY(76);

  EditAdminPassword := TNewEdit.Create(Pagina);
  EditAdminPassword.Parent := Pagina.Surface;
  EditAdminPassword.Left := ScaleX(16);
  EditAdminPassword.Top := ScaleY(96);
  EditAdminPassword.Width := ScaleX(360);
  EditAdminPassword.PasswordChar := '*';

  L3 := TLabel.Create(Pagina);
  L3.Parent := Pagina.Surface;
  L3.Caption := 'Confirmar contrasena:';
  L3.Left := ScaleX(16);
  L3.Top := ScaleY(136);

  EditAdminPassword2 := TNewEdit.Create(Pagina);
  EditAdminPassword2.Parent := Pagina.Surface;
  EditAdminPassword2.Left := ScaleX(16);
  EditAdminPassword2.Top := ScaleY(156);
  EditAdminPassword2.Width := ScaleX(360);
  EditAdminPassword2.PasswordChar := '*';

  L4 := TLabel.Create(Pagina);
  L4.Parent := Pagina.Surface;
  L4.Caption := 'Nombre completo (opcional):';
  L4.Left := ScaleX(16);
  L4.Top := ScaleY(196);

  EditAdminNombre := TNewEdit.Create(Pagina);
  EditAdminNombre.Parent := Pagina.Surface;
  EditAdminNombre.Left := ScaleX(16);
  EditAdminNombre.Top := ScaleY(216);
  EditAdminNombre.Width := ScaleX(360);
  EditAdminNombre.Text := 'Administrador del Sistema';
end;

procedure InitializeWizard;
begin
  CrearPaginaEmpresa;
  CrearPaginaContacto;
  CrearPaginaAdmin;
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
  if CurPageID = PaginaAdminID then
  begin
    if Trim(EditAdminUser.Text) = '' then
    begin
      MsgBox('Debe ingresar un nombre de usuario.', mbError, MB_OK);
      Result := False;
    end
    else if Trim(EditAdminPassword.Text) = '' then
    begin
      MsgBox('Debe ingresar una contrasena.', mbError, MB_OK);
      Result := False;
    end
    else if EditAdminPassword.Text <> EditAdminPassword2.Text then
    begin
      MsgBox('Las contrasenas no coinciden.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

function EscapeJsonString(const S: String): String;
var
  I: Integer;
  C: Char;
  Tmp: String;
begin
  Tmp := '';
  for I := 1 to Length(S) do
  begin
    C := S[I];
    case C of
      '\': Tmp := Tmp + '\\';
      '"': Tmp := Tmp + '\"';
      Chr(13): Tmp := Tmp + '\r';
      Chr(10): Tmp := Tmp + '\n';
      Chr(9): Tmp := Tmp + '\t';
    else
      Tmp := Tmp + C;
    end;
  end;
  Result := Tmp;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  JsonContent: String;
  JsonFile: String;
  SL: TStringList;
begin
  if CurStep = ssPostInstall then
  begin
    JsonFile := ExpandConstant('{app}\onboarding.json');

    JsonContent := '{' + Chr(13) + Chr(10);
    JsonContent := JsonContent + '  "nombre_empresa": "' + EscapeJsonString(EditNombreEmpresa.Text) + '",' + Chr(13) + Chr(10);
    JsonContent := JsonContent + '  "razon_social": "' + EscapeJsonString(EditRazonSocial.Text) + '",' + Chr(13) + Chr(10);
    JsonContent := JsonContent + '  "rfc": "' + EscapeJsonString(EditRFC.Text) + '",' + Chr(13) + Chr(10);
    JsonContent := JsonContent + '  "domicilio": "' + EscapeJsonString(EditDomicilio.Text) + '",' + Chr(13) + Chr(10);
    JsonContent := JsonContent + '  "telefono": "' + EscapeJsonString(EditTelefono.Text) + '",' + Chr(13) + Chr(10);
    JsonContent := JsonContent + '  "email": "' + EscapeJsonString(EditEmail.Text) + '",' + Chr(13) + Chr(10);
    JsonContent := JsonContent + '  "admin_user": "' + EscapeJsonString(EditAdminUser.Text) + '",' + Chr(13) + Chr(10);
    JsonContent := JsonContent + '  "admin_password": "' + EscapeJsonString(EditAdminPassword.Text) + '",' + Chr(13) + Chr(10);
    JsonContent := JsonContent + '  "admin_nombre": "' + EscapeJsonString(EditAdminNombre.Text) + '"' + Chr(13) + Chr(10);
    JsonContent := JsonContent + '}';

    SL := TStringList.Create;
    try
      SL.Text := JsonContent;
      SL.SaveToFile(JsonFile);
    finally
      SL.Free;
    end;
  end;
end;

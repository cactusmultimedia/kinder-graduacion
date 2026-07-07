# Windows 10 Troubleshooting

## Códigos de Error Comunes

### 0x80070002 — Archivo no encontrado
**Causa:** Windows Update o instalación no encuentra archivos
**Soluciones:**
1. `sfc /scannow` — verifica integridad de sistema
2. `DISM /Online /Cleanup-Image /RestoreHealth` — repara imagen del sistema
3. Detener servicio Update: `net stop wuauserv`, renombrar `C:\Windows\SoftwareDistribution` a `SoftwareDistribution.old`, reiniciar servicio
4. `chkdsk C: /f` — revisar disco

### 0x80004005 — Error no especificado
**Causa:** Permisos, archivos corruptos o drivers
**Soluciones:**
1. Ejecutar como Administrador
2. `sfc /scannow` + `DISM /RestoreHealth`
3. Revisar permisos de carpeta
4. `chkdsk C: /f /r`
5. Desinstalar actualización reciente

### 0x80070005 — Acceso denegado
**Causa:** Permisos insuficientes
**Soluciones:**
1. Ejecutar como Administrador
2. `takeown /f C:\ruta /r /d y` + `icacls C:\ruta /grant Administradores:F /t`
3. Desactivar antivirus temporalmente

### 0x800F081F — CBS no puede encontrar archivos
**Causa:** Component Store corrupto
**Soluciones:**
1. `DISM /Online /Cleanup-Image /RestoreHealth /Source:C:\RepairSource\Windows /LimitAccess`
2. Usar ISO de Windows como fuente: montar ISO y apuntar DISM a `X:\sources\install.wim`
3. Windows Update Troubleshooter

### 0x80300024 — Error de instalación en disco
**Causa:** Problemas con partición o BIOS
**Soluciones:**
1. Convertir de MBR a GPT: `mbr2gpt.exe /convert /allowFullOS`
2. En BIOS: cambiar SATA de RAID a AHCI
3. Desconectar discos extras durante instalación

### 0xC000021A — Blue Screen, winlogon.exe falló
**Causa:** Sistema corrupto, driver o antivirus
**Soluciones:**
1. Arrancar en modo seguro
2. `sfc /scannow` desde recovery
3. Última configuración válida
4. Restaurar sistema

### 0xC000000F — Boot selection failed
**Causa:** BCD corrupto
**Soluciones:**
1. `bootrec /fixmbr`
2. `bootrec /fixboot`
3. `bootrec /rebuildbcd`
4. `bcdedit /export C:\bcdbackup` luego `attrib -s -h -r C:\boot\bcd` y renombrar

### 0x8007007E — Módulo no encontrado
**Causa:** DLL faltante o registro corrupto
**Soluciones:**
1. `regsvr32 [dllname]`
2. `sfc /scannow`
3. Reinstalar el programa
4. System Restore

### 0x8024401C — WSUS no responde
**Causa:** Proxy o firewall bloquea Windows Update
**Soluciones:**
1. `netsh winhttp reset proxy`
2. Revisar fecha/hora del sistema
3. `net stop wuauserv` + renombrar `SoftwareDistribution` + `net start wuauserv`

### 0x80070643 — Error de instalación .NET
**Causa:** Instalación corrupta de .NET
**Soluciones:**
1. Windows Update Troubleshooter
2. `dism /online /enable-feature /featurename:NetFx3 /all`
3. Microsoft .NET Framework Repair Tool
4. Revisar `C:\Windows\logs\cbs\cbs.log`

---

## Comandos Esenciales de Reparación

### SFC (System File Checker)
```cmd
sfc /scannow              # escanea y repara archivos
sfc /verifyonly           # solo verifica, no repara
```

### DISM (Deployment Imaging)
```cmd
DISM /Online /Cleanup-Image /CheckHealth
DISM /Online /Cleanup-Image /ScanHealth
DISM /Online /Cleanup-Image /RestoreHealth
DISM /Online /Cleanup-Image /RestoreHealth /Source:C:\RepairSource\Windows /LimitAccess
```

### CHKDSK
```cmd
chkdsk C: /f              # repara errores
chkdsk C: /f /r           # repara + recupera sectores
chkdsk C: /f /r /x        # fuerza desmontar primero
```

### Bootrec (Recovery)
```cmd
bootrec /fixmbr
bootrec /fixboot
bootrec /rebuildbcd
bootrec /scanos
```

### BCDEdit
```cmd
bcdedit /enum              # ver config
bcdedit /export C:\backup  # backup
bcdedit /set {default} safeboot minimal     # modo seguro
bcdedit /deletevalue {default} safeboot     # quitar modo seguro
```

### Network
```cmd
ipconfig /all              # ver config red
ipconfig /flushdns         # limpiar DNS
ipconfig /release && ipconfig /renew   # renovar IP
netsh int ip reset         # resetear TCP/IP
netsh winsock reset        # resetear Winsock
netsh advfirewall reset    # resetear firewall
nslookup google.com        # probar DNS
tracert 8.8.8.8            # ruta a destino
pathping 8.8.8.8           # diagnostico avanzado
```

---

## Modo Seguro y Recovery

### Acceder Modo Seguro
1. `msconfig` → Boot → Safe Boot → Mínimo
2. Shift + Reiniciar → Solucionar problemas → Opciones avanzadas → Configuración de inicio
3. Recovery: `bcdedit /set {default} safeboot minimal`

### Opciones de Recovery
- Restaurar sistema desde punto anterior
- Restablecer este PC (conservar o quitar archivos)
- Símbolo del sistema (Cmd desde recovery)
- Desinstalar actualizaciones
- Reparación de inicio

---

## Problemas de Red

### Sin conexión a internet
1. `ipconfig /all` — ver si tiene IP válida (169.254.x.x = sin DHCP)
2. `ipconfig /release && ipconfig /renew`
3. `netsh int ip reset`
4. `netsh winsock reset`
5. Apagar firewall: `netsh advfirewall set allprofiles state off`
6. `ipconfig /flushdns && netsh int ip reset`
7. Des/reinstalar driver de red en Administrador de Dispositivos
8. `netcfg -d` — resetear todas las configuraciones de red (requiere reboot)

### DNS no resuelve
1. `ipconfig /flushdns`
2. `nslookup google.com 8.8.8.8` — probar con DNS externo
3. Cambiar DNS manual: netsh interface ip set dns "Ethernet" static 8.8.8.8
4. `ipconfig /registerdns`

### DHCP no asigna IP
1. Verificar servicio: `net start dhcp`
2. `ipconfig /release && ipconfig /renew`
3. `netsh interface ip set address "Ethernet" dhcp`
4. Verificar que el cable/conexión WiFi esté activa

### WiFi no conecta
1. `netsh wlan show profiles` — ver perfiles
2. `netsh wlan delete profile name="nombre"`
3. Olvidar red y reconectar
4. `netsh wlan show drivers` — ver si driver está bien
5. Desactivar/activar adaptador WiFi
6. `netsh wlan set hostednetwork mode=allow`

### Ping: "General Failure"
1. `netsh int ip reset`
2. `netsh winsock reset`
3. Reiniciar

---

## Rendimiento

### PC lenta
1. `temp` + `%temp%` + `prefetch` — limpiar temporales
2. `cleanmgr` — liberar espacio
3. `msconfig` — deshabilitar inicio automático de programas
4. `powercfg -h off` — deshabilitar hibernación (libera GBs)
5. `wmic` → `diskdrive get status` — ver estado disco
6. Desfragmentar: `defrag C: /O`
7. `DISM /Online /Cleanup-Image /StartComponentCleanup /ResetBase` — reducir tamaño WinSxS

### Disco al 100%
1. Deshabilitar Superfetch/SysMain: `sc config SysMain start=disabled`
2. Deshabilitar Windows Search: `sc config WSearch start=disabled`
3. Revisar `resmon` → Disk → qué proceso escribe
4. Deshabilitar antivirus temporalmente

### Pantalla azul (BSOD)
1. Anotar código: revisar `C:\Windows\Minidump` con BlueScreenView
2. `sfc /scannow`
3. `DISM /RestoreHealth`
4. Revisar drivers recién instalados
5. Memtest86+ para probar RAM
6. `chkdsk C: /f /r` para disco

---

## Active Directory y Dominio (si aplica)

### No puede unirse a dominio
1. `ping [nombre_dominio]` — probar conectividad
2. `nslookup [nombre_dominio]` — resuelve?
3. Fecha/hora sincronizada con el DC
4. Firewall: puertos 389 (LDAP), 445 (SMB), 88 (Kerberos) abiertos
5. `netdom join %computername% /domain:[dominio] /userd:[usuario] /passwordd:[*]`
6. DNS apuntando al DC: `ipconfig /all` → revisar

### Credenciales expiradas
1. `net user [usuario] * /domain` — cambiar password
2. `klist purge` — limpiar tickets Kerberos
3. Reiniciar sesión

---

## Utilities Útiles

| Herramienta | Comando | Para qué |
|------------|---------|----------|
| Información sistema | `msinfo32` | Hardware, software, recursos |
| Monitor de recursos | `resmon` | CPU, RAM, disco, red |
| Visor de eventos | `eventvwr.msc` | Logs de errores |
| Administrador discos | `diskmgmt.msc` | Particiones, formatos |
| Editor registro | `regedit` | Registro de Windows |
| DirectX | `dxdiag` | Diagnóstico gráficos |
| Firewall | `wf.msc` | Reglas avanzadas firewall |
| Servicios | `services.msc` | Iniciar/detener servicios |
| Rendimiento | `perfmon.msc` | Monitoreo detallado |
| Administrador dispositivos | `devmgmt.msc` | Drivers, hardware |
| Editor GPO | `gpedit.msc` | Políticas de grupo (Pro) |
| Información red | `ncpa.cpl` | Conexiones de red |
| Solucionador problemas | `msdt` | Troubleshooters integrados |

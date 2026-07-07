from __future__ import annotations
import subprocess
import os
import json
import urllib.request
import urllib.parse
import re
import platform
from html.parser import HTMLParser
from pathlib import Path

MAX_OUTPUT = 10000
MAX_FETCH_SIZE = 500000
IS_WINDOWS = platform.system() == "Windows"

async def execute_tool(name: str, arguments: dict) -> str:
    try:
        if name == "read_file":
            return _read_file(arguments.get("path", ""))
        elif name == "write_file":
            return _write_file(arguments.get("path", ""), arguments.get("content", ""))
        elif name == "bash":
            return _bash(arguments.get("command", ""))
        elif name == "list_dir":
            return _list_dir(arguments.get("path", "."))
        elif name == "web_fetch":
            return _web_fetch(arguments.get("url", ""))
        elif name == "web_search":
            return _web_search(arguments.get("query", ""), arguments.get("max_results", 5))
        elif name == "sys_info":
            return _sys_info()
        elif name == "battery_report":
            return _battery_report()
        elif name == "usb_list":
            return _usb_list()
        elif name == "disk_usage":
            return _disk_usage(arguments.get("path", "/"))
        elif name == "ping_test":
            return _ping_test(arguments.get("host", "8.8.8.8"), arguments.get("count", 4))
        elif name == "port_scan":
            return _port_scan(arguments.get("host", "localhost"), arguments.get("ports", "22,80,443,3389,8080"))
        elif name == "wifi_profiles":
            return _wifi_profiles()
        elif name == "pdf_extract":
            return _pdf_extract(arguments.get("path", ""), arguments.get("max_pages", 5))
        elif name == "gen_batch":
            return _gen_batch(arguments.get("path", "script.bat"), arguments.get("commands", "echo Hola"), arguments.get("title", "Script"))
        elif name == "gen_powershell":
            return _gen_powershell(arguments.get("path", "script.ps1"), arguments.get("commands", "Write-Host Hola"), arguments.get("title", "Script"))
        else:
            return f"Unknown tool: {name}"
    except Exception as e:
        return f"Error executing {name}: {e}"

def _read_file(path: str) -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"File not found: {p}"
    if not p.is_file():
        return f"Not a file: {p}"
    content = p.read_text(encoding="utf-8", errors="replace")
    if len(content) > MAX_OUTPUT:
        content = content[:MAX_OUTPUT] + f"\n\n... (truncated, file is {len(content)} chars)"
    return content

def _write_file(path: str, content: str) -> str:
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Written {len(content)} chars to {p}"

def _bash(command: str) -> str:
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = result.stdout + result.stderr
    if len(output) > MAX_OUTPUT:
        output = output[:MAX_OUTPUT] + f"\n\n... (truncated, {len(output)} chars total)"
    if result.returncode != 0:
        output = f"Exit code: {result.returncode}\n{output}"
    return output.strip() or "(no output)"

def _list_dir(path: str) -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"Directory not found: {p}"
    if not p.is_dir():
        return f"Not a directory: {p}"

    entries = []
    for entry in sorted(p.iterdir()):
        suffix = "/" if entry.is_dir() else ""
        size = entry.stat().st_size if entry.is_file() else 0
        if size:
            entries.append(f"  {entry.name}{suffix}  ({_fmt_size(size)})")
        else:
            entries.append(f"  {entry.name}{suffix}")

    return f"Contents of {p}:\n" + "\n".join(entries)

def _fmt_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"

class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "footer", "header"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "footer", "header"):
            self._skip = False
        if tag in ("p", "br", "h1", "h2", "h3", "h4", "li", "div"):
            self.text.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self.text.append(data)

def _extract_text(html: str) -> str:
    stripper = _HTMLStripper()
    try:
        stripper.feed(html)
    except Exception:
        pass
    text = "".join(stripper.text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    lines = [l.strip() for l in text.split("\n")]
    lines = [l for l in lines if len(l) > 30 or (len(l) > 0 and not l.startswith(("http", "@", "//")))]
    return "\n".join(lines[:200])

def _web_fetch(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read(MAX_FETCH_SIZE)
            encoding = resp.headers.get_content_charset() or "utf-8"
            html = raw.decode(encoding, errors="replace")
            text = _extract_text(html)
            if len(raw) >= MAX_FETCH_SIZE:
                text += "\n\n... (truncated)"
            if not text.strip():
                text = html[:2000]
            return text[:MAX_OUTPUT]
    except urllib.error.HTTPError as e:
        if e.code == 403:
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
                    "Accept": "text/html",
                })
                with urllib.request.urlopen(req, timeout=10) as resp:
                    raw = resp.read(MAX_FETCH_SIZE)
                    encoding = resp.headers.get_content_charset() or "utf-8"
                    html = raw.decode(encoding, errors="replace")
                    text = _extract_text(html)
                    return text[:MAX_OUTPUT] or "(blocked by site)"
            except Exception:
                return f"Blocked by {url.split('/')[2]} (403). Try another source."
        return f"HTTP Error {e.code}: {url}"
    except Exception as e:
        return f"Error fetching {url}: {e}"

TRUSTED_NEWS = (
    "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "npr.org",
    "nytimes.com", "wsj.com", "washingtonpost.com", "theguardian.com",
    "economist.com", "bloomberg.com", "ft.com", "cnbc.com",
    "cnn.com", "cnnespanol.cnn.com", "elpais.com", "elmundo.es",
    "abc.es", "elmundo.es", "lanacion.com.ar", "clarin.com",
    "elmexicano.com", "jornada.com.mx", "milenio.com",
    "nature.com", "science.org", "sciencedaily.com",
    "techcrunch.com", "arstechnica.com", "wired.com",
    "github.com", "stackoverflow.com", " wikipedia.org",
)

def _rate_source(url: str) -> str:
    for s in TRUSTED_NEWS:
        if s in url:
            return " ★"
    return ""

def _web_search(query: str, max_results: int = 8) -> str:
    try:
        from ddgs import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                href = r.get("href", "")
                body = r.get("body", "")[:250]
                results.append({
                    "title": r.get("title", ""),
                    "href": href,
                    "body": body,
                    "star": _rate_source(href),
                })
        if not results:
            return "No results found."

        trusted = [r for r in results if r["star"]]
        others = [r for r in results if not r["star"]]
        ordered = trusted + others

        lines = ["Search results:\n"]
        fetch_urls = []
        for r in ordered:
            source = r["href"].split("//")[-1].split("/")[0][:40]
            lines.append(f"{r['star']} {r['title']}")
            lines.append(f"   [{source}] {r['href']}")
            if r["body"]:
                lines.append(f"   {r['body']}")
            lines.append("")
            if r["star"] and len(fetch_urls) < 2:
                fetch_urls.append(r["href"])

        # auto-fetch top trusted source so model gets full content
        if fetch_urls:
            lines.append("\n--- Content from top source ---\n")
            content = _web_fetch(fetch_urls[0])
            domain = fetch_urls[0].split("//")[-1].split("/")[0]
            lines.append(f"[{domain}]\n{content[:2000]}\n")

        return "\n".join(lines)
    except ImportError:
        return "Search unavailable: install ddgs package"
    except Exception as e:
        return f"Search error: {e}"

# === TOOLS DE SISTEMA ===

def _sys_info() -> str:
    try:
        import psutil
        lines = []
        lines.append(f"Sistema: {platform.system()} {platform.release()}")
        lines.append(f"Versión: {platform.version()}")
        lines.append(f"Arquitectura: {platform.machine()}")
        lines.append(f"Procesador: {platform.processor() or platform.machine()}")
        lines.append(f"Hostname: {platform.node()}")
        lines.append(f"CPU: {psutil.cpu_count(logical=True)} núcleos lógicos, {psutil.cpu_count(logical=False)} físicos")
        freq = psutil.cpu_freq()
        if freq:
            lines.append(f"Frecuencia CPU: {freq.current:.0f} MHz")
        mem = psutil.virtual_memory()
        lines.append(f"RAM: {mem.total/1024**3:.1f} GB total, {mem.available/1024**3:.1f} GB libre ({(mem.total-mem.available)/1024**3:.1f} GB usado)")
        disk = psutil.disk_usage('/')
        lines.append(f"Disco '/': {disk.total/1024**3:.1f} GB total, {disk.free/1024**3:.1f} GB libre ({disk.percent}% usado)")
        return "\n".join(l for l in lines if l)
    except ImportError:
        if IS_WINDOWS:
            return _bash("systeminfo | findstr /B /C:\"OS Name\" /C:\"OS Version\" /C:\"System Type\" /C:\"Total Physical Memory\"")
        return _bash("system_profiler SPHardwareDataType 2>/dev/null | head -15")
    except Exception as e:
        return f"sys_info error: {e}"

def _battery_report() -> str:
    try:
        import psutil
        batt = psutil.sensors_battery()
        if not batt:
            return "No battery detected"
        plugged = "Conectado" if batt.power_plugged else "Desconectado"
        pct = batt.percent
        secs = batt.secsleft
        remaining = f"{secs//3600}h {(secs%3600)//60}m" if secs > 0 and secs != -1 else "calculando..."
        return f"Batería: {pct}%\nFuente: {plugged}\nTiempo restante: {remaining}"
    except Exception:
        if IS_WINDOWS:
            return _bash('WMIC PATH Win32_Battery Get EstimatedChargeRemaining,EstimatedRunTime,BatteryStatus 2>nul')
        return _bash("pmset -g batt 2>/dev/null") or "battery_report not available"

def _usb_list() -> str:
    try:
        if IS_WINDOWS:
            return _bash('WMIC logicaldisk where DriveType=2 Get DeviceID,VolumeName,Size,FreeSpace 2>nul')
        out = subprocess.run(
            ["diskutil", "list", "external"],
            capture_output=True, text=True, timeout=10,
        ).stdout
        if not out.strip():
            out = subprocess.run(
                "diskutil list | grep -E 'external|external, physical'",
                shell=True, capture_output=True, text=True, timeout=10,
            ).stdout or "No USB drives detected"
        return out.strip()
    except Exception as e:
        return f"usb_list error: {e}"

def _disk_usage(path: str = "/") -> str:
    try:
        if IS_WINDOWS:
            return _bash(f'WMIC logicaldisk where DeviceID="{path[0].upper()}:" Get DeviceID,Size,FreeSpace 2>nul')
        out = subprocess.run(
            ["du", "-sh", path, "2>/dev/null"],
            capture_output=True, text=True, timeout=30, shell=True,
        ).stdout.strip()
        out2 = subprocess.run(
            f"df -h {path} | tail -1",
            shell=True, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        parts = []
        if out:
            parts.append(f"Tamaño total de '{path}': {out}")
        if out2:
            parts.append(f"Uso de disco: {out2}")
        return "\n".join(parts)
    except Exception as e:
        return f"disk_usage error: {e}"

# === TOOLS DE RED ===

def _ping_test(host: str = "8.8.8.8", count: int = 4) -> str:
    try:
        if IS_WINDOWS:
            out = subprocess.run(
                ["ping", "-n", str(count), "-w", "5000", host],
                capture_output=True, text=True, timeout=30,
            )
        else:
            out = subprocess.run(
                ["ping", "-c", str(count), "-W", "5", host],
                capture_output=True, text=True, timeout=30,
            )
        result = out.stdout + out.stderr
        return result.strip() or f"No response from {host}"
    except Exception as e:
        return f"ping error: {e}"

def _port_scan(host: str = "localhost", ports: str = "22,80,443,3389,8080") -> str:
    import socket
    try:
        port_list = [int(p.strip()) for p in ports.split(",")]
    except ValueError:
        return "Invalid port list. Use comma-separated numbers (e.g. 22,80,443)"
    results = []
    for port in port_list:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            status = "abierto" if result == 0 else "cerrado"
            service = {22: "SSH", 80: "HTTP", 443: "HTTPS", 3389: "RDP", 8080: "HTTP-alt",
                       21: "FTP", 25: "SMTP", 53: "DNS", 110: "POP3", 143: "IMAP",
                       445: "SMB", 3306: "MySQL", 5432: "PostgreSQL", 27017: "MongoDB"}
            label = f" ({service.get(port, '?')})" if result == 0 else ""
            results.append(f"  Puerto {port}: {status}{label}")
        except Exception as e:
            results.append(f"  Puerto {port}: error - {e}")
    return f"Escaneo de {host}:\n" + "\n".join(results)

def _wifi_profiles() -> str:
    try:
        if IS_WINDOWS:
            out = subprocess.run(
                ["netsh", "wlan", "show", "networks", "mode=Bssid"],
                capture_output=True, text=True, timeout=15,
            )
            if out.stdout.strip():
                return "Redes WiFi disponibles:\n" + "\n".join(out.stdout.strip().split("\n")[:20])
            return "No WiFi networks found or no WiFi adapter"
        airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
        out = subprocess.run(
            [airport, "-s"], capture_output=True, text=True, timeout=10,
        ).stdout
        if out.strip():
            lines = out.strip().split("\n")
            return "Redes WiFi disponibles:\n" + "\n".join(lines[:15])
        return "No WiFi networks found or no WiFi hardware"
    except Exception:
        if IS_WINDOWS:
            return "WiFi scan error: netsh command failed"
        try:
            out = subprocess.run(
                "/sbin/ifconfig | grep -E '^(en|wl)'",
                shell=True, capture_output=True, text=True, timeout=10,
            ).stdout
            return f"Interfaces de red:\n{out.strip()}"
        except Exception as e:
            return f"WiFi scan error: {e}"

# === TOOLS DE DOCUMENTOS ===

def _pdf_extract(path: str, max_pages: int = 5) -> str:
    try:
        import fitz
    except ImportError:
        return "PDF extraction requires PyMuPDF. Install with: pip install PyMuPDF"
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return f"File not found: {p}"
        doc = fitz.open(str(p))
        total = len(doc)
        pages = min(max_pages, total)
        lines = [f"PDF: {p.name} | {total} páginas", ""]
        for i in range(pages):
            page = doc[i]
            text = page.get_text()
            lines.append(f"--- Página {i+1} ---")
            if text.strip():
                lines.append(text[:1500])
            else:
                lines.append("(sin texto extraíble, posiblemente escaneado)")
        doc.close()
        if pages < total:
            lines.append(f"\n... y {total - pages} páginas más. Usa pdf_extract con max_pages=N para ver más.")
        return "\n".join(lines)[:MAX_OUTPUT]
    except Exception as e:
        return f"pdf_extract error: {e}"

# === TOOLS DE SCRIPTS ===

def _gen_batch(path: str, commands: str, title: str = "") -> str:
    p = Path(path).expanduser().resolve()
    if not p.suffix:
        p = p.with_suffix(".bat")
    if not p.suffix == ".bat":
        p = p.with_suffix(".bat")

    content = "@echo off\n"
    if title:
        content += f"title {title}\n"
    content += "chcp 65001 >nul\n"
    content += "echo ========================================\n"
    content += f"echo {title or 'Script generado por ollacode'}\n"
    content += "echo ========================================\n"
    content += "echo.\n\n"
    content += commands
    content += "\n\necho.\necho Proceso completado.\npause\n"

    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"✅ Batch creado: {p} ({len(content)} bytes)\n\nContenido:\n{content}"

def _gen_powershell(path: str, commands: str, title: str = "") -> str:
    p = Path(path).expanduser().resolve()
    if not p.suffix:
        p = p.with_suffix(".ps1")
    if not p.suffix == ".ps1":
        p = p.with_suffix(".ps1")

    content = f"<#\n  {title or 'Script generado por ollacode'}\n#>\n"
    content += "$ErrorActionPreference = 'Stop'\n"
    content += "Write-Host '========================================' -ForegroundColor Cyan\n"
    content += f"Write-Host '{title or 'Script'}' -ForegroundColor Cyan\n"
    content += "Write-Host '========================================' -ForegroundColor Cyan\n"
    content += "Write-Host ''\n\n"
    content += commands
    content += '\n\nWrite-Host "Proceso completado." -ForegroundColor Green\n'

    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"✅ PowerShell creado: {p} ({len(content)} bytes)\n\nContenido:\n{content}"

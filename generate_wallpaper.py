#!/usr/bin/env python3
"""
Aurora Desktop Picture
Genera un fondo de pantalla con los datos REALES del hardware y lo aplica
en GNOME. Pensado para ejecutarse automáticamente al iniciar sesión.

Uso:
    python3 generate_wallpaper.py
    python3 generate_wallpaper.py --no-set        # solo crea la imagen
    python3 generate_wallpaper.py --log ARCHIVO   # guarda un registro
"""
from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HOME = Path.home()
DEFAULT_OUTPUT = HOME / "Pictures" / "hardware_wallpaper.png"

FONTS = Path("/usr/share/fonts/truetype/dejavu")
F_MONO = FONTS / "DejaVuSansMono.ttf"
F_MONO_B = FONTS / "DejaVuSansMono-Bold.ttf"
F_SANS_B = FONTS / "DejaVuSans-Bold.ttf"

LOG_FILE: Path | None = None


def log(msg: str) -> None:
    print(msg)
    if LOG_FILE:
        try:
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with LOG_FILE.open("a", encoding="utf-8") as fh:
                fh.write(f"{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}\n")
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Recolección de datos del sistema
# ---------------------------------------------------------------------------

def run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(
            cmd, text=True, stderr=subprocess.DEVNULL, timeout=8
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def first_line(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").splitlines()[0].strip()
    except (OSError, IndexError):
        return ""


def clean_pci(text: str, keep_vendor: bool = False) -> str:
    """Quita prefijos de fabricante y números de revisión para acortar el texto."""
    text = re.sub(r"\s*\(rev [^)]*\)", "", text)
    replacements = {
        "Realtek Semiconductor Co., Ltd. ": "",
        "Intel Corporation ": "Intel " if keep_vendor else "",
        "NVIDIA Corporation ": "NVIDIA " if keep_vendor else "",
        "Advanced Micro Devices, Inc. [AMD/ATI] ": "AMD " if keep_vendor else "",
    }
    for prefix, value in replacements.items():
        text = text.replace(prefix, value)
    if not keep_vendor:
        text = re.sub(r"\s*(PCIe?|USB) Adapter", "", text)
    return re.sub(r"\s+", " ", text).strip()


def local_ips() -> str:
    """Devuelve las IPv4 globales del equipo (o la de salida por defecto)."""
    ips: list[str] = []
    salida = run(["ip", "-4", "-o", "addr", "show", "scope", "global"])
    for linea in salida.splitlines():
        m = re.search(r"\binet\s+([\d.]+)", linea)
        if m:
            ips.append(m.group(1))
    if not ips:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # no envía datos: solo elige la interfaz de salida
            ips.append(s.getsockname()[0])
            s.close()
        except OSError:
            ips.append("127.0.0.1")
    return "  |  ".join(ips)


def os_release() -> tuple[str, str]:
    data = {}
    try:
        for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                data[k] = v.strip().strip('"')
    except OSError:
        pass
    return data.get("PRETTY_NAME", platform.system()), data.get("VERSION_ID", "")


def collect_hardware() -> list[tuple[str, str]]:
    """Devuelve la lista de filas (etiqueta, valor) para el fondo."""

    vendor = first_line("/sys/class/dmi/id/sys_vendor")
    product = first_line("/sys/class/dmi/id/product_name")
    if vendor and product.lower().startswith(vendor.lower()):
        equipo = product
    else:
        equipo = " ".join(p for p in (vendor, product) if p) or "Equipo desconocido"

    cpuinfo = ""
    try:
        cpuinfo = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="replace")
    except OSError:
        pass
    m = re.search(r"^model name\s*:\s*(.+)$", cpuinfo, re.M)
    cpu = m.group(1).strip() if m else (platform.processor() or "CPU desconocida")
    hilos = len(re.findall(r"^processor\s*:", cpuinfo, re.M)) or os.cpu_count() or 1
    m = re.search(r"^cpu cores\s*:\s*(\d+)", cpuinfo, re.M)
    nucleos = int(m.group(1)) if m else max(1, hilos // 2)
    sockets = len(set(re.findall(r"^physical id\s*:\s*(\d+)", cpuinfo, re.M))) or 1

    # Frecuencia base tomada del nombre original, antes de limpiarlo.
    freq_match = re.search(r"@\s*([\d.]+)\s*GHz", cpu)
    base_ghz = freq_match.group(1) if freq_match else ""

    # "Intel(R) Core(TM) i5-7200U CPU @ 2.50GHz" -> "Intel Core i5-7200U"
    cpu = re.sub(r"\(R\)|\(TM\)|\bCPU\b", "", cpu)
    cpu = re.sub(r"@\s*[\d.]+\s*GHz", "", cpu)
    cpu = re.sub(r"\s+", " ", cpu).strip()

    lscpu = run(["lscpu"])
    m_base = re.search(r"(?:CPU MHz|Velocidad b[aá]sica de CPU)[^:]*:\s*([\d.,]+)", lscpu, re.I)
    if not base_ghz and m_base:
        base_ghz = f"{float(m_base.group(1).replace(',', '.')) / 1000:.2f}".rstrip("0").rstrip(".")
    base = f"a {base_ghz} GHz" if base_ghz else ""

    m_max = re.search(r"CPU (?:max|m[aá]x)[^:]*:\s*([\d.,]+)", lscpu, re.I)
    max_ghz = f"{float(m_max.group(1).replace(',', '.')) / 1000:.1f}".rstrip("0").rstrip(".") if m_max else ""
    maximo = f"(máx. {max_ghz} GHz)" if max_ghz else ""

    mem_total_gib = 0.0
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                mem_total_gib = int(line.split()[1]) / 1024 / 1024
                break
    except OSError:
        pass

    lspci = run(["lspci"])
    gpu = "No detectada"
    net = "No detectada"
    for line in lspci.splitlines():
        desc = line.split(": ", 1)[-1] if ": " in line else line
        if re.search(r"VGA|3D controller|Display controller", line, re.I) and gpu == "No detectada":
            gpu = clean_pci(desc, keep_vendor=True)
        if "Network controller" in line and net == "No detectada":
            net = clean_pci(desc)
            if re.search(r"802\.11|wireless|wi-?fi", net, re.I):
                net += " (Wi-Fi)"

    uso = shutil.disk_usage("/")
    gb = 1024 ** 3  # mostramos GiB con la etiqueta "GB", igual que df -h
    disco = (
        f"Disco de {uso.total / gb:.0f} GB "
        f"({uso.used / gb:.0f} GB usados, {uso.free / gb:.0f} GB libres) montado en /"
    )

    pretty, version = os_release()
    so = f"{pretty} ({platform.machine()})"

    return [
        ("Equipo", equipo),
        ("Nombre del equipo", socket.gethostname()),
        ("Procesador", f"{cpu} {base} {maximo}".strip()),
        ("", f"{nucleos} núcleos / {hilos} hilos  -  {sockets} socket(s)"),
        ("Memoria RAM", f"{mem_total_gib:.1f} GiB"),
        ("Gráficos", f"{gpu} (integrada)" if "Intel" in gpu else gpu),
        ("Almacenamiento", disco),
        ("Red", net),
        ("Dirección IP", local_ips()),
        ("Sistema operativo", so),
        ("", f"Kernel {platform.release()}" + (f"  -  versión {version}" if version else "")),
        ("Actualizado", datetime.now().strftime("%d/%m/%Y a las %H:%M")),
    ]


# ---------------------------------------------------------------------------
# Dibujo del fondo
# ---------------------------------------------------------------------------

def pick_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def draw_fit(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font_path: Path,
    size: int,
    fill: tuple[int, int, int, int],
    max_width: int,
    bold: bool = False,
) -> None:
    """Reduce el tamaño de letra si el texto no cabe en el ancho dado."""
    path = F_MONO_B if bold else font_path
    for candidate in range(size, 23, -2):
        font = pick_font(path, candidate)
        if draw.textlength(text, font=font) <= max_width:
            draw.text(xy, text, font=font, fill=fill)
            return
    font = pick_font(path, 23)
    draw.text(xy, text, font=font, fill=fill)


def render(rows: list[tuple[str, str]], output: Path) -> None:
    # Resolución real de pantalla (X11/Wayland) con valores seguros por defecto.
    screen = run(["xdpyinfo"]) if os.environ.get("DISPLAY") else ""
    m = re.search(r"dimensions:\s*(\d+)x(\d+)", screen)
    W, H = (int(m.group(1)), int(m.group(2))) if m else (3072, 1728)

    header_h, row_h, footer_h = 300, 84, 160
    content_h = header_h + len(rows) * row_h + footer_h
    top = max(90, (H - content_h) // 2)
    bottom = min(H - 90, top + content_h)

    img = Image.new("RGB", (W, H))
    px = img.load()
    c0, c1 = (13, 20, 38), (28, 45, 78)
    for y in range(H):
        ty = y / (H - 1)
        for x in range(W):
            t = x / (W - 1) * 0.45 + ty * 0.55
            px[x, y] = tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3))

    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([W - 900, -420, W + 420, 900], fill=(56, 132, 255, 22))
    d.ellipse([-500, H - 780, 700, H + 320], fill=(0, 220, 190, 16))

    pad = max(80, int(W * 0.04))
    panel = [pad, top, W - pad, bottom]
    d.rounded_rectangle(panel, radius=42, fill=(8, 14, 28, 205),
                        outline=(90, 160, 255, 120), width=3)
    d.rounded_rectangle([panel[0] + 60, panel[1] + 46, panel[0] + 72, panel[3] - 46],
                        radius=6, fill=(0, 210, 190, 220))

    x = panel[0] + 130
    right = panel[2] - 100
    draw_fit(d, (x, panel[1] + 58), "ESPECIFICACIONES DEL EQUIPO", F_SANS_B, 82,
             (235, 244, 255, 255), right - x)
    draw_fit(d, (x, panel[1] + 166), "Información de hardware en vivo  //  Aurora Desktop Picture",
             F_MONO, 34, (120, 200, 255, 255), right - x)
    d.line([(x, panel[1] + 232), (right, panel[1] + 232)], fill=(90, 160, 255, 110), width=2)

    label_w = min(500, int((right - x) * 0.22))
    y = panel[1] + header_h - 10
    for label, value in rows:
        if label:
            draw_fit(d, (x, y), label.upper(), F_MONO_B, 40, (0, 215, 195, 255),
                     label_w - 20, bold=True)
        draw_fit(d, (x + label_w, y), value, F_MONO, 40, (226, 235, 250, 255),
                 right - (x + label_w))
        y += row_h

    d.line([(x, panel[3] - 110), (right, panel[3] - 110)], fill=(90, 160, 255, 110), width=2)
    draw_fit(d, (x, panel[3] - 88),
             "Generado automáticamente al iniciar sesión  -  GNOME / Ubuntu",
             F_MONO, 28, (150, 175, 205, 255), right - x)

    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output)
    log(f"Imagen generada: {output}  ({W}x{H})")


def set_background(path: Path) -> None:
    uri = path.resolve().as_uri()
    for key in ("picture-uri", "picture-uri-dark"):
        result = subprocess.run(
            ["gsettings", "set", "org.gnome.desktop.background", key, uri],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            log(f"Aviso: no se pudo aplicar {key}: {result.stderr.strip()}")
            return
    subprocess.run(
        ["gsettings", "set", "org.gnome.desktop.background", "picture-options", "zoom"],
        capture_output=True, text=True,
    )
    log(f"Fondo aplicado: {uri}")


def main() -> int:
    global LOG_FILE
    ap = argparse.ArgumentParser(description="Fondo de pantalla con datos del hardware")
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="ruta del PNG")
    ap.add_argument("--no-set", action="store_true", help="no cambiar el fondo de GNOME")
    ap.add_argument("--log", type=Path, help="archivo de registro")
    ap.add_argument("--print", action="store_true", help="mostrar los datos recogidos")
    args = ap.parse_args()

    LOG_FILE = args.log
    try:
        rows = collect_hardware()
        if args.print:
            for label, value in rows:
                print(f"{label or '  '}: {value}")
        render(rows, args.output)
        if not args.no_set:
            set_background(args.output)
        return 0
    except Exception as exc:  # noqa: BLE001 - queremos registrar cualquier fallo
        log(f"ERROR: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

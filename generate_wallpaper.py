#!/usr/bin/env python3
"""
Aurora Desktop Picture
Genera un fondo de pantalla con los datos REALES del hardware y lo aplica
en GNOME. Pensado para ejecutarse automáticamente al iniciar sesión.

Uso:
    python3 generate_wallpaper.py
    python3 generate_wallpaper.py --no-set        # solo crea la imagen
    python3 generate_wallpaper.py --print         # solo muestra los datos
    python3 generate_wallpaper.py --log ARCHIVO   # guarda un registro
    python3 generate_wallpaper.py --wait-display 20
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
import time
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

HOME = Path.home()
DEFAULT_OUTPUT = HOME / "Pictures" / "hardware_wallpaper.png"

FONTS = Path("/usr/share/fonts/truetype/dejavu")
F_MONO = FONTS / "DejaVuSansMono.ttf"
F_MONO_B = FONTS / "DejaVuSansMono-Bold.ttf"
F_SANS_B = FONTS / "DejaVuSans-Bold.ttf"

MIN_WIDTH = 640
MIN_HEIGHT = 480
MAX_DIMENSION = 16384
FALLBACK_SIZE = (1920, 1080)
NEAREST = getattr(getattr(Image, "Resampling", Image), "NEAREST", Image.NEAREST)

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

def run(cmd: list[str], timeout: int = 8) -> str:
    try:
        return subprocess.check_output(
            cmd, text=True, stderr=subprocess.DEVNULL, timeout=timeout
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
        ("Gráficos", gpu),
        ("Almacenamiento", disco),
        ("Red", net),
        ("Dirección IP", local_ips()),
        ("Sistema operativo", so),
        ("", f"Kernel {platform.release()}" + (f"  -  versión {version}" if version else "")),
        ("Actualizado", datetime.now().strftime("%d/%m/%Y a las %H:%M")),
    ]


# ---------------------------------------------------------------------------
# Resolución y composición del fondo
# ---------------------------------------------------------------------------

def valid_size(width: int, height: int) -> bool:
    """Solo acepta resoluciones con las que el panel se puede dibujar."""
    return (
        MIN_WIDTH <= width <= MAX_DIMENSION
        and MIN_HEIGHT <= height <= MAX_DIMENSION
    )


def parse_dimensions(text: str) -> tuple[int, int] | None:
    """Lee la línea 'dimensions: AxB' de xdpyinfo."""
    m = re.search(r"dimensions:\s*(\d+)\s*x\s*(\d+)", text, re.I)
    if not m:
        return None
    size = (int(m.group(1)), int(m.group(2)))
    return size if valid_size(*size) else None


def parse_xrandr(text: str) -> tuple[int, int] | None:
    """Lee la resolución de la primera pantalla conectada según xrandr."""
    for line in text.splitlines():
        if " connected" not in line:
            continue
        m = re.search(r"\b(\d{3,5})x(\d{3,5})\b", line)
        if m:
            size = (int(m.group(1)), int(m.group(2)))
            if valid_size(*size):
                return size
    return None


def parse_wlr_randr(text: str) -> tuple[int, int] | None:
    """Lee la resolución de wlr-randr (Wayland nativo)."""
    m = re.search(r"\b(\d{3,5})x(\d{3,5})\s*px\b", text)
    if m:
        size = (int(m.group(1)), int(m.group(2)))
        return size if valid_size(*size) else None
    return None


def detect_screen_size(wait_seconds: float = 0.0) -> tuple[int, int]:
    """Detecta la resolución, esperando si X11 aún no está listo al arrancar."""
    deadline = time.monotonic() + max(0.0, wait_seconds)
    while True:
        found: list[tuple[int, int] | None] = []
        if os.environ.get("DISPLAY"):
            found.append(parse_dimensions(run(["xdpyinfo"], timeout=3)))
            found.append(parse_xrandr(run(["xrandr", "--current"], timeout=3)))
        if os.environ.get("WAYLAND_DISPLAY"):
            found.append(parse_wlr_randr(run(["wlr-randr"], timeout=3)))
        for size in found:
            if size:
                return size
        if time.monotonic() >= deadline:
            break
        time.sleep(min(1.0, max(0.0, deadline - time.monotonic())))

    log(
        "Aviso: no se pudo detectar una resolución válida; "
        f"usando {FALLBACK_SIZE[0]}x{FALLBACK_SIZE[1]}"
    )
    return FALLBACK_SIZE


def compute_layout(width: int, height: int, row_count: int) -> dict[str, int | tuple[int, int, int, int]]:
    """Calcula un panel que siempre cabe en la pantalla, con fuentes escaladas."""
    if not valid_size(width, height):
        raise ValueError(f"resolución inválida: {width}x{height}")
    if row_count < 1:
        raise ValueError("no hay filas que dibujar")

    margin = max(16, int(height * 0.03))
    available = height - 2 * margin
    header_h = max(70, min(300, int(available * 0.22)))
    footer_h = max(40, min(160, int(available * 0.12)))
    row_h = min(84, max(18, (available - header_h - footer_h) // row_count))
    content_h = header_h + row_h * row_count + footer_h

    if content_h > available:
        excess = content_h - available
        cut = min(excess, header_h - 70)
        header_h -= cut
        excess -= cut
        cut = min(excess, footer_h - 40)
        footer_h -= cut
        content_h = header_h + row_h * row_count + footer_h

    top = (height - content_h) // 2
    bottom = top + content_h
    pad = max(40, int(width * 0.035))
    panel = (pad, top, width - pad, bottom)
    x = panel[0] + max(40, int(width * 0.055))
    right = panel[2] - max(30, int(width * 0.04))
    label_w = min(500, int((right - x) * 0.24))

    title_size = max(30, min(82, int(header_h * 0.34)))
    title_offset = max(18, int(header_h * 0.12))
    subtitle_size = max(14, min(34, int(header_h * 0.14)))
    subtitle_offset = max(int(header_h * 0.52), title_offset + title_size + 6)

    return {
        "width": width,
        "height": height,
        "panel": panel,
        "x": x,
        "right": right,
        "label_w": label_w,
        "header_h": header_h,
        "row_h": row_h,
        "footer_h": footer_h,
        "content_h": content_h,
        "top": top,
        "bottom": bottom,
        "title_size": title_size,
        "subtitle_size": subtitle_size,
        "body_size": max(12, min(40, int(row_h * 0.62))),
        "footer_size": max(12, min(28, int(footer_h * 0.24))),
        "title_y": panel[1] + title_offset,
        "subtitle_y": panel[1] + subtitle_offset,
        "divider_y": panel[1] + header_h - max(18, int(header_h * 0.10)),
        "rows_y": panel[1] + header_h - max(6, int(header_h * 0.03)),
        "footer_line_y": panel[3] - max(40, int(footer_h * 0.65)),
        "footer_text_y": panel[3] - max(28, int(footer_h * 0.45)),
    }


def make_gradient(width: int, height: int, c0: tuple[int, int, int],
                  c1: tuple[int, int, int]) -> Image.Image:
    """Fondo degradado generado con operaciones de Pillow (sin bucles por píxel)."""
    horizontal = Image.new("L", (width, 1))
    horizontal.putdata([round(i / (width - 1) * 255) for i in range(width)])
    vertical = Image.new("L", (1, height))
    vertical.putdata([round(i / (height - 1) * 255) for i in range(height)])

    t = ImageChops.blend(
        horizontal.resize((width, height), NEAREST),
        vertical.resize((width, height), NEAREST),
        0.55,
    )
    channels = []
    for i in range(3):
        delta = c1[i] - c0[i]
        layer = ImageChops.add(
            Image.new("L", (width, height), c0[i]),
            ImageChops.multiply(t, Image.new("L", (width, height), delta)),
        )
        channels.append(layer)
    return Image.merge("RGB", tuple(channels))


def pick_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def truncate_text(draw: ImageDraw.ImageDraw, text: str,
                  font: ImageFont.FreeTypeFont, max_width: int) -> str:
    """Acorta el texto con '…' hasta que quepa en el ancho disponible."""
    if draw.textlength(text, font=font) <= max_width:
        return text
    ellipsis = "…"
    if draw.textlength(ellipsis, font=font) > max_width:
        return ""
    low, high = 0, len(text)
    while low < high:
        mid = (low + high + 1) // 2
        candidate = f"{text[:mid].rstrip()}{ellipsis}"
        if draw.textlength(candidate, font=font) <= max_width:
            low = mid
        else:
            high = mid - 1
    return f"{text[:low].rstrip()}{ellipsis}" if low else ellipsis


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
    """Reduce la fuente (y si hace falta recorta) para que el texto quepa."""
    path = F_MONO_B if bold else font_path
    max_width = max(1, int(max_width))
    min_size = max(10, int(size * 0.55))
    for candidate in range(size, min_size - 1, -1):
        font = pick_font(path, candidate)
        if draw.textlength(text, font=font) <= max_width:
            draw.text(xy, text, font=font, fill=fill)
            return
    font = pick_font(path, min_size)
    draw.text(xy, truncate_text(draw, text, font, max_width), font=font, fill=fill)


def render(rows: list[tuple[str, str]], output: Path, wait_seconds: float = 0.0) -> None:
    width, height = detect_screen_size(wait_seconds)
    layout = compute_layout(width, height, len(rows))
    panel: tuple[int, int, int, int] = layout["panel"]  # type: ignore[assignment]

    c0, c1 = (13, 20, 38), (28, 45, 78)
    img = make_gradient(width, height, c0, c1)
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([int(width * 0.70), -int(height * 0.24),
               int(width * 1.22), int(height * 0.52)], fill=(56, 132, 255, 22))
    d.ellipse([-int(width * 0.16), int(height * 0.28),
               int(width * 0.36), int(height * 1.19)], fill=(0, 220, 190, 16))

    radius = max(16, min(42, int(min(width, height) * 0.025)))
    d.rounded_rectangle(panel, radius=radius, fill=(8, 14, 28, 205),
                        outline=(90, 160, 255, 120), width=3)
    bar_x = panel[0] + max(24, int(width * 0.02))
    bar_inset = max(16, int(height * 0.02))
    d.rounded_rectangle([bar_x, panel[1] + bar_inset, bar_x + 8, panel[3] - bar_inset],
                        radius=4, fill=(0, 210, 190, 220))

    x = layout["x"]
    right = layout["right"]
    draw_fit(d, (x, layout["title_y"]), "ESPECIFICACIONES DEL EQUIPO", F_SANS_B,
             layout["title_size"], (235, 244, 255, 255), right - x)
    draw_fit(d, (x, layout["subtitle_y"]),
             "Información de hardware en vivo  //  Aurora Desktop Picture",
             F_MONO, layout["subtitle_size"], (120, 200, 255, 255), right - x)
    divider_y = layout["divider_y"]
    d.line([(x, divider_y), (right, divider_y)], fill=(90, 160, 255, 110), width=2)

    label_w = layout["label_w"]
    y = layout["rows_y"]
    for label, value in rows:
        if label:
            draw_fit(d, (x, y), label.upper(), F_MONO_B, layout["body_size"],
                     (0, 215, 195, 255), label_w - 16, bold=True)
        draw_fit(d, (x + label_w, y), value, F_MONO, layout["body_size"],
                 (226, 235, 250, 255), right - (x + label_w))
        y += layout["row_h"]

    footer_line_y = layout["footer_line_y"]
    d.line([(x, footer_line_y), (right, footer_line_y)],
           fill=(90, 160, 255, 110), width=2)
    draw_fit(d, (x, layout["footer_text_y"]),
             "Generado automáticamente al iniciar sesión  -  GNOME / Ubuntu",
             F_MONO, layout["footer_size"], (150, 175, 205, 255), right - x)

    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output)
    log(f"Imagen generada: {output}  ({width}x{height})")


def set_background(path: Path) -> None:
    if not shutil.which("gsettings"):
        log("Aviso: gsettings no está disponible; no se aplicó el fondo")
        return
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
    ap.add_argument("--print", action="store_true", help="mostrar los datos y salir")
    ap.add_argument("--wait-display", type=float, default=0.0, metavar="SEGUNDOS",
                    help="esperar hasta que haya una resolución válida (arranque automático)")
    args = ap.parse_args()

    LOG_FILE = args.log
    try:
        rows = collect_hardware()
        if args.print:
            for label, value in rows:
                print(f"{label or '  '}: {value}")
            return 0
        render(rows, args.output, args.wait_display)
        if not args.no_set:
            set_background(args.output)
        return 0
    except Exception as exc:  # noqa: BLE001 - queremos registrar cualquier fallo
        log(f"ERROR: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

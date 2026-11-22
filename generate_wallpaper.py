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

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps

VERSION = "0.4.3"
RELEASE_DATE = "2026-11-22"

HOME = Path.home()


def default_output() -> Path:
    if sys.platform == "win32":
        import ctypes

        # CSIDL_PERSONAL apunta a Documentos, incluso si está redirigida.
        ruta = ctypes.create_unicode_buffer(260)
        resultado = ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, ruta)
        carpeta = Path(ruta.value) if resultado == 0 and ruta.value else HOME / "Documents"
        return carpeta / "hardware_wallpaper.png"
    return HOME / "Pictures" / "hardware_wallpaper.png"


DEFAULT_OUTPUT = default_output()

if sys.platform == "win32":
    FONTS = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    F_MONO = FONTS / "consola.ttf"
    F_MONO_B = FONTS / "consolab.ttf"
else:
    FONTS = Path("/usr/share/fonts/truetype/dejavu")
    F_MONO = FONTS / "DejaVuSansMono.ttf"
    F_MONO_B = FONTS / "DejaVuSansMono-Bold.ttf"

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


def memoria_windows_gib() -> float:
    import ctypes
    from ctypes import wintypes

    class EstadoMemoria(ctypes.Structure):
        _fields_ = [("longitud", wintypes.DWORD), ("carga", wintypes.DWORD)] + [
            (campo, ctypes.c_ulonglong)
            for campo in ("total", "disponible", "pagina_total", "pagina_disponible",
                          "virtual_total", "virtual_disponible", "virtual_extendida")
        ]

    estado = EstadoMemoria()
    estado.longitud = ctypes.sizeof(estado)
    if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(estado)):
        return estado.total / 1024 ** 3
    return 0.0


def red_windows(direcciones: str) -> str:
    """Identifica la interfaz que tiene una de las IPv4 mostradas."""
    ips = set(direcciones.split("  |  ")) - {"127.0.0.1", ""}
    for bloque in re.split(r"\n\s*\n(?=\S)", run(["ipconfig"])):
        lineas = bloque.splitlines()
        if not lineas:
            continue
        ipv4 = re.findall(r"^\s*[^\n:]*IPv4[^\n:]*:\s*([\d.]+)", bloque, re.M | re.I)
        if ips.intersection(ipv4):
            encabezado = lineas[0].rstrip(":")
            tipo, _, nombre = encabezado.partition(" adapter ")
            if not nombre:
                nombre = re.sub(r"^Adaptador de (?:LAN inalámbrica|Ethernet)\s+",
                                "", encabezado, flags=re.I)
                tipo = encabezado
            if re.search(r"wireless|inalámbrica", tipo, re.I) and not re.search(r"wi-?fi", nombre, re.I):
                return f"{nombre} (Wi-Fi)"
            return nombre
    return "No detectada"


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


def fabricante_modelo() -> tuple[str, str]:
    if sys.platform != "win32":
        return (first_line("/sys/class/dmi/id/sys_vendor"),
                first_line("/sys/class/dmi/id/product_name"))

    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS") as clave:
            valores = []
            for nombre in ("SystemManufacturer", "SystemProductName"):
                try:
                    valor, _ = winreg.QueryValueEx(clave, nombre)
                except OSError:
                    valor = ""
                valores.append(valor.strip() if isinstance(valor, str) else "")
    except OSError:
        return "", ""
    fabricante, modelo = valores
    if fabricante.casefold() == "dell inc.":
        fabricante = "Dell"
    return fabricante, modelo


def collect_hardware() -> list[tuple[str, str]]:
    """Devuelve la lista de filas (etiqueta, valor) para el fondo."""

    vendor, product = fabricante_modelo()
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

    direcciones = local_ips()
    if sys.platform == "win32":
        mem_total_gib = memoria_windows_gib()
        net = red_windows(direcciones)

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
        ("Memoria RAM", f"{mem_total_gib:.1f} GiB" if mem_total_gib else "No detectada"),
        ("Gráficos", gpu),
        ("Almacenamiento", disco),
        ("Red", net),
        ("Dirección IP", direcciones),
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

    margin = max(8, min(width, height) // 50)
    right_edge = width - margin
    bottom = height - margin
    panel_width = (right_edge - width // 2) * 5 // 6
    right_edge -= 40
    left = right_edge - panel_width * 4 // 5
    pad = max(10, margin * 3 // 4)
    alto_maximo = (bottom - height // 2) * 3 // 4
    alto_fila_original = min(31, (alto_maximo - 2 * pad) // row_count)
    alto_panel = (alto_fila_original * row_count + 2 * pad) * 4 // 5
    pad = pad * 4 // 5
    row_h = (alto_panel - 2 * pad) // row_count
    if row_h < 6:
        raise ValueError("demasiadas filas para el panel")
    bottom -= 20
    top = bottom - alto_panel
    x = left + pad
    right = right_edge - max(20, (right_edge - left) * 8 // 100)

    return {
        "panel": (left, top, right_edge, bottom),
        "x": x,
        "right": right,
        "label_w": (right - x) * 40 // 100,
        "row_h": row_h,
        "body_size": min(30, row_h * 7 // 10),
        "rows_y": top + pad,
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
    min_size = min(size, max(7, int(size * 0.65)))
    for candidate in range(size, min_size - 1, -1):
        font = pick_font(path, candidate)
        if draw.textlength(text, font=font) <= max_width:
            draw.text(xy, text, font=font, fill=fill)
            return
    font = pick_font(path, min_size)
    draw.text(xy, truncate_text(draw, text, font, max_width), font=font, fill=fill)


def fondo_configurado() -> Path | None:
    """Lee AURORA_FONDO del archivo .env ubicado junto al script."""
    archivo = Path(__file__).resolve().with_name(".env")
    try:
        lineas = archivo.read_text(encoding="utf-8-sig").splitlines()
    except FileNotFoundError:
        return None

    for linea in lineas:
        clave, _, valor = linea.partition("=")
        if clave.strip() != "AURORA_FONDO":
            continue
        valor = valor.strip()
        if len(valor) >= 2 and valor[0] in ('"', "'") and valor[0] == valor[-1]:
            valor = valor[1:-1]
        if valor:
            ruta = Path(os.path.expandvars(valor)).expanduser()
            return archivo.parent / ruta
        return None
    return None


def render(
    rows: list[tuple[str, str]], output: Path, wait_seconds: float = 0.0,
    *, fondo: Path | None = None,
) -> None:
    width, height = detect_screen_size(wait_seconds)
    layout = compute_layout(width, height, len(rows))
    panel: tuple[int, int, int, int] = layout["panel"]  # type: ignore[assignment]

    if fondo is not None and not fondo.is_file():
        log(f"Aviso: no se encuentra la imagen de fondo {fondo}; se usará negro.")
        fondo = None

    if fondo is None:
        img = Image.new("RGB", (width, height), "black")
    else:
        if fondo.resolve() == output.resolve() or (output.exists() and fondo.samefile(output)):
            raise ValueError("La imagen de fondo y el PNG de salida deben ser archivos distintos.")
        with Image.open(fondo) as original:
            img = ImageOps.fit(ImageOps.exif_transpose(original).convert("RGB"), (width, height))
    d = ImageDraw.Draw(img, "RGBA")

    radius = min(18, layout["row_h"])
    d.rounded_rectangle(panel, radius=radius, fill=(8, 14, 28, 110),
                        outline=(90, 160, 255, 90), width=2)

    x = layout["x"]
    right = layout["right"]
    label_w = layout["label_w"]
    y = layout["rows_y"]
    for label, value in rows:
        if label:
            draw_fit(d, (x, y), label.upper(), F_MONO_B, layout["body_size"],
                     (0, 215, 195, 255), label_w - 6, bold=True)
        value_right = right
        if label == "Actualizado":
            version_text = f"v{VERSION}"
            version_font = pick_font(F_MONO, max(7, layout["body_size"] * 3 // 4))
            version_width = version_font.getbbox(version_text)[2]
            version_x = right - version_width
            d.text((version_x, y + (layout["body_size"] - version_font.size) // 2),
                   version_text, font=version_font, fill=(155, 173, 201, 255))
            value_right = version_x - 8
        draw_fit(d, (x + label_w, y), value, F_MONO, layout["body_size"],
                 (226, 235, 250, 255), value_right - (x + label_w))
        y += layout["row_h"]

    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output)
    log(f"Imagen generada: {output}  ({width}x{height})")


def set_background(path: Path) -> None:
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        aplicar = ctypes.WinDLL("user32", use_last_error=True).SystemParametersInfoW
        aplicar.argtypes = (wintypes.UINT, wintypes.UINT, wintypes.LPCWSTR, wintypes.UINT)
        aplicar.restype = wintypes.BOOL
        ruta = str(path.resolve())
        if not aplicar(20, 0, ruta, 3):  # SPI_SETDESKWALLPAPER y notificación al escritorio.
            codigo = ctypes.get_last_error()
            raise OSError(f"Windows no pudo aplicar el fondo (código {codigo}): {ctypes.FormatError(codigo).strip()}")
        log(f"Fondo aplicado: {ruta}")
        return

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
    ap.add_argument("--version", action="version",
                    version=f"Aurora Desktop Picture {VERSION} ({RELEASE_DATE})",
                    help="mostrar la versión y la fecha de publicación")
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="ruta del PNG")
    ap.add_argument("--fondo", type=Path, help="imagen sobre la que se dibuja la tarjeta")
    ap.add_argument("--no-set", action="store_true", help="generar el PNG sin cambiar el fondo del escritorio")
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
        render(rows, args.output, args.wait_display, fondo=args.fondo if args.fondo is not None else fondo_configurado())
        if not args.no_set:
            set_background(args.output)
        return 0
    except Exception as exc:  # noqa: BLE001 - queremos registrar cualquier fallo
        log(f"ERROR: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

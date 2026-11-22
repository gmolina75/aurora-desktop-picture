#!/usr/bin/env python3
"""Pruebas básicas de resolución, composición y dibujo del fondo."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import generate_wallpaper as gw  # noqa: E402

ROWS = 12
SIZES = [(800, 600), (1366, 768), (1920, 1080), (2560, 1440), (3072, 1728)]


class TestResolution(unittest.TestCase):
    def test_parse_dimensions(self):
        self.assertEqual(gw.parse_dimensions("  dimensions:    1920x1080 pixels"), (1920, 1080))
        self.assertIsNone(gw.parse_dimensions("dimensions: 0x0 pixels"))
        self.assertIsNone(gw.parse_dimensions("dimensions: 200x200 pixels"))
        self.assertIsNone(gw.parse_dimensions("sin datos"))

    def test_parse_xrandr_and_wlr(self):
        xrandr = "Meta-0 connected primary 1920x1080+0+0 (normal) 1920x1080 59.96*+"
        self.assertEqual(gw.parse_xrandr(xrandr), (1920, 1080))
        self.assertEqual(gw.parse_wlr_randr("    1920x1080 px, 59.999Hz"), (1920, 1080))
        self.assertIsNone(gw.parse_xrandr("Meta-0 disconnected"))

    def test_fallback_sin_pantalla(self):
        with patch.dict(gw.os.environ, {"DISPLAY": "", "WAYLAND_DISPLAY": ""}, clear=False):
            self.assertEqual(gw.detect_screen_size(), gw.FALLBACK_SIZE)


class TestLayout(unittest.TestCase):
    def test_layout_cabe_en_la_pantalla(self):
        for width, height in SIZES:
            with self.subTest(size=f"{width}x{height}"):
                layout = gw.compute_layout(width, height, ROWS)
                panel = layout["panel"]
                body = layout["body_size"]

                self.assertGreaterEqual(panel[0], width // 2)
                self.assertGreaterEqual(panel[1], height // 2)
                self.assertLess(panel[2], width)
                self.assertLess(panel[3], height)
                self.assertGreater(panel[2], panel[0])
                self.assertGreater(panel[3], panel[1])

                fuente = gw.pick_font(gw.F_MONO, body)
                alto_texto = fuente.getbbox("Ágj")[3]
                self.assertLessEqual(alto_texto, layout["row_h"])
                ultima_fila = layout["rows_y"] + (ROWS - 1) * layout["row_h"]
                self.assertLess(ultima_fila + alto_texto, panel[3])
                self.assertGreater(layout["label_w"], 0)
                self.assertLess(layout["x"] + layout["label_w"], layout["right"])

    def test_rechaza_resoluciones_invalidas(self):
        for width, height in [(0, 0), (1, 1), (320, 240), (640, 400)]:
            with self.subTest(size=f"{width}x{height}"):
                with self.assertRaises(ValueError):
                    gw.compute_layout(width, height, ROWS)


class TestDibujo(unittest.TestCase):
    def test_gradient_corners(self):
        img = gw.make_gradient(64, 48, (10, 20, 30), (110, 130, 150))
        self.assertEqual(img.getpixel((0, 0)), (10, 20, 30))
        self.assertEqual(img.getpixel((63, 47)), (110, 130, 150))

    def test_truncate_text(self):
        img = gw.Image.new("RGBA", (200, 40))
        draw = gw.ImageDraw.Draw(img)
        font = gw.pick_font(gw.F_MONO, 20)
        self.assertEqual(gw.truncate_text(draw, "corto", font, 500), "corto")
        result = gw.truncate_text(draw, "texto muy largo para el ancho", font, 60)
        self.assertTrue(result.endswith("…"))
        self.assertLessEqual(draw.textlength(result, font=font), 60)


if __name__ == "__main__":
    unittest.main()

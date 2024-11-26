"""Copyright 2024 The excelize Authors. All rights reserved. Use of this source
code is governed by a BSD-style license that can be found in the LICENSE file.

Package excelize-py is a Python port of Go Excelize library, providing a set of
functions that allow you to write and read from XLAM / XLSM / XLSX / XLTM / XLTX
files. Supports reading and writing spreadsheet documents generated by Microsoft
Excel™ 2007 and later. Supports complex components by high compatibility, and
provided streaming API for generating or reading data from a worksheet with huge
amounts of data. This library needs Python version 3.7 or later.
"""

import excelize
import unittest
from dataclasses import dataclass
from unittest.mock import patch
import datetime
from typing import Optional
from ctypes import (
    c_int,
    Structure,
    POINTER,
)

class TestExcelize(unittest.TestCase):

    @patch("platform.architecture")
    def test_platform_architecture(self, mock_architecture):
        mock_architecture.return_value = ("unknown", "ELF")
        with self.assertRaises(SystemExit):
            excelize.load_lib()

    @patch("platform.machine")
    def test_platform_machine(self, mock_machine):
        mock_machine.return_value = "unknown"
        with self.assertRaises(SystemExit):
            excelize.load_lib()

    @patch("platform.machine")
    def test_platform_machine_arm64(self, mock_machine):
        mock_machine.return_value = "arm64"
        excelize.load_lib()

    @patch("platform.system")
    def test_platform_system(self, mock_system):
        mock_system.return_value = "unknown"
        with self.assertRaises(SystemExit):
            excelize.load_lib()

    def test_c_value_to_py(self):
        self.assertIsNone(excelize.c_value_to_py(None, None))

    def test_py_value_to_c(self):
        self.assertIsNone(excelize.py_value_to_c(None, None))

    def test_open_file(self):
        f, err = excelize.open_file("Book1.xlsx")
        self.assertIsNone(f)
        self.assertTrue(err.__str__().startswith("open Book1.xlsx"))

    def test_style(self):
        f = excelize.new_file()
        s = excelize.Style(
            border=[
                excelize.Border(type="left", color="0000FF", style=3),
                excelize.Border(type="right", color="FF0000", style=6),
                excelize.Border(type="top", color="00FF00", style=4),
                excelize.Border(type="bottom", color="FFFF00", style=5),
                excelize.Border(type="diagonalUp", color="A020F0", style=8),
                excelize.Border(type="diagonalDown", color="A020F0", style=8),
            ],
            font=excelize.Font(
                bold=True,
                size=11.5,
                italic=True,
                strike=True,
                color="FFF000",
                underline="single",
                family="Times New Roman",
                color_indexed=6,
                color_theme=1,
                color_tint=0.11,
            ),
            fill=excelize.Fill(shading=1, color=["00FF00", "FFFF00"], type="gradient"),
            alignment=excelize.Alignment(
                horizontal="center",
                indent=1,
                justify_last_line=True,
                reading_order=1,
                relative_indent=1,
                shrink_to_fit=True,
                text_rotation=180,
                vertical="center",
                wrap_text=True,
            ),
            protection=excelize.Protection(hidden=False, locked=True),
            custom_num_fmt=";;;",
        )
        style_id, err = f.new_style(s)
        self.assertIsNone(err)
        self.assertEqual(1, style_id)
        style, err = f.get_style(style_id)
        self.assertIsNone(err)
        self.assertEqual(style, s)
        self.assertIsNone(f.set_cell_style("Sheet1", "A1", "B2", style_id))
        self.assertEqual(f.set_cell_style("SheetN", "A1", "B2", style_id).__str__(), "sheet SheetN does not exist")

        style, err = f.get_style(2)
        self.assertEqual("invalid style ID 2", err.__str__())
        self.assertIsNone(style)
        self.assertIsNone(f.save_as("TestStyle.xlsx"))
        self.assertIsNone(
            f.save_as("TestStyleWithPassword.xlsx", excelize.Options(password="password"))
        )
        self.assertIsNone(f.close())

        f, err = excelize.open_file(
            "TestStyleWithPassword.xlsx", excelize.Options(password="password")
        )
        self.assertIsNone(err)
        with open("chart.png", "rb") as file:
            self.assertIsNone(
                f.set_sheet_background_from_bytes("Sheet1", ".png", file.read())
            )

        self.assertIsNone(f.set_cell_value("Sheet1", "A2", None))
        self.assertIsNone(f.set_cell_value("Sheet1", "A3", "Hello"))
        self.assertIsNone(f.set_cell_value("Sheet1", "A4", 100))
        self.assertIsNone(f.set_cell_value("Sheet1", "A5", 123.45))
        self.assertIsNone(f.set_cell_value("Sheet1", "A6", True))
        self.assertIsNone(f.set_cell_value("Sheet1", "A7", datetime.datetime.now()))
        self.assertIsNone(f.set_cell_value("Sheet1", "A8", datetime.date(2024, 10, 15)))
        self.assertEqual(f.set_cell_value("SheetN", "A9", None).__str__(), "sheet SheetN does not exist")

        idx, err = f.new_sheet("Sheet2")
        self.assertEqual(idx, 1)
        self.assertIsNone(err)
        self.assertIsNone(f.set_active_sheet(idx))

        idx, err = f.new_sheet(":\\/?*[]Maximum 31 characters allowed in sheet title.")
        self.assertEqual(idx, -1)
        self.assertEqual(err.__str__(), "the sheet name length exceeds the 31 characters limit")


        self.assertIsNone(f.save())
        self.assertIsNone(f.save(excelize.Options(password="password")))
        self.assertIsNone(f.close())

    def test_type_convert(self):
        class _T2(Structure):
            _fields_ = [
                ("D", c_int),
            ]

        class _T1(Structure):
            _fields_ = [
                ("ALen", c_int),
                ("A", POINTER(c_int)),
                ("BLen", c_int),
                ("B", POINTER(POINTER(c_int))),
                ("CLen", c_int),
                ("C", POINTER(POINTER(_T2))),
            ]

        @dataclass
        class T2:
            d: int = 0

        @dataclass
        class T1:
            a: Optional[list[int]] = None
            b: Optional[list[Optional[int]]] = None
            c: Optional[list[Optional[T2]]] = None

        t1 = T1(
            a=[1, 2, 3],
            b=[1, 2, 3],
            c=[T2(1), T2(2), T2(3)],
        )
        self.assertEqual(
            excelize.c_value_to_py(excelize.py_value_to_c(t1, _T1()), T1()), t1
        )

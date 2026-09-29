"""DELIBERATE STUB (scope cut): no OCR / CAD / PDF parsing of drawing sheet content.

Drawing sheets (DWG-*.pdf/.dwg/.dxf) are registered via the drawing register CSV. Dimensional callouts
reach the system through the callout schedule CSV (the structured dimension schedule exported alongside
a drawing), NOT by reading the sheet. This function is the single place real extraction (PyMuPDF, ezdxf,
OCR) would go; it returns nothing today, so downstream code will not change when it is filled in.
"""
from pathlib import Path
from models import Callout

def extract_callouts(drawing_file: Path) -> list[Callout]:
    return []

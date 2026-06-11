"""Local compatibility shim for skyfield-data.

The golden astronomy tests expect skyfield_data.get_skyfield_data_path().
This project already vendors de421.bsp at the repository root, so returning
that directory keeps the tests offline and deterministic.
"""
from pathlib import Path


def get_skyfield_data_path() -> str:
    return str(Path(__file__).resolve().parents[1])

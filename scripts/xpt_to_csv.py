"""Convierte los archivos NHANES .XPT a CSV (fuente "archivos planos" del ETL).

Esto materializa la primera de las tres fuentes de datos: archivos CSV/Excel.
Los CSV se escriben en ``data/01_raw/nhanes_csv/``.

Uso:
    python scripts/xpt_to_csv.py
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("xpt_to_csv")


def convert_dir(src: Path, dst: Path) -> int:
    dst.mkdir(parents=True, exist_ok=True)
    files = sorted(src.glob("*.xpt"))
    if not files:
        log.warning("No se encontraron .xpt en %s", src)
        return 1
    for fp in files:
        df = pd.read_sas(fp, format="xport")
        out = dst / f"{fp.stem}.csv"
        df.to_csv(out, index=False)
        log.info("%-14s -> %-16s rows=%d cols=%d", fp.name, out.name, len(df), df.shape[1])
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convierte NHANES .XPT a CSV")
    parser.add_argument("--src", default="data/01_raw/nhanes")
    parser.add_argument("--dst", default="data/01_raw/nhanes_csv")
    args = parser.parse_args(argv)
    return convert_dir(Path(args.src), Path(args.dst))


if __name__ == "__main__":
    sys.exit(main())

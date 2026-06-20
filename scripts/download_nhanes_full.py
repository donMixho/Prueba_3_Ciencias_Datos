"""Descarga COMPLETA de NHANES 2017-2018: todos los archivos de cada componente.

Recorre las páginas de cada componente, extrae todos los enlaces .xpt y los
descarga organizados en data/01_raw/nhanes_full/<componente>/.

Uso:
    python scripts/download_nhanes_full.py
    python scripts/download_nhanes_full.py --component Laboratory
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("download_full")

HOST = "https://wwwn.cdc.gov"
PAGE = HOST + "/nchs/nhanes/search/datapage.aspx?Component={component}&CycleBeginYear={year}"
XPT_RE = re.compile(r"(/Nchs/Data/Nhanes/[^\"' ]+\.xpt)", re.IGNORECASE)

COMPONENTS = [
    "Demographics",
    "Dietary",
    "Examination",
    "Laboratory",
    "Questionnaire",
    "LimitedAccess",
]


def list_xpt(component: str, year: int) -> list[str]:
    """Extrae las rutas .xpt de la página de un componente."""
    url = PAGE.format(component=component, year=year)
    resp = requests.get(url, timeout=90)
    resp.raise_for_status()
    return sorted(set(XPT_RE.findall(resp.text)))


def download(path: str, dest_dir: Path, timeout: int = 120) -> tuple[bool, int]:
    """Descarga un .xpt si no existe. Devuelve (descargado?, bytes)."""
    name = path.rsplit("/", maxsplit=1)[-1]
    dest = dest_dir / name
    if dest.exists() and dest.stat().st_size > 0:
        return False, dest.stat().st_size
    resp = requests.get(HOST + path, timeout=timeout, stream=True)
    resp.raise_for_status()
    with dest.open("wb") as fh:
        for chunk in resp.iter_content(chunk_size=65536):
            fh.write(chunk)
    return True, dest.stat().st_size


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Descarga completa NHANES 2017-2018")
    parser.add_argument("--out", default="data/01_raw/nhanes_full")
    parser.add_argument("--year", type=int, default=2017)
    parser.add_argument("--component", help="Solo este componente (opcional)")
    args = parser.parse_args(argv)

    components = [args.component] if args.component else COMPONENTS
    out_root = Path(args.out)
    grand_files = grand_bytes = grand_errors = 0

    for comp in components:
        dest_dir = out_root / comp
        dest_dir.mkdir(parents=True, exist_ok=True)
        try:
            links = list_xpt(comp, args.year)
        except Exception as exc:  # noqa: BLE001
            log.error("no se pudo listar %s: %s", comp, exc)
            grand_errors += 1
            continue

        if not links:
            log.warning("%-14s -> 0 archivos públicos (¿acceso restringido?)", comp)
            continue

        log.info("== %s: %d archivos ==", comp, len(links))
        comp_bytes = 0
        for i, path in enumerate(links, 1):
            try:
                new, size = download(path, dest_dir)
                comp_bytes += size
                flag = "NUEVO" if new else "existe"
                log.info("  [%2d/%2d] %-6s %-18s %.1f MB", i, len(links), flag, path.split("/")[-1], size / 1e6)
            except Exception as exc:  # noqa: BLE001
                log.error("  fallo %s: %s", path, exc)
                grand_errors += 1
        grand_files += len(links)
        grand_bytes += comp_bytes
        log.info("  subtotal %s: %.1f MB", comp, comp_bytes / 1e6)

    log.info("=" * 50)
    log.info("TOTAL: %d archivos, %.1f MB, %d errores", grand_files, grand_bytes / 1e6, grand_errors)
    return 1 if grand_errors else 0


if __name__ == "__main__":
    sys.exit(main())

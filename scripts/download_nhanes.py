"""Descarga reproducible de los archivos NHANES 2017-2018 (.XPT).

Uso:
    python scripts/download_nhanes.py
    python scripts/download_nhanes.py --out data/01_raw/nhanes --cycle 2017

Todos los archivos comparten la llave de unión ``SEQN``. Las fuentes que el
pipeline ETL consume luego son:
    - Archivos planos (CSV/XPT): DEMO, BMX, BPX, cuestionarios.
    - Base de datos SQL (Postgres): archivos de laboratorio (seed via Docker).
    - API REST: data.cdc.gov (Socrata) para enriquecimiento poblacional.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("download_nhanes")

# Patrón de URL pública de CDC NHANES.
# Usamos el dataset PRE-PANDEMIC 2017-March 2020 (prefijo P_), que combina los
# ciclos 2017-2018 y 2019-2020. El ciclo 2019-2020 NO se publicó por separado
# debido a la interrupción por COVID-19, por lo que este es el modo oficial de
# incluir datos de 2019-2020. La carpeta sigue siendo 2017.
BASE_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{cycle}/DataFiles/{name}.xpt"

# Archivos Pre-Pandemic (prefijo P_) agrupados por componente.
# Nota: la presión arterial pasó a medición oscilométrica (P_BPXO).
FILES: dict[str, list[str]] = {
    "demographics": ["P_DEMO"],
    "dietary": ["P_DR1TOT"],
    "examination": ["P_BMX", "P_BPXO"],
    "laboratory": ["P_GLU", "P_GHB", "P_TCHOL", "P_HDL", "P_TRIGLY"],
    "questionnaire": ["P_DIQ", "P_BPQ", "P_SMQ", "P_PAQ", "P_MCQ"],
}


def download_file(name: str, cycle: str, out_dir: Path, timeout: int = 60) -> Path:
    """Descarga un archivo .XPT si no existe localmente."""
    dest = out_dir / f"{name}.xpt"
    if dest.exists() and dest.stat().st_size > 0:
        log.info("ya existe, omito: %s", dest.name)
        return dest

    url = BASE_URL.format(cycle=cycle, name=name)
    log.info("descargando %s -> %s", url, dest)
    resp = requests.get(url, timeout=timeout, stream=True)
    resp.raise_for_status()
    with dest.open("wb") as fh:
        for chunk in resp.iter_content(chunk_size=8192):
            fh.write(chunk)
    log.info("OK %s (%.1f KB)", dest.name, dest.stat().st_size / 1024)
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Descarga datasets NHANES 2017-2018")
    parser.add_argument("--out", default="data/01_raw/nhanes", help="Carpeta de salida")
    parser.add_argument("--cycle", default="2017", help="Año de carpeta CDC (2017 = ciclo 2017-2018)")
    args = parser.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    errors = 0
    for component, names in FILES.items():
        log.info("== componente: %s ==", component)
        for name in names:
            try:
                download_file(name, args.cycle, out_dir)
            except Exception as exc:  # noqa: BLE001
                log.error("fallo al descargar %s: %s", name, exc)
                errors += 1

    if errors:
        log.error("Finalizado con %d errores", errors)
        return 1
    log.info("Todos los archivos descargados correctamente en %s", out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())

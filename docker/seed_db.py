"""Seed de la base de datos SQL (fuente 2 del ETL).

Carga los archivos NHANES de laboratorio (.XPT) en tablas de Postgres. Se
ejecuta una vez al levantar el stack (servicio ``db-seed`` en docker-compose).

Variables de entorno usadas (con valores por defecto para desarrollo local):
    POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("seed_db")

RAW_DIR = Path(os.getenv("RAW_DIR", "data/01_raw/nhanes"))

# archivo XPT -> (nombre de tabla, columnas a conservar)
TABLES = {
    "GLU_J": ("lab_glucose", ["SEQN", "LBXGLU"]),
    "GHB_J": ("lab_hba1c", ["SEQN", "LBXGH"]),
    "TCHOL_J": ("lab_cholesterol_tc", ["SEQN", "LBXTC"]),
    "HDL_J": ("lab_cholesterol_hdl", ["SEQN", "LBDHDD"]),
    "TRIGLY_J": ("lab_triglycerides", ["SEQN", "LBXTR", "LBDLDL"]),
}


def _engine():
    user = os.getenv("POSTGRES_USER", "nhanes")
    pwd = os.getenv("POSTGRES_PASSWORD", "nhanes")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "nhanes")
    return create_engine(f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}")


def wait_for_db(engine, retries: int = 30, delay: float = 2.0) -> None:
    for i in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            log.info("Postgres disponible")
            return
        except Exception as exc:  # noqa: BLE001
            log.info("esperando Postgres (%d/%d): %s", i, retries, exc)
            time.sleep(delay)
    raise RuntimeError("Postgres no respondió a tiempo")


def main() -> int:
    engine = _engine()
    wait_for_db(engine)

    # vista combinada de colesterol esperada por el catalog (lab_cholesterol)
    for fname, (table, cols) in TABLES.items():
        fp = RAW_DIR / f"{fname}.xpt"
        if not fp.exists():
            log.warning("no existe %s, omito", fp)
            continue
        df = pd.read_sas(fp, format="xport")[cols]
        df.columns = [c.lower() for c in df.columns]
        df.to_sql(table, engine, if_exists="replace", index=False)
        log.info("tabla %-22s <- %s (%d filas)", table, fname, len(df))

    # une TC + HDL en lab_cholesterol (lo que consulta el catalog)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS lab_cholesterol"))
        conn.execute(
            text(
                """
                CREATE TABLE lab_cholesterol AS
                SELECT tc.seqn, tc.lbxtc, hdl.lbdhdd
                FROM lab_cholesterol_tc tc
                LEFT JOIN lab_cholesterol_hdl hdl USING (seqn)
                """
            )
        )
    log.info("tabla lab_cholesterol creada (TC + HDL)")
    log.info("Seed completado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

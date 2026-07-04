"""Nodos de procesamiento: limpieza, integración y features cardiometabólicas."""

from __future__ import annotations

import logging
import os
import pickle
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    mean_absolute_error,
    r2_score,
    roc_auc_score,
    root_mean_squared_error,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from prueba.utils.validation import (
    replace_missing_codes,
    validate_unique_key,
)

log = logging.getLogger(__name__)


def _select(df: pd.DataFrame, cols: list[str], name: str) -> pd.DataFrame:
    """Selecciona columnas existentes y avisa de las ausentes."""
    df = df.copy()
    df.columns = [c.upper() for c in df.columns]
    present = [c for c in cols if c in df.columns]
    missing = set(cols) - set(present)
    if missing:
        log.warning("[%s] columnas ausentes (se omiten): %s", name, missing)
    return df[present].copy()


def merge_clinical(
    demographics: pd.DataFrame,
    body_measures: pd.DataFrame,
    diet: pd.DataFrame,
    blood_pressure: pd.DataFrame,
    glucose: pd.DataFrame,
    hba1c: pd.DataFrame,
    cholesterol: pd.DataFrame,
    triglycerides: pd.DataFrame,
    diabetes_q: pd.DataFrame,
    bloodpressure_q: pd.DataFrame,
    smoking_q: pd.DataFrame,
    activity_q: pd.DataFrame,
    columns: dict,
) -> pd.DataFrame:
    """Une todas las fuentes por la llave SEQN (left join sobre demografía)."""
    base = _select(demographics, columns["demographics"], "demographics")
    validate_unique_key(base, "SEQN", "demographics")

    parts = {
        "body_measures": _select(body_measures, columns["body_measures"], "body_measures"),
        "diet": _select(diet, columns["diet"], "diet"),
        "blood_pressure": _select(blood_pressure, columns["blood_pressure"], "blood_pressure"),
        "glucose": _select(glucose, columns["glucose"], "glucose"),
        "hba1c": _select(hba1c, columns["hba1c"], "hba1c"),
        "cholesterol": _select(cholesterol, columns["cholesterol_total"] + ["LBDHDD"], "cholesterol"),
        "triglycerides": _select(triglycerides, columns["triglycerides"], "triglycerides"),
        "diabetes_q": _select(diabetes_q, columns["diabetes_q"], "diabetes_q"),
        "bloodpressure_q": _select(bloodpressure_q, columns["bloodpressure_q"], "bloodpressure_q"),
        "smoking_q": _select(smoking_q, columns["smoking_q"], "smoking_q"),
        "activity_q": _select(activity_q, columns["activity_q"], "activity_q"),
    }

    merged = base
    for name, part in parts.items():
        merged = merged.merge(part, on="SEQN", how="left")
        log.info("merge %-16s -> %d filas, %d cols", name, len(merged), merged.shape[1])

    return merged


def clean_clinical(merged: pd.DataFrame, validation: dict) -> pd.DataFrame:
    """Limpia códigos especiales y normaliza nombres de columnas."""
    coded_cols = ["DIQ010", "BPQ020", "SMQ020", "PAQ650", "DMDEDUC2"]
    if validation.get("drop_invalid_codes", True):
        merged = replace_missing_codes(merged, coded_cols)

    rename = {
        "RIAGENDR": "sex",
        "RIDAGEYR": "age",
        "RIDRETH3": "race",
        "DMDEDUC2": "education",
        "INDFMPIR": "income_poverty_ratio",
        "BMXBMI": "bmi",
        "BMXWT": "weight_kg",
        "BMXHT": "height_cm",
        "BMXWAIST": "waist_cm",
        "LBXGLU": "glucose_mgdl",
        "LBXGH": "hba1c_pct",
        "LBXTC": "cholesterol_total",
        "LBDHDD": "cholesterol_hdl",
        "LBXTR": "triglycerides",
        "LBDLDL": "cholesterol_ldl",
        # Dieta (totales diarios, P_DR1TOT)
        "DR1TKCAL": "energy_kcal",
        "DR1TSUGR": "sugar_g",
        "DR1TSODI": "sodium_mg",
        "DR1TTFAT": "fat_g",
        "DR1TSFAT": "sat_fat_g",
        "DR1TFIBE": "fiber_g",
        "DR1TPROT": "protein_g",
        "DR1TCARB": "carbs_g",
    }
    df = merged.rename(columns={k: v for k, v in rename.items() if k in merged.columns})
    df["sex"] = df["sex"].map({1: "Hombre", 2: "Mujer"}).astype("object")
    return df


def _bmi_category(bmi: float, t: dict) -> str:
    if pd.isna(bmi):
        return "Desconocido"
    if bmi < t["underweight"]:
        return "Bajo peso"
    if bmi < t["normal"]:
        return "Normal"
    if bmi < t["overweight"]:
        return "Sobrepeso"
    return "Obesidad"


def _age_group(age: float, groups: list[dict]) -> str:
    if pd.isna(age):
        return "Desconocido"
    for g in groups:
        if g["min"] <= age <= g["max"]:
            return g["label"]
    return "Desconocido"


def engineer_features(df: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
    """Crea variables derivadas y banderas clínicas de riesgo."""
    df = df.copy()

    # Presión arterial: media de lecturas válidas.
    # Soporta tanto la medición manual (BPXSY*/BPXDI*) como la oscilométrica
    # (BPXOSY*/BPXODI*) usada en el dataset Pre-Pandemic 2017-2020.
    sys_cols = [c for c in df.columns if c.startswith(("BPXSY", "BPXOSY"))]
    dia_cols = [c for c in df.columns if c.startswith(("BPXDI", "BPXODI"))]
    # diastólica 0 = inválida en NHANES
    df[dia_cols] = df[dia_cols].replace(0, np.nan)
    df["bp_systolic_mean"] = df[sys_cols].mean(axis=1, skipna=True)
    df["bp_diastolic_mean"] = df[dia_cols].mean(axis=1, skipna=True)

    # Categorías
    df["bmi_category"] = df["bmi"].apply(lambda b: _bmi_category(b, thresholds["bmi"]))
    df["age_group"] = df["age"].apply(lambda a: _age_group(a, thresholds["age_groups"]))

    # Banderas clínicas
    df["hypertension_flag"] = (
        (df["bp_systolic_mean"] >= thresholds["hypertension_systolic"])
        | (df["bp_diastolic_mean"] >= thresholds["hypertension_diastolic"])
    ).astype("Int64")

    df["diabetes_flag"] = (
        (df.get("hba1c_pct") >= thresholds["diabetes_hba1c"])
        | (df.get("glucose_mgdl") >= thresholds["diabetes_fasting_glucose"])
        | (df.get("DIQ010") == 1)
    ).astype("Int64")

    df["obesity_flag"] = (df["bmi_category"] == "Obesidad").astype("Int64")
    df["smoker_flag"] = (df.get("SMQ020") == 1).astype("Int64")

    # Score compuesto de riesgo cardiometabólico (0-4)
    df["cardiometabolic_risk"] = (
        df[["hypertension_flag", "diabetes_flag", "obesity_flag", "smoker_flag"]]
        .fillna(0)
        .sum(axis=1)
        .astype("Int64")
    )

    log.info("Features generadas: %d filas, %d columnas", len(df), df.shape[1])
    return df


def train_risk_model(df: pd.DataFrame, model_params: dict) -> Pipeline:
    """Entrena un clasificador binario de alto riesgo cardiometabólico.

    Define la variable objetivo como ``cardiometabolic_risk >= target_threshold``
    (1 = alto riesgo, 0 = bajo riesgo) y entrena un ``RandomForestClassifier``
    sobre un subconjunto de variables clínicas. Las variables con valores
    ausentes (frecuentes en NHANES, p. ej. glucosa o HbA1c medidas solo en
    ayunas) se imputan por mediana dentro de un ``Pipeline`` de scikit-learn,
    de modo que el artefacto resultante pueda predecir aunque falte algún dato.

    Las métricas (accuracy y AUC) se calculan sobre un conjunto de prueba
    retenido (``test_size``) y se registran en el log.

    Args:
        df: DataFrame primario ``prm_cardiometabolic`` con las features y la
            columna objetivo ``cardiometabolic_risk``.
        model_params: parámetros del modelo. Claves esperadas: ``features``,
            ``target_col``, ``target_threshold``, ``test_size``,
            ``random_state``, ``n_estimators``, ``max_depth``.

    Returns:
        El ``Pipeline`` (imputación + RandomForest) ya entrenado, listo para
        serializarse como artefacto y ser consumido por la API.

    Raises:
        ValueError: si faltan columnas requeridas o si la variable objetivo
            tiene una sola clase (no se puede entrenar un clasificador binario).
    """
    features: list[str] = model_params["features"]
    target_col: str = model_params.get("target_col", "cardiometabolic_risk")
    threshold: int = model_params.get("target_threshold", 2)

    missing = [c for c in [*features, target_col] if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas para entrenar el modelo: {missing}")

    # X: features numéricas (coerciona texto/categorías a NaN para imputar).
    x = df[features].apply(pd.to_numeric, errors="coerce")
    # y: alto riesgo (1) si el score compuesto supera el umbral.
    y = (df[target_col] >= threshold).astype(int)

    if y.nunique() < 2:
        raise ValueError(
            "La variable objetivo tiene una sola clase; no se puede entrenar "
            "un clasificador binario."
        )

    log.info(
        "Entrenando modelo de riesgo | muestras=%d | alto_riesgo=%.1f%% | features=%s",
        len(y),
        100 * y.mean(),
        features,
    )

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=model_params.get("test_size", 0.2),
        random_state=model_params.get("random_state", 42),
        stratify=y,
    )

    model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=model_params.get("n_estimators", 200),
                    max_depth=model_params.get("max_depth"),
                    class_weight="balanced",
                    random_state=model_params.get("random_state", 42),
                    n_jobs=-1,
                ),
            ),
        ]
    )
    model.fit(x_train, y_train)

    # Métricas sobre el conjunto de prueba retenido.
    try:
        y_pred = model.predict(x_test)
        y_proba = model.predict_proba(x_test)[:, 1]
        accuracy = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_proba)
        log.info(
            "Modelo entrenado | accuracy=%.3f | AUC=%.3f | test=%d muestras",
            accuracy,
            auc,
            len(y_test),
        )
    except Exception as exc:  # noqa: BLE001 - las métricas no deben tumbar el pipeline
        log.warning("No se pudieron calcular las métricas del modelo: %s", exc)

    return model


def train_bioage_model(df: pd.DataFrame, model_params: dict) -> Pipeline:
    """Entrena un regresor de EDAD BIOLÓGICA como proxy de longevidad.

    Predice la edad cronológica (``age``) a partir de biomarcadores
    cardiometabólicos (``features``), **sin** usar la edad como entrada. La
    diferencia entre la edad biológica estimada y la edad real (*age gap*) es un
    indicador de envejecimiento acelerado (proxy de menor longevidad) o
    saludable (mayor longevidad), inspirado en enfoques tipo *PhenoAge*.

    Solo se usan adultos (``min_age``) con los biomarcadores mínimos presentes
    (``required_features``); el resto de nulos se imputa por mediana dentro de
    un ``Pipeline`` de scikit-learn. Las métricas (MAE, RMSE, R²) se calculan
    sobre un conjunto de prueba retenido y se registran en el log.

    Args:
        df: DataFrame primario ``prm_cardiometabolic`` con biomarcadores y edad.
        model_params: parámetros del modelo. Claves esperadas: ``features``,
            ``target_col``, ``min_age``, ``required_features``, ``test_size``,
            ``random_state``, ``n_estimators``, ``max_depth``.

    Returns:
        El ``Pipeline`` (imputación + RandomForestRegressor) ya entrenado.

    Raises:
        ValueError: si faltan columnas requeridas o no quedan filas usables.
    """
    features: list[str] = model_params["features"]
    target_col: str = model_params.get("target_col", "age")
    min_age: int = model_params.get("min_age", 18)
    required: list[str] = model_params.get("required_features", ["bmi", "bp_systolic_mean"])

    missing = [c for c in [*features, target_col] if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas para el modelo de edad biológica: {missing}")

    # Solo adultos con los biomarcadores mínimos (evita ruido de menores/vacíos).
    data = df[df[target_col] >= min_age].dropna(subset=required)
    if data.empty:
        raise ValueError("No quedan filas usables tras filtrar adultos y nulos.")

    x = data[features].apply(pd.to_numeric, errors="coerce")
    y = data[target_col]

    log.info(
        "Entrenando modelo de edad biológica | muestras=%d | edad media=%.1f | features=%s",
        len(y),
        y.mean(),
        features,
    )

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=model_params.get("test_size", 0.2),
        random_state=model_params.get("random_state", 42),
    )

    model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            (
                "reg",
                RandomForestRegressor(
                    n_estimators=model_params.get("n_estimators", 300),
                    max_depth=model_params.get("max_depth", 12),
                    random_state=model_params.get("random_state", 42),
                    n_jobs=-1,
                ),
            ),
        ]
    )
    model.fit(x_train, y_train)

    # Métricas sobre el conjunto de prueba retenido.
    try:
        y_pred = model.predict(x_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = root_mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        log.info(
            "Edad biológica entrenada | MAE=%.1f años | RMSE=%.1f | R2=%.3f | test=%d",
            mae,
            rmse,
            r2,
            len(y_test),
        )
    except Exception as exc:  # noqa: BLE001 - las métricas no deben tumbar el pipeline
        log.warning("No se pudieron calcular las métricas de edad biológica: %s", exc)

    return model


def train_clustering_model(
    df: pd.DataFrame,
    clustering_params: dict,
) -> Pipeline:
    """Entrena un modelo KMeans para segmentar la población en perfiles de salud.

    Aplica un aprendizaje **no supervisado** sobre un subconjunto de variables
    cardiometabólicas (``features``) para agrupar a las personas en
    ``n_clusters`` perfiles de salud. Las variables se imputan por mediana y se
    estandarizan (``StandardScaler``) dentro de un ``Pipeline`` de scikit-learn
    antes de ajustar el ``KMeans``, de modo que el artefacto resultante pueda
    etiquetar a nuevas personas aunque falte algún dato y sin verse dominado por
    las variables de mayor escala.

    Se registran en el log el número de muestras, la inercia del modelo y el
    tamaño de cada cluster.

    Args:
        df: DataFrame primario ``prm_cardiometabolic`` con las features.
        clustering_params: parámetros del modelo. Claves esperadas: ``features``,
            ``n_clusters``, ``random_state``.

    Returns:
        El ``Pipeline`` (imputación + estandarización + KMeans) ya entrenado,
        listo para serializarse como artefacto y etiquetar perfiles de salud.

    Raises:
        ValueError: si faltan columnas requeridas para el clustering.
    """
    features: list[str] = clustering_params["features"]
    n_clusters: int = clustering_params.get("n_clusters", 4)

    missing = [c for c in features if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas para el modelo de clustering: {missing}")

    # X: features numéricas (coerciona texto/categorías a NaN para imputar).
    x = df[features].apply(pd.to_numeric, errors="coerce")

    log.info(
        "Entrenando modelo de clustering | muestras=%d | n_clusters=%d | features=%s",
        len(x),
        n_clusters,
        features,
    )

    model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "kmeans",
                KMeans(
                    n_clusters=n_clusters,
                    random_state=clustering_params.get("random_state", 42),
                    n_init=10,
                ),
            ),
        ]
    )
    model.fit(x)

    # Métricas del clustering: inercia y tamaño de cada perfil de salud.
    try:
        kmeans = model.named_steps["kmeans"]
        labels = model.predict(x)
        sizes = pd.Series(labels).value_counts().sort_index().to_dict()
        log.info(
            "Clustering entrenado | inercia=%.1f | tamaños por cluster=%s",
            kmeans.inertia_,
            sizes,
        )
    except Exception as exc:  # noqa: BLE001 - las métricas no deben tumbar el pipeline
        log.warning("No se pudieron calcular las métricas de clustering: %s", exc)

    return model


def build_predictions(
    df: pd.DataFrame,
    risk_model: Pipeline,
    bioage_model: Pipeline,
    clustering_model: Pipeline,
    risk_params: dict,
    bioage_params: dict,
    clustering_params: dict,
) -> pd.DataFrame:
    """Aplica los tres modelos a cada persona y arma la tabla de predicciones.

    Genera un DataFrame (una fila por ``SEQN``) con la predicción del modelo de
    riesgo (clase y probabilidad), la del modelo de edad biológica (solo para
    adultos, incluyendo el *age gap*) y la etiqueta de perfil de salud asignada
    por el modelo de clustering. El resultado se persiste en la base de datos
    SQL del proyecto a través del catálogo (``model_predictions``).

    Args:
        df: DataFrame primario ``prm_cardiometabolic``.
        risk_model: Pipeline del modelo de riesgo entrenado.
        bioage_model: Pipeline del modelo de edad biológica entrenado.
        clustering_model: Pipeline del modelo de clustering entrenado.
        risk_params: parámetros del modelo de riesgo (usa ``features``).
        bioage_params: parámetros del modelo de edad biológica (``features``, ``min_age``).
        clustering_params: parámetros del modelo de clustering (usa ``features``).

    Returns:
        DataFrame con las predicciones por persona.
    """
    risk_features = risk_params["features"]
    bio_features = bioage_params["features"]
    cluster_features = clustering_params["features"]
    min_age = bioage_params.get("min_age", 18)

    out = pd.DataFrame({"SEQN": df["SEQN"].astype("int64"), "age": df["age"]})

    # --- Modelo 1: riesgo cardiometabólico ---
    x_risk = df[risk_features].apply(pd.to_numeric, errors="coerce")
    out["high_risk_proba"] = risk_model.predict_proba(x_risk)[:, 1].round(4)
    out["high_risk"] = (out["high_risk_proba"] >= 0.5).astype("int64")

    # --- Modelo 2: edad biológica (solo adultos; en menores queda nulo) ---
    x_bio = df[bio_features].apply(pd.to_numeric, errors="coerce")
    bio_pred = np.round(bioage_model.predict(x_bio), 1)
    is_adult = df["age"] >= min_age
    out["biological_age"] = np.where(is_adult, bio_pred, np.nan)
    out["age_gap"] = (out["biological_age"] - out["age"]).round(1)

    # --- Modelo 3: perfil de salud (clustering no supervisado, 0-3) ---
    x_cluster = df[cluster_features].apply(pd.to_numeric, errors="coerce")
    out["health_cluster"] = clustering_model.predict(x_cluster).astype("int64")

    log.info(
        "Predicciones generadas: %d personas | alto riesgo=%d | con edad biológica=%d | clusters=%d",
        len(out),
        int(out["high_risk"].sum()),
        int(out["biological_age"].notna().sum()),
        out["health_cluster"].nunique(),
    )
    return out


def store_models_in_db(
    risk_model: Pipeline,
    bioage_model: Pipeline,
    clustering_model: Pipeline,
    db_params: dict,
) -> dict:
    """Guarda los modelos serializados (pickle) como BLOB en la base de datos.

    Crea/reemplaza la tabla ``ml_models`` con una fila por modelo (nombre, fecha
    de entrenamiento, nº de features y el binario pickle). Permite versionar y
    recuperar el artefacto desde la propia base de datos del proyecto.

    Args:
        risk_model: Pipeline del modelo de riesgo entrenado.
        bioage_model: Pipeline del modelo de edad biológica entrenado.
        clustering_model: Pipeline del modelo de clustering entrenado.
        db_params: dict con la clave ``url`` (cadena de conexión SQLAlchemy).

    Returns:
        Resumen con los modelos almacenados (consumido como reporte en memoria).

    Raises:
        ValueError: si no se proporciona la URL de conexión a la base de datos.
    """
    # La variable de entorno DB_URL (Postgres en Docker) tiene prioridad.
    url = os.getenv("DB_URL") or db_params.get("url")
    if not url:
        raise ValueError("Falta la URL de la base de datos (DB_URL o params:db.url).")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []
    for name, model in (
        ("risk_model", risk_model),
        ("bioage_model", bioage_model),
        ("clustering_model", clustering_model),
    ):
        n_features = getattr(model.named_steps["imputer"], "n_features_in_", None)
        rows.append(
            {
                "name": name,
                "model_type": type(model.steps[-1][1]).__name__,
                "trained_at": now,
                "n_features": int(n_features) if n_features is not None else None,
                "model_blob": pickle.dumps(model),
            }
        )

    df = pd.DataFrame(rows)
    try:
        engine = create_engine(url)
        df.to_sql("ml_models", engine, if_exists="replace", index=False)
        log.info("Modelos guardados en la BD (tabla 'ml_models'): %s", [r["name"] for r in rows])
    except Exception as exc:  # noqa: BLE001 - el guardado en BD no debe tumbar el pipeline
        log.warning("No se pudieron guardar los modelos en la BD: %s", exc)

    return {"stored_models": [r["name"] for r in rows], "trained_at": now}
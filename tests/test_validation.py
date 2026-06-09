"""Tests de utilidades de validación."""

from __future__ import annotations

import pandas as pd
import pytest

from prueba.utils.validation import (
    SchemaValidationError,
    replace_missing_codes,
    validate_columns,
    validate_min_rows,
    validate_unique_key,
)


def test_validate_columns_ok():
    df = pd.DataFrame({"SEQN": [1], "x": [2]})
    assert validate_columns(df, ["SEQN", "x"], "t") is df


def test_validate_columns_missing():
    df = pd.DataFrame({"SEQN": [1]})
    with pytest.raises(SchemaValidationError):
        validate_columns(df, ["SEQN", "missing"], "t")


def test_validate_min_rows():
    df = pd.DataFrame({"a": [1, 2, 3]})
    validate_min_rows(df, 3, "t")
    with pytest.raises(SchemaValidationError):
        validate_min_rows(df, 4, "t")


def test_validate_unique_key():
    df = pd.DataFrame({"SEQN": [1, 2, 2]})
    with pytest.raises(SchemaValidationError):
        validate_unique_key(df, "SEQN", "t")


def test_replace_missing_codes():
    df = pd.DataFrame({"DIQ010": [1, 2, 9, 7777]})
    out = replace_missing_codes(df, ["DIQ010"])
    assert out["DIQ010"].isna().sum() == 2
    assert out["DIQ010"].tolist()[:2] == [1, 2]

import pandas as pd
import pytest

from support_classifier.data import clean_dataframe, validate_dataframe


def test_clean_and_validate_data():
    frame = pd.DataFrame(
        {
            "query": ["  hello   there ", "hello there", "change my pin", "cash please"],
            "intent": ["greeting", "greeting", "pin", "cash"],
        }
    )
    clean = clean_dataframe(frame)
    assert clean["query"].tolist()[0] == "hello there"
    assert len(clean) == 3
    report = validate_dataframe(clean, min_rows_per_class=1)
    assert report["classes"] == 3
    assert report["duplicates"] == 0


def test_missing_column_is_rejected():
    with pytest.raises(ValueError, match="Missing required columns"):
        clean_dataframe(pd.DataFrame({"query": ["hello"]}))


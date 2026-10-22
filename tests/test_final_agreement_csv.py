from pathlib import Path

import pytest

from lifecycle_mapper.reference import final_reference

ROOT = Path(__file__).resolve().parents[1]


def test_authoritative_csv_matches_current_export():
    labels = final_reference(ROOT / "data/final_agreement.csv")
    assert len(labels) == 100
    assert labels == final_reference(ROOT / "results/benchmark-100/workbook/final_agreement.csv")
    assert sum(len(value) for value in labels.values()) == 600


@pytest.mark.parametrize(
    "content",
    [
        "GitHub URL,Collection,Processing,Method,Experimentation,Evaluation,Dissemination\nhttps://github.com/a/b,1,0,1,0,1,2\n",
        "GitHub URL,Collection,Processing,Method,Experimentation,Evaluation,Dissemination\nhttps://github.com/a/b,1,0,1,0,1,0\nhttps://github.com/A/B,1,0,1,0,1,0\n",
        "GitHub URL,Collection,Processing,Method,Experimentation,Evaluation,Dissemination\nhttps://github.com/a/b,1,0\n",
    ],
)
def test_reject_invalid_authoritative_csv(tmp_path, content):
    path = tmp_path / "labels.csv"
    path.write_text(content)
    with pytest.raises(ValueError):
        final_reference(path)


def test_benchmark_execution_keeps_supplied_order():
    from lifecycle_mapper.corpus import selected_records

    labels = final_reference(ROOT / "data/final_agreement.csv")
    records = selected_records(ROOT / "data/corpus/benchmark_100.txt", None, "unused", 0, 1)
    assert [r["url"].removeprefix("https://github.com/").casefold() for r in records] == list(
        labels
    )
    assert records[0]["url"].casefold().endswith("mspeich/forhytm")

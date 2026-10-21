from pathlib import Path

import pytest

from lifecycle_mapper.reference import final_reference
from lifecycle_mapper.dataset import dataset_reference
from lifecycle_mapper.canonical import read_json

ROOT = Path(__file__).resolve().parents[1]


def test_authoritative_csv_matches_workbook_and_dataset():
    labels = final_reference(ROOT / "data/final_agreement.csv")
    assert len(labels) == 100
    assert labels == final_reference(ROOT / "data/research_lifecycle_benchmark_100_msr27.xlsx")
    assert labels == {
        key.casefold(): value
        for key, value in dataset_reference(
            read_json(ROOT / "data/research_lifecycle_benchmark_100_msr27.json")
        ).items()
    }
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

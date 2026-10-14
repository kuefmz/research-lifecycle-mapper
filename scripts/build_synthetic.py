"""Generate clearly marked synthetic fixtures, never human benchmark labels."""

from pathlib import Path

from lifecycle_mapper import STAGES
from lifecycle_mapper.acquisition import POLICY_VERSION, source_kind
from lifecycle_mapper.canonical import sha256, write_json

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "benchmark/synthetic"
DOCS = [
    "We collect raw research data from sensors.",
    "We clean the research dataset before analysis.",
    "We implement the proposed algorithm.",
    "We run controlled experiments.",
    "We evaluate predictive performance against a baseline.",
    "We deposit research dataset on Zenodo with a DOI.",
]
CODE = """def collect_research_data():
    return requests.get("https://example.invalid/research")

def clean_research_dataset(data):
    return data.dropna()

def fit_statistical_model(objective):
    return minimize(objective)

def run_controlled_experiments():
    for seed in trial_seeds:
        run_trial(seed)

def evaluate_research_predictions(ground_truth, predictions):
    return f1_score(ground_truth, predictions)

def deposit_research_dataset(dataset):
    return zenodo.deposit(dataset)
"""
NEGATIVE = """import requests
def main():
    return requests.get("https://example.invalid/health")
def parse_configuration(text):
    return text.split(",")
"""


def build() -> None:
    specifications = [
        ("docs-positive", {"README.md": "\n".join(DOCS) + "\n"}, list(STAGES), False),
        ("code-positive", {"src/methods.py": CODE}, list(STAGES), False),
        (
            "generic-negative",
            {
                "README.md": "Install this library with pip. Unit tests verify behavior.\n",
                "src/run.py": NEGATIVE,
                "requirements.txt": "requests\n",
            },
            [],
            False,
        ),
        (
            "excluded-negative",
            {
                "docs/roadmap.md": "\n".join("Future work: " + line for line in DOCS) + "\n",
                "tests/test_research.py": CODE,
            },
            [],
            False,
        ),
        ("incomplete", {"src/methods.py": CODE}, list(STAGES), True),
    ]
    repositories = []
    for name, contents, labels, incomplete in specifications:
        repo = "synthetic/" + name
        commit = sha256(repo.encode())[
            :40
        ]  # Explicit synthetic identity, never an actual Git commit.
        root = BASE / "snapshots" / name
        files = []
        for path, content in sorted(contents.items()):
            data = content.encode()
            source, reason = source_kind(path)
            record = {
                "path": path,
                "size": len(data),
                "source": source,
                "mode": "100644",
                "git_blob_sha": None,
                "status": "captured" if source else "excluded",
                "reason": reason,
                "sha256": sha256(data) if source else None,
            }
            if source:
                target = root / "content" / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            files.append(record)
        if incomplete:
            files.insert(
                0,
                {
                    "path": "README.md",
                    "size": 100,
                    "source": "documentation",
                    "mode": "100644",
                    "git_blob_sha": None,
                    "status": "unavailable",
                    "reason": "synthetic-download-error",
                    "sha256": None,
                },
            )
        snapshot = {
            "schema_version": 1,
            "repository": repo,
            "source_url": "https://github.com/" + repo,
            "commit": commit,
            "tree_sha": None,
            "inventory_complete": True,
            "policy_version": POLICY_VERSION,
            "max_bytes": 250000,
            "redistribution": "synthetic-original-test-content",
            "synthetic": True,
            "files": files,
        }
        write_json(root / "manifest.json", snapshot)
        repositories.append(
            {
                "repository": repo,
                "commit": commit,
                "snapshot": "snapshots/" + name,
                "snapshot_sha256": sha256((root / "manifest.json").read_bytes()),
                "labels": {stage: int(stage in labels) for stage in STAGES},
            }
        )
    write_json(
        BASE / "manifest.json",
        {
            "schema_version": 1,
            "status": "approved",
            "kind": "synthetic",
            "version": "synthetic-v1",
            "codebook_version": "candidate-synthetic-v1",
            "stages": list(STAGES),
            "repositories": repositories,
            "approval_scope": "software-test-fixture-only",
        },
    )


if __name__ == "__main__":
    build()

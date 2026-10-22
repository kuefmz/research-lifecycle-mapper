"""Generate the paper selection funnel from versioned counts.

Run with Matplotlib 3.10.8; see figures/README.md for provenance and verification.
"""

import argparse
import json
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, default=ROOT / "figures")
parser.add_argument("--full-summary", type=Path)
parser.add_argument("--filtered-summary", type=Path)
args = parser.parse_args()
OUT = args.output
OUT.mkdir(parents=True, exist_ok=True)
source = json.loads((ROOT / "figures/openaire_funnel_counts.json").read_text())
COUNTS = source["counts"]
for path, mapping in (
    (
        args.full_summary,
        {
            "software_records": "total",
            "records_with_repository_field": "repo_fields",
            "github_record_links": "github_links",
            "unique_github_repositories": "all_unique",
        },
    ),
    (
        args.filtered_summary,
        {
            "records_with_description_text": "descriptions",
            "records_matching_description": "experiment",
            "selected_records_with_repository_field": "intersection_records",
            "github_record_links": "intersection_links",
            "unique_github_repositories": "unique_experiment",
        },
    ),
):
    if path is not None:
        summary = json.loads(path.read_text())
        if summary["source_tar_sha256"] != source["source_tar_sha256"]:
            raise ValueError("Archive hash differs from the paper source")
        for field, key in mapping.items():
            if summary["counts"][field] != COUNTS[key]:
                raise ValueError(f"Funnel mismatch: {field}")
matplotlib.rcParams["svg.hashsalt"] = "openaire-paper-funnel"
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["svg.fonttype"] = "none"
COLORS = dict(
    navy="#172d4b",
    muted="#62758d",
    line="#8296aa",
    blue="#165eac",
    blue_bg="#eaf4ff",
    blue_edge="#93c2f3",
    green="#087b57",
    green_bg="#e9f8f0",
    green_edge="#95d9b4",
    purple="#673ab0",
    purple_bg="#f3edfc",
    purple_edge="#c7b0ee",
    orange="#bd6019",
    orange_bg="#fff3e9",
    orange_edge="#f1bb8d",
    source_bg="#f3f6fa",
    source_edge="#a9b9ce",
)
TEXT = dict(
    title="OpenAIRE software corpus",
    subtitle="Parallel selection by experimental context and GitHub availability",
    a="A  ·  EXPERIMENTAL CONTEXT",
    b="B  ·  GITHUB AVAILABILITY",
    c="VERIFIED REPOSITORY CONTAINMENT",
)
# Layout in 0..100 horizontal units; box positions: x, bottom y, width, height.
BOXES = dict(
    source=(32, 86, 36, 11),
    description=(6, 64, 40, 12),
    fields=(54, 64, 40, 12),
    experiment=(6, 44, 40, 13),
    links=(54, 44, 40, 13),
    intersection=(29, 29, 42, 10),
    unique=(29, 16, 42, 10),
    publication=(29, 2, 42, 9),
    benchmark=(31, -11, 38, 9),
)

fig, ax = plt.subplots(figsize=(14, 14.7))
fig.patch.set_facecolor("white")
ax.set_xlim(0, 100)
ax.set_ylim(-19, 106)
ax.axis("off")


def panel(key, label, count, unit, family, *, label_font=12, number_font=25):
    x, y, w, h = BOXES[key]
    bg = COLORS.get(f"{family}_bg", "#ffffff")
    edge = COLORS.get(f"{family}_edge", "#cccccc")
    accent = COLORS[family] if family in COLORS else COLORS["navy"]
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.45,rounding_size=1.5",
            facecolor=bg,
            edgecolor=edge,
            linewidth=1.3,
            zorder=3,
        )
    )
    cx = x + w / 2
    ax.text(
        cx,
        y + h - 1.6,
        label,
        ha="center",
        va="top",
        color=COLORS["navy"],
        weight="semibold",
        fontsize=label_font,
        zorder=4,
        linespacing=1.15,
    )
    ax.text(
        cx,
        y + h / 2 - 0.7,
        f"{count:,}",
        ha="center",
        va="center",
        color=accent,
        weight="bold",
        fontsize=number_font,
        zorder=4,
    )
    ax.text(
        cx, y + 1.0, unit, ha="center", va="bottom", color=COLORS["muted"], fontsize=10.5, zorder=4
    )


def segment(a, b, color="line", dashed=False, arrowhead=False):
    col = COLORS[color]
    if arrowhead:
        ax.add_patch(
            FancyArrowPatch(
                a,
                b,
                arrowstyle="-|>",
                mutation_scale=16,
                lw=1.7,
                color=col,
                linestyle=(0, (4, 3)) if dashed else "-",
                zorder=1,
            )
        )
    else:
        ax.plot(
            [a[0], b[0]],
            [a[1], b[1]],
            color=col,
            lw=1.7,
            ls=(0, (4, 3)) if dashed else "-",
            zorder=1,
        )


def arrow_label(x, y, label, color, fontsize=11.5):
    # Labels sit directly beside/on the connector with a white text backing,
    # not in separate colored boxes.
    ax.text(
        x,
        y,
        label,
        ha="center",
        va="center",
        fontsize=fontsize,
        color=COLORS[color],
        weight="bold",
        zorder=5,
        bbox=dict(facecolor="white", edgecolor="none", pad=2.5),
    )


ax.text(
    50,
    103,
    TEXT["title"],
    ha="center",
    va="center",
    fontsize=24,
    color=COLORS["navy"],
    weight="bold",
)
ax.text(50, 99.9, TEXT["subtitle"], ha="center", va="center", fontsize=11.2, color=COLORS["muted"])

panel(
    "source",
    "OpenAIRE software records",
    COUNTS["total"],
    "Zenodo record: 20428976",
    "source",
    number_font=29,
)
# Split into parallel branches, with A and B positioned as labels ON arrows.
segment((50, 86), (50, 82))
segment((26, 82), (74, 82))
segment((26, 82), (26, 76.8), color="blue", arrowhead=True)
segment((74, 82), (74, 76.8), color="green", arrowhead=True)
arrow_label(26, 79.5, TEXT["a"], "blue", fontsize=10.5)
arrow_label(74, 79.5, TEXT["b"], "green", fontsize=10.5)

panel(
    "description",
    "Records with description text",
    COUNTS["descriptions"],
    "software records",
    "blue",
)
panel(
    "fields", "Records with a repository field", COUNTS["repo_fields"], "software records", "green"
)
segment((26, 64), (26, 57.8), "blue", arrowhead=True)
segment((74, 64), (74, 57.8), "green", arrowhead=True)
panel(
    "experiment",
    "Mention “experiment” or “experiments”\nin the description",
    COUNTS["experiment"],
    "software records",
    "blue",
    label_font=11.5,
)
panel(
    "links",
    "Valid GitHub links",
    COUNTS["github_links"],
    f"links; {COUNTS['all_unique']:,} unique repositories",
    "green",
)
# Two branches converge into their intersection.
segment((26, 44), (26, 41))
segment((74, 44), (74, 41))
segment((26, 41), (50, 41))
segment((74, 41), (50, 41))
segment((50, 41), (50, 39.6), arrowhead=True)
panel(
    "intersection",
    "INTERSECTION  ·  EXPERIMENT + GITHUB",
    COUNTS["intersection_links"],
    f"valid GitHub links  ·  {COUNTS['intersection_records']:,} records with repository fields",
    "purple",
    label_font=11.5,
)
segment((50, 29), (50, 26.7), arrowhead=True)
panel(
    "unique",
    "After deduplication",
    COUNTS["unique_experiment"],
    "unique GitHub repositories",
    "purple",
)
# Repository containment is verified; the publication-selection query is unavailable.
segment((50, 16), (50, 11.8), "orange", arrowhead=True)
arrow_label(50, 13.9, TEXT["c"], "orange", fontsize=10.7)
panel(
    "publication",
    "Publication-associated repositories",
    COUNTS["publication"],
    "supplied publication associations",
    "orange",
)
segment((50, 2), (50, -1.4), "orange", arrowhead=True)
panel("benchmark", "Manually annotated benchmark", COUNTS["benchmark"], "repositories", "orange")
ax.text(
    50,
    -14.0,
    f"Remaining {COUNTS['additional']:,} repositories: additional repository analysis",
    ha="center",
    fontsize=10.5,
    color=COLORS["muted"],
)
ax.text(
    50,
    -17.2,
    f"Other {COUNTS['remainder']:,} repositories complete the 3,211 corpus; publication-selection query not reconstructed.",
    ha="center",
    fontsize=9.4,
    color=COLORS["muted"],
)

fig.subplots_adjust(left=0.035, right=0.965, top=0.985, bottom=0.025)
fig.savefig(
    OUT / "openaire_funnel.pdf",
    facecolor="white",
    metadata={"Creator": "Research Lifecycle Mapper", "CreationDate": None, "ModDate": None},
)
fig.savefig(
    OUT / "openaire_funnel.svg",
    facecolor="white",
    metadata={"Date": None, "Creator": "Research Lifecycle Mapper"},
)
plt.close(fig)
print("Saved:", OUT / "openaire_funnel.pdf")

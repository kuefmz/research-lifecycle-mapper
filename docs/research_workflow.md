# Research workflow implemented by this artifact

The repository supports the six research activities below. The workflow is inspectable in executable code, input tables, dated comparisons and reproduction commands. The full OpenAIRE corpus experiment is a separate run whose completion must be reported from its actual outputs.

## Collection

We acquire research observations from software metadata and repository files. The OpenAIRE extractor streams software records from software.tar, and the acquisition modules collect repository documentation and implementation artifacts at one resolved commit. Source release IDs, archive checksums and snapshot inventories identify the collected inputs.

## Processing

We preprocess the research data by normalizing GitHub repository identifiers, rejecting invalid links, deduplicating identities and converting the annotation workbook to machine-readable reference tables. File inventories distinguish captured, excluded and unavailable content. These transformations are implemented in openaire.py, batch.py, dataset.py and reference.py.

## Method

We implement a deterministic classification algorithm that maps contextual repository evidence to six independent research-lifecycle labels. Versioned rule catalogs and source-specific matching routines define the model. analysis.py and documentation.py preserve matching excerpts, physical line locations, stable occurrence identities and rule attributions.

## Experimentation

The experimental workflow compares documentation-only, code-only and combined evidence modes on captured repositories. The dated implementation report records the earlier development and operational test comparisons and their limitations. The corpus runner executes the same frozen method over selected repositories, with checkpoints and fixed acquisition parameters. New main/master-policy experiments must retain their own completed-run manifests.

## Evaluation

We evaluate classification predictions against jointly adjudicated documentation reference labels using per-stage precision, recall, F1 and confusion counts. Complete-case coverage, constant baselines and repository-level bootstrap intervals accompany the new documentation summary. Independent reviewer agreement and final adjudication remain distinct. Code evidence receives a separate human review rather than being treated as documentation gold.

## Dissemination

We distribute research outputs through the source artifact: annotated tables, the all-sheet anonymous workbook, method implementation, versioned rules, dated aggregate results and instructions to reproduce the experiments. Generated run outputs are retained under data/. The anonymous review mirror and preserved DOI release are publication steps whose availability must be stated truthfully; a planned DOI is not an issued DOI.

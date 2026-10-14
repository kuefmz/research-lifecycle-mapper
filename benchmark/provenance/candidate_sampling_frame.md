# Documented upstream corpus — sample relationship unverified

Inspected source documentation at commit `dfb22f9545860a99a57199975dd78a4d9cb80fea`:

https://github.com/kuefmz/research_artefacts_and_processes/blob/dfb22f9545860a99a57199975dd78a4d9cb80fea/data/openaire_zenodo_12819872/summary.json

The upstream summary reports an OpenAIRE software archive from Zenodo record https://zenodo.org/records/12819872, named `software.tar`, size 122337280 bytes, SHA-256 `e4d47e3ff113cc324446634a1fb60090b44044a8395b2e374f77eadddc74378e`.

The compiler reads software JSON records, uses `codeRepositoryUrl`, filters valid GitHub-host repository references, normalizes to owner/repository URLs, and deduplicates repository identities case-insensitively while retaining linked OpenAIRE records. The summary reports 375072 software records, 119246 records with code repository URLs, 112467 GitHub record links and 105516 unique GitHub repositories. Its repository-level CSV hash is reported as `2ea95bb4ba8eef3e4324897bfa927f6bbbb1f77805259e1fb922fa90e1ae80b7`.

These are values read from the upstream documentation, **not counts or checksums independently regenerated here**. The archive and CSVs are not redistributed in this project. The upstream annotations README explicitly separates manual labels and describes a future validation sample. Its README's random batch defaults do not establish the actual human sample's selection strategy or inclusion criteria.

To approve sampling provenance, supply the source frame version/checksum actually used, exact sample list, selection procedure/seed if applicable, exclusions, sample dates, historical repository revisions and any restrictions. Until then this is a candidate frame note, not approved benchmark sampling documentation; do not set `sampling_verified` based on this note alone.

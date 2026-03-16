# Portal Data Models

Unified, standards-compliant data models for phenotypes and other entities used across the [A2F Knowledge Portal](https://a2f.hugeamp.org/) and related Flannick Lab resources.

**[Browse the phenotype mappings interactively](https://akleao.com/preview/561bd3b1-8308-43f2-a9af-4deae461c61b)**

## What's in here

Each phenotype in the portal gets:

- A **stable numeric ID** (`PORTAL:0000001` through `PORTAL:0006982`)
- A **trait type classification** (disease, measurement, interaction, stratified, adjusted, etc.)
- **Cross-ontology mappings** to EFO, MESH, MONDO, HP, DOID, ORPHANET, CHEBI, OBA, CMO, and ICD10CM
- A **SKOS predicate** for each mapping (`exactMatch`, `broadMatch`, `closeMatch`, `narrowMatch`, `relatedMatch`)
- A **confidence score** and **provenance** for every mapping

Output is a [LinkML](https://linkml.io/) schema with data conforming to the [SSSOM](https://mapping-commons.github.io/sssom/) specification.

## Quick start

```bash
# Install dependencies
uv sync

# Generate v0.0.1 from source files (~5 min first run)
./scripts/phenotype/v0.0.1/generate.sh

# Fast rebuild (skip OWL parsing + API calls)
./scripts/phenotype/v0.0.1/generate.sh --skip-owl --skip-api
```

Output lands in `versions/phenotype/v0.0.1/`.

## Repository structure

```
portal-data-models/
├── schemas/phenotype/
│   └── portal_phenotype.yaml              # LinkML schema definition
│
├── scripts/phenotype/
│   └── v0.0.1/                            # Scripts that generate v0.0.1
│       ├── generate.sh                    # Single entry point
│       ├── 01_parse_sources.py            # Parse raw source files
│       ├── 02_parse_efo_xrefs.py          # Extract OWL cross-references
│       ├── 03_enrich.py                   # Enrichment pipeline (7 phases)
│       ├── 04_generate_output.py          # Assign IDs, write versioned output
│       └── 05_quality_report.py           # Coverage report
│
├── raw/phenotype/                         # Source data (read-only, do not modify)
│   ├── Phenotypes.tsv                     # 6,982 phenotypes (master registry)
│   ├── portal_to_mesh_curated_collected.tsv
│   ├── amp-traits-mapping-portal-phenotypes_06262024.csv
│   ├── gcat_v1.0.3.1.tsv                 # GWAS Catalog studies
│   ├── efo.owl                            # EFO ontology (330 MB, Git LFS)
│   ├── ORDO_en_4.5.owl                   # Orphanet ontology (45 MB, Git LFS)
│   └── mondo_mappings/                    # MONDO→ICD10CM SSSOM files
│
├── data/phenotype/                        # Intermediate files (gitignored)
│
├── versions/phenotype/                    # Versioned output (checked into git)
│   └── v0.0.1/
│       ├── portal_phenotypes.yaml
│       ├── portal_phenotype_mappings.sssom.tsv
│       ├── portal_phenotype_registry.tsv
│       └── mapping_coverage.md
│
├── .env                                   # API keys (optional, gitignored)
└── pyproject.toml
```

## Versioning philosophy

Every version is **fully reproducible** from its scripts and inputs.

### How versions work

Each version has its own scripts directory (`scripts/phenotype/v{X.Y.Z}/`) and output directory (`versions/phenotype/v{X.Y.Z}/`). This creates a complete chain of provenance:

- **v0.0.1** — the base version. Generated entirely from raw source files (`raw/phenotype/`). Running `scripts/phenotype/v0.0.1/generate.sh` always produces the same output. This is the automated baseline.

- **v0.0.2, v0.0.3, ...** — refinement versions. Each builds on the *previous version's output* as its starting point (e.g., v0.0.2 reads `versions/phenotype/v0.0.1/portal_phenotypes.yaml`). Scripts in these versions make targeted corrections: fixing bad mappings, adding missing ones, updating predicates, etc.

- **v0.1.0, v1.0.0, ...** — major versions for schema changes, new source data, or significant re-curation.

### Creating a new version

1. **Create the scripts directory:**
   ```bash
   mkdir -p scripts/phenotype/v0.0.2
   ```

2. **Write scripts that transform the previous version's output.** Your scripts should:
   - Read from `versions/phenotype/v0.0.1/portal_phenotypes.yaml` (or the SSSOM/JSON)
   - Apply specific, documented changes (fix mappings, add new ones, etc.)
   - Write to `versions/phenotype/v0.0.2/`

   Example script structure:
   ```python
   # scripts/phenotype/v0.0.2/01_fix_mappings.py
   """Fix specific mapping issues identified in v0.0.1 review."""

   # Read v0.0.1 output
   with open(VERSIONS / "v0.0.1" / "portal_phenotypes.yaml") as f:
       data = yaml.safe_load(f)

   # Apply corrections
   for pheno in data["phenotypes"]:
       if pheno["portal_id"] == "PORTAL:0000042":
           # Fix: AF was mapped to wrong MeSH term
           ...

   # Write v0.0.2 output
   ```

3. **Include a `generate.sh`** that runs all scripts in order:
   ```bash
   #!/usr/bin/env bash
   # Generate v0.0.2 from v0.0.1 + corrections
   set -euo pipefail
   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
   REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
   cd "$REPO_ROOT"

   uv run python scripts/phenotype/v0.0.2/01_fix_mappings.py
   uv run python scripts/phenotype/v0.0.2/02_add_icd_codes.py
   # ... etc
   ```

4. **Commit everything** — scripts, output, and quality report:
   ```bash
   git add scripts/phenotype/v0.0.2/ versions/phenotype/v0.0.2/
   git commit -m "Phenotype mappings v0.0.2: fix AF mapping, add ICD codes"
   ```

### Version provenance chain

```
raw/phenotype/*  ──→  scripts/v0.0.1/  ──→  versions/v0.0.1/
                                                    │
                                                    ▼
                      scripts/v0.0.2/  ──→  versions/v0.0.2/
                                                    │
                                                    ▼
                      scripts/v0.0.3/  ──→  versions/v0.0.3/
```

Anyone can verify any version by running its scripts. v0.0.1 regenerates from source. v0.0.2 regenerates from v0.0.1's output. And so on.

## v0.0.1 pipeline

The base version runs 5 steps via `generate.sh`:

| Step | Script | What it does | Time |
|------|--------|-------------|------|
| 1 | `01_parse_sources.py` | Parse Phenotypes.tsv, MeSH mappings, AMP/EFO mappings, GWAS Catalog, Orphanet IDs | ~5s |
| 2 | `02_parse_efo_xrefs.py` | Extract cross-references from EFO and ORDO OWL files | ~75s |
| 3 | `03_enrich.py` | 7-phase enrichment: xref expansion, OLS API, GWAS Catalog, broad EFO, ICD10CM chaining, label backfill, validation | ~4 min |
| 4 | `04_generate_output.py` | Assign PORTAL IDs, generate SSSOM + YAML + registry | ~5s |
| 5 | `05_quality_report.py` | Generate mapping coverage report | ~2s |

Flags: `--skip-owl` reuses cached OWL cross-references. `--skip-api` skips OLS/OMIM API calls.

## v0.0.1 coverage

| Target | Result |
|--------|--------|
| >90% portal phenotypes mapped to EFO/MONDO/MESH | 100% |
| >95% rare disease phenotypes mapped to ORPHANET | 100% |
| >80% GWAS Catalog traits mapped to EFO | 100% |

## Manual review workflow

To review mappings in a spreadsheet and create a corrected version:

```bash
# 1. Export review spreadsheet from current data
uv run python scripts/phenotype/v0.0.1/09_export_review_table.py

# 2. Open data/phenotype/review_mappings.tsv in Excel/Google Sheets
#    Flag issues in the "flag" column: remove, broad, narrow, close, related, exact
#    Save the file

# 3. Apply your flags
uv run python scripts/phenotype/v0.0.1/10_apply_review.py

# 4. Generate a new version
uv run python scripts/phenotype/v0.0.1/04_generate_output.py --version 0.0.2
uv run python scripts/phenotype/v0.0.1/05_quality_report.py --version 0.0.2
```

## Contributing

1. **Found a bad mapping?** Open an issue with the phenotype name, the wrong mapping, and what the correct one should be.

2. **Want to fix mappings?** Create a new version with correction scripts (see [Creating a new version](#creating-a-new-version)), then open a PR.

3. **Adding a new data model?** Create subdirectories under `schemas/`, `scripts/`, `raw/`, and `versions/` (e.g., `schemas/variant/`). Follow the phenotype pattern.

### PR checklist

- [ ] Scripts in `scripts/phenotype/v{X.Y.Z}/` with a `generate.sh`
- [ ] Output in `versions/phenotype/v{X.Y.Z}/` with all files
- [ ] Quality report shows all targets passing
- [ ] No invalid target IDs (`MESH:none`, etc.)
- [ ] All ontology prefixes are uppercase (`MESH`, `ORPHANET`, not `MeSH`, `Orphanet`)

## Git LFS

Large source files are stored with [Git LFS](https://git-lfs.github.com/).

```bash
# Install (macOS)
brew install git-lfs

# After cloning
git lfs install
git lfs pull
```

Tracked: `raw/**/*.owl`, `raw/**/*.tsv` (see `.gitattributes`).

## Dependencies

Install with `uv sync`. Key packages: `linkml`, `rdflib`, `pandas`, `aiohttp`, `python-dotenv`.

## Optional: OMIM labels

Create `.env` at repo root with `OMIM_API_KEY=your_key_here` ([get one](https://omim.org/api)). Without it, OMIM mappings are included but without labels.

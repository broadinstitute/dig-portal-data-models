#!/usr/bin/env bash
# Generate portal phenotype data model from source files.
#
# Usage:
#   ./scripts/phenotype/generate.sh              # full pipeline, outputs v0.0.1
#   ./scripts/phenotype/generate.sh --version 0.0.2  # custom version
#   ./scripts/phenotype/generate.sh --skip-owl    # skip OWL parsing (uses cached xrefs)
#   ./scripts/phenotype/generate.sh --skip-api    # skip OLS/OMIM API calls
#
# Pipeline:
#   01_parse_sources.py     — parse raw source files
#   02_parse_efo_xrefs.py   — extract cross-references from EFO/ORDO OWL
#   03_enrich.py            — OLS API + GWAS Catalog + xref expansion + labels + validation
#   04_generate_output.py   — assign PORTAL IDs, write versioned SSSOM + YAML
#   05_quality_report.py    — generate coverage report

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

VERSION="0.0.1"
SKIP_OWL=false
SKIP_API=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --version) VERSION="$2"; shift 2 ;;
        --skip-owl) SKIP_OWL=true; shift ;;
        --skip-api) SKIP_API=true; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

echo "============================================"
echo "Portal Phenotype Data Model — v${VERSION}"
echo "============================================"
echo ""

# Step 1: Parse sources
echo ">>> Step 1: Parsing source files..."
uv run python scripts/phenotype/v0.0.1/01_parse_sources.py
echo ""

# Step 2: Parse OWL cross-references (slow — ~75s)
XREF_FILE="data/phenotype/02_ontology_xref_table.tsv"
if [ "$SKIP_OWL" = true ] && [ -f "$XREF_FILE" ]; then
    echo ">>> Step 2: Skipping OWL parsing (using cached $XREF_FILE)"
else
    echo ">>> Step 2: Parsing EFO/ORDO OWL files (this takes ~75 seconds)..."
    uv run python scripts/phenotype/v0.0.1/02_parse_efo_xrefs.py
fi
echo ""

# Step 3: Enrich mappings
if [ "$SKIP_API" = true ]; then
    echo ">>> Step 3: Enriching mappings (API calls skipped)..."
    uv run python scripts/phenotype/v0.0.1/03_enrich.py --skip-api
else
    echo ">>> Step 3: Enriching mappings (OLS API + GWAS Catalog + labels)..."
    uv run python scripts/phenotype/v0.0.1/03_enrich.py
fi
echo ""

# Step 4: Generate versioned output
echo ">>> Step 4: Generating v${VERSION} output..."
uv run python scripts/phenotype/v0.0.1/04_generate_output.py --version "$VERSION"
echo ""

# Step 5: Quality report
echo ">>> Step 5: Quality report..."
uv run python scripts/phenotype/v0.0.1/05_quality_report.py --version "$VERSION"
echo ""

echo "============================================"
echo "Done! Output in versions/phenotype/v${VERSION}/"
echo "============================================"
echo ""
echo "Files:"
ls -la "versions/phenotype/v${VERSION}/" 2>/dev/null || echo "  (no output yet)"

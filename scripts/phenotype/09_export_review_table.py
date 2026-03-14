#!/usr/bin/env python3
"""Export all mappings as a review-friendly TSV for manual curation.

Each row = one mapping. Columns are designed for spreadsheet review:
  - Phenotype context (name, group, trait type)
  - Mapping details (target ID, label, ontology, predicate, confidence)
  - Empty `flag` and `notes` columns for the reviewer to fill in

Reviewer workflow:
  1. Open the TSV in Excel/Google Sheets
  2. Sort/filter by display_group, ontology, predicate, etc.
  3. In the `flag` column, mark issues:
       "remove"      → delete this mapping entirely
       "broad"       → change predicate to skos:broadMatch
       "narrow"      → change predicate to skos:narrowMatch
       "related"     → change predicate to skos:relatedMatch
       "close"       → change predicate to skos:closeMatch
       "exact"       → upgrade to skos:exactMatch
       "wrong_label" → label needs correction (put correct label in notes)
       (leave blank for mappings that look fine)
  4. Save the file
  5. Run 10_apply_review.py to apply the flags

Writes:
  - data/phenotype/review_mappings.tsv
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data" / "phenotype"


def main():
    print("Exporting review table\n")

    with open(DATA / "03_ols_enriched_mappings.json") as f:
        records = json.load(f)

    # Sort by display_group, then phenotype name for easier review
    records.sort(key=lambda r: (r.get("display_group", ""), r.get("phenotype_name", "")))

    fieldnames = [
        "row_id",
        "display_group",
        "phenotype",
        "phenotype_name",
        "trait_type",
        "target_id",
        "target_label",
        "target_ontology",
        "mapping_predicate",
        "confidence",
        "mapping_justification",
        "source",
        "flag",
        "notes",
    ]

    output_path = DATA / "review_mappings.tsv"
    row_id = 0
    total_mappings = 0

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()

        for r in records:
            for m in r.get("mappings", []):
                row_id += 1
                total_mappings += 1
                writer.writerow({
                    "row_id": row_id,
                    "display_group": r.get("display_group", ""),
                    "phenotype": r["phenotype"],
                    "phenotype_name": r["phenotype_name"],
                    "trait_type": r["trait_type"],
                    "target_id": m.get("target_id", ""),
                    "target_label": m.get("target_label", ""),
                    "target_ontology": m.get("target_ontology", ""),
                    "mapping_predicate": m.get("mapping_predicate", ""),
                    "confidence": m.get("confidence", ""),
                    "mapping_justification": m.get("mapping_justification", ""),
                    "source": m.get("source", ""),
                    "flag": "",
                    "notes": "",
                })

    print(f"Wrote {total_mappings} mappings to {output_path}")
    print(f"\nOpen in Excel/Google Sheets and fill the 'flag' column:")
    print(f"  remove  → delete this mapping")
    print(f"  broad   → change to skos:broadMatch")
    print(f"  narrow  → change to skos:narrowMatch")
    print(f"  related → change to skos:relatedMatch")
    print(f"  close   → change to skos:closeMatch")
    print(f"  exact   → upgrade to skos:exactMatch")
    print(f"  (blank) → mapping is fine, keep as-is")
    print(f"\nThen run: uv run python scripts/phenotype/10_apply_review.py")


if __name__ == "__main__":
    main()

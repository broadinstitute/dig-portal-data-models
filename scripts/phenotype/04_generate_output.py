#!/usr/bin/env python3
"""Step 4: Assign stable PORTAL IDs and generate versioned output files.

Reads:
  - data/phenotype/03_ols_enriched_mappings.json

Writes (into data/phenotype/v{VERSION}/):
  - portal_phenotype_registry.tsv — the ID registry
  - portal_phenotype_mappings.sssom.tsv — SSSOM mapping set
  - portal_phenotypes.yaml — LinkML instance data

The base version generated from source files is always v0.0.1.
Subsequent manual curation versions increment from there.

Usage:
  python 04_generate_output.py              # generates v0.0.1
  python 04_generate_output.py --version 0.0.2  # generates v0.0.2

Dependencies: pyyaml
"""
import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data" / "phenotype"

JUSTIFICATION_TO_SEMAPV = {
    "manual_curation": "semapv:ManualMappingCuration",
    "lexical_match": "semapv:LexicalMatching",
    "cross_reference": "semapv:MappingByLogicalReasoning",
    "semantic_similarity": "semapv:SemanticSimilarityThresholdMatching",
    "gwas_catalog": "semapv:MappingByLogicalReasoning",
    "inherited": "semapv:ManualMappingCuration",
}


def load_input(input_path: Path | None = None) -> list[dict]:
    """Load enriched data."""
    if input_path and input_path.exists():
        print(f"  Loading from {input_path}")
        with open(input_path) as f:
            return json.load(f)

    default = DATA / "03_ols_enriched_mappings.json"
    if default.exists():
        print(f"  Loading from {default}")
        with open(default) as f:
            return json.load(f)

    print("ERROR: No input data found. Run Steps 1-3 first.")
    sys.exit(1)


def assign_portal_ids(records: list[dict]) -> list[dict]:
    group_order = {"portal": 0, "gcat_trait": 1, "rare_v2": 2}
    records.sort(
        key=lambda r: (
            group_order.get(r["trait_group"], 9),
            r.get("display_group", ""),
            r.get("phenotype", ""),
        )
    )
    for i, record in enumerate(records, start=1):
        record["portal_id"] = f"PORTAL:{i:07d}"
    return records


def select_primary_mapping(mappings: list[dict]) -> dict | None:
    if not mappings:
        return None
    ontology_priority = {"EFO": 0, "MONDO": 1, "MESH": 2, "HP": 3, "DOID": 4, "ORPHANET": 5}
    predicate_priority = {
        "skos:exactMatch": 0,
        "skos:closeMatch": 1,
        "skos:broadMatch": 2,
        "skos:narrowMatch": 3,
        "skos:relatedMatch": 4,
    }

    def score(m):
        return (
            predicate_priority.get(m.get("mapping_predicate", ""), 9),
            -m.get("confidence", 0),
            ontology_priority.get(m.get("target_ontology", ""), 9),
        )

    return min(mappings, key=score)


def generate_registry(records: list[dict], output_path: Path):
    fieldnames = [
        "portal_id", "legacy_trait_group", "legacy_phenotype_id",
        "phenotype_name", "display_group", "trait_type",
    ]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for r in records:
            writer.writerow({
                "portal_id": r["portal_id"],
                "legacy_trait_group": r["trait_group"],
                "legacy_phenotype_id": r["phenotype"],
                "phenotype_name": r["phenotype_name"],
                "display_group": r.get("display_group", ""),
                "trait_type": r["trait_type"],
            })
    print(f"  Wrote registry: {output_path} ({len(records)} entries)")


def generate_sssom(records: list[dict], output_path: Path, version: str):
    today = date.today().isoformat()
    header_lines = [
        "# curie_map:",
        "#   PORTAL: https://kp.a2f.org/phenotype/",
        "#   EFO: http://www.ebi.ac.uk/efo/EFO_",
        "#   MESH: http://id.nlm.nih.gov/mesh/",
        "#   MONDO: http://purl.obolibrary.org/obo/MONDO_",
        "#   HP: http://purl.obolibrary.org/obo/HP_",
        "#   DOID: http://purl.obolibrary.org/obo/DOID_",
        "#   ORPHANET: http://www.orpha.net/ORDO/Orphanet_",
        "#   CHEBI: http://purl.obolibrary.org/obo/CHEBI_",
        "#   OBA: http://purl.obolibrary.org/obo/OBA_",
        "#   CMO: http://purl.obolibrary.org/obo/CMO_",
        "# mapping_set_id: https://kp.a2f.org/phenotype/mappings",
        f"# mapping_set_version: v{version} ({today})",
    ]
    fieldnames = [
        "subject_id", "subject_label", "predicate_id",
        "object_id", "object_label", "mapping_justification", "confidence",
    ]

    total = 0
    with open(output_path, "w", newline="") as f:
        for line in header_lines:
            f.write(line + "\n")
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for r in records:
            for m in r.get("mappings", []):
                semapv = JUSTIFICATION_TO_SEMAPV.get(
                    m.get("mapping_justification", ""), "semapv:UnspecifiedMatching"
                )
                writer.writerow({
                    "subject_id": r["portal_id"],
                    "subject_label": r["phenotype_name"],
                    "predicate_id": m.get("mapping_predicate", ""),
                    "object_id": m.get("target_id", ""),
                    "object_label": m.get("target_label", ""),
                    "mapping_justification": semapv,
                    "confidence": m.get("confidence", ""),
                })
                total += 1
    print(f"  Wrote SSSOM: {output_path} ({total} mappings)")


def generate_linkml_instances(records: list[dict], output_path: Path):
    phenotypes = []
    for r in records:
        primary = select_primary_mapping(r.get("mappings", []))
        pheno = {
            "portal_id": r["portal_id"],
            "legacy_id": r["phenotype"],
            "legacy_trait_group": r["trait_group"],
            "phenotype_name": r["phenotype_name"],
            "display_group": r.get("display_group", ""),
            "trait_type": r["trait_type"],
        }
        if r.get("amp_description"):
            pheno["description"] = r["amp_description"]
        if r.get("amp_dichotomous"):
            pheno["is_dichotomous"] = r["amp_dichotomous"] == "1"
        if primary:
            pheno["primary_mapping"] = {
                "target_id": primary["target_id"],
                "target_label": primary.get("target_label", ""),
                "target_ontology": primary["target_ontology"],
                "mapping_predicate": primary["mapping_predicate"],
                "mapping_justification": primary.get("mapping_justification", ""),
                "confidence": primary.get("confidence"),
            }
        if r.get("mappings"):
            pheno["mappings"] = []
            for m in r["mappings"]:
                entry = {
                    "target_id": m["target_id"],
                    "target_ontology": m["target_ontology"],
                    "mapping_predicate": m["mapping_predicate"],
                    "mapping_justification": m.get("mapping_justification", ""),
                    "confidence": m.get("confidence"),
                }
                if m.get("target_label"):
                    entry["target_label"] = m["target_label"]
                if m.get("source"):
                    entry["source"] = m["source"]
                if m.get("notes"):
                    entry["notes"] = m["notes"]
                pheno["mappings"].append(entry)
        phenotypes.append(pheno)

    with open(output_path, "w") as f:
        yaml.dump(
            {"phenotypes": phenotypes}, f,
            default_flow_style=False, allow_unicode=True, sort_keys=False, width=120,
        )
    print(f"  Wrote LinkML instances: {output_path} ({len(phenotypes)} phenotypes)")


def main():
    parser = argparse.ArgumentParser(description="Generate versioned portal phenotype output")
    parser.add_argument("--version", default="0.0.1", help="Version string (default: 0.0.1)")
    parser.add_argument("--input", default=None, help="Input JSON path (default: 03_ols_enriched_mappings.json)")
    args = parser.parse_args()

    version = args.version
    VERSIONS = ROOT / "versions" / "phenotype"
    version_dir = VERSIONS / f"v{version}"
    version_dir.mkdir(exist_ok=True, parents=True)

    print(f"Generating v{version} output\n")

    input_path = Path(args.input) if args.input else None
    records = load_input(input_path)
    print(f"  {len(records)} phenotype records\n")

    print("Assigning PORTAL IDs...")
    records = assign_portal_ids(records)
    print(f"  {records[0]['portal_id']} to {records[-1]['portal_id']}\n")

    print("Generating output files...")
    generate_registry(records, version_dir / "portal_phenotype_registry.tsv")
    generate_sssom(records, version_dir / "portal_phenotype_mappings.sssom.tsv", version)
    generate_linkml_instances(records, version_dir / "portal_phenotypes.yaml")

    print(f"\nOutput: {version_dir}/")
    print(f"\nTo validate:")
    print(f"  linkml-validate -s schemas/phenotype/portal_phenotype.yaml {version_dir}/portal_phenotypes.yaml")


if __name__ == "__main__":
    main()

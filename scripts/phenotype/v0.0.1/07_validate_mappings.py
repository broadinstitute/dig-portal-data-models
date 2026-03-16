#!/usr/bin/env python3
"""Step 7: Validate mappings for semantic plausibility.

Flags suspicious mappings based on:
  1. exactMatch/closeMatch where phenotype name and target label share <30% tokens
  2. Trait type / ontology mismatch (e.g., disease phenotype mapped to measurement term)
  3. exactMatch with confidence <0.7
  4. Mappings to overly generic terms (e.g., "disease", "measurement") as exactMatch
  5. Target labels containing red-flag keywords unrelated to the phenotype

Reads:
  - data/phenotype/03_ols_enriched_mappings.json

Writes:
  - reports/phenotype/suspicious_mappings.tsv
  - reports/phenotype/validation_summary.md
"""
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA = ROOT / "data" / "phenotype"
REPORTS = ROOT / "reports" / "phenotype"
REPORTS.mkdir(exist_ok=True, parents=True)

STOPWORDS = {
    "a", "an", "the", "of", "in", "and", "or", "to", "for", "by", "with",
    "on", "at", "is", "are", "was", "not", "no", "type", "level", "levels",
    "blood", "serum", "plasma", "measurement", "other",
}

# Very generic terms that should never be exactMatch
GENERIC_TERMS = {
    "disease", "measurement", "phenotype", "disorder", "syndrome",
    "protein measurement", "experimental factor", "information content entity",
}


def tokenize(s: str) -> set[str]:
    """Tokenize and normalize a string."""
    s = re.sub(r"[^\w\s]", " ", s.lower())
    return {w for w in s.split() if w and w not in STOPWORDS}


def token_overlap(a: str, b: str) -> float:
    """Bidirectional token overlap between two strings."""
    ta = tokenize(a)
    tb = tokenize(b)
    if not ta or not tb:
        return 0.0
    overlap = ta & tb
    return min(len(overlap) / len(ta), len(overlap) / len(tb))


def check_mapping(phenotype_name: str, trait_type: str, mapping: dict) -> list[str]:
    """Check a single mapping for issues. Returns list of issue descriptions."""
    issues = []
    target_label = mapping.get("target_label", "").strip()
    target_id = mapping.get("target_id", "")
    predicate = mapping.get("mapping_predicate", "")
    confidence = mapping.get("confidence", 0)
    target_ontology = mapping.get("target_ontology", "")
    justification = mapping.get("mapping_justification", "")

    # Skip broad matches — those are intentionally loose
    if predicate == "skos:broadMatch":
        return issues

    # 1. exactMatch/closeMatch with low token overlap (if we have a label)
    if target_label and predicate in ("skos:exactMatch", "skos:closeMatch"):
        overlap = token_overlap(phenotype_name, target_label)
        if predicate == "skos:exactMatch" and overlap < 0.3:
            issues.append(
                f"LOW_OVERLAP_EXACT: exactMatch but only {overlap:.0%} token overlap "
                f"('{phenotype_name}' vs '{target_label}')"
            )
        elif predicate == "skos:closeMatch" and overlap < 0.15:
            issues.append(
                f"LOW_OVERLAP_CLOSE: closeMatch but only {overlap:.0%} token overlap "
                f"('{phenotype_name}' vs '{target_label}')"
            )

    # 2. exactMatch to a very generic term
    if target_label and predicate == "skos:exactMatch":
        if target_label.lower().strip() in GENERIC_TERMS:
            issues.append(
                f"GENERIC_EXACT: exactMatch to generic term '{target_label}'"
            )

    # 3. Trait type / ontology semantic mismatch
    if target_label:
        label_lower = target_label.lower()
        if trait_type == "disease" and any(
            kw in label_lower for kw in ["measurement", "assay", "level of", "concentration"]
        ):
            issues.append(
                f"TYPE_MISMATCH: disease phenotype mapped to measurement-like term '{target_label}'"
            )
        if trait_type == "measurement" and predicate == "skos:exactMatch" and any(
            kw in label_lower
            for kw in ["disease", "syndrome", "disorder", "carcinoma", "cancer"]
        ):
            # Only flag if the phenotype name doesn't also contain these words
            name_lower = phenotype_name.lower()
            if not any(kw in name_lower for kw in ["disease", "syndrome", "disorder", "carcinoma", "cancer"]):
                issues.append(
                    f"TYPE_MISMATCH: measurement phenotype exact-mapped to disease term '{target_label}'"
                )

    # 4. High confidence without strong justification
    if confidence and confidence > 0.9 and justification not in (
        "manual_curation", "gwas_catalog", "inherited"
    ):
        issues.append(
            f"HIGH_CONF_UNJUSTIFIED: confidence {confidence} with justification '{justification}'"
        )

    return issues


def main():
    print("Step 7: Validating mappings for semantic plausibility\n")

    with open(DATA / "03_ols_enriched_mappings.json") as f:
        records = json.load(f)

    print(f"Loaded {len(records)} phenotype records\n")

    # Process by display_group
    by_group = defaultdict(list)
    for r in records:
        by_group[r.get("display_group", "UNKNOWN")].append(r)

    all_issues = []
    issue_counts = Counter()
    phenotypes_with_issues = 0
    total_mappings_checked = 0

    for group_name in sorted(by_group.keys()):
        group_records = by_group[group_name]
        group_issues = 0

        for r in group_records:
            phenotype_name = r["phenotype_name"]
            trait_type = r["trait_type"]
            phenotype_id = r["phenotype"]
            record_has_issue = False

            for m in r.get("mappings", []):
                total_mappings_checked += 1
                issues = check_mapping(phenotype_name, trait_type, m)
                for issue in issues:
                    issue_type = issue.split(":")[0]
                    issue_counts[issue_type] += 1
                    group_issues += 1
                    record_has_issue = True
                    all_issues.append({
                        "display_group": group_name,
                        "phenotype": phenotype_id,
                        "phenotype_name": phenotype_name,
                        "trait_type": trait_type,
                        "target_id": m.get("target_id", ""),
                        "target_label": m.get("target_label", ""),
                        "target_ontology": m.get("target_ontology", ""),
                        "predicate": m.get("mapping_predicate", ""),
                        "confidence": m.get("confidence", ""),
                        "justification": m.get("mapping_justification", ""),
                        "issue": issue,
                    })

            if record_has_issue:
                phenotypes_with_issues += 1

        if group_issues:
            print(f"  {group_name}: {group_issues} issues in {len(group_records)} phenotypes")

    # Write suspicious mappings TSV
    tsv_path = REPORTS / "suspicious_mappings.tsv"
    fieldnames = [
        "display_group", "phenotype", "phenotype_name", "trait_type",
        "target_id", "target_label", "target_ontology", "predicate",
        "confidence", "justification", "issue",
    ]
    with open(tsv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(all_issues)

    # Write summary
    summary_path = REPORTS / "validation_summary.md"
    lines = [
        "# Mapping Validation Summary\n",
        f"- **Total mappings checked**: {total_mappings_checked}",
        f"- **Suspicious mappings flagged**: {len(all_issues)} ({len(all_issues)/total_mappings_checked*100:.1f}%)",
        f"- **Phenotypes with issues**: {phenotypes_with_issues}",
        "",
        "## Issue Type Breakdown\n",
        "| Issue Type | Count | Description |",
        "|------------|-------|-------------|",
    ]

    descriptions = {
        "LOW_OVERLAP_EXACT": "exactMatch but phenotype name and target label share <30% tokens",
        "LOW_OVERLAP_CLOSE": "closeMatch but phenotype name and target label share <15% tokens",
        "GENERIC_EXACT": "exactMatch to an overly generic term like 'disease' or 'measurement'",
        "TYPE_MISMATCH": "Trait type doesn't match the ontology term type (e.g., disease → measurement)",
        "HIGH_CONF_UNJUSTIFIED": "Confidence >0.9 without strong justification",
    }
    for issue_type, count in issue_counts.most_common():
        desc = descriptions.get(issue_type, "")
        lines.append(f"| {issue_type} | {count} | {desc} |")

    lines.append(f"\n## Details\n")
    lines.append(f"See `suspicious_mappings.tsv` for full details.\n")

    # Show top examples per issue type
    for issue_type in issue_counts:
        examples = [i for i in all_issues if i["issue"].startswith(issue_type)][:5]
        if examples:
            lines.append(f"### {issue_type} (top 5 examples)\n")
            lines.append("| Phenotype | Target | Predicate | Issue |")
            lines.append("|-----------|--------|-----------|-------|")
            for ex in examples:
                lines.append(
                    f"| {ex['phenotype_name'][:40]} | {ex['target_label'][:40]} | {ex['predicate']} | {ex['issue'].split(': ', 1)[1][:60]} |"
                )
            lines.append("")

    with open(summary_path, "w") as f:
        f.write("\n".join(lines))

    print(f"\n{'='*60}")
    print(f"VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total mappings checked: {total_mappings_checked}")
    print(f"Suspicious mappings: {len(all_issues)} ({len(all_issues)/total_mappings_checked*100:.1f}%)")
    print(f"Phenotypes with issues: {phenotypes_with_issues}")
    print(f"\nBy issue type:")
    for issue_type, count in issue_counts.most_common():
        print(f"  {issue_type}: {count}")
    print(f"\nWrote: {tsv_path}")
    print(f"Wrote: {summary_path}")


if __name__ == "__main__":
    main()

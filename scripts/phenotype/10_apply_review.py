#!/usr/bin/env python3
"""Apply manual review flags from the review TSV back to the enriched mappings.

Reads:
  - data/phenotype/review_mappings.tsv (with filled-in flag/notes columns)
  - data/phenotype/03_ols_enriched_mappings.json

Writes:
  - data/phenotype/03_ols_enriched_mappings.json (updated)
  - reports/phenotype/review_changes.md (summary of changes)

Flag values:
  "remove"  → delete the mapping
  "broad"   → change predicate to skos:broadMatch
  "narrow"  → change predicate to skos:narrowMatch
  "related" → change predicate to skos:relatedMatch
  "close"   → change predicate to skos:closeMatch
  "exact"   → change predicate to skos:exactMatch
  (blank)   → no change
"""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data" / "phenotype"
REPORTS = ROOT / "reports" / "phenotype"
REPORTS.mkdir(exist_ok=True, parents=True)

FLAG_TO_PREDICATE = {
    "broad": "skos:broadMatch",
    "narrow": "skos:narrowMatch",
    "related": "skos:relatedMatch",
    "close": "skos:closeMatch",
    "exact": "skos:exactMatch",
}


def main():
    print("Applying manual review flags\n")

    review_path = DATA / "review_mappings.tsv"
    if not review_path.exists():
        print(f"ERROR: {review_path} not found. Run 09_export_review_table.py first.")
        return

    # Load review flags
    flags = {}  # (phenotype, target_id) → {flag, notes, row}
    with open(review_path, newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            flag = row.get("flag", "").strip().lower()
            notes = row.get("notes", "").strip()
            if flag:
                key = (row["phenotype"], row["target_id"])
                flags[key] = {
                    "flag": flag,
                    "notes": notes,
                    "phenotype_name": row["phenotype_name"],
                    "target_label": row.get("target_label", ""),
                    "old_predicate": row.get("mapping_predicate", ""),
                }

    if not flags:
        print("No flags found in review file. Nothing to do.")
        return

    print(f"Found {len(flags)} flagged mappings")

    # Load and modify records
    with open(DATA / "03_ols_enriched_mappings.json") as f:
        records = json.load(f)

    changes = Counter()
    change_details = []

    for r in records:
        phenotype = r["phenotype"]
        new_mappings = []

        for m in r.get("mappings", []):
            key = (phenotype, m.get("target_id", ""))
            if key in flags:
                flag_info = flags[key]
                flag = flag_info["flag"]

                if flag == "remove":
                    changes["removed"] += 1
                    change_details.append({
                        "action": "REMOVED",
                        "phenotype": flag_info["phenotype_name"],
                        "target": f"{m.get('target_id', '')} ({m.get('target_label', '')})",
                        "old_predicate": m.get("mapping_predicate", ""),
                        "notes": flag_info["notes"],
                    })
                    continue  # Skip — don't add to new_mappings

                elif flag in FLAG_TO_PREDICATE:
                    old_pred = m.get("mapping_predicate", "")
                    new_pred = FLAG_TO_PREDICATE[flag]
                    if old_pred != new_pred:
                        changes[f"{old_pred}→{new_pred}"] += 1
                        change_details.append({
                            "action": f"PREDICATE: {old_pred} → {new_pred}",
                            "phenotype": flag_info["phenotype_name"],
                            "target": f"{m.get('target_id', '')} ({m.get('target_label', '')})",
                            "old_predicate": old_pred,
                            "notes": flag_info["notes"],
                        })
                    m["mapping_predicate"] = new_pred
                    m["mapping_justification"] = "manual_curation"

                # Apply notes as label correction if flag is "wrong_label"
                if flag == "wrong_label" and flag_info["notes"]:
                    m["target_label"] = flag_info["notes"]
                    changes["label_corrected"] += 1

                # Add reviewer notes
                if flag_info["notes"] and flag != "wrong_label":
                    m["notes"] = flag_info["notes"]

            new_mappings.append(m)

        r["mappings"] = new_mappings

    # Save
    with open(DATA / "03_ols_enriched_mappings.json", "w") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    # Write change report
    report_path = REPORTS / "review_changes.md"
    lines = [
        "# Manual Review Changes\n",
        f"Applied {len(flags)} flags from `review_mappings.tsv`\n",
        "## Summary\n",
        "| Action | Count |",
        "|--------|-------|",
    ]
    for action, count in changes.most_common():
        lines.append(f"| {action} | {count} |")

    if change_details:
        lines.append("\n## All Changes\n")
        lines.append("| Action | Phenotype | Target | Notes |")
        lines.append("|--------|-----------|--------|-------|")
        for d in change_details:
            lines.append(
                f"| {d['action']} | {d['phenotype'][:40]} | {d['target'][:50]} | {d.get('notes', '')[:40]} |"
            )

    with open(report_path, "w") as f:
        f.write("\n".join(lines))

    print(f"\nChanges applied:")
    for action, count in changes.most_common():
        print(f"  {action}: {count}")
    print(f"\nUpdated: {DATA / '03_ols_enriched_mappings.json'}")
    print(f"Report: {report_path}")
    print(f"\nNow run:")
    print(f"  uv run python scripts/phenotype/05_generate_output.py")
    print(f"  uv run python scripts/phenotype/06_quality_report.py")


if __name__ == "__main__":
    main()

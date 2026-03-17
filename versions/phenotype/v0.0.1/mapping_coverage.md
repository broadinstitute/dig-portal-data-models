# Portal Phenotype Mapping Coverage Report — v0.0.1

## Overall Summary

- **Total phenotypes**: 6982
- **Total mappings**: 16870
- **Phenotypes with any mapping**: 6982 (100.0%)
- **Phenotypes with NO mapping**: 0 (0.0%)

## Coverage by Ontology

| Ontology | Mapped | % of Total |
|----------|--------|------------|
| EFO | 5461 | 78.2% |
| MESH | 2526 | 36.2% |
| MONDO | 448 | 6.4% |
| HP | 192 | 2.7% |
| DOID | 369 | 5.3% |
| ORPHANET | 1679 | 24.0% |
| CHEBI | 0 | 0.0% |
| OBA | 613 | 8.8% |
| CMO | 14 | 0.2% |
| ICD10CM | 284 | 4.1% |

## Coverage by Trait Group

| Trait Group | Total | EFO | MESH | MONDO | ORPHANET | Any | None |
|-------------|-------|-----|------|-------|----------|-----|------|
| portal | 1437 | 1437 (100%) | 915 (64%) | 198 (14%) | 54 (4%) | 1437 (100%) | 0 (0%) |
| gcat_trait | 4022 | 4022 (100%) | 1153 (29%) | 249 (6%) | 102 (3%) | 4022 (100%) | 0 (0%) |
| rare_v2 | 1523 | 2 (0%) | 458 (30%) | 1 (0%) | 1523 (100%) | 1523 (100%) | 0 (0%) |

## Quality Targets

| Target | Actual | Status |
|--------|--------|--------|
| >90% portal → EFO/MONDO/MESH | 100.0% (1437/1437) | PASS |
| >95% rare_v2 → ORPHANET | 100.0% (1523/1523) | PASS |
| >80% gcat_trait → EFO | 100.0% (4022/4022) | PASS |

## Predicate Distribution

| Predicate | Count | % |
|-----------|-------|---|
| skos:exactMatch | 14452 | 85.7% |
| skos:broadMatch | 2090 | 12.4% |
| oboInOwl:hasDbXref | 314 | 1.9% |
| skos:relatedMatch | 12 | 0.1% |
| skos:closeMatch | 2 | 0.0% |

## Trait Type Distribution

| Trait Type | Count | % |
|------------|-------|---|
| measurement | 3275 | 46.9% |
| phenotype | 1650 | 23.6% |
| rare_disease | 1523 | 21.8% |
| disease | 291 | 4.2% |
| adjusted | 102 | 1.5% |
| stratified | 102 | 1.5% |
| interaction | 17 | 0.2% |
| subgroup | 14 | 0.2% |
| composite | 8 | 0.1% |
# Portal Phenotype Mapping Coverage Report — v0.0.1

## Overall Summary

- **Total phenotypes**: 6982
- **Total mappings**: 21081
- **Phenotypes with any mapping**: 6982 (100.0%)
- **Phenotypes with NO mapping**: 0 (0.0%)

## Coverage by Ontology

| Ontology | Mapped | % of Total |
|----------|--------|------------|
| EFO | 5590 | 80.1% |
| MESH | 2706 | 38.8% |
| MONDO | 1333 | 19.1% |
| HP | 453 | 6.5% |
| DOID | 741 | 10.6% |
| ORPHANET | 1679 | 24.0% |
| CHEBI | 27 | 0.4% |
| OBA | 613 | 8.8% |
| CMO | 14 | 0.2% |

## Coverage by Trait Group

| Trait Group | Total | EFO | MESH | MONDO | ORPHANET | Any | None |
|-------------|-------|-----|------|-------|----------|-----|------|
| portal | 1437 | 1437 (100%) | 959 (67%) | 249 (17%) | 54 (4%) | 1437 (100%) | 0 (0%) |
| gcat_trait | 4022 | 4022 (100%) | 1259 (31%) | 417 (10%) | 102 (3%) | 4022 (100%) | 0 (0%) |
| rare_v2 | 1523 | 131 (9%) | 488 (32%) | 667 (44%) | 1523 (100%) | 1523 (100%) | 0 (0%) |

## Quality Targets

| Target | Actual | Status |
|--------|--------|--------|
| >90% portal → EFO/MONDO/MESH | 100.0% (1437/1437) | PASS |
| >95% rare_v2 → ORPHANET | 100.0% (1523/1523) | PASS |
| >80% gcat_trait → EFO | 100.0% (4022/4022) | PASS |

## Predicate Distribution

| Predicate | Count | % |
|-----------|-------|---|
| skos:exactMatch | 15457 | 73.3% |
| skos:closeMatch | 3309 | 15.7% |
| skos:broadMatch | 2023 | 9.6% |
| skos:relatedMatch | 292 | 1.4% |

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
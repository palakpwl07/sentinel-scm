# Evaluation Results

Scenarios: 25 | Agent calls: ~113 | Run date: 2026-07-19T09:33:34+00:00

## Headline

| Metric | Agent Society | Single-Agent Baseline | Delta |
|---|---|---|---|
| Supplier detection precision | 1.00 | 0.97 | +0.03 |
| Supplier detection recall | 1.00 | 0.82 | +0.18 |
| Supplier detection F1 | 1.00 | 0.87 | +0.13 |
| Risk level accuracy | 0.87 | 0.77 | +0.10 |
| Cost estimate MAPE | 0.0% | n/a% | n/a |
| Correct material prioritised | 15/25 | 14/25 | +1 |

## By scenario tier

| Tier | Agent F1 | Baseline F1 |
|---|---|---|
| Single event (5) | 1.00 | 0.85 |
| Event pairs (10) | 1.00 | 0.84 |
| Event triples (5) | 1.00 | 0.85 |
| Novel events (5) | 1.00 | 0.97 |

## Per-scenario detail

| Scenario | Agent P/R/F1 | Baseline P/R/F1 | Agent FN | Baseline FN |
|---|---|---|---|---|
| EVAL-01 (Israel conflict only) | 1.00/1.00/1.00 | 1.00/1.00/1.00 | — | — |
| EVAL-02 (Red Sea attacks only) | 1.00/1.00/1.00 | 0.86/1.00/0.92 | — | — |
| EVAL-03 (Hormuz closure only) | 1.00/1.00/1.00 | 1.00/1.00/1.00 | — | — |
| EVAL-04 (QatarEnergy force majeure) | 1.00/1.00/1.00 | 1.00/0.50/0.67 | — | SG-PM-01 |
| EVAL-05 (Jebel Ali disruption only) | 1.00/1.00/1.00 | 1.00/0.50/0.67 | — | SG-HE-01 |
| EVAL-06 (Israel conflict + Red Sea attacks) | 1.00/1.00/1.00 | 0.83/0.83/0.83 | — | SG-HE-04 |
| EVAL-07 (Israel conflict + Hormuz closure) | 1.00/1.00/1.00 | 1.00/1.00/1.00 | — | — |
| EVAL-08 (Israel conflict + Qatar force majeure) | 1.00/1.00/1.00 | 1.00/0.75/0.86 | — | SG-PM-01 |
| EVAL-09 (Israel conflict + Jebel Ali disruption) | 1.00/1.00/1.00 | 1.00/0.75/0.86 | — | SG-HE-01 |
| EVAL-10 (Red Sea attacks + Hormuz closure) | 1.00/1.00/1.00 | 1.00/0.50/0.67 | — | SG-HE-04, SG-OC-02, SG-SC-01, SG-SC-03 |
| EVAL-11 (Red Sea attacks + Qatar force majeure) | 1.00/1.00/1.00 | 0.75/0.38/0.50 | — | SG-HE-04, SG-OC-02, SG-PM-01, SG-SC-01, SG-SC-03 |
| EVAL-12 (Red Sea attacks + Jebel Ali disruption) | 1.00/1.00/1.00 | 1.00/0.50/0.67 | — | SG-HE-04, SG-OC-02, SG-SC-01, SG-SC-03 |
| EVAL-13 (Hormuz closure + Qatar force majeure) | 1.00/1.00/1.00 | 1.00/1.00/1.00 | — | — |
| EVAL-14 (Hormuz closure + Jebel Ali disruption) | 1.00/1.00/1.00 | 1.00/1.00/1.00 | — | — |
| EVAL-15 (Qatar force majeure + Jebel Ali disruption) | 1.00/1.00/1.00 | 1.00/1.00/1.00 | — | — |
| EVAL-16 (Israel conflict + Red Sea attacks + Hormuz closure) | 1.00/1.00/1.00 | 1.00/0.50/0.67 | — | SG-HE-04, SG-OC-02, SG-SC-01, SG-SC-03 |
| EVAL-17 (Hormuz closure + Qatar force majeure + Jebel Ali disruption) | 1.00/1.00/1.00 | 1.00/1.00/1.00 | — | — |
| EVAL-18 (Israel conflict + Hormuz closure + Qatar force majeure) | 1.00/1.00/1.00 | 1.00/1.00/1.00 | — | — |
| EVAL-19 (Red Sea attacks + Hormuz closure + Jebel Ali disruption) | 1.00/1.00/1.00 | 1.00/0.50/0.67 | — | SG-HE-04, SG-OC-02, SG-SC-01, SG-SC-03 |
| EVAL-20 (Israel conflict + Red Sea attacks + Jebel Ali disruption) | 1.00/1.00/1.00 | 1.00/0.88/0.93 | — | SG-OC-02 |
| EVAL-21 (Typhoon closes Kaohsiung) | 1.00/1.00/1.00 | 1.00/1.00/1.00 | — | — |
| EVAL-22 (Fire at PenangChip) | 1.00/1.00/1.00 | 1.00/1.00/1.00 | — | — |
| EVAL-23 (Taiwan Strait closure) | 1.00/1.00/1.00 | 1.00/1.00/1.00 | — | — |
| EVAL-24 (Shanghai port congestion) | 1.00/1.00/1.00 | 0.75/1.00/0.86 | — | — |
| EVAL-25 (Typhoon + Taiwan Strait) | 1.00/1.00/1.00 | 1.00/1.00/1.00 | — | — |

## Failure analysis

No scenario fell below agent F1 0.8 and no scenario errored.

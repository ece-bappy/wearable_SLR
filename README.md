# Wearable Biometric Authentication SLR Repository

This repository contains the data extraction and analysis workflow for a systematic literature review (SLR) on wearable biometric authentication.

## Overview

The project is built around:

- `extract_data.ipynb`: a notebook that extracts structured metadata from wearable biometric authentication papers.
- `analysis.ipynb`: a notebook that loads, cleans, normalizes, and analyzes the extracted paper metadata.
- `jsons/`: a collection of per-paper JSON records produced by the extraction workflow.
- `master.json`: an aggregated dataset of extracted records.
- `wearable_auth_final.json`: a final curated wearable authentication metadata collection.
- `references.bib`: bibliography references used for the review.

## Revised analysis (manuscript revision, November 2026)

The revised manuscript is based on the files in `revision/`. Every statistic, figure, and table in the revised paper can be regenerated from them.

**Corpus.** A DOI- and title-level audit found 16 papers that had been extracted twice. `revision/data/jsons_dedup/` is `jsons_w_citekey/` with those 16 duplicate records removed; their file numbers are listed in `revision/data/removed_duplicates.txt`. The final corpus contains **263 unique included studies**: 280 records, of which 17 are marked `exclude`.

| Path | Purpose |
|---|---|
| `revision/phase2/analysis_revised.py` | Revised version of `analysis.ipynb`; every change is marked `# REV:`. Produces the RQ1–RQ3 figures and `numbers.json`. It covers the evidence tiers, the paired lab/field values, and one EER definition shared by all analyses: the first reported EER, taken as a percentage. |
| `revision/phase3/analysis_phase3.py` | Hardware telemetry (latency and energy normalization), multimodal fusion vs. unimodal analysis, and the corpus table (`tables/S1_corpus_263.csv`, `.xlsx`). Produces `numbers_phase3.json`. |
| `revision/phase3/prisma.py` | Draws the PRISMA flow diagram. The post-extraction counts are derived from the data. |
| `revision/tools/make_highlights_ga.py`, `make_ga_v4.py` | Highlights and the graphical abstract. Every number is read from the JSON outputs. |
| `revision/phase2/list_paired.py` | Lists the paired lab/field studies. Each pair was checked manually against the source article. `Camara_2023` is excluded because its two values come from different datasets, not from lab and field conditions. |

**Reproduce** (Python 3.11+, with `pandas numpy scipy matplotlib seaborn python-docx openpyxl`). On Windows, set `PYTHONUTF8=1` first.

```bash
cd revision/phase2 && python analysis_revised.py
cd ../phase3 && python analysis_phase3.py && python prisma.py
cd ../.. && python revision/tools/make_highlights_ga.py && python revision/tools/make_ga_v4.py
```

The original notebook `analysis.ipynb` reads a folder named `jsons_test/`. To reproduce the originally submitted figures (279 records, before de-duplication), copy `jsons_w_citekey/` to `jsons_test/`.

## Purpose

The repository supports research into wearable biometric authentication systems by capturing:

- system relevance and scope
- biometric modality and device details
- dataset characteristics and collection settings
- machine learning methods and models
- evaluation metrics (EER, FAR, FRR, AUC)
- real-world and temporal robustness insights
- security, spoofing, and usability analysis
- reproducibility information

This enables structured analysis of wearable authentication literature across sensors such as ECG, PPG, motion, gait, and more.

## Repository Structure

- `analysis.ipynb`
  - Loads extracted JSON records
  - Normalizes modalities and model labels
  - Computes derived metrics and trends
  - Prepares visualizations for the literature review

- `extract_data.ipynb`
  - Uses PDF text extraction and generative AI guidance
  - Filters papers by relevance to wearable biometric authentication
  - Produces validated JSON output for each paper
  - Includes extraction rules, mapping policies, and quality checks

- `jsons/`
  - Structured paper records with fields such as `title`, `year`, `biometric`, `data`, `method`, `evaluation`, `security`, and `usability`

- `jsons_w_citekey/`
  - Similar JSON output files with citation key metadata included

- `master.json`
  - Aggregated extraction result for the reviewed corpus

- `wearable_auth_final.json`
  - Curated final dataset of wearable authentication papers

## How to Use

1. Install the required Python packages.
   - The notebooks use libraries such as `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy`, `PyMuPDF`/`fitz`, `python-dotenv`, and `google.generativeai`.

2. Configure API access for extraction.
   - Create a `.env` file containing `GOOGLE_API_KEY`.
   - Do not commit the `.env` file or API keys to the public repository.

3. Place source PDFs in the `pdfs/` folder.

4. Run `extract_data.ipynb` to generate/update JSON records in `jsons/`.

5. Run `analysis.ipynb` to explore and visualize the extracted dataset.

## Notes for a Public Repository

- Do not store API keys or other secrets in the repository.
- Keep `.env` local and add it to `.gitignore` if not already excluded.
- The notebooks are intended to document and reproduce the extraction and analysis pipeline.

## Data Schema Highlights

Each extracted paper record includes key research dimensions such as:

- `relevance`
- `biometric.type`
- `biometric.modality`
- `biometric.device`
- `data.dataset_type`
- `data.collection_setting`
- `method.learning_type`
- `evaluation.metric`
- `security.spoofing_tested`
- `usability.authentication_type`
- `reproducibility.code_available`

## Contact

This repository is intended for research and review of wearable biometric authentication literature. You are welcome to contribute to this project. ping at `ece.bappy@gmail.com`

## Cite
This work is under submission. Citation details may be added once accepted.

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

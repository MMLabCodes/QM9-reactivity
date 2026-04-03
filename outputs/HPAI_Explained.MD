# H-PAI — Structured Lab Recording Framework

> <i>**Special Message for Fran (If you ever find this)**</i>; The Following Files always updated on OneDrive

## Overview

H-PAI stands for:

- **H** → Hypothesis
- **P** → Plan
- **A** → Action
- **I** → Interpretation of Results

> (SIKE! You (reader) really thought I called it that coz it was name?? Of course not... Don't be silly...)

It is a **structured recording system** designed to standardise how experiments, analyses, and computational workflows are documented.

---

## Why H-PAI?

The goal is to enforce a **clear scientific thinking pipeline**:

1. **Hypothesis**  
   Define what you believe and why.

2. **Plan**  
   Outline how you will test it.

3. **Action**  
   Record what was actually done.

4. **Interpretation**  
   Analyse outcomes and link back to the hypothesis.

This prevents:

- unclear reasoning
- missing experimental logic
- post-hoc interpretation bias

---

## Document Template Structure

Each record follows a fixed template:

- Metadata (Author, Project, Date, Experiment Name, Update Type)
- **1. Hypothesis**
- **2. Plan**
- **3. Action**
- **4. Interpretation of Results**
- **5. Figures (Optional)**
- **6. Notes / Next Steps**

Placeholders (e.g., `{{Assumption}}`, `{{Figure}}`) are automatically filled via `HPAI.py`.

---

## Recording Philosophy

H-PAI is designed to:

- Capture **thinking before and after execution**
- Separate **intent vs reality**
- Enable **traceable, reproducible workflows**
- Support both:
  - computational chemistry pipelines (DFT, descriptors, PCA/UMAP)
  - general experimental workflows

---

## Update Types

Documents can be tagged by frequency:

- **WU** → Weekly Update
- **BW** → Biweekly Update
- **MU** → Monthly Update

Used for structured reporting and version tracking.

---

## Output Format

Generated documents follow:

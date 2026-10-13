# LawCodex — Samoa (`ws`)

Legislation of the Independent State of Samoa as plain Markdown, from the **Consolidation of Laws
of Samoa 2024** as published by the Samoa Ministry of Justice and Courts Administration (MJCA),
<https://mjca.gov.ws/legislation/legislation.html> (tab "Consolidation of Laws of Samoa 2024").

Part of [LawCodex](https://github.com/LawCodex): the legislation of every country as Markdown in git.

Retrieved: **2026-10-13**.

## Contents

| Category | Directory | Files |
|---|---|---:|
| Constitution of the Independent State of Samoa 1960 (consolidated) | `constitution/` | 1 |
| Consolidated Acts and Ordinances | `acts/` | 268 |
| **Total** | | **269** |

These are all 269 consolidated Acts that MJCA publishes (English text).

## What is NOT covered

- Subsidiary legislation (regulations, by-laws), Acts passed after the 2024 consolidation and
  amending Acts, which are not on the MJCA page.
- Samoan-language texts (the consolidation is published in English).
- The official legislation portal `samoalaws.gov.ws` did not resolve (no DNS) at retrieval time,
  and has no Internet Archive captures. PacLII/SamLII (`paclii.org`, `samlii.org`) are behind a
  bot challenge (HTTP 403 "Just a moment…") and were not used.
- Layout: text extracted from the official PDFs with poppler `pdftotext`; running headers, page
  numbers and the arrangement of provisions are removed; tables, forms and schedules are
  flattened; signature blocks of the Constitution are run together. Headings: `## PART …`,
  `### Division …`, `#### N. heading`.

## Structure

```
constitution/constitution-of-the-independent-state-of-samoa-1960.md
acts/<slug of title>.md            acts/crimes-act-2013.md
```

`identifier` is the document id in MJCA's catalogue; `source` is the PDF URL published by MJCA.

## Sources and licence

- Official source: Ministry of Justice and Courts Administration of Samoa. The MJCA page loads its
  catalogue of consolidated Acts from a public Firestore collection (`consolidatedActs`, project
  `mjca-samoa`) and links each Act to a PDF in the ministry's Firebase storage; `scripts/ws_fetch.py`
  reads the same collection through the Firestore REST API and downloads the PDFs (2 parallel
  requests, identifying User-Agent). No terms of use restricting this were found.
- Note from PacLII's description of the consolidation: official printed versions bear the Attorney
  General's certificate. This repository is **not** an official version.

## Regenerate

```sh
python3 scripts/ws_fetch.py   ../_raw/ws
python3 scripts/ws_convert.py ../_raw/ws .    # needs poppler `pdftotext`
```

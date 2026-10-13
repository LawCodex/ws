#!/usr/bin/env python3
"""Fetch the 'Consolidation of Laws of Samoa 2024' as published by the Samoa Ministry of Justice
and Courts Administration (https://mjca.gov.ws/legislation/legislation.html).

The MJCA page reads its list of consolidated Acts from a public Firestore collection
('consolidatedActs', project 'mjca-samoa'); each entry links to the official PDF in the
ministry's Firebase storage bucket. We read the same collection through the Firestore REST API
and download each PDF (verified complete) into RAW/pdf/.
Usage: ws_fetch.py RAW_DIR
"""
import json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
import requests

UA = "LawCodex/1.0 (+https://github.com/LawCodex)"
LIST = "https://firestore.googleapis.com/v1/projects/mjca-samoa/databases/(default)/documents/consolidatedActs?pageSize=300"
RAW = sys.argv[1]
S = requests.Session()
S.headers["User-Agent"] = UA


def get_list():
    docs, token = [], None
    while True:
        r = S.get(LIST + (f"&pageToken={token}" if token else ""), timeout=120)
        r.raise_for_status()
        d = r.json()
        docs += d.get("documents", [])
        token = d.get("nextPageToken")
        if not token:
            return docs


def dl(rec):
    p = os.path.join(RAW, "pdf", rec["file"])
    if os.path.exists(p):
        return True
    for a in range(5):
        try:
            r = S.get(rec["pdfURL"], timeout=300)
            if r.status_code == 200 and r.content[:5] == b"%PDF-" and b"%%EOF" in r.content[-2048:]:
                with open(p + ".tmp", "wb") as f:
                    f.write(r.content)
                os.replace(p + ".tmp", p)
                return True
            print("bad", r.status_code, len(r.content), rec["name"], file=sys.stderr)
            if r.status_code == 404:
                return False
        except Exception as e:
            print("ERR", rec["name"], e, file=sys.stderr)
        time.sleep(3 * 2 ** a)
    return False


def main():
    os.makedirs(os.path.join(RAW, "pdf"), exist_ok=True)
    recs = []
    for d in get_list():
        f = {k: list(v.values())[0] for k, v in d["fields"].items()}
        if not f.get("pdfURL") or f.get("published") is False:
            continue
        f["id"] = d["name"].split("/")[-1]
        f["file"] = f["id"] + ".pdf"
        recs.append(f)
    with ThreadPoolExecutor(2) as ex:
        ok = list(ex.map(dl, recs))
    for r, o in zip(recs, ok):
        r["downloaded"] = o
    with open(os.path.join(RAW, "index.json"), "w") as fh:
        json.dump(recs, fh, indent=1, ensure_ascii=False)
    print(len(recs), "acts;", sum(ok), "downloaded")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Convert the Samoa consolidated-Acts PDFs fetched by ws_fetch.py into LawCodex Markdown.

Usage: ws_convert.py RAW_DIR OUT_DIR    (needs poppler `pdftotext`)
"""
import collections, datetime, json, os, re, subprocess, sys, unicodedata

RAW, OUT = sys.argv[1], sys.argv[2]
TODAY = datetime.date.today().isoformat()
PUA = re.compile("[-]")
START = re.compile(r"^(AN ACT|AN ORDINANCE|An Act|An Ordinance|IN THE HOLY NAME|BE IT ENACTED|AN ACT\b)")
PART = re.compile(r"^PART\s+[0-9IVXLC]+[A-Z]?$")
DIVISION = re.compile(r"^(Division|DIVISION)\s+\d+[A-Z]?\b")
SCHEDULE = re.compile(r"^(SCHEDULE|FIRST SCHEDULE|SECOND SCHEDULE|THIRD SCHEDULE|Schedule \d+|SCHEDULE \d+)\b")
SECTION = re.compile(r"^(\d{1,3}[A-Z]{0,2})\.\s+([^–—]{2,150}?)\s*(–|—|--|-)\s*(.*)$")
SECTION_ONLY = re.compile(r"^(\d{1,3}[A-Z]{0,2})\.\s+([A-Z][^.;:]{2,120})$")
LABEL = re.compile(r"^(\(\w{1,6}\)|“|\"|\[)")


def slug(s, n=90):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:n].rstrip("-")


def yq(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def pdftext(path):
    out = subprocess.run(["pdftotext", "-enc", "UTF-8", path, "-"], capture_output=True, check=True).stdout
    pages = PUA.sub("", out.decode("utf-8", "replace")).split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return pages


def norm(l):
    return re.sub(r"\d+", "#", l.strip().lower())


def body_lines(pages):
    # running headers/footers: short lines (digits normalised) present on many pages
    cnt = collections.Counter()
    for p in pages:
        for k in {norm(l) for l in p.split("\n") if 0 < len(l.strip()) < 90}:
            cnt[k] += 1
    thr = max(3, len(pages) * 0.3)
    hdr = {k for k, v in cnt.items() if v >= thr and not re.match(r"^(part|division|schedule|#\.|\(|“)", k)}
    lines = []
    for p in pages:
        for l in p.split("\n"):
            s = l.strip()
            if not s:
                lines.append("")
                continue
            if norm(s) in hdr or re.fullmatch(r"\d{1,4}", s):
                continue
            lines.append(s)
    return lines


def structure(lines):
    out, para = [], []
    last = 0
    skip = 0

    def flush():
        if para:
            out.append(" ".join(para))
            para.clear()

    for i, s in enumerate(lines):
        if skip:
            skip -= 1
            continue
        if not s:
            if para and re.search(r"[.:;—–-]$", para[-1]):
                flush()
            continue
        nxt = next((x for x in lines[i + 1:i + 3] if x), "")
        if PART.match(s):
            j, head = i + 1, s
            while j < len(lines) and j <= i + 3 and (not lines[j] or (lines[j].upper() == lines[j] and re.search(r"[A-Z]{2}", lines[j]) and len(lines[j]) < 80)):
                if lines[j]:
                    head += " " + lines[j]
                j += 1
            skip = j - i - 1
            flush(); out.append("## " + head); continue
        if DIVISION.match(s) and len(s) < 120:
            flush(); out.append("### " + s); continue
        if SCHEDULE.match(s) and len(s) < 100:
            flush(); out.append("## " + s); last = 0; continue
        lone = re.fullmatch(r"(\d{1,3}[A-Z]{0,2})\.", s)
        if lone and nxt and len(nxt) < 150 and not LABEL.match(nxt):
            n = int(re.match(r"\d+", lone.group(1)).group())
            if last <= n <= last + 15:
                flush()
                out.append(f"#### {lone.group(1)}. {nxt.rstrip(':').strip()}")
                last = n
                # skip the heading line (and blank lines before it)
                j = i + 1
                while j < len(lines) and not lines[j]:
                    j += 1
                skip = j - i
                continue
        m = SECTION.match(s) or SECTION_ONLY.match(s)
        if m:
            n = int(re.match(r"\d+", m.group(1)).group())
            if last <= n <= last + 15:
                flush()
                out.append(f"#### {m.group(1)}. {m.group(2).strip()}")
                rest = m.group(4).strip() if m.re is SECTION and m.lastindex >= 4 else ""
                if rest:
                    para.append(rest)
                last = n
                continue
        if LABEL.match(s):
            flush()
        para.append(s)
        if re.search(r"[.:;\]]$", s) and nxt and (LABEL.match(nxt) or nxt[:1].isupper()):
            flush()
    flush()
    return "\n\n".join(out)


def convert(path):
    pages = pdftext(path)
    lines = body_lines(pages)
    start = next((i for i, l in enumerate(lines) if START.match(l)), None)
    if start is not None:
        # keep the 'YYYY No. N' line that precedes the long title
        for k in range(max(0, start - 4), start):
            if re.match(r"^\d{4}\s*No\.?\s*\d+", lines[k]):
                start = k
                break
        lines = lines[start:]
    return structure(lines), len(pages)


def main():
    recs = json.load(open(os.path.join(RAW, "index.json")))
    counts, used, problems = collections.Counter(), set(), []
    for r in recs:
        p = os.path.join(RAW, "pdf", r["file"])
        if not os.path.exists(p):
            problems.append(("missing", r["name"]))
            continue
        body, npages = convert(p)
        if len(body) < 200:
            problems.append(("empty", r["name"]))
            continue
        title = re.sub(r"\s+", " ", r["name"]).strip()
        is_const = title.startswith("Constitution of the Independent State of Samoa")
        d = "constitution" if is_const else "acts"
        name = slug(title)
        if name in used:
            name += "-" + r["id"][:6].lower()
        used.add(name)
        kind = "constitution" if is_const else ("ordinance" if "Ordinance" in title else "act")
        m = re.search(r"(1[89]\d\d|20\d\d)\s*$", title)
        fm = ["---", f"title: {yq(title)}", f"identifier: {yq(r['id'])}", f"type: {kind}",
              "jurisdiction: ws", "language: en"]
        if m:
            fm.append(f"year: {m.group(1)}")
        fm += ['consolidation: "Consolidation of Laws of Samoa 2024"', "status: in_force",
               f"source: {yq(r['pdfURL'])}",
               'source_page: "https://mjca.gov.ws/legislation/legislation.html"',
               'format_note: "text extracted from the official PDF; layout not preserved"',
               f"retrieved: {TODAY}", "---", ""]
        out = os.path.join(OUT, d, name + ".md")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(fm) + f"# {title}\n\n" + body + "\n")
        counts[d] += 1
    print(dict(counts))
    print(len(problems), problems)


if __name__ == "__main__":
    main()

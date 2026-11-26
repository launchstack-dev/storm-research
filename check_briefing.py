"""Validate a hand-rendered STORM briefing against its ledger. Usage: check_briefing.py <run folder>"""
import re, sys
from html.parser import HTMLParser
from pathlib import Path

run = Path(sys.argv[1])
page = (run / "briefing.html").read_text()
ledger = (run / "ledger.md").read_text()
errs = []

if "{{" in page or "}}" in page:
    errs.append(f"unfilled tokens: {re.findall(r'.{0,30}\{\{.{0,40}', page)[:3]}")
if re.search(r"\{C\d", page) or re.search(r"\bC\d+\b(?=[\],])", page):
    errs.append("raw C-ids left in page")

class P(HTMLParser):
    VOID = {"meta", "link", "br", "img", "hr", "input", "wbr", "source"}
    def __init__(s):
        super().__init__(); s.stack = []; s.hrefs = []; s.bad = []
    def handle_starttag(s, t, a):
        if t == "a":
            s.hrefs.append(dict(a).get("href", ""))
        if t not in s.VOID:
            s.stack.append(t)
    def handle_endtag(s, t):
        if t in s.VOID: return
        if s.stack and s.stack[-1] == t: s.stack.pop()
        else: s.bad.append((t, list(s.stack[-3:])))
p = P(); p.feed(page)
if p.bad: errs.append(f"mismatched tags (first 3): {p.bad[:3]}")
if p.stack: errs.append(f"unclosed tags: {p.stack[-5:]}")
bad_href = [h for h in p.hrefs if not h.startswith(("http://", "https://", "#"))]
if bad_href: errs.append(f"non-http hrefs: {bad_href[:5]}")

# references: items inside the References <ol>
at = page.find('<div class="refs">')
refsec = page[at:] if at >= 0 else ""
nrefs = len(re.findall(r"<li", refsec.split("</ol>")[0])) if refsec else 0
body = page[:at] if at >= 0 else page
body = re.sub(r"<style.*?</style>", "", body, flags=re.S)
cited, first = set(), []
for grp in re.findall(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\]", body):
    for part in re.split(r"\s*,\s*", grp):
        ends = [int(x) for x in re.split(r"\s*[–-]\s*", part)]
        for n in range(ends[0], ends[-1] + 1):
            if n not in cited: first.append(n)
            cited.add(n)
if first != sorted(first): errs.append(f"[n] not numbered by first appearance: {first[:12]}...")
if nrefs == 0: errs.append("no References list found")
if cited - set(range(1, nrefs + 1)): errs.append(f"[n] with no reference: {sorted(cited - set(range(1, nrefs + 1)))}")
if set(range(1, nrefs + 1)) - cited: errs.append(f"references never cited: {sorted(set(range(1, nrefs + 1)) - cited)}")

# banner tally vs ledger
blocks = re.split(r"(?=^### C\d+)", ledger, flags=re.M)[1:]
st = lambda k, v: sum(1 for b in blocks if re.search(rf"^- {k}: {v}\b", b, re.M))
tally = dict(X=st("status", "false"), Y=st("status", "corrected"), Z=st("flags", "demoted"), U=st("status", "unverified"))
m = re.search(r"(\d+) claims independently checked.*?(\d+) fabricated, (\d+) corrected, (\d+) demoted, (\d+) unverified", re.sub(r"<[^>]+>", "", page), re.S)
if not m: errs.append("banner tally not found")
else:
    got = dict(zip("NXYZU", map(int, m.groups())))
    for k, v in tally.items():
        if got[k] != v: errs.append(f"banner {k}={got[k]} but ledger says {v}")
    print("banner:", got)
print(f"refs {nrefs}, cited {len(cited)}, ledger claims {len(blocks)}, ledger tally {tally}")
print("\n".join("FAIL " + e for e in errs) or "OK")
sys.exit(1 if errs else 0)

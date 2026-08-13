#!/usr/bin/env python3
"""Render FAQ.md into faq.html using the site's own shell.

FAQ.md is the single source of truth: the inbox-triage automation appends
question/answer pairs to it, and this script regenerates the page. Editing
faq.html by hand will be overwritten — edit the markdown instead.

Each question gets a stable slug id derived from its text, so other pages can
deep-link a specific answer (e.g. cfp.html -> faq#does-the-workshop-accept-...).
Slugs follow the question wording rather than its position, so inserting a new
entry never breaks an existing link.

Usage:  python3 tools/build_faq.py        (from the repo root)
"""

from __future__ import annotations

import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "FAQ.md"
OUT = ROOT / "faq.html"

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>FAQ · Interpretability as a Science</title>
  <meta name="description" content="Frequently asked questions about the Interpretability as a Science workshop at NeurIPS 2026: reviewing, submissions, presentation, and scope." />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="static/styles.css" />
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>

  <header class="site-header is-scrolled" data-header>
    <div class="header-inner">
      <a class="wordmark" href=".">Interp<span>Science</span></a>
      <nav class="nav" aria-label="Primary">
        <a href=".">Home</a>
        <a href="program">Program</a>
        <a href="faq" aria-current="page">FAQ</a>
        <a class="nav-cta" href="cfp">Call for Papers</a>
      </nav>
      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="mobile-nav" data-nav-toggle>
        <span class="sr-only">Menu</span>
        <span></span><span></span>
      </button>
    </div>
    <nav id="mobile-nav" class="mobile-nav" data-mobile-nav hidden>
      <a href=".">Home</a>
      <a href="program">Program</a>
      <a href="faq">FAQ</a>
      <a href="cfp">Call for Papers</a>
    </nav>
  </header>

  <main id="main">
    <section class="page-hero">
      <div class="section-inner narrow">
        <p class="eyebrow">NeurIPS 2026 · Sydney</p>
        <h1>Frequently asked questions</h1>
        <p class="page-lede">
          Answers to the questions we are asked most often. If yours is not here, write to
          <a href="mailto:interpscience@gmail.com">interpscience@gmail.com</a>.
        </p>
      </div>
    </section>

    <section class="section page-section">
      <div class="section-inner narrow">
"""

FOOT = """      </div>
    </section>
  </main>

  <footer class="site-footer">
    <div class="footer-inner">
      <div class="footer-left">
        <p class="footer-brand">Interpretability as a Science</p>
        <p>NeurIPS 2026 Workshop · Sydney</p>
      </div>
      <div class="footer-right">
        <p class="footer-contact-label">Contact us</p>
        <p class="footer-contact"><a href="mailto:interpscience@gmail.com">interpscience@gmail.com</a></p>
      </div>
    </div>
  </footer>

  <script src="static/script.js"></script>
</body>
</html>
"""


def slugify(text: str) -> str:
    s = text.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    return re.sub(r"[\s-]+", "-", s).strip("-")


def inline(md: str) -> str:
    """Escape, then restore the small inline subset the FAQ actually uses."""
    out = html.escape(md, quote=False)
    # [label](url)
    out = re.sub(
        r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
        lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>',
        out,
    )
    # Bare URLs not already inside an href. The trailing character class excludes
    # sentence punctuation, so "see https://example.com/x." does not put the full
    # stop inside the href and break the link.
    out = re.sub(
        r'(?<!href=")(?<!>)(https?://[^\s<)]*[^\s<).,;:])(?![^<]*</a>)',
        lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>',
        out,
    )
    return out


def main() -> None:
    if not SRC.exists():
        sys.exit(f"missing {SRC}")
    lines = SRC.read_text(encoding="utf-8").splitlines()

    entries: list[tuple[str, list[str]]] = []
    question: str | None = None
    buf: list[str] = []
    for ln in lines:
        if ln.startswith("## "):
            if question is not None:
                entries.append((question, buf))
            question, buf = ln[3:].strip(), []
        elif ln.startswith("# "):
            continue
        elif question is not None:
            buf.append(ln)
    if question is not None:
        entries.append((question, buf))

    if not entries:
        sys.exit("FAQ.md contains no '## question' headings")

    parts, seen = [], set()
    for q, body in entries:
        slug = slugify(q)
        n = 2
        while slug in seen:
            slug, n = f"{slugify(q)}-{n}", n + 1
        seen.add(slug)
        paras = [" ".join(p.split()) for p in re.split(r"\n\s*\n", "\n".join(body)) if p.strip()]
        parts.append(f'        <h2 id="{slug}">{inline(q)}</h2>')
        parts.extend(f"        <p>{inline(p)}</p>" for p in paras)

    OUT.write_text(HEAD + "\n".join(parts) + "\n" + FOOT, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} — {len(entries)} entries")
    for q in (e[0] for e in entries):
        print(f"  faq#{slugify(q)}")


if __name__ == "__main__":
    main()

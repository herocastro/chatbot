"""Convert MANUAL.md to a print-ready PDF using markdown + weasyprint."""

import pathlib
import markdown

# ── Paths ──────────────────────────────────────────────────────────────────
BASE = pathlib.Path(__file__).parent
MD_FILE = BASE / "MANUAL.md"
PDF_FILE = BASE / "MANUAL.pdf"

# ── Read source ─────────────────────────────────────────────────────────────
md_text = MD_FILE.read_text(encoding="utf-8")

# ── Convert Markdown → HTML ─────────────────────────────────────────────────
md = markdown.Markdown(extensions=["tables", "fenced_code", "toc"])
body_html = md.convert(md_text)

# ── Full HTML with print-optimised CSS ──────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>LLORA — Library Assistant Manual</title>
<style>
  /* ── Page setup ── */
  @page {{
    size: A4;
    margin: 2.2cm 2.4cm 2.4cm 2.4cm;
    @bottom-center {{
      content: counter(page);
      font-family: 'Segoe UI', Arial, sans-serif;
      font-size: 9pt;
      color: #888;
    }}
  }}

  /* ── Base typography ── */
  body {{
    font-family: 'Segoe UI', Arial, Helvetica, sans-serif;
    font-size: 10.5pt;
    line-height: 1.65;
    color: #1a1a1a;
    margin: 0;
    padding: 0;
  }}

  /* ── Headings ── */
  h1 {{
    font-size: 22pt;
    font-weight: 700;
    color: #0E553F;
    border-bottom: 3px solid #0E553F;
    padding-bottom: 6pt;
    margin-top: 0;
    margin-bottom: 14pt;
    page-break-before: avoid;
  }}
  h2 {{
    font-size: 14pt;
    font-weight: 700;
    color: #0E553F;
    border-bottom: 1.5px solid #c8e6c9;
    padding-bottom: 4pt;
    margin-top: 22pt;
    margin-bottom: 8pt;
    page-break-after: avoid;
  }}
  h3 {{
    font-size: 11.5pt;
    font-weight: 700;
    color: #1b5e20;
    margin-top: 16pt;
    margin-bottom: 5pt;
    page-break-after: avoid;
  }}
  h4 {{
    font-size: 10.5pt;
    font-weight: 700;
    color: #333;
    margin-top: 12pt;
    margin-bottom: 4pt;
    page-break-after: avoid;
  }}

  /* ── Cover block (first h1) ── */
  h1:first-of-type {{
    font-size: 26pt;
    text-align: center;
    border-bottom: none;
    padding-bottom: 0;
    margin-bottom: 4pt;
  }}

  /* ── Paragraphs ── */
  p {{
    margin: 0 0 8pt 0;
    orphans: 3;
    widows: 3;
  }}

  /* ── Links ── */
  a {{
    color: #0E553F;
    text-decoration: none;
  }}

  /* ── Code ── */
  code {{
    font-family: 'Courier New', Courier, monospace;
    font-size: 9pt;
    background: #f4f4f4;
    border: 1px solid #ddd;
    border-radius: 3px;
    padding: 1px 4px;
  }}
  pre {{
    background: #f4f4f4;
    border: 1px solid #ddd;
    border-left: 4px solid #0E553F;
    border-radius: 4px;
    padding: 10pt 12pt;
    font-family: 'Courier New', Courier, monospace;
    font-size: 8.5pt;
    line-height: 1.5;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-all;
    margin: 8pt 0 12pt 0;
    page-break-inside: avoid;
  }}
  pre code {{
    background: none;
    border: none;
    padding: 0;
    font-size: inherit;
  }}

  /* ── Tables ── */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 10pt 0 14pt 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
  }}
  thead tr {{
    background: #0E553F;
    color: #fff;
  }}
  thead th {{
    padding: 6pt 8pt;
    text-align: left;
    font-weight: 600;
  }}
  tbody tr:nth-child(even) {{
    background: #f0f7f4;
  }}
  tbody tr:nth-child(odd) {{
    background: #fff;
  }}
  td, th {{
    padding: 5pt 8pt;
    border: 1px solid #c8e6c9;
    vertical-align: top;
  }}

  /* ── Lists ── */
  ul, ol {{
    margin: 4pt 0 10pt 0;
    padding-left: 20pt;
  }}
  li {{
    margin-bottom: 3pt;
  }}

  /* ── Blockquotes (used for notes) ── */
  blockquote {{
    border-left: 4px solid #D4A017;
    background: #fffde7;
    margin: 10pt 0;
    padding: 8pt 12pt;
    border-radius: 0 4px 4px 0;
    font-size: 9.5pt;
  }}
  blockquote p {{
    margin: 0;
  }}

  /* ── Horizontal rule ── */
  hr {{
    border: none;
    border-top: 1.5px solid #c8e6c9;
    margin: 18pt 0;
  }}

  /* ── TOC ── */
  .toc {{
    background: #f0f7f4;
    border: 1px solid #c8e6c9;
    border-radius: 6px;
    padding: 12pt 16pt;
    margin-bottom: 20pt;
    page-break-inside: avoid;
  }}
  .toc ul {{
    margin: 0;
    padding-left: 16pt;
  }}
  .toc li {{
    margin-bottom: 2pt;
  }}

  /* ── Page breaks ── */
  h2 {{ page-break-before: auto; }}
  h2:nth-of-type(1) {{ page-break-before: avoid; }}
</style>
</head>
<body>
{body_html}
</body>
</html>"""

# ── Render to PDF ────────────────────────────────────────────────────────────
from weasyprint import HTML, CSS

print(f"Rendering {MD_FILE.name} → {PDF_FILE.name} ...")
HTML(string=html, base_url=str(BASE)).write_pdf(str(PDF_FILE))
print(f"Done! PDF saved to: {PDF_FILE}")

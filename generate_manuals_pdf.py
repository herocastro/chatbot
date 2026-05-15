"""Generate PDFs for MANUAL_LIBRARIAN.md and MANUAL_PATRON.md."""

import pathlib
import markdown
from weasyprint import HTML

BASE = pathlib.Path(__file__).parent

# ── Shared CSS ───────────────────────────────────────────────────────────────
SHARED_CSS = """
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
body {{
    font-family: 'Segoe UI', Arial, Helvetica, sans-serif;
    font-size: 10.5pt;
    line-height: 1.65;
    color: #1a1a1a;
    margin: 0;
    padding: 0;
}}
h1 {{
    font-size: 22pt;
    font-weight: 700;
    color: {accent};
    border-bottom: 3px solid {accent};
    padding-bottom: 6pt;
    margin-top: 0;
    margin-bottom: 14pt;
    page-break-before: avoid;
}}
h2 {{
    font-size: 14pt;
    font-weight: 700;
    color: {accent};
    border-bottom: 1.5px solid {accent_light};
    padding-bottom: 4pt;
    margin-top: 22pt;
    margin-bottom: 8pt;
    page-break-after: avoid;
}}
h3 {{
    font-size: 11.5pt;
    font-weight: 700;
    color: {accent_dark};
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
p {{
    margin: 0 0 8pt 0;
    orphans: 3;
    widows: 3;
}}
a {{
    color: {accent};
    text-decoration: none;
}}
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
    border-left: 4px solid {accent};
    border-radius: 4px;
    padding: 10pt 12pt;
    font-family: 'Courier New', Courier, monospace;
    font-size: 8.5pt;
    line-height: 1.5;
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
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 10pt 0 14pt 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
}}
thead tr {{
    background: {accent};
    color: #fff;
}}
thead th {{
    padding: 6pt 8pt;
    text-align: left;
    font-weight: 600;
}}
tbody tr:nth-child(even) {{
    background: {row_alt};
}}
tbody tr:nth-child(odd) {{
    background: #fff;
}}
td, th {{
    padding: 5pt 8pt;
    border: 1px solid {accent_light};
    vertical-align: top;
}}
ul, ol {{
    margin: 4pt 0 10pt 0;
    padding-left: 20pt;
}}
li {{
    margin-bottom: 3pt;
}}
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
hr {{
    border: none;
    border-top: 1.5px solid {accent_light};
    margin: 18pt 0;
}}
"""

def build_html(md_text: str, accent: str, accent_light: str, accent_dark: str, row_alt: str) -> str:
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc"])
    body = md.convert(md_text)
    css = SHARED_CSS.format(
        accent=accent,
        accent_light=accent_light,
        accent_dark=accent_dark,
        row_alt=row_alt,
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>{css}</style>
</head>
<body>{body}</body>
</html>"""


# ── Librarian Manual ─────────────────────────────────────────────────────────
print("Generating MANUAL_LIBRARIAN.pdf ...")
lib_md = (BASE / "MANUAL_LIBRARIAN.md").read_text(encoding="utf-8")
lib_html = build_html(
    lib_md,
    accent="#0E553F",       # library green
    accent_light="#c8e6c9",
    accent_dark="#1b5e20",
    row_alt="#f0f7f4",
)
HTML(string=lib_html, base_url=str(BASE)).write_pdf(str(BASE / "MANUAL_LIBRARIAN.pdf"))
print("  → MANUAL_LIBRARIAN.pdf done")


# ── Patron Guide ─────────────────────────────────────────────────────────────
print("Generating MANUAL_PATRON.pdf ...")
pat_md = (BASE / "MANUAL_PATRON.md").read_text(encoding="utf-8")
pat_html = build_html(
    pat_md,
    accent="#1565C0",       # friendly blue for patron-facing doc
    accent_light="#bbdefb",
    accent_dark="#0d47a1",
    row_alt="#e3f2fd",
)
HTML(string=pat_html, base_url=str(BASE)).write_pdf(str(BASE / "MANUAL_PATRON.pdf"))
print("  → MANUAL_PATRON.pdf done")

print("\nAll PDFs generated successfully.")

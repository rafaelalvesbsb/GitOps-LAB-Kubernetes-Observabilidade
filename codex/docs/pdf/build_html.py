#!/usr/bin/env python3
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "_build.html"
VENDOR = HERE / "vendor"

DOCS = [
    ("prompt", "PROMPT.md", ROOT / "PROMPT.md"),
    ("arquitetura", "ARQUITETURA.md", ROOT / "docs" / "ARQUITETURA.md"),
    ("guia", "GUIA-DE-IMPLEMENTACAO.md", ROOT / "docs" / "GUIA-DE-IMPLEMENTACAO.md"),
]

CSS = """
:root{
  --bg:#0b1020; --panel:#111827; --panel2:#162032; --border:#2f3f5f;
  --text:#d8e1ee; --muted:#8ea3bd; --heading:#f8fafc;
  --blue:#67e8f9; --green:#86efac; --orange:#fbbf24; --red:#fca5a5;
  --mono:'JetBrains Mono','Consolas','Courier New',monospace;
  --sans:'Segoe UI','Inter',Arial,sans-serif;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{background:var(--bg); color:var(--text); font-family:var(--sans); font-size:14px; line-height:1.62}
.page{max-width:900px; margin:0 auto; padding:48px 58px}
.cover{
  min-height:100vh; display:flex; flex-direction:column; justify-content:center;
  background:linear-gradient(135deg,#0b1020 0%,#152238 52%,#0b1020 100%);
  border-bottom:1px solid var(--border); page-break-after:always;
}
.cover .badge{
  display:inline-block; font-family:var(--mono); font-size:11px; font-weight:700;
  letter-spacing:.22em; color:var(--blue); text-transform:uppercase;
  border:1px solid rgba(103,232,249,.35); padding:6px 12px; border-radius:5px;
  background:rgba(103,232,249,.08); margin-bottom:22px;
}
.cover h1{font-family:var(--mono); color:var(--heading); font-size:38px; line-height:1.22; margin:0 0 16px}
.cover p{color:var(--muted); max-width:680px; font-size:15px; margin:0 0 34px}
.chips{display:flex; flex-wrap:wrap; gap:8px; max-width:700px}
.chip{font-family:var(--mono); color:var(--green); font-size:11px; padding:5px 10px; border-radius:5px; border:1px solid rgba(134,239,172,.28); background:rgba(134,239,172,.07)}
.meta{margin-top:46px; color:#6f829a; font-family:var(--mono); font-size:11px}
.toc{page-break-after:always}
.toc h2{font-family:var(--mono); color:var(--blue); letter-spacing:.16em; text-transform:uppercase; font-size:14px}
.toc ol{list-style:none; counter-reset:toc; padding:0; margin:20px 0 0}
.toc li{counter-increment:toc; display:flex; gap:14px; padding:11px 0; border-bottom:1px solid var(--panel2)}
.toc li:before{content:counter(toc, decimal-leading-zero); font-family:var(--mono); color:var(--orange); min-width:30px}
.toc a{color:var(--heading); text-decoration:none; font-weight:700}
.toc span{display:block; color:var(--muted); font-size:12px; margin-top:2px}
.doc-cover{
  page-break-before:always; page-break-after:always; min-height:48vh;
  display:flex; flex-direction:column; justify-content:center; padding:48px;
  background:var(--panel); border-left:6px solid var(--blue); border-radius:8px;
}
.doc-cover .tag{font-family:var(--mono); color:var(--muted); font-size:12px; letter-spacing:.18em; text-transform:uppercase; margin-bottom:12px}
.doc-cover h1{font-family:var(--mono); color:var(--heading); font-size:30px; margin:0}
.doc-body h1{font-family:var(--mono); color:var(--blue); font-size:24px; margin:38px 0 16px; padding-bottom:10px; border-bottom:1px solid var(--border); page-break-before:always}
.doc-body > h1:first-child{page-break-before:avoid}
.doc-body h2{font-family:var(--mono); color:var(--orange); font-size:19px; margin:30px 0 12px}
.doc-body h3{font-family:var(--mono); color:var(--green); font-size:15px; margin:24px 0 10px}
.doc-body p,.doc-body li{font-size:13.5px}
.doc-body strong{color:var(--heading)}
.doc-body a{color:var(--blue)}
.doc-body code{font-family:var(--mono); font-size:12px; color:var(--blue); background:rgba(103,232,249,.10); border:1px solid rgba(103,232,249,.18); padding:1px 5px; border-radius:4px}
.doc-body pre{background:var(--panel); border:1px solid var(--border); border-radius:8px; padding:16px; overflow-x:auto; page-break-inside:avoid}
.doc-body pre code{background:none; border:none; color:#bed4ea; padding:0; font-size:11.5px}
.doc-body table{border-collapse:collapse; width:100%; margin:18px 0; font-size:12px; page-break-inside:avoid}
.doc-body th{font-family:var(--mono); color:var(--blue); background:var(--panel); border:1px solid var(--border); padding:8px 11px; text-align:left}
.doc-body td{border:1px solid var(--border); padding:8px 11px; vertical-align:top}
.doc-body blockquote{border-left:3px solid var(--blue); margin:16px 0; padding:8px 16px; background:rgba(103,232,249,.06); color:var(--muted)}
.footer{text-align:center; color:#60758f; font-family:var(--mono); font-size:11px; padding:28px}
@media print{.page{padding:0 8px} body{font-size:12.5px}}
"""

HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8"/>
<title>Plataforma GitOps Kubernetes - Codex</title>
<style>__CSS__</style>
</head>
<body>
<section class="cover">
  <div class="page">
    <span class="badge">Codex · GitOps · Kubernetes</span>
    <h1>Plataforma GitOps Kubernetes<br/>Implementacao Codex</h1>
    <p>
      Prompt, arquitetura e guia de implementacao para uma plataforma GitOps Kubernetes
      entregue em fases: MVP funcional primeiro, depois observabilidade, seguranca,
      CI/CD, producao e backup.
    </p>
    <div class="chips">__CHIPS__</div>
    <div class="meta">Repositorio: GitOps-LAB-Kubernetes-Observabilidade · Documento Codex</div>
  </div>
</section>
<section class="page toc">
  <h2>Sumario</h2>
  <ol>
    <li><div><a href="#doc-prompt">PROMPT</a><span>Especificacao da implementacao Codex</span></div></li>
    <li><div><a href="#doc-arquitetura">ARQUITETURA</a><span>Camadas, paineis web e decisoes tecnicas</span></div></li>
    <li><div><a href="#doc-guia">GUIA DE IMPLEMENTACAO</a><span>Fases incrementais e criterios de saida</span></div></li>
  </ol>
</section>
__SECTIONS__
<div class="footer">Gerado a partir de codex/PROMPT.md e codex/docs/*.md</div>
<script type="text/markdown" id="md-prompt">__MD_PROMPT__</script>
<script type="text/markdown" id="md-arquitetura">__MD_ARQUITETURA__</script>
<script type="text/markdown" id="md-guia">__MD_GUIA__</script>
<script>__MARKED_JS__</script>
<script>
marked.setOptions({gfm:true, breaks:false});
function render(id,target){document.getElementById(target).innerHTML = marked.parse(document.getElementById(id).textContent);}
render('md-prompt','render-prompt');
render('md-arquitetura','render-arquitetura');
render('md-guia','render-guia');
</script>
</body>
</html>
"""

SECTION = """
<section class="page" id="doc-__ANCHOR__">
  <div class="doc-cover">
    <div class="tag">Documento __NUM__ de 3 · __FILENAME__</div>
    <h1>__TITLE__</h1>
  </div>
  <div class="doc-body" id="render-__ANCHOR__"></div>
</section>
"""

TITLES = {
    "prompt": "PROMPT - Especificacao Codex",
    "arquitetura": "ARQUITETURA - Visao e Decisoes",
    "guia": "GUIA DE IMPLEMENTACAO - Fases",
}

CHIPS = [
    "kind", "ArgoCD", "Kustomize", "NGINX Ingress", "cert-manager",
    "Headlamp", "Grafana", "Prometheus", "Sealed Secrets", "Velero"
]


def main():
    sections = []
    markdown = {}
    for index, (anchor, filename, path) in enumerate(DOCS, start=1):
        markdown[anchor] = path.read_text(encoding="utf-8")
        sections.append(
            SECTION
            .replace("__ANCHOR__", anchor)
            .replace("__NUM__", str(index))
            .replace("__FILENAME__", filename)
            .replace("__TITLE__", TITLES[anchor])
        )

    marked_js = (VENDOR / "marked.min.js").read_text(encoding="utf-8")
    html = (
        HTML
        .replace("__CSS__", CSS)
        .replace("__CHIPS__", "".join(f'<span class="chip">{chip}</span>' for chip in CHIPS))
        .replace("__SECTIONS__", "".join(sections))
        .replace("__MD_PROMPT__", markdown["prompt"])
        .replace("__MD_ARQUITETURA__", markdown["arquitetura"])
        .replace("__MD_GUIA__", markdown["guia"])
        .replace("__MARKED_JS__", marked_js)
    )
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({len(html)} bytes)")


if __name__ == "__main__":
    main()

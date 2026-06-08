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
  --bg:#0A0E1A; --panel:#0D1321; --border:#1E3A5F;
  --text:#D7E3F4; --muted:#7A9CC0; --heading:#F0F6FF;
  --blue:#7BC8FF; --blue2:#326CE5; --orange:#EF7B4D;
  --green:#4ADE80; --purple:#A78BFA; --yellow:#FBBF24;
  --mono:'JetBrains Mono','Fira Code','Courier New',monospace;
  --sans:'Segoe UI','Inter',Arial,sans-serif;
}
*{box-sizing:border-box;}
html,body{margin:0;padding:0;}
body{
  background:var(--bg); color:var(--text); font-family:var(--sans);
  font-size:14px; line-height:1.65;
}
.page{ max-width:880px; margin:0 auto; padding:48px 56px; }

/* Cover */
.cover{
  min-height:100vh; display:flex; flex-direction:column; justify-content:center;
  background:linear-gradient(135deg,#0D1321 0%,#1A2744 50%,#0D1321 100%);
  border-bottom:1px solid var(--border); padding:64px;
  page-break-after:always;
}
.cover .badge{
  display:inline-block; font-family:var(--mono); font-size:11px; font-weight:700;
  letter-spacing:.25em; color:var(--blue); text-transform:uppercase;
  background:rgba(50,108,229,.12); padding:5px 14px; border-radius:4px;
  border:1px solid rgba(50,108,229,.35); margin-bottom:22px;
}
.cover h1{
  font-family:var(--mono); font-size:38px; font-weight:800; color:var(--heading);
  margin:0 0 14px; line-height:1.25; letter-spacing:-0.02em;
}
.cover p.sub{ color:var(--muted); font-size:15px; margin:0 0 36px; max-width:620px;}
.cover .stack{ display:flex; flex-wrap:wrap; gap:8px; max-width:640px; }
.cover .chip{
  font-family:var(--mono); font-size:11px; color:var(--blue);
  background:rgba(50,108,229,.10); border:1px solid rgba(50,108,229,.28);
  border-radius:5px; padding:5px 12px;
}
.cover .meta{ margin-top:48px; color:#4A6A8A; font-family:var(--mono); font-size:11px; }

/* TOC */
.toc{ page-break-after:always; padding-top:24px;}
.toc h2{ font-family:var(--mono); color:var(--blue); letter-spacing:.12em; font-size:14px; text-transform:uppercase;}
.toc ol{ list-style:none; counter-reset:toc; padding:0; margin:18px 0 0;}
.toc li{
  counter-increment:toc; display:flex; gap:14px; align-items:baseline;
  padding:10px 0; border-bottom:1px solid var(--panel);
}
.toc li::before{
  content: counter(toc, decimal-leading-zero); font-family:var(--mono); color:var(--blue2);
  font-size:12px; min-width:28px;
}
.toc li a{ color:var(--heading); text-decoration:none; font-weight:600; font-size:14px;}
.toc li span{ color:var(--muted); font-size:12px; }

/* Section divider */
.doc-cover{
  page-break-before:always; page-break-after:always;
  min-height:50vh; display:flex; flex-direction:column; justify-content:center;
  border-left:6px solid var(--blue2); background:var(--panel); border-radius:8px;
  padding:48px;
}
.doc-cover .tag{ font-family:var(--mono); color:var(--muted); font-size:12px; letter-spacing:.18em; text-transform:uppercase; margin-bottom:10px;}
.doc-cover h1{ font-family:var(--mono); font-size:30px; color:var(--heading); margin:0; }

/* Markdown content rendering */
.doc-body{ padding-top:8px; }
.doc-body h1{
  font-family:var(--mono); color:var(--blue); font-size:24px; margin:40px 0 16px;
  padding-bottom:10px; border-bottom:1px solid var(--border);
  page-break-before:always;
}
.doc-body > h1:first-child{ page-break-before:avoid; }
.doc-body h2{ font-family:var(--mono); color:var(--orange); font-size:19px; margin:32px 0 12px; }
.doc-body h3{ font-family:var(--mono); color:var(--green); font-size:15px; margin:26px 0 10px; }
.doc-body h4{ color:var(--purple); font-size:13px; margin:20px 0 8px; }
.doc-body p, .doc-body li{ color:var(--text); font-size:13.5px; }
.doc-body strong{ color:var(--heading); }
.doc-body a{ color:var(--blue); }
.doc-body code{
  font-family:var(--mono); font-size:12px; background:rgba(50,108,229,.12);
  color:var(--blue); padding:1px 6px; border-radius:4px; border:1px solid rgba(50,108,229,.2);
}
.doc-body pre{
  background:var(--panel); border:1px solid var(--border); border-radius:8px;
  padding:16px; overflow-x:auto; page-break-inside:avoid;
}
.doc-body pre code{
  background:none; border:none; color:#A8C4E0; padding:0; font-size:11.5px; line-height:1.6;
}
.doc-body blockquote{
  border-left:3px solid var(--blue2); margin:16px 0; padding:8px 18px;
  background:rgba(50,108,229,.06); color:var(--muted); border-radius:0 6px 6px 0;
  page-break-inside:avoid;
}
.doc-body table{
  border-collapse:collapse; width:100%; margin:18px 0; font-size:12px;
  page-break-inside:avoid;
}
.doc-body th{
  font-family:var(--mono); text-align:left; color:var(--blue); background:var(--panel);
  border:1px solid var(--border); padding:8px 12px; font-size:11px; letter-spacing:.04em;
}
.doc-body td{ border:1px solid var(--border); padding:8px 12px; color:var(--text); vertical-align:top;}
.doc-body tr:nth-child(even) td{ background:rgba(255,255,255,.02); }
.doc-body hr{ border:none; border-top:1px solid var(--border); margin:36px 0; }
.doc-body ul, .doc-body ol{ padding-left:22px; }
.doc-body li{ margin:4px 0; }
.doc-body li > ul, .doc-body li > ol { margin-top:4px; }
.doc-body input[type=checkbox]{ margin-right:8px; }

/* Mermaid diagrams */
.doc-body .mermaid{
  background:var(--panel); border:1px solid var(--border); border-radius:8px;
  padding:18px; margin:18px 0; page-break-inside:avoid; text-align:center;
}

/* Footer / page meta (screen only, print uses browser headers off) */
.footer{ text-align:center; color:#2A4A6A; font-size:11px; padding:28px 0 4px; font-family:var(--mono);}

@media print{
  .page{ padding:0 8px; }
  body{ font-size:12.5px; }
}
"""

# NOTE: uses __TOKEN__ placeholders + str.replace() (not str.format()) because the
# vendored JS payloads contain literal "{" / "}" that would break .format().
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8"/>
<title>Plataforma GitOps Kubernetes — Dev + Produção</title>
<style>__CSS__</style>
</head>
<body>

<section class="cover">
  <div class="page" style="max-width:720px;">
    <span class="badge">GitOps · Kubernetes · Observabilidade</span>
    <h1>Plataforma GitOps Kubernetes<br/>Multi-Ambiente — Dev + Produção</h1>
    <p class="sub">
      Especificação, arquitetura e guia de implementação de um laboratório GitOps
      completo: Kubernetes (kind/cloud-agnostic) · ArgoCD · Prometheus &amp; Grafana ·
      Headlamp · cert-manager · CoreDNS · GitHub Actions — desenhado com rigor de
      produção desde o primeiro commit (segurança, observabilidade e promoção
      dev → prod via Pull Request).
    </p>
    <div class="stack">
      __CHIPS__
    </div>
    <div class="meta">
      Repositório: GitOps-LAB-Kubernetes-Observabilidade &nbsp;·&nbsp;
      Documento gerado para planejamento e execução faseada
    </div>
  </div>
</section>

<section class="page toc">
  <h2>Sumário</h2>
  <ol>
    <li><a href="#doc-prompt">PROMPT — Especificação / Blueprint</a><span>O que construir, requisitos por componente, critérios de aceite</span></li>
    <li><a href="#doc-arquitetura">ARQUITETURA — Visão Geral e Decisões</a><span>Diagramas, comparação dev↔prod, justificativas técnicas</span></li>
    <li><a href="#doc-guia">GUIA DE IMPLEMENTAÇÃO — Passo a Passo</a><span>12 fases com critério de saída objetivo, comandos e troubleshooting</span></li>
  </ol>
</section>

__SECTIONS__

<div class="footer">Plataforma GitOps Kubernetes · Dev + Produção — documento técnico gerado a partir de PROMPT.md, ARQUITETURA.md e GUIA-DE-IMPLEMENTACAO.md</div>

<script type="text/markdown" id="md-prompt">__MD_PROMPT__</script>
<script type="text/markdown" id="md-arquitetura">__MD_ARQUITETURA__</script>
<script type="text/markdown" id="md-guia">__MD_GUIA__</script>

<script>/* ---- marked.js (vendored) ---- */ __MARKED_JS__</script>
<script>/* ---- mermaid.js (vendored) ---- */ __MERMAID_JS__</script>
<script>
  marked.setOptions({ gfm:true, breaks:false });

  function render(id, target) {
    var src = document.getElementById(id).textContent;
    document.getElementById(target).innerHTML = marked.parse(src);
  }
  render('md-prompt', 'render-prompt');
  render('md-arquitetura', 'render-arquitetura');
  render('md-guia', 'render-guia');

  // Convert ```mermaid code blocks (rendered as <pre><code class="language-mermaid">) into <div class="mermaid">
  document.querySelectorAll('.doc-body pre > code.language-mermaid').forEach(function(code){
    var div = document.createElement('div');
    div.className = 'mermaid';
    div.textContent = code.textContent;
    code.parentElement.replaceWith(div);
  });

  mermaid.initialize({ startOnLoad:false, theme:'dark', securityLevel:'loose',
    themeVariables: {
      background:'#0D1321', primaryColor:'#16233d', primaryTextColor:'#E2E8F0',
      primaryBorderColor:'#326CE5', lineColor:'#4A6A8A', secondaryColor:'#1A2744',
      tertiaryColor:'#0D1321', fontFamily:'JetBrains Mono, monospace'
    }
  });
  mermaid.run({ querySelector:'.mermaid' }).then(function(){
    var d = document.createElement('div');
    d.id = '__render_done__';
    document.body.appendChild(d);
  });
</script>

</body>
</html>
"""

SECTION_TEMPLATE = """
<section class="page" id="doc-__ANCHOR__">
  <div class="doc-cover">
    <div class="tag">Documento __NUM__ de 3 · __FILENAME__</div>
    <h1>__TITLE__</h1>
  </div>
  <div class="doc-body" id="render-__ANCHOR__"></div>
</section>
"""

CHIPS = ["Kubernetes (kind / cloud-agnostic)", "ArgoCD · App of Apps", "Prometheus + Grafana",
         "Headlamp", "cert-manager · TLS", "CoreDNS / external-dns", "GitHub Actions CI/CD",
         "Kustomize base + overlays", "Sealed Secrets", "Velero backup"]

def esc_for_script(text: str) -> str:
    # Content lives inside <script type="text/markdown">; only the literal sequence
    # "</script" would terminate it early. Markdown here never contains that.
    return text

def main():
    titles = {
        "prompt": "PROMPT — Especificação / Blueprint da Plataforma",
        "arquitetura": "ARQUITETURA — Visão Geral, Diagramas e Decisões",
        "guia": "GUIA DE IMPLEMENTAÇÃO — Passo a Passo Faseado",
    }
    sections_html = []
    md = {}
    for i, (anchor, filename, path) in enumerate(DOCS, start=1):
        text = path.read_text(encoding="utf-8")
        md[anchor] = esc_for_script(text)
        section = (SECTION_TEMPLATE
                   .replace("__ANCHOR__", anchor)
                   .replace("__NUM__", str(i))
                   .replace("__FILENAME__", filename)
                   .replace("__TITLE__", titles[anchor]))
        sections_html.append(section)

    chips_html = "\n      ".join(f'<span class="chip">{c}</span>' for c in CHIPS)

    marked_js = (VENDOR / "marked.min.js").read_text(encoding="utf-8")
    mermaid_js = (VENDOR / "mermaid.min.js").read_text(encoding="utf-8")

    html = (HTML_TEMPLATE
            .replace("__CSS__", CSS)
            .replace("__CHIPS__", chips_html)
            .replace("__SECTIONS__", "".join(sections_html))
            .replace("__MD_PROMPT__", md["prompt"])
            .replace("__MD_ARQUITETURA__", md["arquitetura"])
            .replace("__MD_GUIA__", md["guia"])
            .replace("__MARKED_JS__", marked_js)
            .replace("__MERMAID_JS__", mermaid_js))

    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({len(html)} bytes)")

if __name__ == "__main__":
    main()

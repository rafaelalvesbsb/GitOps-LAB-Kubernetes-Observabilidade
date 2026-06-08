# PDF da documentação

`Plataforma-GitOps-K8s-Dev-Prod.pdf` é a versão consolidada e estilizada (capa, sumário,
diagramas Mermaid renderizados, tabelas) de três documentos-fonte:

- [`../../PROMPT.md`](../../PROMPT.md)
- [`../ARQUITETURA.md`](../ARQUITETURA.md)
- [`../GUIA-DE-IMPLEMENTACAO.md`](../GUIA-DE-IMPLEMENTACAO.md)

> **Os `.md` acima são a fonte da verdade.** O PDF é gerado a partir deles — para
> atualizar o PDF, edite os `.md` e rode o build novamente (abaixo). Não edite o PDF
> diretamente.

## Como regenerar

Pré-requisitos (uma vez): bibliotecas JS vendorizadas localmente em `vendor/`
(`marked.min.js` e `mermaid.min.js`) — necessárias porque o PDF é renderizado via
um navegador headless sem depender de CDN externo durante a geração:

```bash
mkdir -p vendor
curl -sS -o vendor/marked.min.js   https://cdn.jsdelivr.net/npm/marked/marked.min.js
curl -sS -o vendor/mermaid.min.js  https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js
```

1. Monta o HTML estilizado a partir dos três `.md` (Markdown → HTML via `marked.js`,
   diagramas ```mermaid``` → SVG via `mermaid.js`, tudo embutido inline no HTML):

   ```bash
   python3 build_html.py        # gera ./_build.html
   ```

2. Imprime o HTML em PDF usando o Microsoft Edge (Chromium) em modo headless —
   funciona em qualquer Windows com Edge instalado, sem depender de `pandoc`/`wkhtmltopdf`:

   ```bash
   "/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
     --headless=new --disable-gpu --no-sandbox \
     --user-data-dir="$(pwd)/edge-profile" \
     --virtual-time-budget=30000 \
     --run-all-compositor-stages-before-draw \
     --print-to-pdf="$(pwd)/Plataforma-GitOps-K8s-Dev-Prod.pdf" \
     --print-to-pdf-no-header \
     "file:///C:/<caminho completo até este diretório>/_build.html"
   ```

   > ⚠️ O `file://` precisa do caminho no formato Windows com letra de unidade
   > (`file:///C:/Users/...`), não no formato estilo-Unix do Git Bash (`/c/Users/...`)
   > — o Edge interpreta o segundo como um 404.

3. `_build.html` e `edge-profile/` são artefatos de build (ignorados no Git) — pode
   apagá-los a qualquer momento; `python3 build_html.py` os recria.

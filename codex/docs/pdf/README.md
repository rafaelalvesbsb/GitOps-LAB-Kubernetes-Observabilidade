# PDF da documentacao Codex

`Plataforma-GitOps-K8s-Codex.pdf` e a versao consolidada e estilizada dos documentos:

- [`../../PROMPT.md`](../../PROMPT.md)
- [`../ARQUITETURA.md`](../ARQUITETURA.md)
- [`../GUIA-DE-IMPLEMENTACAO.md`](../GUIA-DE-IMPLEMENTACAO.md)

Os arquivos Markdown sao a fonte da verdade. O PDF deve ser regenerado depois de editar
os `.md`.

O PDF inclui uma secao visual de diagramas desenhados pelo gerador:

- visao de componentes;
- acesso web e entrada de trafego;
- fluxo GitOps e promocao;
- observabilidade.

## Como regenerar

1. Gerar o HTML:

   ```bash
   python build_html.py
   ```

2. Gerar o PDF com Microsoft Edge headless:

   ```bash
   "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" ^
     --headless=new --disable-gpu --no-sandbox ^
     --user-data-dir="%CD%\edge-profile" ^
     --virtual-time-budget=30000 ^
     --run-all-compositor-stages-before-draw ^
     --print-to-pdf="%CD%\Plataforma-GitOps-K8s-Codex.pdf" ^
     --print-to-pdf-no-header ^
     "file:///%CD:\=/%/_build.html"
   ```

`_build.html` e `edge-profile/` sao artefatos de build e podem ser removidos.

## Geracao offline recomendada

No servidor atual, o Edge headless pode falhar por limitacao de GPU/headless. O caminho
recomendado para gerar o PDF Codex e o gerador estilizado offline:

```bash
python build_pdf_styled.py
```

#!/usr/bin/env python3
import pathlib
import re
import textwrap

from fpdf import FPDF

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "Plataforma-GitOps-K8s-Codex.pdf"

DOCS = [
    ("PROMPT", "Especificacao da implementacao Codex", ROOT / "PROMPT.md"),
    ("ARQUITETURA", "Camadas, paineis web e decisoes tecnicas", ROOT / "docs" / "ARQUITETURA.md"),
    ("GUIA DE IMPLEMENTACAO", "Fases incrementais e criterios de saida", ROOT / "docs" / "GUIA-DE-IMPLEMENTACAO.md"),
]

FONT_DIR = pathlib.Path("C:/Windows/Fonts")


def clean_inline(text):
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.strip()


def safe_text(text):
    return text.encode("latin-1", "replace").decode("latin-1")


def parse_markdown(path):
    items = []
    in_code = False
    code_lang = ""
    code = []
    table = []

    def flush_table():
        nonlocal table
        if table:
            rows = []
            for row in table:
                cols = [clean_inline(col.strip()) for col in row.strip("|").split("|")]
                if not all(set(col) <= {"-", ":", " "} for col in cols):
                    rows.append(cols)
            if rows:
                items.append(("table", rows))
            table = []

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_table()
            if in_code:
                items.append(("mermaid", code) if code_lang == "mermaid" else ("code", code))
                code = []
                code_lang = ""
                in_code = False
            else:
                code_lang = stripped.strip("`").strip()
                in_code = True
            continue

        if in_code:
            code.append(line)
            continue

        if "|" in stripped and stripped.count("|") >= 2:
            table.append(stripped)
            continue
        flush_table()

        if not stripped:
            items.append(("space", ""))
        elif stripped.startswith("# "):
            items.append(("h1", clean_inline(stripped[2:])))
        elif stripped.startswith("## "):
            items.append(("h2", clean_inline(stripped[3:])))
        elif stripped.startswith("### "):
            items.append(("h3", clean_inline(stripped[4:])))
        elif re.match(r"^[-*]\s+", stripped):
            items.append(("bullet", clean_inline(re.sub(r"^[-*]\s+", "", stripped))))
        elif re.match(r"^\d+\.\s+", stripped):
            items.append(("number", clean_inline(stripped)))
        else:
            items.append(("p", clean_inline(stripped)))

    flush_table()
    if code:
        items.append(("mermaid", code) if code_lang == "mermaid" else ("code", code))
    return items


class CodexPdf(FPDF):
    bg = (10, 14, 26)
    panel = (13, 19, 33)
    panel2 = (20, 31, 49)
    border = (36, 58, 88)
    body_text = (218, 228, 240)
    muted = (128, 154, 184)
    heading = (245, 249, 255)
    blue = (123, 200, 255)
    kube = (50, 108, 229)
    green = (74, 222, 128)
    orange = (239, 123, 77)

    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(17, 18, 17)
        self.alias_nb_pages()
        self._load_fonts()
        self.section_title = ""

    def _load_fonts(self):
        try:
            self.add_font("Segoe", "", str(FONT_DIR / "segoeui.ttf"))
            self.add_font("Segoe", "B", str(FONT_DIR / "segoeuib.ttf"))
            self.add_font("Segoe", "I", str(FONT_DIR / "segoeuii.ttf"))
            self.add_font("Consolas", "", str(FONT_DIR / "consola.ttf"))
        except Exception:
            self.set_font("Helvetica", "", 10)

    def font_name(self, mono=False):
        return "Consolas" if mono else "Segoe"

    def set_rgb(self, color, fill=False):
        if fill:
            self.set_fill_color(*color)
        else:
            self.set_text_color(*color)

    def header(self):
        if self.page_no() <= 2:
            return
        self.set_fill_color(*self.bg)
        self.rect(0, 0, 210, 297, "F")
        self.set_fill_color(*self.panel2)
        self.rect(0, 0, 210, 8, "F")
        self.set_draw_color(*self.border)
        self.line(17, 16, 193, 16)
        self.set_font(self.font_name(True), "", 7.5)
        self.set_text_color(*self.muted)
        self.set_xy(17, 10)
        self.cell(120, 4, safe_text("Codex · GitOps Kubernetes"), border=0)
        self.set_xy(130, 10)
        self.cell(63, 4, safe_text(self.section_title), border=0, align="R")
        self.set_y(22)

    def footer(self):
        if self.page_no() <= 1:
            return
        self.set_draw_color(*self.border)
        self.line(17, 282, 193, 282)
        self.set_font(self.font_name(True), "", 7.5)
        self.set_text_color(*self.muted)
        self.set_xy(17, 286)
        self.cell(80, 4, "GitOps-LAB-Kubernetes-Observabilidade")
        self.set_xy(160, 286)
        self.cell(33, 4, f"Pagina {self.page_no()}/{{nb}}", align="R")

    def dark_page(self):
        self.add_page()
        self.set_fill_color(*self.bg)
        self.rect(0, 0, 210, 297, "F")

    def cover(self):
        self.dark_page()
        self.set_fill_color(*self.panel)
        self.rect(0, 0, 210, 297, "F")
        self.set_fill_color(*self.kube)
        self.rect(0, 0, 7, 297, "F")
        self.set_fill_color(16, 30, 50)
        self.rect(7, 0, 203, 95, "F")
        self.set_fill_color(10, 14, 26)
        self.rect(7, 95, 203, 202, "F")

        self.set_xy(22, 56)
        self.set_font(self.font_name(True), "", 8)
        self.set_text_color(*self.blue)
        self.cell(0, 5, "CODEX · GITOPS · KUBERNETES · OBSERVABILIDADE")

        self.set_xy(22, 78)
        self.set_font(self.font_name(), "B", 30)
        self.set_text_color(*self.heading)
        self.cell(0, 12, "Plataforma GitOps")
        self.set_xy(22, 92)
        self.cell(0, 12, "Kubernetes")

        self.set_xy(22, 112)
        self.set_font(self.font_name(), "B", 17)
        self.set_text_color(*self.green)
        self.cell(0, 8, "Implementacao Codex")

        self.set_xy(22, 133)
        self.set_font(self.font_name(), "", 10.5)
        self.set_text_color(*self.muted)
        self.multi_cell(150, 6, safe_text(
            "Prompt, arquitetura e guia de implementacao para uma plataforma GitOps Kubernetes "
            "entregue em fases: MVP funcional primeiro, depois observabilidade, seguranca, "
            "CI/CD, producao e backup."
        ))

        chips = ["kind", "ArgoCD", "Kustomize", "NGINX Ingress", "cert-manager",
                 "Headlamp", "Grafana", "Prometheus", "Sealed Secrets", "Velero"]
        x, y = 22, 170
        self.set_font(self.font_name(True), "", 7.5)
        for chip in chips:
            width = max(18, self.get_string_width(chip) + 8)
            if x + width > 185:
                x, y = 22, y + 11
            self.set_fill_color(15, 32, 48)
            self.set_draw_color(44, 92, 118)
            self.rect(x, y, width, 7, "DF")
            self.set_xy(x + 4, y + 1.5)
            self.set_text_color(*self.green)
            self.cell(width - 8, 3, chip)
            x += width + 4

        self.set_xy(22, 255)
        self.set_font(self.font_name(True), "", 7.5)
        self.set_text_color(*self.muted)
        self.cell(0, 5, "Repositorio: GitOps-LAB-Kubernetes-Observabilidade")

    def toc(self):
        self.dark_page()
        self.set_xy(17, 38)
        self.set_font(self.font_name(True), "", 8)
        self.set_text_color(*self.blue)
        self.cell(0, 5, "SUMARIO")
        self.set_xy(17, 50)
        self.set_font(self.font_name(), "B", 24)
        self.set_text_color(*self.heading)
        self.cell(0, 10, "Documentos")

        y = 78
        toc_items = [("DIAGRAMAS", "Visao visual do ambiente, acessos, GitOps e monitoramento")]
        toc_items.extend((title, subtitle) for title, subtitle, _path in DOCS)
        for index, (title, subtitle) in enumerate(toc_items, start=1):
            self.set_fill_color(*self.panel)
            self.set_draw_color(*self.border)
            self.rect(17, y, 176, 27, "DF")
            self.set_xy(24, y + 6)
            self.set_font(self.font_name(True), "", 10)
            self.set_text_color(*self.orange)
            self.cell(16, 5, f"{index:02d}")
            self.set_xy(43, y + 5)
            self.set_font(self.font_name(), "B", 12)
            self.set_text_color(*self.heading)
            self.cell(0, 5, safe_text(title))
            self.set_xy(43, y + 13)
            self.set_font(self.font_name(), "", 8.5)
            self.set_text_color(*self.muted)
            self.cell(0, 5, safe_text(subtitle))
            y += 35

    def doc_divider(self, title, subtitle, index):
        self.section_title = title
        self.dark_page()
        self.set_fill_color(*self.panel)
        self.rect(21, 82, 168, 98, "F")
        self.set_fill_color(*self.kube)
        self.rect(21, 82, 4, 98, "F")
        self.set_xy(35, 112)
        self.set_font(self.font_name(True), "", 8)
        self.set_text_color(*self.muted)
        self.cell(0, 5, f"DOCUMENTO {index:02d} DE 03")
        self.set_xy(35, 126)
        self.set_font(self.font_name(), "B", 25)
        self.set_text_color(*self.heading)
        self.cell(0, 10, safe_text(title))
        self.set_xy(35, 142)
        self.set_font(self.font_name(), "", 10)
        self.set_text_color(*self.muted)
        self.cell(0, 6, safe_text(subtitle))

    def diagram_divider(self):
        self.section_title = "DIAGRAMAS"
        self.dark_page()
        self.set_fill_color(*self.panel)
        self.rect(21, 82, 168, 98, "F")
        self.set_fill_color(*self.green)
        self.rect(21, 82, 4, 98, "F")
        self.set_xy(35, 112)
        self.set_font(self.font_name(True), "", 8)
        self.set_text_color(*self.muted)
        self.cell(0, 5, "VISAO VISUAL DO AMBIENTE")
        self.set_xy(35, 126)
        self.set_font(self.font_name(), "B", 25)
        self.set_text_color(*self.heading)
        self.cell(0, 10, "Diagramas")
        self.set_xy(35, 142)
        self.set_font(self.font_name(), "", 10)
        self.set_text_color(*self.muted)
        self.cell(0, 6, "Componentes, acesso web, GitOps e observabilidade")

    def d_title(self, title, subtitle):
        self.set_xy(17, 30)
        self.set_font(self.font_name(True), "", 8)
        self.set_text_color(*self.blue)
        self.cell(0, 5, "DIAGRAMA")
        self.set_xy(17, 42)
        self.set_font(self.font_name(), "B", 20)
        self.set_text_color(*self.heading)
        self.cell(0, 9, safe_text(title))
        self.set_xy(17, 54)
        self.set_font(self.font_name(), "", 9)
        self.set_text_color(*self.muted)
        self.cell(0, 5, safe_text(subtitle))

    def d_box(self, x, y, w, h, title, body="", accent="blue"):
        color = self.blue if accent == "blue" else self.green if accent == "green" else self.orange
        self.set_fill_color(*self.panel)
        self.set_draw_color(*self.border)
        self.rect(x, y, w, h, "DF")
        self.set_fill_color(*color)
        self.rect(x, y, 2.2, h, "F")
        self.set_xy(x + 5, y + 4)
        self.set_font(self.font_name(), "B", 8.5)
        self.set_text_color(*self.heading)
        self.multi_cell(w - 8, 4, safe_text(title))
        if body:
            self.set_xy(x + 5, y + h - 8)
            self.set_font(self.font_name(True), "", 6.4)
            self.set_text_color(*self.muted)
            self.cell(w - 8, 3, safe_text(body[:42]))

    def d_arrow(self, x1, y1, x2, y2, label=""):
        self.set_draw_color(*self.blue)
        self.set_line_width(0.45)
        self.line(x1, y1, x2, y2)
        if x2 >= x1:
            self.line(x2, y2, x2 - 2.5, y2 - 1.5)
            self.line(x2, y2, x2 - 2.5, y2 + 1.5)
        else:
            self.line(x2, y2, x2 + 2.5, y2 - 1.5)
            self.line(x2, y2, x2 + 2.5, y2 + 1.5)
        if label:
            self.set_font(self.font_name(True), "", 6)
            self.set_text_color(*self.muted)
            self.set_xy((x1 + x2) / 2 - 11, (y1 + y2) / 2 - 4)
            self.cell(22, 3, safe_text(label), align="C")

    def diagram_components(self):
        self.dark_page()
        self.d_title("Visao de componentes", "Repositorio GitOps reconciliado por ArgoCD nos ambientes dev e prod")
        self.d_box(18, 74, 56, 112, "Repositorio GitOps", "base, overlays, apps, CI", "blue")
        for i, name in enumerate(["PROMPT/docs", "infra/base", "overlays/dev", "overlays/prod", "argocd/apps", ".github/workflows"]):
            self.d_box(24, 88 + i * 14, 44, 9, name, "", "blue")
        self.d_box(90, 74, 44, 26, "ArgoCD DEV", "kind local", "green")
        self.d_box(90, 124, 44, 26, "ArgoCD PROD", "HA/SSO", "orange")
        self.d_arrow(74, 118, 90, 87, "sync")
        self.d_arrow(74, 134, 90, 137, "sync")
        for name, x, y in [("NGINX", 151, 68), ("cert-manager", 151, 88), ("Headlamp", 151, 108), ("Grafana", 151, 128), ("Prometheus", 151, 148), ("sample-app", 151, 168)]:
            self.d_box(x, y, 40, 12, name, "", "green")
            self.d_arrow(134, 87, x, y + 6)
        for name, x, y in [("external-dns", 151, 204), ("Velero", 151, 224), ("Ingress HA", 92, 204), ("TLS LE", 92, 224)]:
            self.d_box(x, y, 40, 12, name, "", "orange")
            self.d_arrow(112, 150, x, y + 6)

    def diagram_web_access(self):
        self.dark_page()
        self.d_title("Acesso web e entrada de trafego", "Como o navegador chega aos servicos em dev, prod generico e AWS opcional")
        self.d_box(18, 78, 34, 16, "Browser", "", "blue")
        self.d_box(72, 56, 42, 16, "hosts local.dev", "dev", "green")
        self.d_box(128, 56, 42, 16, "kind 80/443", "", "green")
        self.d_box(72, 88, 42, 16, "DNS real", "prod", "orange")
        self.d_box(128, 88, 42, 16, "LoadBalancer", "", "orange")
        self.d_box(72, 126, 42, 16, "Route53", "AWS opcional", "blue")
        self.d_box(128, 126, 42, 16, "AWS ALB", "", "blue")
        self.d_box(90, 176, 44, 16, "NGINX Ingress", "", "green")
        self.d_box(90, 212, 44, 16, "Service", "", "blue")
        self.d_box(90, 248, 44, 16, "Pod / Container", "", "orange")
        for y in [64, 96, 134]:
            self.d_arrow(52, 86, 72, y)
        self.d_arrow(114, 64, 128, 64)
        self.d_arrow(114, 96, 128, 96)
        self.d_arrow(114, 134, 128, 134)
        self.d_arrow(149, 72, 112, 176)
        self.d_arrow(149, 104, 112, 176)
        self.d_arrow(149, 142, 112, 176)
        self.d_arrow(112, 192, 112, 212)
        self.d_arrow(112, 228, 112, 248)

    def diagram_gitops_flow(self):
        self.dark_page()
        self.d_title("Fluxo GitOps e promocao", "CI publica imagem e abre PR; ArgoCD sincroniza o Git no cluster")
        steps = [
            ("Dev push", "sample-app"), ("GitHub Actions", "test/build"),
            ("Trivy + cosign", "scan/sign"), ("GHCR", "imagem :sha"),
            ("Pull Request", "altera overlay"), ("Merge main", "aprovado"),
            ("ArgoCD", "detecta diff"), ("Kubernetes", "sync/health"),
        ]
        x, y = 22, 78
        prev = None
        for index, (title, body) in enumerate(steps):
            self.d_box(x, y, 42, 18, title, body, "green" if index < 4 else "orange")
            if prev:
                self.d_arrow(prev[0] + 42, prev[1] + 9, x, y + 9)
            prev = (x, y)
            x += 48
            if x > 155:
                x = 22
                y += 54
                prev = None
        self.d_arrow(64, 141, 22, 187, "PR")
        self.d_arrow(64, 195, 22, 241, "sync")

    def diagram_observability(self):
        self.dark_page()
        self.d_title("Observabilidade", "Metricas e alertas versionados como codigo")
        sources = [("Nodes", 18, 78), ("Pods/containers", 18, 106), ("NGINX Ingress", 18, 134), ("ArgoCD", 18, 162), ("cert-manager", 18, 190), ("sample-app", 18, 218)]
        for name, x, y in sources:
            self.d_box(x, y, 42, 14, name, "", "blue")
        self.d_box(88, 126, 42, 24, "Prometheus", "scrape + rules", "green")
        self.d_box(150, 88, 42, 18, "Grafana", "dashboards", "orange")
        self.d_box(150, 146, 42, 18, "Alertmanager", "rotas/silence", "orange")
        self.d_box(88, 200, 42, 18, "Dashboards", "as code", "green")
        self.d_box(88, 230, 42, 18, "PrometheusRule", "as code", "green")
        for _name, x, y in sources:
            self.d_arrow(x + 42, y + 7, 88, 138)
        self.d_arrow(130, 138, 150, 97)
        self.d_arrow(130, 138, 150, 155)
        self.d_arrow(109, 200, 160, 106)
        self.d_arrow(109, 230, 109, 150)

    def diagrams(self):
        self.diagram_divider()
        self.diagram_components()
        self.diagram_web_access()
        self.diagram_gitops_flow()
        self.diagram_observability()

    def paragraph(self, value):
        if not value:
            self.ln(2)
            return
        self.set_font(self.font_name(), "", 9.2)
        self.set_text_color(*self.body_text)
        self.multi_cell(176, 5.3, safe_text(value))
        self.ln(1.2)

    def heading1(self, value):
        self.ln(4)
        self.set_font(self.font_name(), "B", 17)
        self.set_text_color(*self.blue)
        self.multi_cell(176, 8, safe_text(value))
        self.set_draw_color(*self.border)
        self.line(17, self.get_y() + 1, 193, self.get_y() + 1)
        self.ln(6)

    def heading2(self, value):
        self.ln(3)
        self.set_font(self.font_name(), "B", 13.5)
        self.set_text_color(*self.orange)
        self.multi_cell(176, 6.5, safe_text(value))
        self.ln(2)

    def heading3(self, value):
        self.ln(2)
        self.set_font(self.font_name(), "B", 10.5)
        self.set_text_color(*self.green)
        self.multi_cell(176, 5.5, safe_text(value))
        self.ln(1)

    def bullet(self, value):
        self.set_font(self.font_name(), "", 9.1)
        self.set_text_color(*self.body_text)
        x = self.get_x()
        y = self.get_y()
        self.set_text_color(*self.green)
        self.cell(5, 5, "-")
        self.set_xy(x + 6, y)
        self.set_text_color(*self.body_text)
        self.multi_cell(170, 5.1, safe_text(value))
        self.ln(0.5)

    def code_block(self, lines):
        wrapped = []
        for line in lines:
            wrapped.extend(textwrap.wrap(line, 88, replace_whitespace=False) or [""])
        height = min(70, max(12, len(wrapped) * 4.3 + 7))
        if self.get_y() + height > 270:
            self.add_page()
        x, y = 17, self.get_y() + 1
        self.set_fill_color(*self.panel)
        self.set_draw_color(*self.border)
        self.rect(x, y, 176, height, "DF")
        self.set_xy(x + 4, y + 4)
        self.set_font(self.font_name(True), "", 7.2)
        self.set_text_color(190, 212, 234)
        max_lines = int((height - 7) / 4.3)
        for line in wrapped[:max_lines]:
            self.cell(168, 4.3, safe_text(line), ln=1)
            self.set_x(x + 4)
        self.set_y(y + height + 4)

    def table(self, rows):
        if not rows:
            return
        max_cols = max(len(row) for row in rows)
        col_w = 176 / max_cols
        if self.get_y() + 12 + len(rows) * 7 > 270:
            self.add_page()
        self.set_font(self.font_name(), "B", 7.5)
        for r_index, row in enumerate(rows):
            fill = self.panel2 if r_index == 0 else self.panel
            self.set_fill_color(*fill)
            self.set_draw_color(*self.border)
            self.set_text_color(*(self.blue if r_index == 0 else self.body_text))
            y = self.get_y()
            max_h = 7
            for c_index in range(max_cols):
                value = row[c_index] if c_index < len(row) else ""
                x = 17 + (c_index * col_w)
                self.set_xy(x, y)
                self.rect(x, y, col_w, max_h, "DF")
                self.set_xy(x + 1.5, y + 1.5)
                self.cell(col_w - 3, 3, safe_text(value[:28]))
            self.set_y(y + max_h)
        self.ln(4)

    def render_items(self, items):
        self.add_page()
        self.set_y(24)
        for kind, value in items:
            if kind == "space":
                self.ln(2)
            elif kind == "h1":
                self.heading1(value)
            elif kind == "h2":
                self.heading2(value)
            elif kind == "h3":
                self.heading3(value)
            elif kind in ("bullet", "number"):
                self.bullet(value)
            elif kind == "code":
                self.code_block(value)
            elif kind == "mermaid":
                self.ln(2)
                self.set_font(self.font_name(True), "", 8)
                self.set_text_color(*self.muted)
                self.multi_cell(176, 4.8, "Diagrama Mermaid versionado. A versao visual correspondente esta na secao Diagramas do PDF.")
                self.ln(2)
            elif kind == "table":
                self.table(value)
            else:
                self.paragraph(value)


def main():
    pdf = CodexPdf()
    pdf.cover()
    pdf.toc()
    pdf.diagrams()
    for index, (title, subtitle, path) in enumerate(DOCS, start=1):
        pdf.doc_divider(title, subtitle, index)
        pdf.render_items(parse_markdown(path))
    pdf.output(str(OUT))
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

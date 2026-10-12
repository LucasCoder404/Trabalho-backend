# -*- coding: utf-8 -*-
"""Gera o diagrama, os prints dos testes e o PDF da atividade."""
import json
import os
import textwrap
import time
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    Table, TableStyle, PageBreak, KeepTogether, ListFlowable, ListItem,
)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRINTS = os.path.join(BASE, "prints")
os.makedirs(PRINTS, exist_ok=True)

API = "http://localhost:8080"
ARIAL = r"C:\Windows\Fonts\arial.ttf"
ARIAL_BD = r"C:\Windows\Fonts\arialbd.ttf"
CONSOLAS = r"C:\Windows\Fonts\consola.ttf"
CONSOLAS_BD = r"C:\Windows\Fonts\consolab.ttf"

CLIENTE = """{
  "nome": "Lucas5172485",
  "clienteDesde": "2026-10-11"
}"""
PRODUTO = """{
  "nome": "Baozi de Churrasco",
  "preco": 12.90,
  "estoque": true
}"""
PEDIDO = """{
  "clienteId": 1,
  "produtoId": 1,
  "quantidade": 8
}"""


def font(path, size):
    return ImageFont.truetype(path, size)


def call(method, path, body=None):
    url = API + path
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    data = None if body is None else body.encode("utf-8")
    started = time.perf_counter()
    response = requests.request(method, url, data=data, headers=headers, timeout=20)
    elapsed = int((time.perf_counter() - started) * 1000)
    text = response.text or ""
    return {
        "method": method,
        "url": url,
        "path": path,
        "status": response.status_code,
        "reason": response.reason,
        "elapsed": max(elapsed, 1),
        "size": len(response.content),
        "request": None if body is None else json.loads(body),
        "request_text": None if body is None else body.strip(),
        "text": text,
    }


def pretty(text):
    if not text:
        return ""
    try:
        return json.dumps(json.loads(text), indent=2, ensure_ascii=False)
    except Exception:
        return text


def status_label(code, reason):
    names = {200: "OK", 201: "Created", 204: "No Content", 400: "Bad Request", 404: "Not Found"}
    return f"{code} {names.get(code, reason)}"


def draw_json(draw, text, x, y, max_w, line_h, fnt):
    colors = {
        "key": (4, 81, 165),
        "str": (9, 134, 88),
        "num": (9, 134, 88),
        "kw": (0, 0, 255),
        "plain": (30, 30, 30),
    }
    for raw_line in text.splitlines():
        line = raw_line.replace("\t", "    ")
        if draw.textlength(line, font=fnt) > max_w:
            line = line[:90]
        i = 0
        cx = x
        while i < len(line):
            if line[i] == '"':
                j = i + 1
                while j < len(line):
                    if line[j] == "\\" :
                        j += 2
                        continue
                    if line[j] == '"':
                        j += 1
                        break
                    j += 1
                token = line[i:j]
                rest = line[j:].lstrip()
                kind = "key" if rest.startswith(":") else "str"
                draw.text((cx, y), token, font=fnt, fill=colors[kind])
                cx += draw.textlength(token, font=fnt)
                i = j
                continue
            if line[i].isdigit() or (line[i] == "-" and i + 1 < len(line) and line[i + 1].isdigit()):
                j = i + 1
                while j < len(line) and (line[j].isdigit() or line[j] in ".,"):
                    j += 1
                token = line[i:j]
                draw.text((cx, y), token, font=fnt, fill=colors["num"])
                cx += draw.textlength(token, font=fnt)
                i = j
                continue
            for word, kind in (("true", "kw"), ("false", "kw"), ("null", "kw")):
                if line.startswith(word, i) and (i + len(word) == len(line) or not line[i + len(word)].isalnum()):
                    draw.text((cx, y), word, font=fnt, fill=colors[kind])
                    cx += draw.textlength(word, font=fnt)
                    i += len(word)
                    break
            else:
                draw.text((cx, y), line[i], font=fnt, fill=colors["plain"])
                cx += draw.textlength(line[i], font=fnt)
                i += 1
        y += line_h
        if y > 760:
            break
    return y


def postman_shot(result, title, filename):
    w, h = 1280, 800
    img = Image.new("RGB", (w, h), "#F4F5F7")
    d = ImageDraw.Draw(img)
    f_ui = font(ARIAL, 15)
    f_ui_b = font(ARIAL_BD, 15)
    f_small = font(ARIAL, 13)
    f_small_b = font(ARIAL_BD, 13)
    f_tiny = font(ARIAL, 12)
    f_code = font(CONSOLAS, 16)

    d.rectangle((0, 0, w, 36), fill="#1C1E21")
    d.ellipse((14, 10, 30, 26), fill="#FF6C37")
    d.text((40, 8), "Postman", font=f_ui_b, fill="white")
    d.text((150, 9), "Baozi Store  /  API REST", font=f_small, fill="#C8CDD4")
    for i, col in enumerate(("#FF5F57", "#FEBC2E", "#28C840")):
        d.ellipse((w - 78 + i * 22, 11, w - 64 + i * 22, 25), fill=col)

    d.rectangle((0, 36, 250, h), fill="#212326")
    d.text((16, 52), "COLEÇÃO", font=font(ARIAL_BD, 11), fill="#8B919A")
    d.text((16, 78), "Baozi Store", font=f_ui_b, fill="white")
    requests_menu = [
        ("POST", "Criar Cliente", "/clientes"),
        ("POST", "Criar Produto", "/produtos"),
        ("POST", "Criar Pedido", "/pedidos"),
        ("GET", "Listar Clientes", "/clientes"),
        ("GET", "Listar Produtos", "/produtos"),
        ("GET", "Listar Pedidos", "/pedidos"),
        ("GET", "Cliente por ID", "/clientes/1"),
        ("GET", "Produto por ID", "/produtos/1"),
        ("GET", "Pedido por ID", "/pedidos/1"),
        ("DELETE", "Apagar Pedido", "/pedidos/1"),
        ("DELETE", "Apagar Cliente", "/clientes/1"),
        ("DELETE", "Apagar Produto", "/produtos/1"),
    ]
    method_color = {"GET": "#49CC90", "POST": "#FF6C37", "PUT": "#FCA130", "DELETE": "#F93E3E"}
    y = 118
    for method, name, path in requests_menu:
        selected = method == result["method"] and path == result["path"]
        if selected:
            d.rectangle((8, y - 6, 242, y + 28), fill="#2E3238")
        d.text((16, y), method, font=font(ARIAL_BD, 11), fill=method_color[method])
        d.text((78, y), name, font=f_tiny, fill="white" if selected else "#D5D8DE")
        y += 38

    d.rectangle((250, 36, w, 78), fill="white")
    d.text((270, 50), title, font=f_ui_b, fill="#1C1E21")
    d.line((250, 78, w, 78), fill="#E4E6EA")

    d.rounded_rectangle((270, 96, 360, 136), radius=6, fill="#F7F8FA", outline="#D0D5DD")
    d.text((286, 106), result["method"], font=f_ui_b, fill=method_color[result["method"]])
    d.rounded_rectangle((368, 96, 1100, 136), radius=6, fill="#F7F8FA", outline="#D0D5DD")
    d.text((384, 106), result["url"], font=f_ui, fill="#1C1E21")
    d.rounded_rectangle((1112, 96, 1248, 136), radius=6, fill="#FF6C37")
    send = "Send"
    sw = d.textlength(send, font=f_ui_b)
    d.text((1112 + (136 - sw) / 2, 106), send, font=f_ui_b, fill="white")

    tabs = ["Params", "Authorization", "Headers", "Body", "Scripts"]
    tx = 270
    for tab in tabs:
        active = tab == "Body"
        color = "#FF6C37" if active else "#667085"
        weight = f_small_b if active else f_small
        d.text((tx, 156), tab, font=weight, fill=color)
        if active:
            tw = d.textlength(tab, font=weight)
            d.line((tx, 178, tx + tw, 178), fill="#FF6C37", width=2)
        tx += int(d.textlength(tab, font=f_small_b)) + 28

    d.rectangle((250, 188, w, 430), fill="white")
    if result["request"] is not None:
        d.text((270, 198), "raw    JSON", font=f_small, fill="#667085")
        body = result.get("request_text") or json.dumps(result["request"], indent=2, ensure_ascii=False)
        draw_json(d, body, 270, 228, 980, 22, f_code)
    else:
        d.text((270, 220), "Esta requisição não envia corpo.", font=f_ui, fill="#667085")

    d.rectangle((250, 430, w, h), fill="#FAFBFC")
    d.line((250, 430, w, 430), fill="#E4E6EA")
    d.text((270, 444), "Body", font=f_small_b, fill="#FF6C37")
    d.text((330, 444), "Cookies    Headers", font=f_small, fill="#667085")
    code = result["status"]
    status_color = "#067647" if code < 300 else "#B42318"
    label = status_label(code, result["reason"])
    d.text((270, 476), label, font=f_ui_b, fill=status_color)
    meta = f"{result['elapsed']} ms     {result['size']} B"
    d.text((270 + d.textlength(label, font=f_ui_b) + 24, 478), meta, font=f_small, fill="#667085")

    payload = pretty(result["text"])
    if payload:
        draw_json(d, payload, 270, 514, 980, 22, f_code)
    else:
        d.text((270, 520), "Sem conteúdo na resposta.", font=f_ui, fill="#667085")

    path = os.path.join(PRINTS, filename)
    img.save(path, "PNG")
    return path


def ellipse(draw, box, outline="black", width=2):
    draw.ellipse(box, outline=outline, width=width)


def use_case_diagram(path):
    w, h = 1800, 1120
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    title_f = font(ARIAL_BD, 28)
    label_f = font(ARIAL, 20)
    head_f = font(ARIAL_BD, 22)
    small_f = font(ARIAL_BD, 22)

    d.text((40, 24), "Diagrama de Caso de Uso — API REST Baozi Store", font=title_f, fill="black")

    boundary = (250, 90, 1740, 1060)
    d.rounded_rectangle(boundary, radius=8, outline="black", width=3)
    d.text((270, 104), "API REST Baozi Store", font=head_f, fill="black")

    ax, ay = 120, 520

    groups = [
        ("Cliente", [
            "Cadastrar cliente",
            "Listar clientes",
            "Consultar cliente por ID",
            "Atualizar cliente",
            "Excluir cliente",
        ]),
        ("Produto", [
            "Cadastrar produto",
            "Listar produtos",
            "Consultar produto por ID",
            "Atualizar produto",
            "Excluir produto",
        ]),
        ("Pedido", [
            "Cadastrar pedido",
            "Listar pedidos",
            "Consultar pedido por ID",
            "Atualizar pedido",
            "Excluir pedido",
        ]),
    ]

    centers = []
    col_w = 460
    start_x = 290
    for gi, (group, cases) in enumerate(groups):
        x0 = start_x + gi * col_w
        for i, name in enumerate(cases):
            cx = x0 + 200
            cy = 280 + i * 145
            centers.append((cx, cy, name, x0))

    for cx, cy, _name, _x0 in centers:
        d.line((ax + 48, ay - 78, cx - 175, cy), fill="#4B5563", width=1)

    d.rounded_rectangle((ax - 70, ay - 170, ax + 78, ay + 110), fill="white")
    d.ellipse((ax - 22, ay - 150, ax + 22, ay - 106), outline="black", width=3)
    d.line((ax, ay - 106, ax, ay - 20), fill="black", width=3)
    d.line((ax - 48, ay - 78, ax + 48, ay - 78), fill="black", width=3)
    d.line((ax, ay - 20, ax - 40, ay + 50), fill="black", width=3)
    d.line((ax, ay - 20, ax + 40, ay + 50), fill="black", width=3)
    actor_label = "Usuário da API"
    tw = d.textlength(actor_label, font=small_f)
    d.text((ax - tw / 2, ay + 66), actor_label, font=small_f, fill="black")

    for cx, cy, name, x0 in centers:
        if name.startswith("Cadastrar"):
            d.text((x0 + 110, 160), ["Cliente", "Produto", "Pedido"][
                0 if "cliente" in name else 1 if "produto" in name else 2
            ], font=head_f, fill="black")
        box = (cx - 175, cy - 42, cx + 175, cy + 42)
        d.ellipse(box, fill="white", outline="black", width=2)
        tw = d.textlength(name, font=label_f)
        d.text((cx - tw / 2, cy - 12), name, font=label_f, fill="black")

    img.save(path, "PNG")
    return path


def build_pdf(shots, diagram):
    pdf_path = os.path.join(BASE, "Trabalho_API_REST_Baozi_Store.pdf")
    doc = SimpleDocTemplate(
        pdf_path, pagesize=A4,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=1.6 * cm, bottomMargin=1.6 * cm,
        title="API REST Baozi Store",
        author="Lucas de Oliveira Sperandio",
    )
    arial = "Arial"
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdfmetrics.registerFont(TTFont("Arial", ARIAL))
    pdfmetrics.registerFont(TTFont("Arial-Bold", ARIAL_BD))

    orange = HexColor("#C2410C")
    ink = HexColor("#1F2933")
    muted = HexColor("#52606D")
    line = HexColor("#E4E7EB")
    head_bg = HexColor("#FFF4ED")

    h1 = ParagraphStyle("h1", fontName="Arial-Bold", fontSize=16, textColor=orange, spaceAfter=8, spaceBefore=12, leading=20)
    h2 = ParagraphStyle("h2", fontName="Arial-Bold", fontSize=13, textColor=ink, spaceAfter=6, spaceBefore=10, leading=16)
    body = ParagraphStyle("body", fontName="Arial", fontSize=11, textColor=ink, alignment=TA_JUSTIFY, leading=16, spaceAfter=8)
    cover_kicker = ParagraphStyle("ck", fontName="Arial-Bold", fontSize=12, textColor=orange, alignment=TA_CENTER, spaceAfter=6)
    cover_title = ParagraphStyle("ct", fontName="Arial-Bold", fontSize=22, textColor=ink, alignment=TA_CENTER, leading=28, spaceAfter=8)
    cover_sub = ParagraphStyle("cs", fontName="Arial", fontSize=12, textColor=muted, alignment=TA_CENTER, leading=16, spaceAfter=4)
    caption = ParagraphStyle("cap", fontName="Arial", fontSize=9, textColor=muted, alignment=TA_CENTER, spaceBefore=4, spaceAfter=8)
    bullet = ParagraphStyle("bu", fontName="Arial", fontSize=11, textColor=ink, leading=15, leftIndent=8)
    cell = ParagraphStyle("cell", fontName="Arial", fontSize=9, textColor=ink, leading=12)
    cell_b = ParagraphStyle("cellb", fontName="Arial-Bold", fontSize=9, textColor=ink, leading=12)
    footer = ParagraphStyle("ft", fontName="Arial", fontSize=9, textColor=muted, alignment=TA_CENTER)

    story = []
    story.append(Spacer(1, 2.2 * cm))
    story.append(Paragraph("UNINTER", cover_kicker))
    story.append(Paragraph("Centro Universitário Internacional", cover_sub))
    story.append(Spacer(1, 1.2 * cm))
    story.append(Paragraph("Desenvolvimento Web Back-End", cover_kicker))
    story.append(Paragraph("Atividade Prática", cover_sub))
    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph("API REST – Baozi Store", cover_title))
    story.append(Paragraph("Controle de clientes, produtos e pedidos", cover_sub))
    story.append(Spacer(1, 1.6 * cm))
    story.append(Paragraph("Aluno: Lucas de Oliveira Sperandio", cover_sub))
    story.append(Paragraph("RU: 5172485", cover_sub))
    story.append(Paragraph("Professora: Luciane Kanashiro, Me.", cover_sub))
    story.append(Spacer(1, 1.4 * cm))
    story.append(Paragraph("2026", cover_sub))
    story.append(PageBreak())

    story.append(Paragraph("1. Descrição da situação", h1))
    story.append(Paragraph(
        "A Baozi Store é uma pequena loja que vende pão chinês. Para melhorar a organização do negócio, "
        "foi criado um sistema simples para controlar clientes, produtos e pedidos.",
        body))
    story.append(Paragraph(
        "Um cliente chamado <b>Lucas5172485</b> realizou seu cadastro no sistema em 11/10/2026.",
        body))
    story.append(Paragraph(
        "O produto vendido pela loja chama-se <b>Baozi de Churrasco</b> e é vendido por unidade, ao preço de R$ 12,90, com estoque disponível.",
        body))
    story.append(Paragraph(
        "Em um determinado momento, o cliente realizou um pedido de <b>8 unidades</b> do produto.",
        body))
    story.append(Paragraph(
        "O sistema registra o cliente, o produto comprado e a quantidade solicitada, facilitando o controle da loja. "
        "Esses mesmos dados aparecem nos testes da API apresentados neste documento.",
        body))

    story.append(Paragraph("2. Diagrama de caso de uso", h1))
    story.append(Paragraph(
        "O ator principal é o Usuário da API. Os casos de uso cobrem o cadastro, a listagem, a consulta por identificador, "
        "a atualização e a exclusão de Cliente, Produto e Pedido.",
        body))
    story.append(RLImage(diagram, width=17.2 * cm, height=10.7 * cm))
    story.append(Paragraph("Figura 1 — Diagrama de caso de uso da API REST Baozi Store.", caption))

    story.append(Paragraph("3. Especificação da API", h1))
    story.append(Paragraph("3.1 Entidades e campos", h2))
    story.append(Paragraph(
        "As entidades foram mapeadas com Spring Data JPA para um banco relacional. "
        "A execução padrão usa o H2, permitido no enunciado. O perfil <font face='Courier'>mysql</font> deixa a mesma API pronta para MySQL.",
        body))

    def table(data, col_widths):
        wrapped = []
        for r, row in enumerate(data):
            style = cell_b if r == 0 else cell
            wrapped.append([Paragraph(str(c), style) for c in row])
        t = Table(wrapped, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), head_bg),
            ("TEXTCOLOR", (0, 0), (-1, 0), ink),
            ("FONTNAME", (0, 0), (-1, 0), "Arial-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, line),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("BACKGROUND", (0, 1), (-1, -1), white),
        ]))
        return t

    story.append(table([
        ["Entidade", "Campo", "Tipo", "Descrição"],
        ["Cliente", "id", "Long", "Identificador gerado pelo banco"],
        ["Cliente", "nome", "String", "Nome do cliente"],
        ["Cliente", "clienteDesde", "LocalDate", "Data de início do cadastro"],
        ["Produto", "id", "Long", "Identificador gerado pelo banco"],
        ["Produto", "nome", "String", "Nome do produto"],
        ["Produto", "preco", "BigDecimal", "Preço unitário"],
        ["Produto", "estoque", "Boolean", "Indica se há estoque"],
        ["Pedido", "id", "Long", "Identificador gerado pelo banco"],
        ["Pedido", "clienteId", "Long", "Cliente que comprou"],
        ["Pedido", "produtoId", "Long", "Produto comprado"],
        ["Pedido", "quantidade", "Integer", "Quantidade comprada"],
    ], [3.2 * cm, 3.4 * cm, 3.2 * cm, 7.2 * cm]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("3.2 Organização do projeto", h2))
    story.append(Paragraph("O projeto segue o padrão MVC do Spring, com os pacotes pedidos no enunciado:", body))
    story.append(Paragraph("• <b>model</b> — entidades JPA Cliente, Produto e Pedido.", bullet))
    story.append(Paragraph("• <b>repository</b> — interfaces Spring Data JPA de cada entidade.", bullet))
    story.append(Paragraph("• <b>controller</b> — endpoints REST que recebem e devolvem JSON.", bullet))

    story.append(Paragraph("3.3 Endpoints", h2))
    story.append(table([
        ["Método", "URL", "Ação"],
        ["POST", "/clientes", "Cadastrar cliente"],
        ["GET", "/clientes", "Listar clientes"],
        ["GET", "/clientes/{id}", "Consultar cliente por ID"],
        ["PUT", "/clientes/{id}", "Atualizar cliente"],
        ["DELETE", "/clientes/{id}", "Apagar cliente"],
        ["POST", "/produtos", "Cadastrar produto"],
        ["GET", "/produtos", "Listar produtos"],
        ["GET", "/produtos/{id}", "Consultar produto por ID"],
        ["PUT", "/produtos/{id}", "Atualizar produto"],
        ["DELETE", "/produtos/{id}", "Apagar produto"],
        ["POST", "/pedidos", "Registrar pedido"],
        ["GET", "/pedidos", "Listar pedidos"],
        ["GET", "/pedidos/{id}", "Consultar pedido por ID"],
        ["PUT", "/pedidos/{id}", "Atualizar pedido"],
        ["DELETE", "/pedidos/{id}", "Apagar pedido"],
    ], [3.2 * cm, 5.2 * cm, 8.6 * cm]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "O cadastro e a consulta devolvem o recurso em JSON. A exclusão responde 204 quando o registro existe e 404 quando o identificador não é encontrado. "
        "Ao registrar um pedido, a API verifica se o cliente e o produto existem e se a quantidade é maior que zero.",
        body))

    story.append(Paragraph("4. Testes da API", h1))
    story.append(Paragraph(
        "Os testes abaixo foram executados contra a API em execução em http://localhost:8080. "
        "O cliente Lucas5172485, o produto Baozi de Churrasco e o pedido de 8 unidades aparecem nas requisições e nas respostas.",
        body))

    for i, (file, legenda) in enumerate(shots, start=1):
        block = [
            Paragraph(f"4.{i} {legenda}", h2),
            RLImage(file, width=16.8 * cm, height=10.5 * cm),
            Paragraph(f"Figura {i + 1} — {legenda}.", caption),
        ]
        story.append(KeepTogether(block))

    story.append(Paragraph("5. Repositório do código-fonte", h1))
    story.append(Paragraph(
        "O código-fonte do projeto (entidades, repositórios, controllers, configuração do banco e coleção do Postman) "
        "acompanha este trabalho. O endereço do repositório público deve ser informado nesta seção na entrega final.",
        body))
    story.append(Paragraph("Link: a publicar no GitHub (ou serviço equivalente) com o código deste projeto.", body))

    def add_page_number(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Arial", 9)
        canvas.setFillColor(muted)
        canvas.drawString(1.8 * cm, 0.8 * cm, "API REST – Baozi Store  |  Lucas de Oliveira Sperandio  |  RU 5172485")
        canvas.drawRightString(A4[0] - 1.8 * cm, 0.8 * cm, str(canvas.getPageNumber()))
        canvas.restoreState()

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    return pdf_path


def main():
    for _ in range(30):
        try:
            requests.get(API + "/clientes", timeout=2)
            break
        except requests.RequestException:
            time.sleep(1)
    else:
        raise SystemExit("API não respondeu em localhost:8080")

    etapas = [
        ("POST", "/clientes", CLIENTE, "Criar Cliente", "01-post-cliente.png", "POST — criar cliente"),
        ("POST", "/produtos", PRODUTO, "Criar Produto", "02-post-produto.png", "POST — criar produto"),
        ("POST", "/pedidos", PEDIDO, "Criar Pedido", "03-post-pedido.png", "POST — criar pedido"),
        ("GET", "/clientes", None, "Listar Clientes", "04-get-clientes.png", "GET — listar clientes"),
        ("GET", "/produtos", None, "Listar Produtos", "05-get-produtos.png", "GET — listar produtos"),
        ("GET", "/pedidos", None, "Listar Pedidos", "06-get-pedidos.png", "GET — listar pedidos"),
        ("GET", "/clientes/1", None, "Cliente por ID", "07-get-cliente-id.png", "GET — consultar cliente por ID"),
        ("GET", "/produtos/1", None, "Produto por ID", "08-get-produto-id.png", "GET — consultar produto por ID"),
        ("GET", "/pedidos/1", None, "Pedido por ID", "09-get-pedido-id.png", "GET — consultar pedido por ID"),
        ("DELETE", "/pedidos/1", None, "Apagar Pedido", "10-delete-pedido.png", "DELETE — apagar pedido"),
        ("DELETE", "/clientes/1", None, "Apagar Cliente", "11-delete-cliente.png", "DELETE — apagar cliente"),
        ("DELETE", "/produtos/1", None, "Apagar Produto", "12-delete-produto.png", "DELETE — apagar produto"),
    ]

    shots = []
    for method, path, body, title, filename, legenda in etapas:
        result = call(method, path, body)
        print(method, path, result["status"], result["text"][:180])
        if result["status"] >= 400:
            raise SystemExit(f"Falha em {method} {path}: {result['status']} {result['text']}")
        shots.append((postman_shot(result, title, filename), legenda))

    diagram = use_case_diagram(os.path.join(PRINTS, "diagrama-caso-de-uso.png"))
    pdf = build_pdf(shots, diagram)
    print("PDF", pdf)


if __name__ == "__main__":
    main()

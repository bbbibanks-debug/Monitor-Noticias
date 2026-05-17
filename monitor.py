import requests
from lxml import html

sites = [
    {"id": "g1", "nome": "G1 Globo", "url": "https://globo.com", "xpath": "//a[contains(@class, 'feed-post-link')] | //a[contains(@class, 'post__link')] | //div[contains(@class, 'bstn-fd-main')]//a", "cor": "#c4170c"},
    {"id": "cnn", "nome": "CNN Brasil", "url": "https://cnnbrasil.com.br", "xpath": "/html/body//a", "cor": "#cc0000"},
    {"id": "times", "nome": "Times Brasil", "url": "https://timesbrasil.com.br", "xpath": "/html/body//a", "cor": "#002447"},
    {"id": "jovempan", "nome": "Jovem Pan", "url": "https://jovempan.com.br", "xpath": "/html/body//a", "cor": "#00441b"}
]

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
dados_finais = {site["id"]: [] for site in sites}
print("Iniciando a raspagem de dados...")

for site in sites:
    try:
        response = requests.get(site["url"], headers=headers, timeout=10)
        conteudo_html = response.content.decode('utf-8', errors='ignore')
        tree = html.fromstring(conteudo_html)
        elementos = tree.xpath(site["xpath"])
        vistas = set()
        for item in elementos:
            texto = item.text_content().strip()
            link = item.get('href')
            if texto and link and len(texto) > 30 and texto not in vistas:
                vistas.add(texto)
                if link.startswith('/'): link = f"{site['url'].rstrip('/')}{link}"
                dados_finais[site["id"]].append({"texto": texto, "link": link})
        print(f"-> {len(dados_finais[site['id']])} noticias coletadas do {site['nome']}")
    except Exception as e:
        print(f"Erro ao acessar {site['nome']}: {e}")

html_template = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel de Notícias</title>
    <style>
        :root { --bg-color: #121214; --card-bg: #1a1a1e; --text-color: #e1e1e6; --text-muted: #a8a8b3; --border-color: #29292e; }
        body { font-family: 'Segoe UI', Roboto, sans-serif; background-color: var(--bg-color); color: var(--text-color); margin: 0; padding: 40px 20px; display: flex; flex-direction: column; align-items: center; }
        .container { width: 100%; max-width: 800px; }
        h1 { text-align: center; margin-bottom: 40px; font-size: 2.5rem; background: linear-gradient(45deg, #e1e1e6, #a8a8b3); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .fonte-box { background-color: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; margin-bottom: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.2); transition: transform 0.2s; }
        .fonte-box:hover { transform: translateY(-2px); }
        .fonte-header { padding: 24px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; font-size: 1.3rem; font-weight: 600; border-left: 6px solid #fff; }
        .fonte-header::after { content: '▼'; font-size: 0.9rem; color: var(--text-muted); transition: transform 0.3s; }
        .fonte-box.ativo .fonte-header::after { transform: rotate(-180deg); }
        .fonte-content { max-height: 0; overflow: hidden; transition: max-height 0.4s ease-out, padding 0.4s ease; padding: 0 24px; background-color: rgba(0,0,0,0.1); }
        .fonte-box.ativo .fonte-content { max-height: 10000px; padding: 16px 24px 24px 24px; border-top: 1px solid var(--border-color); }
        .noticia-item { display: block; padding: 14px 0; text-decoration: none; color: var(--text-color); border-bottom: 1px solid rgba(255,255,255,0.05); transition: color 0.2s; }
        .noticia-item:hover { color: #52a5ff; }
        .noticia-titulo { font-size: 1.05rem; line-height: 1.5; margin-bottom: 4px; }
        .noticia-link { font-size: 0.85rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Central de Notícias</h1>
"""

for site in sites:
    noticias_html = ""
    for noti in dados_finais[site["id"]]:
        noticias_html += f'            <a href="{noti["link"]}" target="_blank" class="noticia-item"><div class="noticia-titulo">🔥 {noti["texto"]}</div><div class="noticia-link">{noti["link"]}</div></a>'
    if not noticias_html: noticias_html = "<p style='color:var(--text-muted);'>Nenhuma notícia encontrada.</p>"
    html_template += f'        <div class="fonte-box"><div class="fonte-header" style="border-left-color: {site["cor"]};" onclick="toggleBox(this)">{site["nome"]}</div><div class="fonte-content">{noticias_html}</div></div>'

html_template += """    </div>
    <script>function toggleBox(header) { header.parentElement.classList.toggle('ativo'); }</script>
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:f.write(html_template)
print("Arquivo index.html configurado.")


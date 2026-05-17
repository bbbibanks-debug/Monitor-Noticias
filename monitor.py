import os
import requests
from lxml import html
from datetime import datetime, timedelta

# Tenta carregar a biblioteca de tradução para o Market News
try:
    from mtranslate import translate
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mtranslate"])
    from mtranslate import translate

# Lista de fontes atualizada (10 grandes fontes integradas)
sites = [
    {
        "id": "g1",
        "nome": "G1 Globo",
        "url": "https://globo.com",
        "xpath": "//a[contains(@class, 'feed-post-link')] | //a[contains(@class, 'post__link')] | //div[contains(@class, 'bstn-fd-main')]//a",
        "cor": "#c4170c",
        "tamanho_min": 35
    },
    {
        "id": "cnn",
        "nome": "CNN Brasil",
        "url": "https://cnnbrasil.com.br",
        "xpath": "/html/body//a",
        "cor": "#cc0000",
        "tamanho_min": 35
    },
    {
        "id": "times",
        "nome": "Times Brasil",
        "url": "https://timesbrasil.com.br",
        "xpath": "/html/body//a",
        "cor": "#002447",
        "tamanho_min": 35
    },
    {
        "id": "jovempan",
        "nome": "Jovem Pan",
        "url": "https://jovempan.com.br",
        "xpath": "/html/body//a",
        "cor": "#00441b",
        "tamanho_min": 35
    },
    {
        "id": "uol",
        "nome": "UOL",
        "url": "https://uol.com.br",
        "xpath": "/html/body//a",
        "cor": "#f6a800",
        "tamanho_min": 35
    },
    {
        "id": "correio",
        "nome": "Correio Braziliense",
        "url": "https://correiobraziliense.com.br",
        "xpath": "/html/body//a",
        "cor": "#005ca9",
        "tamanho_min": 35
    },
    {
        "id": "finviz",
        "nome": "Market News",
        "url": "https://finviz.com",
        "xpath": "//a[contains(@class, 'nn-tab-link')] | //td[contains(@class, 'nn-text')]//a | /html/body//a",
        "cor": "#3f9c35",
        "tamanho_min": 25
    },
    {
        "id": "moneytimes",
        "nome": "Money Times",
        "url": "https://moneytimes.com.br",
        "xpath": "/html/body//a",
        "cor": "#173321",
        "tamanho_min": 35
    },
    {
        "id": "infomoney",
        "nome": "InfoMoney",
        "url": "https://infomoney.com.br",
        "xpath": "/html/body//a",
        "cor": "#001a30",
        "tamanho_min": 35
    },
    {
        "id": "r7",
        "nome": "R7 Notícias",
        "url": "https://r7.com",
        "xpath": "/html/body/div/main//a",
        "cor": "#1d70b8",
        "tamanho_min": 35
    }
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

dados_finais = {site["id"]: [] for site in sites}

print("Iniciando a raspagem de dados via HTML Puro de todas as fontes...")

for site in sites:
    try:
        response = requests.get(site["url"], headers=headers, timeout=12)
        conteudo_html = response.content.decode('utf-8', errors='ignore')
        
        tree = html.fromstring(conteudo_html)
        elementos = tree.xpath(site["xpath"])
        vistas = set()
        
        for item in elementos:
            texto = item.text_content().strip()
            link = item.get('href')
            
            if texto and link and len(texto) > site["tamanho_min"] and texto not in vistas:
                vistas.add(texto)
                
                if link.startswith('/'):
                    url_base = site["url"].split('?').rstrip('/')
                    link = f"{url_base}{link}"
                    
                if "javascript:" not in link and link.startswith('http'):
                    if site["id"] == "finviz":
                        try:
                            texto_traduzido = translate(texto, "pt")
                            dados_finais[site["id"]].append({
                                "texto": texto, 
                                "texto_traduzido": texto_traduzido, 
                                "link": link
                            })
                        except Exception:
                            dados_finais[site["id"]].append({"texto": texto, "link": link})
                    else:
                        dados_finais[site["id"]].append({"texto": texto, "link": link})
                
        print(f"-> {len(dados_finais[site['id']])} notícias coletadas do {site['nome']}")
    except Exception as e:
        print(f"Erro ao acessar {site['nome']}: {e}")

# --- CAPTURA E FORMATAÇÃO DO HORÁRIO (FUSO HORÁRIO DO BRASIL - BRASÍLIA) ---
# GitHub Actions roda em UTC. Subtraímos 3 horas para marcar o horário correto de Brasília.
hora_brasilia = datetime.utcnow() - timedelta(hours=3)
texto_data_hora = hora_brasilia.strftime("Ultima captura de informações feita no dia %d/%m/%Y as %H:%M hrs")

# --- GERAÇÃO DO HTML INTERATIVO ---

html_template = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel de Notícias</title>
    <style>
        :root {
            --bg-color: #121214;
            --card-bg: #1a1a1e;
            --text-color: #e1e1e6;
            --text-muted: #a8a8b3;
            --border-color: #29292e;
        }
        body {
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 40px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .container {
            width: 100%;
            max-width: 800px;
        }
        h1 {
            text-align: center;
            margin-bottom: 40px;
            font-size: 2.5rem;
            letter-spacing: -1px;
            background: linear-gradient(45deg, #e1e1e6, #a8a8b3);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .fonte-box {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            margin-bottom: 16px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .fonte-box:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.3);
        }
        .fonte-header {
            padding: 24px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 1.3rem;
            font-weight: 600;
            user-select: none;
            border-left: 6px solid #fff;
        }
        .fonte-header::after {
            content: '▼';
            font-size: 0.9rem;
            color: var(--text-muted);
            transition: transform 0.3s;
        }
        .fonte-box.ativo .fonte-header::after {
            transform: rotate(-180deg);
        }
        .fonte-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.4s ease-out, padding 0.4s ease;
            padding: 0 24px;
            background-color: rgba(0,0,0,0.1);
        }
        .fonte-box.ativo .fonte-content {
            max-height: 10000px;
            padding: 16px 24px 24px 24px;
            border-top: 1px solid var(--border-color);
        }
        .noticia-item {
            display: block;
            padding: 14px 0;
            text-decoration: none;
            color: var(--text-color);
            border-bottom: 1px solid rgba(255,255,255,0.05);
            transition: color 0.2s, padding-left 0.2s;
        }
        .noticia-item:last-child {
            border-bottom: none;
        }
        .noticia-item:hover {
            color: #52a5ff;
            padding-left: 6px;
        }
        .noticia-titulo {
            font-size: 1.05rem;
            line-height: 1.5;
            margin-bottom: 4px;
        }
        .noticia-traducao {
            font-size: 0.9rem;
            color: #9cdcfe;
            margin-top: 2px;
            margin-bottom: 4px;
            line-height: 1.4;
        }
        .noticia-link {
            font-size: 0.85rem;
            color: var(--text-muted);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        /* Estilo elegante para a frase do rodapé */
        .rodape-tempo {
            text-align: center;
            margin-top: 40px;
            margin-bottom: 20px;
            font-size: 0.9rem;
            color: var(--text-muted);
            border-top: 1px solid var(--border-color);
            padding-top: 20px;
            width: 100%;
        }
    </style>
</head>
<body>

    <div class="container">
        <h1>Central de Notícias</h1>
"""

for site in sites:
    noticias_html = ""
    for noti in dados_finais[site["id"]]:
        if site["id"] == "finviz" and "texto_traduzido" in noti:
            noticias_html += f"""
                <a href="{noti['link']}" target="_blank" class="noticia-item">
                    <div class="noticia-titulo">🇺🇸 {noti['texto']}</div>
                    <div class="noticia-traducao">🇧🇷 {noti['texto_traduzido']}</div>
                    <div class="noticia-link">{noti['link']}</div>
                </a>"""
        else:
            noticias_html += f"""
                <a href="{noti['link']}" target="_blank" class="noticia-item">
                    <div class="noticia-titulo">🔥 {noti['texto']}</div>
                    <div class="noticia-link">{noti['link']}</div>
                </a>"""
    
    if not noticias_html:
        noticias_html = "<p style='color:var(--text-muted);'>Nenhuma notícia relevante encontrada no momento.</p>"

    html_template += f"""
        <div class="fonte-box">
            <div class="fonte-header" style="border-left-color: {site['cor']};" onclick="toggleBox(this)">
                {site['nome']}
            </div>
            <div class="fonte-content">
                {noticias_html}
            </div>
        </div>"""

# Injeta dinamicamente a frase solicitada no rodapé da página
html_template += f"""
        <div class="rodape-tempo">
            {texto_data_hora}
        </div>
    </div>

    <script>
        function toggleBox(header) {{
            const box = header.parentElement;
            box.classList.toggle('ativo');
        }}
    </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"\nSucesso! Carimbo adicionado: {texto_data_hora}")

import os
import requests
from lxml import html
from datetime import datetime, timedelta
try:
    from mtranslate import translate
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mtranslate"])
    from mtranslate import translate

sites = [
    {"id": "g1", "nome": "G1 Globo", "url": "https://globo.com", "xpath": "//a[contains(@class, 'feed-post-link')] | //a[contains(@class, 'post__link')] | //div[contains(@class, 'bstn-fd-main')]//a", "cor": "#c4170c", "tamanho_min": 15},
    {"id": "cnn", "nome": "CNN Brasil", "url": "https://cnnbrasil.com.br", "xpath": "//a", "cor": "#cc0000", "tamanho_min": 15},
    {"id": "times", "nome": "Times Brasil", "url": "https://timesbrasil.com.br", "xpath": "//a", "cor": "#002447", "tamanho_min": 15},
    {"id": "jovempan", "nome": "Jovem Pan", "url": "https://jovempan.com.br", "xpath": "//div[contains(@class, 'post-item')]//a | //main//a", "cor": "#00441b", "tamanho_min": 15},
    {"id": "uol", "nome": "UOL", "url": "https://uol.com.br", "xpath": "//div[contains(@class, 'hu-commons')]//a | //a[contains(@class, 'hyperlink')]", "cor": "#f6a800", "tamanho_min": 15},
    {"id": "correio", "nome": "Correio Braziliense", "url": "https://correiobraziliense.com.br", "xpath": "//a", "cor": "#005ca9", "tamanho_min": 15},
    {"id": "finviz", "nome": "Market News", "url": "https://finviz.com", "xpath": "//a[contains(@class, 'nn-tab-link')] | //td[contains(@class, 'nn-text')]//a", "cor": "#3f9c35", "tamanho_min": 15},
    {"id": "moneytimes", "nome": "Money Times", "url": "https://moneytimes.com.br", "xpath": "//h2/a | //h3/a | //div[contains(@class, 'news-item')]//a", "cor": "#173321", "tamanho_min": 15},
    {"id": "infomoney", "nome": "InfoMoney", "url": "https://infomoney.com.br", "xpath": "//a[contains(@class, 'typography__link')] | //main//a", "cor": "#001a30", "tamanho_min": 15},
    {"id": "r7", "nome": "R7 Notícias", "url": "https://r7.com", "xpath": "//a[contains(@class, 'r7-flex-title-link')] | /html/body/div/main//a", "cor": "#1d70b8", "tamanho_min": 15},
    {"id": "metropoles", "nome": "Metrópoles", "url": "https://metropoles.com", "xpath": "//h1/a | //h2/a | //h3/a | //h5/a | //a[contains(@class, 'm-title')]", "cor": "#ff0055", "tamanho_min": 15},
    {"id": "terra", "nome": "Terra", "url": "https://terra.com.br", "xpath": "//a[contains(@class, 'card-news__url')] | //main//a", "cor": "#2b3640", "tamanho_min": 15},
    {"id": "band", "nome": "Band", "url": "https://band.com.br", "xpath": "//a[@data-bnd-link] | //div[contains(@class, 'card')]//a | //main//a", "cor": "#006432", "tamanho_min": 15},
    {"id": "ig", "nome": "iG", "url": "https://ig.com.br", "xpath": "//h2/a | //h3/a | //main//a", "cor": "#1a4a7c", "tamanho_min": 15},
    {"id": "estadao", "nome": "Estadão", "url": "https://estadao.com.br", "xpath": "//a", "cor": "#007a87", "tamanho_min": 15},
    {"id": "folha", "nome": "Folha de S.Paulo", "url": "https://uol.com.br", "xpath": "//a", "cor": "#222222", "tamanho_min": 15},
    {"id": "bloomberg", "nome": "Bloomberg Línea", "url": "https://bloomberglinea.com.br", "xpath": "//a", "cor": "#ffdf00", "tamanho_min": 15},
    {"id": "sbtnews", "nome": "SBT News", "url": "https://sbtnews.com.br", "xpath": "//a[contains(@class, 'news-card')] | //h2/a | //h3/a | //main//a", "cor": "#3b5998", "tamanho_min": 15}
]

headers_padrao = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

termos_bloqueados = [
    "fale conosco", "politica de privacidade", "sobre o terra", "anuncie", "expediente",
    "termos de uso", "assine", "minha conta", "perfil", "todos os direitos", "quem somos", 
    "home", "noticias", "contato", "newsletter", "cookies", "ajuda", "sac", "login",
    "cadastre-se", "painel", "editorial", "videos"
]

def higienizar_string_url(url_bruta):
    if not url_bruta:
        return ""
    return url_bruta.strip().replace("\n", "").replace("\t", "").replace(" ", "")

def extrair_url_base_pura(url_higienizada):
    if not url_higienizada:
        return ""
    url_base = url_higienizada.split('?')[0]
    url_base = url_base.split('#')[0]
    return url_base.strip().rstrip('/')

urls_bloqueadas_brutas = set()
urls_bloqueadas_bases = set()

if os.path.exists("blacklist.txt"):
    with open("blacklist.txt", "r", encoding="utf-8") as f:
        for linha in f:
            linha_limpa = linha.strip()
            if linha_limpa and not linha_limpa.startswith("#"):
                url_limpa = higienizar_string_url(linha_limpa)
                urls_bloqueadas_brutas.add(url_limpa)
                urls_bloqueadas_bases.add(extrair_url_base_pura(url_limpa))
    print(f"-> Blacklist carregada com sucesso! {len(urls_bloqueadas_brutas)} caminhos mapeados.")
else:
    print("-> Aviso: 'blacklist.txt' não encontrado.")

dados_finais = {site["id"]: [] for site in sites}
print("Iniciando a raspagem com checagem estrita de igualdade...")

session = requests.Session()
session.headers.update(headers_padrao)

for site in sites:
    try:
        response = session.get(site["url"], timeout=15)
        conteudo_html = response.content.decode('utf-8', errors='ignore')
        
        tree = html.fromstring(conteudo_html)
        elementos = tree.xpath(site["xpath"])
        vistas = set()
        
        for item in elementos:
            texto = item.text_content().strip()
            link = item.get('href')
            
            if texto and link and len(texto) > site["tamanho_min"] and texto not in vistas:
                texto_lower = texto.lower()
                if any(termo in texto_lower for termo in termos_bloqueados):
                    continue
                
                vistas.add(texto)
                
                if link.startswith('/'):
                    url_base = site["url"].split('?')[0].rstrip('/')
                    link = f"{url_base}{link}"
                
                if "javascript:" not in link and link.startswith('http'):
                    link_higienizado = higienizar_string_url(link)
                    
                    if link_higienizado in urls_bloqueadas_brutas:
                        continue
                    
                    link_base_puro = extrair_url_base_pura(link_higienizado)
                    if link_base_puro in urls_bloqueadas_bases:
                        continue
                    
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

hora_brasilia = datetime.utcnow() - timedelta(hours=3)
texto_data_hora = hora_brasilia.strftime("Última captura de informações feita no dia %d/%m/%Y às %H:%M hrs")

html_template = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel de Notícias</title>
    <link rel="manifest" href="manifest.json">
    <meta name="theme-color" content="#1a1a1e">
    <style>
        :root {{
            --bg-color: #121214;
            --card-bg: #1a1a1e;
            --text-color: #e1e1e6;
            --text-muted: #a8a8b3;
            --border-color: #29292e;
        }}
        body {{
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 40px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .container {{
            width: 100%;
            max-width: 1200px;
        }}
        h1 {{
            text-align: center;
            margin-bottom: 40px;
            font-size: 2.5rem;
            letter-spacing: -1px;
            background: linear-gradient(45deg, #e1e1e6, #a8a8b3);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .grid-noticias {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 16px;
            align-items: start;
        }}
        .fonte-box {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .fonte-box:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.3);
        }}
        .fonte-header {{
            padding: 16px 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 1.15rem;
            font-weight: 600;
            user-select: none;
            border-left: 6px solid #fff;
        }}
        .fonte-header::after {{
            content: '▼';
            font-size: 0.8rem;
            color: var(--text-muted);
            transition: transform 0.3s;
        }}
        .fonte-box.ativo .fonte-header::after {{
            transform: rotate(-180deg);
        }}
        .fonte-content {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.4s ease-out, padding 0.4s ease;
            padding: 0 20px;
            background-color: rgba(0,0,0,0.1);
        }}
        .fonte-box.ativo .fonte-content {{
            max-height: none;
            padding: 12px 20px;
            border-top: 1px solid var(--border-color);
        }}
        .noticia-item {{
            display: block;
            padding: 10px 0;
            text-decoration: none;
            color: var(--text-color);
            border-bottom: 1px solid rgba(255,255,255,0.05);
            transition: color 0.2s, padding-left 0.2s;
        }}
        .noticia-item:last-child {{
            border-bottom: none;
        }}
        .noticia-item:hover {{
            color: #52a5ff;
            padding-left: 6px;
        }}
        .noticia-titulo {{
            font-size: 0.95rem;
            line-height: 1.4;
            margin-bottom: 2px;
        }}
        .noticia-traducao {{
            font-size: 0.85rem;
            color: #9cdcfe;
            margin-top: 2px;
            margin-bottom: 2px;
            line-height: 1.3;
        }}
        .noticia-link {{
            font-size: 0.75rem;
            color: var(--text-muted);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .rodape-tempo {{
            text-align: center;
            margin-top: 40px;
            margin-bottom: 20px;
            font-size: 0.9rem;
            color: var(--text-muted);
            border-top: 1px solid var(--border-color);
            padding-top: 20px;
            width: 100%;
        }}
    </style>
    <script>
        if ('serviceWorker' in navigator) {{
            navigator.serviceWorker.register('./sw.js')
            .then(reg => console.log('App Ready'))
            .catch(err => console.log('Err:', err));
        }}
    </script>
</head>
<body>
    <div class="container">
        <h1>Central de Notícias</h1>
        <div class="grid-noticias">
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

html_template += f"""
        </div>
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

# --- BLOCO CORRIGIDO: GERAR RESUMO MENOR PARA O WHATSAPP ---
linhas_resumo = ["✅ O processo de raspagem rodou com sucesso!\n\n📌 *Amostra das últimas notícias:*"]

# Pegamos apenas os primeiros 5 sites para não estourar o limite de caracteres
for site in sites[:5]:
    noticias_do_site = dados_finais[site["id"]]
    if noticias_do_site:
        linhas_resumo.append(f"\n📰 *{site['nome']}:*")
        for i, noti in enumerate(noticias_do_site[:3]):
            titulo = noti.get("texto_traduzido", noti["texto"])
            # Mantém apenas os primeiros 80 caracteres de cada manchete no WhatsApp
            if len(titulo) > 80:
                titulo = titulo[:77] + "..."
            linhas_resumo.append(f"{i+1}. {titulo}")
            
with open("resumo.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(linhas_resumo))



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

# Lista de fontes configuradas
sites = [
    {"id": "g1", "nome": "G1 Globo", "url": "https://globo.com", "xpath": "//a[contains(@class, 'feed-post-link')] | //a[contains(@class, 'post__link')] | //div[contains(@class, 'bstn-fd-main')]//a", "cor": "#c4170c", "tamanho_min": 15},
    {"id": "cnn", "nome": "CNN Brasil", "url": "https://cnnbrasil.com.br", "xpath": "//a[contains(@class, 'home__list__tag')] | //a[contains(@class, 'home__title')] | //main//a", "cor": "#cc0000", "tamanho_min": 15},
    {"id": "times", "nome": "Times Brasil", "url": "https://timesbrasil.com.br", "xpath": "//main//a | //article//a", "cor": "#002447", "tamanho_min": 15},
    {"id": "jovempan", "nome": "Jovem Pan", "url": "https://jovempan.com.br", "xpath": "//div[contains(@class, 'post-item')]//a | //main//a", "cor": "#00441b", "tamanho_min": 15},
    {"id": "uol", "nome": "UOL", "url": "https://uol.com.br", "xpath": "//div[contains(@class, 'hu-commons')]//a | //a[contains(@class, 'hyperlink')]", "cor": "#f6a800", "tamanho_min": 15},
    {"id": "correio", "nome": "Correio Braziliense", "url": "https://correiobraziliense.com.br", "xpath": "//main//a | //a[contains(@class, 'title')]", "cor": "#005ca9", "tamanho_min": 15},
    {"id": "finviz", "nome": "Market News", "url": "https://finviz.com", "xpath": "//a[contains(@class, 'nn-tab-link')] | //td[contains(@class, 'nn-text')]//a", "cor": "#3f9c35", "tamanho_min": 15},
    {"id": "moneytimes", "nome": "Money Times", "url": "https://moneytimes.com.br", "xpath": "//h2/a | //h3/a | //div[contains(@class, 'news-item')]//a", "cor": "#173321", "tamanho_min": 15},
    {"id": "infomoney", "nome": "InfoMoney", "url": "https://infomoney.com.br", "xpath": "//a[contains(@class, 'typography__link')] | //main//a", "cor": "#001a30", "tamanho_min": 15},
    {"id": "r7", "nome": "R7 Notícias", "url": "https://r7.com", "xpath": "//a[contains(@class, 'r7-flex-title-link')] | /html/body/div/main//a", "cor": "#1d70b8", "tamanho_min": 15},
    {"id": "metropoles", "nome": "Metrópoles", "url": "https://metropoles.com", "xpath": "//h1/a | //h2/a | //h3/a | //h5/a | //a[contains(@class, 'm-title')]", "cor": "#ff0055", "tamanho_min": 15},
    {"id": "terra", "nome": "Terra", "url": "https://terra.com.br", "xpath": "//a[contains(@class, 'card-news__url')] | //main//a", "cor": "#2b3640", "tamanho_min": 15},
    {"id": "band", "nome": "Band", "url": "https://band.com.br", "xpath": "//a[@data-bnd-link] | //div[contains(@class, 'card')]//a | //main//a", "cor": "#006432", "tamanho_min": 15},
    {"id": "ig", "nome": "iG", "url": "https://ig.com.br", "xpath": "//h2/a | //h3/a | //main//a", "cor": "#1a4a7c", "tamanho_min": 15},
    {"id": "estadao", "nome": "Estadão", "url": "https://estadao.com.br", "xpath": "//section//a | //div[contains(@class, 'box')]//a | //main//a", "cor": "#007a87", "tamanho_min": 15},
    {"id": "folha", "nome": "Folha de S.Paulo", "url": "https://www.folha.uol.com.br/", "xpath": "//div[contains(@class, 'c-main-headline')]//a | //div[contains(@class, 'c-headline')]//a | //main//a", "cor": "#222222", "tamanho_min": 15}
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Termos gerais bloqueados em texto de botões de menus
termos_bloqueados = [
    "fale conosco", "politica de privacidade", "sobre o terra", "anuncie", "expediente", 
    "termos de uso", "assine", "minha conta", "perfil", "todos os direitos", "quem somos", 
    "home", "noticias", "contato", "newsletter", "cookies", "ajuda", "sac", "login",
    "cadastre-se", "painel", "editorial", "videos"
]

# BANCO DE DADOS DE EXCLUSÃO DE SITES (URLs Limpas - Lista ampliada)
urls_bloqueadas = {
    "uol.com.br",
    "uol.com.br/://uol.com.br",
    "://uol.com.br",
    "://uol.com.br/lp/esportes/max",
    "://uol.com.br",
    "://uol.com.br",
    "://uol.com.br",
    "://uol.com.br/loja-virtual",
    "://uol.com.br/criador-de-sites",
    "://uol.com.br/e-mail",
    "://uol.com.br/index.html",
    "://uol.com.br",
    "://uol.com.br",
    "://uol.com.br/politica/governo-lula",
    "://uol.com.br/internacional",
    "://uol.com.br/previsao-do-tempo",
    "://uol.com.br/ultimas",
    "://uol.com.br/loterias",
    "uol.com.br/esporte/podcast/posse-de-bola",
    "uol.com.br/universa/podcast/desculpa-alguma-coisa",
    "uol.com.br/play/diva-de-cnpj",
    "://uol.com.br/podcast/midia-e-marketing",
    "uol.com.br/carros/lancamentos-e-mercado",
    "uol.com.br/carros/avaliacao",
    "uol.com.br/carros/legislacao-multas-e-transito",
    "uol.com.br/carros/carros-eletricos",
    "uol.com.br/carros/manutencao-e-seguranca",
    "uol.com.br/carros/carros-curiosos",
    "uol.com.br/carros/na-garagem",
    "://uol.com.br/mais",
    "://uol.com.br/empresas-e-negocios",
    "://uol.com.br/empreendedorismo",
    "://uol.com.br/dinheiro-e-renda",
    "://uol.com.br/guia-de-compras",
    "://uol.com.br/guia-de-economia",
    "://uol.com.br/imposto-de-renda",
    "://uol.com.br/cotacoes/cambio",
    "://uol.com.br/cotacoes/bolsas",
    "://uol.com.br/cotacoes/cambio/criptomoeda",
    "://uol.com.br/imposto-de-renda/noticias/redacao/2026/03/20/imposto-de-renda-download-programa-declaracao.ghtm",
    "://uol.com.br/imposto-de-renda/duvidas",
    "://uol.com.br/bolsa-familia",
    "://uol.com.br/pis",
    "://uol.com.br/preco-dos-combustiveis",
    "://uol.com.br/inflacao",
    "://uol.com.br/banco-central",
    "://uol.com.br/temas/juros",
    "://uol.com.br/colunaseblogs",
    "uol.com.br/esporte/futebol/central-de-jogos",
    "uol.com.br/esporte/futebol/campeonatos/copa-do-mundo",
    "uol.com.br/esporte/futebol/campeonatos/libertadores",
    "uol.com.br/esporte/futebol/campeonatos/copa-do-brasil",
    "uol.com.br/esporte/futebol/campeonatos/copa-sul-americana",
    "uol.com.br/esporte/futebol/campeonatos/liga-dos-campeoes",
    "uol.com.br/esporte/futebol/campeonatos",
    "uol.com.br/esporte/colunas/mercado-da-bola",
    "uol.com.br/esporte/futebol/times/brasil",
    "uol.com.br/esporte/futebol/ultimas-noticias/2026/05/18/convocacao-selecao-brasileira-copa-do-mundo-ancelotti.ghtm",
    "uol.com.br/esporte/futebol/times/brasil/proximos-jogos",
    "uol.com.br/esporte/futebol/ultimas-noticias/2025/12/05/o-hexa-vem-simule-os-possiveis-jogos-da-copa-2026-apos-sorteio-dos-grupos.htm",
    "uol.com.br/esporte/futebol/ultimas-noticias/2026/05/19/convoque-selecao.ghtm",
    "uol.com.br/splash/bbb/enquetes",
    "uol.com.br/splash/musica/festivais",
    "uol.com.br/splash/reality-shows",
    "uol.com.br/splash/teatro-e-musicais",
    "uol.com.br/splash/novelas/coracao-acelerado",
    "uol.com.br/splash/novelas/a-nobreza-do-amor",
    "uol.com.br/splash/novelas/terra-nostra",
    "://uol.com.br/banca",
    "://uol.com.br/livros",
    "uol.com.br/universa/maria-vai-com-os-outros",
    "uol.com.br/universa/inspira/lab-da-beleza",
    "uol.com.br/universa/universa-talks",
    "uol.com.br/vivabem/equilibrio",
    "uol.com.br/vivabem/movimento",
    "uol.com.br/vivabem/saude/bula",
    "uol.com.br/vivabem/saude/emagrecimento",
    "uol.com.br/vivabem/saude/gravidez-e-maternidade",
    "uol.com.br/vivabem/saude/gripes-e-resfriados",
    "uol.com.br/vivabem/saude/doencas-de-a-z",
    "uol.com.br/vivabem/saude/qual-e-o-remedio",
    "uol.com.br/vivabem/alimentacao/chas-e-seus-beneficios",
    # Novas inclusões solicitadas
    "uol.com.br/vivabem/colunas/guia-do-supermercado",
    "uol.com.br/tilt/fique-por-dentro",
    "uol.com.br/tilt/tec-a-seu-favor",
    "uol.com.br/tilt/novos-habitos",
    "uol.com.br/tilt/redes-sociais",
    "uol.com.br/tilt/isso-e-golpe",
    "uol.com.br/tilt/teste-velocidade-internet",
    "uol.com.br/tilt/dicas-matadoras",
    "uol.com.br/tilt/a-tecnologia-por-tras",
    "uol.com.br/tilt/no-brasil-nao-tem",
    "uol.com.br/ecoa/crise-climatica",
    "uol.com.br/ecoa/iniciativas-que-inspiram",
    "uol.com.br/ecoa/temas/meio-ambiente",
    "uol.com.br/ecoa/energia-limpa",
    "uol.com.br/nossa/reportagens-especiais/ultimas",
    "uol.com.br/nossa/cozinha/receitas",
    "uol.com.br/nossa/cozinha/receitas/lista",
    "uol.com.br/nossa/cozinha/receita-de-familia",
    "uol.com.br/nossa/cozinha/gastronobasico",
    "uol.com.br/nossa/viagem/fora-da-rota",
    "uol.com.br/toca/de-ponta-a-ponta",
    "uol.com.br/toca/rota-dos-shows",
    "uol.com.br/toca/reality",
    "uol.com.br/guia-de-compras/bebes-e-criancas",
    "uol.com.br/guia-de-compras/casa-e-cozinha",
    "uol.com.br/guia-de-compras/roupas-e-acessorios"
}

dados_finais = {site["id"]: [] for site in sites}
print("Iniciando a raspagem de dados com banco de dados de exclusão ampliado...")

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
                texto_lower = texto.lower()
                if any(termo in texto_lower for termo in termos_bloqueados):
                    continue
                
                vistas.add(texto)
                
                if link.startswith('/'):
                    url_base = site["url"].split('?').rstrip('/')
                    link = f"{url_base}{link}"
                
                if "javascript:" not in link and link.startswith('http'):
                    
                    # Normalização rigorosa para validação estrutural contra a lista negra
                    link_limpo = link.replace("https://", "").replace("http://", "").split('?')[0].split('#')[0].rstrip('/')
                    link_limpo_com_www = link_limpo.replace("www.", "")
                    
                    if link_limpo in urls_bloqueadas or link_limpo_com_www in urls_bloqueadas:
                        continue
                    
                    if site["id"] in ["estadao", "folha", "band"]:
                        partes_url = link_limpo.split('/')
                        if len(partes_url) < 3:
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

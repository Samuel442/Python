import io
import pdfkit
import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime
import base64 
import plotly.io as pio 

try:
    # garante que exista um dict kaleido em defaults
    if not isinstance(pio.defaults.get('kaleido'), dict):
        pio.defaults['kaleido'] = {}

    # define args recomendados para evitar subprocess/browser errors no Windows
    pio.defaults['kaleido']['chromium_args'] = [
        "--single-process",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage"
    ]

    # opcional: evita injeção de MathJax (às vezes reduz problemas)
    pio.defaults['kaleido']['mathjax'] = None

except Exception:
    # se qualquer erro ocorrer (versões antigas etc.), não interrompe o app
    # mas ainda assim prosseguimos — o Kaleido pode usar configurações padrão.
    pass


# ------------------ Função segura de leitura ------------------
def _safe_val(df: pd.DataFrame, col: str, default=None):
    """Lê o último valor não nulo de uma coluna do DataFrame."""
    try:
        return df.dropna(subset=[col]).iloc[-1][col]
    except Exception:
        return default

# ------------------ Funções de formatação seguras ------------------
def fmt_money(v):
    """Formata como dinheiro (ex: $95,224)."""
    if isinstance(v, (int, float)):
        # Garante duas casas decimais para preço, mas zero para outros
        return f"${v:,.2f}" if v > 1000 else f"${v:,.2f}"
    return str(v)

def fmt_money_trillion(v):
    """Formata grandes valores em trilhões (ex: $3.28 T)."""
    return f"${v/1e12:.2f} T" if isinstance(v, (int, float)) else str(v)

def fmt_percent(v):
    """Formata como porcentagem (ex: 57.25 %)."""
    return f"{v:.2f} %" if isinstance(v, (int, float)) else str(v)

def fmt_delta(v):
    """Formata como delta com sinal (+/-) e cores (Melhorias Visuais)."""
    if isinstance(v, (int, float)):
        color = 'color: #1abc9c;' if v >= 0 else 'color: #e74c3c;' # Verde para positivo, Vermelho para negativo
        return f"<span style='{color}'>{v:+.0f}</span>"
    return "N/A"


# =====================================================================
# ======================= FUNÇÃO PRINCIPAL =============================
# =====================================================================

def generate_aba6_pdf_bytes(
    df_btc: pd.DataFrame,
    df_global: pd.DataFrame,
    df_sentiment: pd.DataFrame,
    df_news: pd.DataFrame,
    figs: Optional[Dict[str, Any]] = None,
    wkhtmltopdf_path: Optional[str] = None,
    pdfkit_options: Optional[Dict[str, Any]] = None
) -> bytes:
    """
    Gera o PDF final espelhando a Aba 6 com um visual modernizado.
    
    O dicionário 'figs' deve ter as chaves esperadas:
    'price', 'dom', 'vol', 'comp'
    """

    # -------- opções padrão do wkhtmltopdf --------
    if pdfkit_options is None:
        pdfkit_options = {
            'enable-local-file-access': None,
            'enable-javascript': None,
            'no-stop-slow-scripts': None,
            'javascript-delay': 800,
            'encoding': "UTF-8",
            'page-size': 'A4',
            'margin-top': '15mm',
            'margin-bottom': '15mm',
            'margin-left': '12mm',
            'margin-right': '12mm'
        }

    # -------- configuração do wkhtmltopdf --------
    if wkhtmltopdf_path:
        try:
            config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
        except Exception:
            config = None
    else:
        config = None

    # -------- métricas --------
    last_btc = _safe_val(df_btc, "price_usd", default="N/A")
    prev_btc = _safe_val(df_btc.iloc[:-1] if len(df_btc) > 1 else df_btc, "price_usd", default=None)

    delta_btc_val = (
        last_btc - prev_btc
        if isinstance(last_btc, (int, float)) and isinstance(prev_btc, (int, float))
        else "N/A"
    )
    # Formata o delta com cores (uso de span com estilo)
    delta_btc_html = fmt_delta(delta_btc_val)


    last_mc = _safe_val(df_global, "total_market_cap", default="N/A")
    last_dom = _safe_val(df_global, "btc_dominance", default="N/A")
    last_sent = _safe_val(df_sentiment, "fear_greed_index", default="N/A")
    
    sent_text = "N/A"
    if isinstance(last_sent, (int, float)):
        if last_sent <= 20: sent_text = "Extreme Fear"
        elif last_sent <= 40: sent_text = "Fear"
        elif last_sent <= 60: sent_text = "Neutral"
        elif last_sent <= 80: sent_text = "Greed"
        else: sent_text = "Extreme Greed"

    # -------- gráficos (Usa KALEIDO para garantir renderização estática) --------
    figs_html = {}
    graph_keys = ['price', 'dom', 'vol', 'comp']
    
    if figs:
        for k in graph_keys:
            f = figs.get(k)
            if f is not None:
                try:
                    image_bytes = pio.to_image(
                        f, 
                        format="png", 
                        width=900, 
                        height=500, 
                        scale=1.5, 
                        engine="kaleido"
                    ) 
                    
                    base64_encoded_image = base64.b64encode(image_bytes).decode('utf-8')
                    
                    # Tag HTML IMG estática
                    figs_html[k] = f"""
                    <div class='graph-container'>
                        <h3 class="graph-title">{k.replace('_', ' ').title()}</h3>
                        <img src='data:image/png;base64,{base64_encoded_image}' 
                             style='width:100%; height:auto; display:block;'
                             alt='Gráfico {k}'/>
                    </div>
                    """
                except Exception as e:
                    # Mensagem de erro aprimorada, mantendo o alerta sobre o problema ambiental
                    figs_html[k] = f"""
                    <div class='graph-error'>
                        <h3 class="graph-title">{k.replace('_', ' ').title()}</h3>
                        <p>⚠️ Falha de Renderização Plotly/Kaleido: {e}</p>
                        <p>O erro 'browser subprocess' para <b>{k.upper()}</b> é geralmente ambiental (permissão ou conflito). Tente: <code>pip install -U kaleido</code></p>
                    </div>
                    """
            else:
                # Mensagem para 'indisponível'
                figs_html[k] = f"""
                <div class='graph-unavailable'>
                    <h3 class="graph-title">{k.replace('_', ' ').title()}</h3>
                    <p>Gráfico {k} indisponível.</p>
                </div>
                """

    # -------- CSS (Visual Moderno: Clean & Professional) --------
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    css = """
    <style>
    /* Estilos Gerais & Modernização */
    body { font-family: 'Inter', Arial, sans-serif; background:#f8f9fa; color:#212529; line-height: 1.6; }
    .container { 
        max-width: 900px; 
        margin:20px auto; 
        padding:30px; 
        background:#fff; 
        border-radius:15px; 
        box-shadow: 0 10px 30px rgba(0,0,0,0.08); /* Sombra mais suave */
    }
    
    /* Títulos */
    h1 { color:#0056b3; font-size: 28px; border-bottom: 3px solid #0056b3; padding-bottom: 12px; margin-bottom: 10px; font-weight: 700; }
    h2 { color:#343a40; font-size: 22px; margin-top: 35px; border-left: 6px solid #0056b3; padding-left: 15px; font-weight: 600; }
    h3 { color:#495057; font-size: 18px; margin: 0 0 10px; }

    /* Métricas (Cards) */
    .metrics { display:flex; gap:20px; margin-bottom:30px; flex-wrap:wrap; }
    .card { 
        background:linear-gradient(145deg, #ffffff, #f2f2f2); /* Leve gradiente */
        padding:20px; 
        border-radius:12px; 
        box-shadow:0 4px 10px rgba(0,0,0,0.05); 
        flex:1 1 200px; 
        min-width: 180px;
        border: 1px solid #e0e0e0;
        transition: transform 0.2s;
    }
    .card:hover {
        transform: translateY(-3px); /* Efeito de hover */
        box-shadow:0 6px 15px rgba(0,0,0,0.1);
    }
    .card h3 { color:#0056b3; margin:0 0 8px; font-size:15px; text-transform: uppercase; letter-spacing: 0.5px; }
    .card p { margin:0; font-size:24px; font-weight: 700; }
    .card p:last-child { font-weight: normal; font-size: 13px; color: #6c757d; margin-top: 5px; }
    
    /* Seções e Gráficos */
    .section { margin-top:30px; }
    .graph-container { 
        background:#ffffff; 
        padding:20px; 
        border: 1px solid #e9ecef; 
        border-radius:10px; 
        margin-bottom: 30px; 
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
    }
    .graph-title { color:#343a40; font-size:20px; text-align: center; border-bottom: 2px dashed #adb5bd; padding-bottom: 10px; margin-bottom: 15px; font-weight: 500; }
    
    /* Mensagens de Erro e Indisponível (Cores Fortes) */
    .graph-error { color: #8b0000; background: #fff0f0; padding: 18px; border-radius: 10px; margin-bottom: 30px; border: 1px solid #e74c3c; }
    .graph-unavailable { color: #8a6d3b; background: #fff9e6; padding: 18px; border-radius: 10px; margin-bottom: 30px; border: 1px solid #f39c12; }

    /* Notícias */
    .news-item { 
        padding:15px; 
        border-radius:8px; 
        background:#343a40; 
        color:#ffffff; 
        margin-bottom:10px; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .news-item b { color:#ffd700; } /* Destaque em amarelo ouro */
    .news-item a { color:#ffffff; text-decoration:none; font-weight:bold; }
    .news-item a:hover { text-decoration:underline; color: #cccccc; }
    .news-item div { font-size:12px; color:#adb5bd; margin-top:6px; }
    
    /* Rodapé */
    .footer { font-size:12px; color:#6c757d; margin-top:40px; padding-top:15px; border-top: 1px dashed #ced4da; text-align:center; }
    </style>
    """

    # -------- notícias --------
    news_html = ""
    if not df_news.empty and ("headline" in df_news.columns or "title" in df_news.columns):
        df_news_sorted = df_news.copy()

        if "date" in df_news_sorted.columns:
            df_news_sorted["date"] = pd.to_datetime(df_news_sorted["date"], errors="coerce")
            df_news_sorted = df_news_sorted.sort_values("date", ascending=False).head(7)

        for _, r in df_news_sorted.iterrows():
            headline = r.get("headline") or r.get("title") or "Título indisponível"
            source = r.get("source") or "Fonte Desconhecida"
            link = r.get("link") or "#"
            date = r.get("date")
            date_str = date.strftime("%d/%m/%Y") if hasattr(date, "strftime") else "Data N/A"

            news_html += f"""
            <div class='news-item'>
                <b>{source}</b>: <a href='{link}'>{headline}</a>
                <div>📅 {date_str}</div>
            </div>
            """
    else:
        news_html = "<p class='graph-unavailable'>Nenhuma notícia disponível no momento.</p>"

    # =====================================================================
    # ======================= HTML FINAL COMPLETO =========================
    # =====================================================================

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    {css}
    <title>Relatório de Mercado Cripto Moderno</title>
    </head>
    <body>
      <div class="container">
        <h1>Relatório de Mercado Cripto <span style="color:#ffd700;">PRO</span></h1>
        <p style='color:#6c757d; font-size: 13px; margin-top:-10px;'>Gerado em: {now} | Todas as métricas em UTC</p>

        <div class="section metrics">
        
          <div class="card">
            <h3>Preço BTC (USD)</h3>
            <p>{fmt_money(last_btc)}</p>
            <p>Variação diária: {delta_btc_html}</p>
          </div>

          <div class="card">
            <h3>Market Cap Global</h3>
            <p>{fmt_money_trillion(last_mc)}</p>
            <p>Capitalização total do mercado</p>
          </div>

          <div class="card">
            <h3>Dominância BTC</h3>
            <p>{fmt_percent(last_dom)}</p>
            <p>Peso do Bitcoin no mercado</p>
          </div>

          <div class="card">
            <h3>Índice Fear & Greed</h3>
            <p>{last_sent}</p>
            <p style='color:#0056b3; font-weight: bold;'>{sent_text}</p>
          </div>

        </div>

        <div class="section">
          <h2>Análise Gráfica Detalhada</h2>
          {figs_html.get('price', '<div class="graph-unavailable"><p>Gráfico de Preço indisponível.</p></div>')}
          {figs_html.get('dom', '<div class="graph-unavailable"><p>Gráfico de Dominância indisponível.</p></div>')}
          {figs_html.get('vol', '<div class="graph-unavailable"><p>Gráfico de Volume indisponível.</p></div>')}
          {figs_html.get('comp', '<div class="graph-unavailable"><p>Comparação de Performance indisponível.</p></div>')}
        </div>

        <div class="section">
          <h2>Notícias & Sentimento</h2>
          {news_html}
        </div>

        <div class="footer">
          <p>Relatório de Geração Automática. Todos os dados são baseados nas últimas informações disponíveis no momento da compilação.</p>
        </div>

      </div>
    </body>
    </html>
    """

    # -------- gerar PDF --------
    try:
        if config:
            pdf_bytes = pdfkit.from_string(html, False, options=pdfkit_options, configuration=config)
        else:
            pdf_bytes = pdfkit.from_string(html, False, options=pdfkit_options)

        return pdf_bytes if isinstance(pdf_bytes, bytes) else pdf_bytes.encode("utf-8")

    except Exception as e:
        raise RuntimeError(f"Erro CRÍTICO ao gerar PDF (wkhtmltopdf): {e}")
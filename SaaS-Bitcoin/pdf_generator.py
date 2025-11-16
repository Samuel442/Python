# pdf_generator.py
import io
import pdfkit
import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime


def _safe_val(df: pd.DataFrame, col: str, default=None):
    try:
        return df.dropna(subset=[col]).iloc[-1][col]
    except Exception:
        return default

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
    Gera o PDF (bytes) espelhando a Aba 6.

    Parâmetros:
    - df_btc, df_global, df_sentiment, df_news: pandas DataFrames já filtrados conforme o período.
    - figs: dicionário opcional com figuras Plotly (ex: {'price': fig_price, 'dom': fig_dom, 'vol': fig_vol})
    - wkhtmltopdf_path: caminho absoluto para wkhtmltopdf executável (ex: r"venv\\Scripts\\wkhtmltopdf.exe" no Windows)
    - pdfkit_options: dict de opções para pdfkit (wkhtmltopdf). Se None, usa opções padrão sugeridas.

    Retorna:
    - bytes do PDF gerado
    """

    # -------------- opções seguras padrão para wkhtmltopdf --------------
    if pdfkit_options is None:
        pdfkit_options = {
            'enable-local-file-access': None,    # permite carregar arquivos locais se precisar
            'enable-javascript': None,
            'no-stop-slow-scripts': None,
            'javascript-delay': 700,            # ms (aumente se os gráficos não renderizarem)
            'encoding': "UTF-8",
            'page-size': 'A4',
            'margin-top': '15mm',
            'margin-bottom': '15mm',
            'margin-left': '12mm',
            'margin-right': '12mm'
        }

    # -------------- Configuração do pdfkit (wkhtmltopdf) --------------
    if wkhtmltopdf_path:
        try:
            config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
        except Exception:
            config = None
    else:
        config = None

    # -------------- Extrai métricas (com fallback) --------------
    last_btc = _safe_val(df_btc, "price_usd", default="N/A")
    prev_btc = _safe_val(df_btc.iloc[:-1] if len(df_btc) > 1 else df_btc, "price_usd", default=None)
    try:
        delta_btc = (last_btc - prev_btc) if (isinstance(last_btc, (int, float)) and isinstance(prev_btc, (int, float))) else None
    except Exception:
        delta_btc = None

    last_mc = _safe_val(df_global, "total_market_cap", default="N/A")
    last_dom = _safe_val(df_global, "btc_dominance", default="N/A")
    last_sent = _safe_val(df_sentiment, "fear_greed_index", default="N/A")
    sent_text = _safe_val(df_sentiment, "sentiment_text", default="N/A")

    # -------------- Gera HTML dos gráficos (usando fig.to_html) --------------
    # figs é um dicionário: ex: {'price': fig_price, 'dom': fig_dom, 'vol': fig_vol}
    figs_html = {}
    if figs:
        for k, f in figs.items():
            try:
                # Produz apenas o snippet do div (sem <html> completo). Inclui plotly.js via CDN.
                figs_html[k] = f.to_html(full_html=False, include_plotlyjs='cdn')
            except Exception as e:
                figs_html[k] = f"<div><p>Erro ao gerar gráfico {k}: {e}</p></div>"

    # -------------- Prepara HTML do relatório (estilo simples e responsivo) --------------
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    css = """
    <style>
    body { font-family: Arial, Helvetica, sans-serif; color: #222; background: #fff; }
    .container { max-width: 1024px; margin: auto; padding: 12px; }
    h1 { color: #111; }
    .metrics { display:flex; gap:12px; margin-bottom:12px; flex-wrap:wrap; }
    .card { background:#f7f7f7; padding:12px; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.06); flex:1 1 220px; }
    .card h3 { margin:0 0 6px 0; font-size:14px; }
    .card p { margin:0; font-size:13px; }
    .section { margin-top:18px; }
    .news-item { padding:10px; border-radius:6px; background:#222; color:#fff; margin-bottom:8px; }
    .news-item a { color:#ffd54f; text-decoration:none; }
    .footer { font-size:11px; color:#666; margin-top:18px; }
    </style>
    """

    # Lista de notícias em HTML
    news_html = ""
    try:
        if (not df_news.empty) and ("headline" in df_news.columns):
            df_news_sorted = df_news.copy()
            if "date" in df_news_sorted.columns:
                df_news_sorted["date"] = pd.to_datetime(df_news_sorted["date"], errors='coerce')
                df_news_sorted = df_news_sorted.sort_values("date", ascending=False)
            for _, r in df_news_sorted.head(7).iterrows():
                headline = r.get("headline") or r.get("title") or ""
                source = r.get("source") or ""
                link = r.get("link") or "#"
                date = r.get("date")
                if hasattr(date, "strftime"):
                    date = date.strftime("%d/%m/%Y")
                else:
                    date = str(date)
                news_html += f"<div class='news-item'><b>{source}</b>: <a href='{link}'>{headline}</a><div style='font-size:11px;color:#bbb;margin-top:6px;'>📅 {date}</div></div>"
    except Exception:
        news_html = "<p>Nenhuma notícia disponível.</p>"

    # Monta o HTML final
    html = f"""
    <html>
    <head>
    <meta charset="utf-8">
    {css}
    <title>Resumo Geral do Mercado</title>
    </head>
    <body>
      <div class="container">
        <h1>📘 Resumo Geral do Mercado</h1>
        <p>Gerado em: {now}</p>

        <div class="section metrics">
          <div class="card">
            <h3>Preço BTC (USD)</h3>
            <p><b>{last_btc if last_btc is not None else 'N/A'}</b></p>
            <p>Δ: {delta_btc if delta_btc is not None else 'N/A'}</p>
          </div>

          <div class="card">
            <h3>Market Cap (Total)</h3>
            <p><b>{last_mc}</b></p>
          </div>

          <div class="card">
            <h3>Dominância BTC (%)</h3>
            <p><b>{last_dom}</b></p>
          </div>

          <div class="card">
            <h3>Fear & Greed</h3>
            <p><b>{last_sent}</b></p>
            <p>{sent_text}</p>
          </div>
        </div>

        <div class="section">
          <h2>📈 Gráficos</h2>
          {figs_html.get('price','<p>Preço indisponível.</p>')}
          {figs_html.get('dom','')}
          {figs_html.get('vol','')}
        </div>

        <div class="section">
          <h2>📰 Últimas Notícias</h2>
          {news_html}
        </div>

        <div class="footer">
          <p>Relatório gerado automaticamente — espelho da Aba 6</p>
        </div>
      </div>
    </body>
    </html>
    """

    # -------------- Converter para PDF (retorna bytes) --------------
    try:
        pdf_bytes = None
        # gera PDF em memória retornando bytes
        if config:
            pdf_bytes = pdfkit.from_string(html, False, options=pdfkit_options, configuration=config)
        else:
            pdf_bytes = pdfkit.from_string(html, False, options=pdfkit_options)
        if isinstance(pdf_bytes, bytes):
            return pdf_bytes
        else:
            # pdfkit às vezes retorna str; garantir bytes
            return pdf_bytes.encode("utf-8")
    except Exception as e:
        # caso falhe, retorna exceção para o chamador tratar
        raise RuntimeError(f"Erro ao gerar PDF: {e}")

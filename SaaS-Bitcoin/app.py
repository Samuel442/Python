import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from datetime import datetime, timedelta, timezone 


# --- CONFIGURAÇÃO INICIAL E ESTILO ---
st.set_page_config(
    page_title="Crypto Dashboard",
    layout = "wide",
    initial_sidebar_state = "expanded"
)


# --- ESTILO ---
st.markdown("""
<style>
/* ====== FUNDO GERAL COM DEGRADÊ ====== */
.stApp {
    background: linear-gradient(135deg, #1a1a1a 0%, #111111 70%, #1e1e1e 100%);
    color: white;
}
/* ====== ESTILO PARA OS CARDS (KPIs) ====== */
.stMetric {
    background-color: #2D2D2D;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.4);
    color: white;
}
/* ====== TABELAS E CAIXAS ====== */
.rounded-box {
    background-color: #2D2D2D;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.3);
}
/* ====== TÍTULOS E TEXTOS ====== */
h1, h2, h3, h4, .css-1d3z3vf, .st-cl, .st-bu, .st-bq {
    color: white !important;
}
/* ====== ESTILO DAS ABAS COMO BOTÕES ====== */
[data-baseweb="tab-list"] {
    gap: 8px !important;
}
[data-baseweb="tab"] {
    background-color: #2D2D2D;
    border: 1px solid #444;
    border-radius: 10px;
    padding: 10px 20px;
    color: #CCCCCC !important;
    font-weight: 500;
    transition: all 0.2s ease-in-out;
}
[data-baseweb="tab"]:hover {
    background-color: #3A3A3A;
    border-color: #888;
    color: white !important;
}
[data-baseweb="tab"][aria-selected="true"] {
    background-color: #4C4C4C;
    border: 1px solid #00BFFF;
    color: white !important;
    font-weight: 600;
    box-shadow: 0px 0px 8px rgba(0, 191, 255, 0.5);
}
/* Aplica bordas arredondadas a todos os gráficos Plotly */
div.stPlotlyChart {
    border-radius: 10px; /* Ajuste o valor conforme a sua preferência */
    overflow: hidden; /* Garante que o conteúdo interno respeite o border-radius */
    border: 1px solid #3A3A3A; /* Opcional: Adiciona uma linha sutil para separar, como nos st.metric */
}
/* ====== SUAVIZA O SCROLL ====== */
html {
    scroll-behavior: smooth;
}
</style>
""", unsafe_allow_html=True)



# --- Carregando dados do toml
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Erro: Não foi possível carregar as credenciais do Supabase. Verifique se o arquivo .streamlit/secrets.toml está correto.")
    st.stop()



st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600&display=swap');
    .neon-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 46px;
        text-align: center;
        color: #00E0FF;
        text-shadow:
            0 0 3px #00E0FF,
            0 0 6px rgba(0, 224, 255, 0.5);
        letter-spacing: 2px;
        margin-bottom: 25px;
    }
    </style>
    <h1 class="neon-title">₿ SaaS Crypto</h1>
""", unsafe_allow_html=True)







@st.cache_data(ttl=600) # Cachea os dados por 10 minutos
def load_data_api(table_name: str) -> pd.DataFrame:
    """Busca dados da tabela especificada no Supabase e retorna um DataFrame."""
    try:
        # A função 'select' é uma string vazia para selecionar todas as colunas
        response = supabase.table(table_name).select("*").execute()
        # O data está no índice [1] da resposta
        data = response.data
        # Converte para DataFrame do Pandas
        df = pd.DataFrame(data)
        # Converte a coluna 'timestamp' para datetime E GARANTE O FUSO HORÁRIO
        if 'timestamp' in df.columns:
            # 1. Converte o timestamp para objeto datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce') 
            # 2. SE o Pandas ainda não souber o fuso horário (tz is None), 
            #    ele é forçado a ser UTC para combinar com as datas do filtro.
            if df['timestamp'].dt.tz is None:
                df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados da tabela '{table_name}': {e}")
        return pd.DataFrame()


# --- FUNÇÃO PARA CARREGAR DADOS E FILTRO LATERAL ---
# Dicionário de opções para o filtro lateral
DATE_OPTIONS = {
    "Últimos 7 Dias": 7,
    "Últimos 30 Dias": 30,
    "Últimos 90 Dias": 90,
    "Desde o Início": 0
}
# --- BARRA LATERAL (st.sidebar) ---
st.sidebar.markdown("## 📊 Filtros de Análise")
# 1. Seletor de Período
selected_period = st.sidebar.selectbox(
    "Selecione o Período:",
    options=list(DATE_OPTIONS.keys()),
    index=1 # Padrão: 30 dias
)
# 2. Lógica para Definir o Filtro de Data
end_date = datetime.now().replace(tzinfo=timezone.utc) 
start_date = None
if selected_period == "Personalizado":
    # Permite ao usuário escolher as datas
    st.sidebar.markdown("---")
    # Garantir que temos duas datas no range
    if len(date_range) == 2:
        # datetime.combine transforma date_input (date) em datetime. Adicione .replace(tzinfo=timezone.utc)
        start_date = datetime.combine(date_range[0], datetime.min.time()).replace(tzinfo=timezone.utc)
        end_date = datetime.combine(date_range[1], datetime.max.time()).replace(tzinfo=timezone.utc) 
    else:
        st.sidebar.warning("Selecione o intervalo completo.")
elif selected_period in DATE_OPTIONS:
    days = DATE_OPTIONS[selected_period]
    if days > 0:
        # A subtração de timedelta é feita com tz-aware datetime
        start_date = end_date - timedelta(days=days)
    else:
        start_date = None
# --- FIM DA BARRA LATERAL ---



# ----------------- ESTRUTURA DE ABAS (Baseada no Modelo BI) -----------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Visão Geral", 
                                       "Preço e Tendências", 
                                             "Adoção e Uso", 
                                    "Sentimento e Notícias",
                                             "Comparativos",
                                        "Relatório Semanal"])



# ==============================================================================
# ABA 1 - VISÃO GERAL
# ==============================================================================
with tab1:
    # --- SEÇÃO A: PREÇOS ATUAIS (USD, BRL, CAPITALIZAÇÃO) ---
    col_price_usd, col_price_brl, col_market_cap = st.columns([1.5, 1.5, 1.5])
    df_prices = load_data_api("prices_btc")
    if not df_prices.empty and start_date:
        df_prices = df_prices[
            (df_prices['timestamp'] >= start_date) & 
            (df_prices['timestamp'] <= end_date)
        ].reset_index(drop=True)
    if not df_prices.empty and len(df_prices) >= 2:
        latest_usd = df_prices['price_usd'].iloc[-1]
        latest_brl = df_prices['price_brl'].iloc[-1]
        previous_usd = df_prices['price_usd'].iloc[-2]
        previous_brl = df_prices['price_brl'].iloc[-2]
        change_usd = (latest_usd - previous_usd) / previous_usd
        change_brl = (latest_brl - previous_brl) / previous_brl
        delta_usd_str = f"{change_usd * 100:.2f} %"
        delta_brl_str = f"{change_brl * 100:.2f} %"
        has_data = True
    else:
        has_data = False
        delta_usd_str = "N/A"
        delta_brl_str = "N/A"
    # --- Cartões de preço USD e BRL ---
    with col_price_usd:
        if has_data:
            st.metric("PREÇO ATUAL (USD)", f"$ {latest_usd:,.2f}", delta_usd_str)
        else:
            st.warning("⚠️ Dados de preço não disponíveis.")
    with col_price_brl:
        if has_data:
            st.metric(
                "PREÇO ATUAL (BRL)",
                f"R$ {latest_brl:,.2f}".replace(",", "_TEMP_").replace(".", ",").replace("_TEMP_", "."),
                delta_brl_str
            )
    # --- Card de Capitalização de Mercado ---
    df_market = load_data_api("market_global")
    if not df_market.empty and start_date:
        df_market = df_market[
            (df_market['timestamp'] >= start_date) & 
            (df_market['timestamp'] <= end_date)
        ].reset_index(drop=True)
    with col_market_cap:
        if not df_market.empty and 'total_market_cap' in df_market.columns:
            latest_market_cap = df_market['total_market_cap'].iloc[-1]
            previous_market_cap = df_market['total_market_cap'].iloc[-2]
            change_market_cap = (latest_market_cap - previous_market_cap) / previous_market_cap
            color = "#00FF7F" if change_market_cap > 0 else "#FF4500"
            arrow = "⬆️" if change_market_cap > 0 else "⬇️"
            market_cap_billions = latest_market_cap / 1_000_000_000
            value_str = f"${market_cap_billions:,.2f} B"
            delta_str = f"{change_market_cap * 100:,.2f}%"
            st.markdown(
                f"""
                <div class="rounded-box" style="padding: 15px; background-color: #2D2D2D; height: 130px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div style="color: white; font-size: 1.1em;">CAPITALIZAÇÃO DE MERCADO</div>
                    <div style="font-size: 1.8em; font-weight: bold; color: white;">{value_str}</div>
                    <div style="font-size: 1.2em; color: {color};">{arrow} {delta_str}</div>
                </div>
                """, 
                unsafe_allow_html=True
            )
        else:
            st.warning("⚠️ Dados de Capitalização de Mercado indisponíveis.")
    st.markdown("---")


    # --- SEÇÃO B: KPI’s SECUNDÁRIOS (Gauge + Volume) ---
    GRAPH_HEIGHT = 250
    # Deixa o gráfico de volume mais largo que o gauge
    col_gauge, col_volume = st.columns([1.2, 1.8])
    # 1️⃣ Gauge (Fear & Greed)
    df_sentiment = load_data_api("sentiment")
    with col_gauge:
        if not df_sentiment.empty and 'fear_greed_index' in df_sentiment.columns:
            latest_score = df_sentiment['fear_greed_index'].iloc[-1]
            latest_sentiment_text = df_sentiment['sentiment_text'].iloc[-1]
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=latest_score,
                title={
                    'text': f"Índice Medo & Ganância<br><span style='font-size:0.9em; color:#FFFFFF;'>{latest_sentiment_text.upper()}</span>", 
                    'font': {'size': 18, 'color': '#00BFFF'}
                },
                gauge={
                    'axis': {'range': [0, 100], 'tickcolor': "#777"},
                    'bar': {'color': "rgba(0,0,0,0)"},
                    'steps': [
                        {'range': [0, 25], 'color': "#8B0000"},
                        {'range': [25, 50], 'color': "#CC0000"},
                        {'range': [50, 75], 'color': "#009900"},
                        {'range': [75, 100], 'color': "#006400"},
                    ],
                    'threshold': {'line': {'color': "#FFF", 'width': 4}, 'value': latest_score}
                }
            ))
            fig_gauge.update_layout(paper_bgcolor="#2D2D2D", height=GRAPH_HEIGHT, font={'color': "white"})
            st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})
        else:
            st.warning("⚠️ Dados de Sentimento indisponíveis.")


    # 2️⃣ Volume de Negociação (Gráfico de Barras)
    with col_volume:
        if not df_market.empty and 'total_volume' in df_market.columns:
            df_volume = df_market.copy()
            fig_vol = go.Figure(data=[
                go.Bar(
                    x=df_volume['timestamp'], 
                    y=df_volume['total_volume'], 
                    marker_color="#00BFFF"
                )
            ])
            fig_vol.update_layout(
                title=f"Volume de Negociação ({selected_period})",
                paper_bgcolor="#2D2D2D",
                plot_bgcolor="#2D2D2D",
                font=dict(color="white"),
                height=GRAPH_HEIGHT,
                margin=dict(l=20, r=20, t=40, b=30)
            )
            st.plotly_chart(fig_vol, use_container_width=True, config={'displayModeBar': False})
        else:
            st.warning("⚠️ Dados de Volume não encontrados.")

 
# ==============================================================================
# ABA 2
# ==============================================================================
with tab2:
    st.header("Análise Detalhada (Para Holders)")
    st.info("Em construção: Focaremos em métricas de longo prazo, tendências de acumulação e eventos macroeconômicos.")





# ==============================================================================
# ABA 3
# ==============================================================================
with tab3:
    st.header("Em breve")
    




# ==============================================================================
# ABA 4
# ==============================================================================
with tab4:
    st.header("Em breve")



    
# ==============================================================================
# ABA 5
# ==============================================================================
with tab5:
    st.header("Em breve")






# ==============================================================================
# ABA 6
# ==============================================================================
with tab6:
    st.header("Em breve")
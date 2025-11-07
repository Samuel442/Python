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



# --- Título ---
st.markdown("<h1 style='text-align: center; color: white;'>₿ SaaS Crypto</h1>",
                                                        unsafe_allow_html=True)



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
    "Desde o Início": 0,
    "Personalizado": -1
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
end_date = datetime.now().replace(tzinfo=timezone.utc) # <-- MODIFICADO
start_date = None
if selected_period == "Personalizado":
    # Permite ao usuário escolher as datas
    st.sidebar.markdown("---")
    # Garantir que temos duas datas no range
    if len(date_range) == 2:
        # datetime.combine transforma date_input (date) em datetime. Adicione .replace(tzinfo=timezone.utc)
        start_date = datetime.combine(date_range[0], datetime.min.time()).replace(tzinfo=timezone.utc) # <-- MODIFICADO
        end_date = datetime.combine(date_range[1], datetime.max.time()).replace(tzinfo=timezone.utc) # <-- MODIFICADO
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
# ABA 1
# ==============================================================================
with tab1:
    # Cria DUAS colunas para os preços (USD e BRL) e uma coluna para o espaço do BI
    # Proporção: 1.5 para USD, 1.5 para BRL e 3 para o BI
    col_price_usd, col_price_brl, col_empty = st.columns([1.5, 1.5, 3]) 
    # --- 1. CARREGAR OS DADOS ---
    # Assume que a tabela de preços se chama 'prices_btc'
    df_prices = load_data_api("prices_btc")
    # --- NOVO: FILTRAR OS DADOS PELA SELEÇÃO LATERAL ---
    if not df_prices.empty and start_date: # Só filtra se houver data de início
        df_prices = df_prices[
            (df_prices['timestamp'] >= start_date) & 
            (df_prices['timestamp'] <= end_date)
        ].reset_index(drop=True)
    # --------------------------------------------------
    # --- PREPARAÇÃO E CÁLCULO DAS MÉTRICAS ---
    if not df_prices.empty and len(df_prices) >= 2:
        # Preços mais recentes
        latest_usd = df_prices['price_usd'].iloc[-1]
        latest_brl = df_prices['price_brl'].iloc[-1]
        # Preços anteriores (para o cálculo da variação)
        previous_usd = df_prices['price_usd'].iloc[-2]
        previous_brl = df_prices['price_brl'].iloc[-2]
        # Cálculo da variação (DELTA)
        change_usd = (latest_usd - previous_usd) / previous_usd
        change_brl = (latest_brl - previous_brl) / previous_brl
        delta_usd_str = f"{change_usd * 100:.2f} %"
        delta_brl_str = f"{change_brl * 100:.2f} %"
        has_data = True
    else:
        has_data = False
        delta_usd_str = "N/A"
        delta_brl_str = "N/A"
    # --- 3. EXIBIR OS CARTÕES DE PREÇO ---
    # Cartão do Dólar (USD)
    with col_price_usd:
        if has_data:
            st.metric(
                label="PREÇO ATUAL (USD)",
                value=f"$ {latest_usd:,.2f}", # Formato de moeda
                delta=delta_usd_str,
                delta_color="normal"
            )
        else:
            st.warning("⚠️ Dados de preço não disponíveis ou insuficientes para o período selecionado. Verifique o ETL.") 
    # Cartão do Real (BRL)
    with col_price_brl:
        if has_data:
            st.metric(
                label="PREÇO ATUAL (BRL)",
                value=f"R$ {latest_brl:,.2f}".replace(",", "_TEMP_").replace(".", ",").replace("_TEMP_", "."),
                delta=delta_brl_str,
                delta_color="normal" 
            )
        # Se não houver dados, a primeira coluna já exibiu o aviso.
    
    
    # --- INÍCIO DO CÓDIGO DO GAUGE CHART E OUTROS KPIS (Versão Final com Rótulo de Texto) ---
    st.markdown("---") # Linha separadora
    col_gauge, col_kpi_volume, col_kpi_capitalizacao = st.columns([1.5, 1.5, 3])
    # --- 1. CARREGAR DADOS DE SENTIMENTO ---
    df_sentiment = load_data_api("sentiment")
    with col_gauge:
        # CORREÇÃO: Usando 'fear_greed_index' conforme a sua tabela do Supabase
        if not df_sentiment.empty and 'fear_greed_index' in df_sentiment.columns and 'sentiment_text' in df_sentiment.columns:
            # Pega a pontuação mais recente
            latest_score = df_sentiment['fear_greed_index'].iloc[-1]
            # Pega o texto de sentimento mais recente
            latest_sentiment_text = df_sentiment['sentiment_text'].iloc[-1]
            # --- CONFIGURAÇÃO DO GAUGE PLOTLY (DESIGN FINAL) ---
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = latest_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                # NOVIDADE: Título com o rótulo de texto e formatação HTML
                title = {
                    'text': f"Índice Medo & Ganância<br><span style='font-size:0.9em; color:#FFFFFF;'>{latest_sentiment_text.upper()}</span>", 
                    'font': {'size': 18, 'color': '#00BFFF'}
                }, 
                gauge = {
                    'shape': "angular", 
                    'axis': {
                        'range': [None, 100], 
                        'tickwidth': 1, 
                        'tickcolor': "#777777", 
                        'visible': True, 
                        'tickmode': 'linear',
                        'dtick': 50, # Mostra 0, 50, 100
                        'tickfont': {'color': "#FFFFFF"} 
                    },
                    
                    'bar': {'color': "rgba(0,0,0,0)", 'thickness': 0.1}, 
                    'borderwidth': 0,
                    # Cores de Medo a Ganância Extrema (O Anel)
                    'steps': [
                        {'range': [0, 25], 'color': "#8B0000", 'name': 'Medo Extremo'}, 
                        {'range': [25, 50], 'color': "#CC0000", 'name': 'Medo'},       
                        {'range': [50, 75], 'color': "#009900", 'name': 'Ganância'},  
                        {'range': [75, 100], 'color': "#006400", 'name': 'Ganância Extrema'} 
                    ], 
                    # Ponteiro (Threshold)
                    'threshold': {
                        'line': {'color': "#FFFFFF", 'width': 4}, 
                        'thickness': 0.75,
                        'value': latest_score
                    }
                }
            ))
            # Ajustes de Layout
            fig_gauge.update_layout(
                paper_bgcolor="#2D2D2D", 
                font={'color': "white", 'family': "Arial"},
                height=250, 
                margin=dict(l=50, r=50, t=30, b=20)
            )
            st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})
        else:
            with col_gauge:
                st.warning("⚠️ Dados de Sentimento (Fear & Greed Index) não encontrados.")
    # --- FIM DO CÓDIGO DO GAUGE CHART ---

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
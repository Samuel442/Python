import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

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
st.markdown("<h1 style='text-align: center; color: white;'>₿ SaaS Crypto</h1>", unsafe_allow_html=True)


# --- FUNÇÕES DE CARREGAMENTO DE DADOS ---
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
        # Converte a coluna 'timestamp' para datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados da tabela '{table_name}': {e}")
        return pd.DataFrame()
# --- FIM DAS FUNÇÕES DE CARREGAMENTO ---



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
    # --- 2. PREPARAÇÃO E CÁLCULO DAS MÉTRICAS ---
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
        # Como o cálculo do delta é o mesmo para USD e BRL (ambos refletem o movimento do BTC),
        # podemos usar uma variável para ambos. No entanto, usaremos as específicas para maior clareza.
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
            st.warning("⚠️ Dados de preço não disponíveis. Verifique o ETL.") 
    # Cartão do Real (BRL)
    with col_price_brl:
        if has_data:
            # Observação: A CoinGecko normalmente não usa o "milhar" no preço do BRL
            # mas o Python usa por padrão. O BRL costuma ter vírgula para decimal.
            st.metric(
                label="PREÇO ATUAL (BRL)",
                # O valor é formatado usando o locale ('.', ',' e 2 casas decimais)
                value=f"R$ {latest_brl:,.2f}".replace(",", "_TEMP_").replace(".", ",").replace("_TEMP_", "."),
                delta=delta_brl_str,
                delta_color="normal" 
            )
        # Se não houver dados, a primeira coluna já exibiu o aviso.            
        
        
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
    st.header("Notícias & Eventos")
    




# ==============================================================================
# ABA 4
# ==============================================================================
with tab4:
    st.header(" Notícias & Eventos")



    
# ==============================================================================
# ABA 5
# ==============================================================================
with tab5:
    st.header("Notícias & Eventos")






# ==============================================================================
# ABA 6
# ==============================================================================
with tab6:
    st.header("Notícias & Eventos")
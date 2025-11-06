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


# --- 5. INÍCIO DA APLICAÇÃO STREAMLIT ---
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
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Visão Geral", "Preço e Tendências", "Adoção e Uso", "Sentimento e Notícias","Comparativos", "Relatório Semanal"])


# ==============================================================================
# ABA 1
# ==============================================================================
with tab1:
    # Criamos uma coluna para o preço e duas colunas vazias para ocupar o espaço do BI
    col_price, col_empty1, col_empty2 = st.columns([1.5, 1, 3]) 

    # --- 1. CARREGAR OS DADOS ---
    # Assume que a tabela de preços se chama 'prices_btc'
    df_prices = load_data_api("prices_btc")

    # --- 2. EXIBIR O CARTÃO DE PREÇO ---
    with col_price:
        if not df_prices.empty:
            # Encontra o preço mais recente (assumindo que o DF está ordenado pelo timestamp)
            latest_price = df_prices['price_usd'].iloc[-1]
            
            # Cálculo de variação (Exemplo: 24h ou último preço vs anterior)
            # Para simplificar, vamos usar uma variação simulada de 1% por enquanto:
            
            # Variação real do último registro vs o penúltimo:
            if len(df_prices) >= 2:
                previous_price = df_prices['price_usd'].iloc[-2]
                change_24h = (latest_price - previous_price) / previous_price
                delta_str = f"{change_24h * 100:.2f} %"
            else:
                # Caso não haja dados suficientes para o cálculo
                delta_str = "N/A" 
                
            # Exibir o st.metric (o seu CSS o transforma no cartão arredondado)
            st.metric(
                label="PREÇO ATUAL DO BITCOIN",
                value=f"$ {latest_price:,.2f}", # Formato de moeda
                delta=delta_str,
                delta_color="normal" # 'normal' é verde/vermelho padrão
            )
        else:
            st.warning("⚠️ Dados de preço não disponíveis. Verifique o ETL.")   
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
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
DATE_OPTIONS = {
    "Últimas 24 Horas": 1,
    "Últimos 7 Dias": 7,
    "Últimos 30 Dias": 30,
    "Últimos 90 Dias": 90,
    "Desde o Início": 0
}
# --- BARRA LATERAL ---
st.sidebar.markdown("## 📊 Filtros de Análise")
# Seletor de Período
selected_period = st.sidebar.selectbox(
    "Selecione o Período:",
    options=list(DATE_OPTIONS.keys()),
    index=0,
    key="selected_period"  # <-- garante que o valor seja global
)
# Lógica de Data
end_date = datetime.now().replace(tzinfo=timezone.utc)
start_date = None
if selected_period == "Personalizado":
    # (Opcional) se quiser permitir intervalo manual
    date_range = st.sidebar.date_input("Selecione o intervalo:", [])
    if len(date_range) == 2:
        start_date = datetime.combine(date_range[0], datetime.min.time()).replace(tzinfo=timezone.utc)
        end_date = datetime.combine(date_range[1], datetime.max.time()).replace(tzinfo=timezone.utc)
    else:
        st.sidebar.warning("Selecione o intervalo completo.")
else:
    days = DATE_OPTIONS[selected_period]
    if days > 0:
        start_date = end_date - timedelta(days=days)
    else:
        start_date = None




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
            # Mantém a formatação de BRL
            st.metric(
                "PREÇO ATUAL (BRL)",
                f"R$ {latest_brl:,.2f}".replace(",", "_TEMP_").replace(".", ",").replace("_TEMP_", "."),
                delta_brl_str
            )
    # --- Card de Capitalização de Mercado (AGORA PADRONIZADO COM st.metric) ---
    df_market = load_data_api("market_global")
    if not df_market.empty and start_date:
        df_market = df_market[
            (df_market['timestamp'] >= start_date) & 
            (df_market['timestamp'] <= end_date)
        ].reset_index(drop=True)
    with col_market_cap:
        if not df_market.empty and 'total_market_cap' in df_market.columns and len(df_market) >= 2:
            latest_market_cap = df_market['total_market_cap'].iloc[-1]
            previous_market_cap = df_market['total_market_cap'].iloc[-2]
            # Cálculo e formatação do Delta
            change_market_cap = (latest_market_cap - previous_market_cap) / previous_market_cap
            delta_str = f"{change_market_cap * 100:,.2f}%"
            # Formatação do Valor em Bilhões (B)
            market_cap_billions = latest_market_cap / 1_000_000_000
            value_str = f"${market_cap_billions:,.2f} B"
            # USANDO st.metric para padronização
            st.metric(
                "CAPITALIZAÇÃO DE MERCADO",
                value_str,
                delta_str
            )
        else:
            st.warning("⚠️ Dados de Capitalização de Mercado indisponíveis.")   
    st.markdown("---")
    
    # --- SEÇÃO B: KPI’s SECUNDÁRIOS (Gauge + Volume) ---
    GRAPH_HEIGHT = 250
    col_gauge, col_volume = st.columns([1.2, 1.8])
    # Gauge (Fear & Greed)
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


    # Volume de Negociação (Gráfico de Barras) - COM CORREÇÃO E ESTILIZAÇÃO NEON
    with col_volume:
        if not df_market.empty and 'total_volume' in df_market.columns:
            # --- AGREGAÇÃO DIÁRIA DO VOLUME ---
            df_volume = df_market[['timestamp', 'total_volume']].copy()
            df_volume = df_volume.set_index('timestamp')
            df_volume_diario = df_volume.resample('D')['total_volume'].sum().reset_index()
            df_volume_diario = df_volume_diario[df_volume_diario['total_volume'] > 0]
            # --- PLOTAGEM COM DADOS AGREGADOS E ESTILIZAÇÃO NEON ---
            NEON_PURPLE = "#50C878"
            fig_vol = go.Figure(data=[
                go.Bar(
                    x=df_volume_diario['timestamp'], 
                    y=df_volume_diario['total_volume'], 
                    # Cor roxo neon nas barras
                    marker_color=NEON_PURPLE, 
                    marker_line_color=NEON_PURPLE,
                    marker_line_width=1.5,
                    # Adiciona e posiciona o rótulo
                    text=df_volume_diario['total_volume'],
                    textposition='outside'
                )
            ])
            # Configuração do formato e cor do rótulo (branco)
            fig_vol.update_traces(
                texttemplate='$%{text:.2s}', 
                textfont=dict(color="white", size=11), 
                textangle=0,
                cliponaxis=False 
            )
            # Ajustes nos eixos
            fig_vol.update_yaxes(
                title_text="Volume (USD)",
                tickformat=".2s", 
                hoverformat="$,.2f",
                title_standoff=0
            )
            # Ajusta o layout para centralizar o título e alinhar a altura com o Gauge
            fig_vol.update_layout(
                title=f"Volume de Negociação Diário ({selected_period})",
                title_x=0.2, # Centraliza o título
                title_font_color=NEON_PURPLE, 
                paper_bgcolor="#2D2D2D",
                plot_bgcolor="#2D2D2D",
                font=dict(color="white"),
                height=GRAPH_HEIGHT, # Alinha a altura com o Gauge
                margin=dict(l=20, r=20, t=60, b=30), # Aumenta a margem superior para acomodar o rótulo
                xaxis={'title': {'standoff': 15}, 'color': NEON_PURPLE}, 
                yaxis={'color': NEON_PURPLE} 
            )
            st.plotly_chart(fig_vol, use_container_width=True, config={'displayModeBar': False})
        else:
            st.warning("⚠️ Dados de Volume não encontrados.")
 
 
# ==============================================================================
# ABA 2 - PREÇO E TENDÊNCIAS
# ==============================================================================
with tab2:
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Preço e Tendências</h2>", unsafe_allow_html=True)
    # --- Carrega dados ---
    df_prices = load_data_api("prices_btc")
    # --- Filtragem de acordo com o filtro lateral ---
    if not df_prices.empty and start_date:
        df_prices = df_prices[
            (df_prices['timestamp'] >= start_date) & 
            (df_prices['timestamp'] <= end_date)
        ].reset_index(drop=True)
    # --- Verifica se há dados ---
    if df_prices.empty:
        st.warning("⚠️ Nenhum dado de preço disponível para o período selecionado.")
    else:
        # SEÇÃO 1 - Correlação de Tendência (BTC/USD vs BTC/BRL)
        st.markdown("### 🔍 Correlação de Tendência entre BTC/USD e BTC/BRL")
        # Converter timestamps para data e calcular médias diárias
        df_prices['date'] = pd.to_datetime(df_prices['timestamp']).dt.date
        df_avg = df_prices.groupby('date', as_index=False)[['price_usd', 'price_brl']].mean()
        # Calcular variação percentual diária
        df_avg['var_usd'] = df_avg['price_usd'].pct_change() * 100
        df_avg['var_brl'] = df_avg['price_brl'].pct_change() * 100
        # Calcular correlação
        corr_value = df_avg[['var_usd', 'var_brl']].corr().iloc[0, 1]
        # Interpretação da correlação
        if corr_value > 0.8:
            corr_text = "🔒 Altamente correlacionado (movem-se quase juntos)"
            corr_color = "#00FF7F"  # verde forte
        elif corr_value > 0.5:
            corr_text = "📈 Moderadamente correlacionado"
            corr_color = "#ADFF2F"  # verde limão
        elif corr_value > 0:
            corr_text = "⚖️ Correlação fraca"
            corr_color = "#FFD700"  # amarelo
        else:
            corr_text = "🔻 Correlação negativa (movem-se em sentidos opostos)"
            corr_color = "#FF6347"  # vermelho claro
        # Gráfico de linhas — variação percentual no período
        fig_lines = go.Figure()
        fig_lines.add_trace(go.Scatter(
            x=df_avg['date'], y=df_avg['var_usd'], mode='lines',
            name='BTC/USD', line=dict(color="#00BFFF", width=2)
        ))
        fig_lines.add_trace(go.Scatter(
            x=df_avg['date'], y=df_avg['var_brl'], mode='lines',
            name='BTC/BRL', line=dict(color="#39FF14", width=2)
        ))
        fig_lines.update_layout(
            title=dict(text="Tendência Diária - Variação Percentual", font=dict(color="white"), x=0.5),
            paper_bgcolor="#2D2D2D", plot_bgcolor="#2D2D2D",
            font=dict(color="white"), height=300,
            margin=dict(l=40, r=40, t=50, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_lines, use_container_width=True, config={'displayModeBar': False})
        # --- Heatmap pequeno, didático e simétrico ---
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(
                "<h5 style='text-align:center; color:white;'>🧭 Correlação BTC/USD × BTC/BRL</h5>",
                unsafe_allow_html=True
            )
            fig_heatmap = go.Figure(data=go.Heatmap(
                z=[[corr_value]],
                x=["BTC/USD"],
                y=["BTC/BRL"],
                colorscale=[[0, "#FF6347"], [0.5, "#FFD700"], [1, "#00FF7F"]],
                zmin=-1, zmax=1,
                showscale=True,
                colorbar=dict(
                    tickvals=[-1, 0, 1],
                    ticktext=["-1 (oposto)", "0 (sem relação)", "+1 (juntos)"],
                    title="Correlação"
                ),
                text=[[f"{corr_value:.2f}"]],
                texttemplate="%{text}",
                textfont={"color": "black", "size": 16}
            ))
            fig_heatmap.update_layout(
                paper_bgcolor="#2D2D2D",
                plot_bgcolor="#2D2D2D",
                font=dict(color="white"),
                xaxis=dict(showgrid=False, showticklabels=True),
                yaxis=dict(showgrid=False, showticklabels=True),
                height=260,
                width=500,
                margin=dict(l=60, r=60, t=40, b=20)
            )
            st.plotly_chart(fig_heatmap, use_container_width=False)
            st.markdown(
                f"<p style='text-align:center; color:{corr_color}; font-size:16px; font-weight:500;'>{corr_text}</p>",
                unsafe_allow_html=True
            )
        st.markdown("---")




        # SEÇÃO 2 - Gráfico principal (linha)
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=df_prices['timestamp'],
            y=df_prices['price_usd'],
            mode='lines+markers',
            name='BTC/USD',
            line=dict(color="#00BFFF", width=2),
            marker=dict(size=4)
        ))
        fig_line.add_trace(go.Scatter(
            x=df_prices['timestamp'],
            y=df_prices['price_brl'],
            mode='lines+markers',
            name='BTC/BRL',
            line=dict(color="#39FF14", width=2),
            marker=dict(size=4)
        ))
        fig_line.update_layout(
            title="Evolução do Preço (USD vs BRL)",
            paper_bgcolor="#2D2D2D",
            plot_bgcolor="#2D2D2D",
            font=dict(color="white"),
            height=400,
            margin=dict(l=40, r=40, t=60, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})


        # SEÇÃO 3 - Variação de preço no período selecionado
        # Obtém o período selecionado no filtro global
        selected_period = st.session_state.get("selected_period", "Últimas 24 Horas")
        # Define o título e o número de dias conforme o filtro
        if selected_period == "Últimas 24 Horas":
            label = "💰 Variação Diária (24h)"
            days = 1
        elif selected_period == "Últimos 7 Dias":
            label = "💰 Variação Semanal (7 dias)"
            days = 7
        elif selected_period == "Últimos 30 Dias":
            label = "💰 Variação Mensal (30 dias)"
            days = 30
        elif selected_period == "Últimos 90 Dias":
            label = "💰 Variação Trimestral (90 dias)"
            days = 90
        elif selected_period == "Desde o Início":
            label = "💰 Variação Acumulada (Desde o Início)"
            days = None
        else:
            label = "💰 Variação de Preço"
            days = None
        st.markdown(f"### {label}")
        # Determina o intervalo de dados com base no filtro
        if not df_prices.empty:
            end_date = df_prices['timestamp'].max()
            if days is not None:
                start_date = end_date - timedelta(days=days)
                df_period = df_prices[(df_prices['timestamp'] >= start_date) & (df_prices['timestamp'] <= end_date)]
            else:
                df_period = df_prices.copy()  # Pega tudo se for "Desde o Início"
            if not df_period.empty:
                # Calcula o maior e menor preço no período
                high_price = df_period['price_usd'].max()
                low_price = df_period['price_usd'].min()
                # Calcula a diferença percentual para exibir como delta
                first_price = df_period['price_usd'].iloc[0]
                delta_high = ((high_price - first_price) / first_price) * 100
                delta_low = ((low_price - first_price) / first_price) * 100
                # Exibe os cards de métrica com setas
                col_high, col_low = st.columns(2)
                with col_high:
                    st.metric(
                        label="Maior preço",
                        value=f"$ {high_price:,.2f}",
                        delta=f"{delta_high:+.2f}%",
                        delta_color="normal"  # seta verde para positivo, vermelha para negativo
                    )
                with col_low:
                    st.metric(
                        label="Menor preço",
                        value=f"$ {low_price:,.2f}",
                        delta=f"{delta_low:+.2f}%",
                        delta_color="inverse"  # inverte: seta vermelha pra baixo
                    )
            else:
                st.warning("⚠️ Sem dados disponíveis para o período selecionado.")
        else:
            st.warning("⚠️ Dados de preços não encontrados.")
        st.markdown("---")


        # SEÇÃO 4 - Comparação BTC/USD vs BTC/BRL (barras duplas)
        st.markdown("### 💹 Comparação BTC/USD vs BTC/BRL")
        # Converter timestamps para data e calcular médias diárias
        df_prices['date'] = pd.to_datetime(df_prices['timestamp']).dt.date
        df_avg = df_prices.groupby('date', as_index=False)[['price_usd', 'price_brl']].mean()
        # Criar gráfico de barras duplas com rótulos
        fig_compare = go.Figure(data=[
            go.Bar(
                name='BTC/USD',
                x=df_avg['date'],
                y=df_avg['price_usd'],
                text=[f"$ {v:,.2f}" for v in df_avg['price_usd']],  # adiciona valores formatados
                textposition='outside',  # pode ser 'outside', 'auto', ou 'inside'
                marker_color="#00BFFF"
            ),
            go.Bar(
                name='BTC/BRL',
                x=df_avg['date'],
                y=df_avg['price_brl'],
                text=[f"R$ {v:,.2f}" for v in df_avg['price_brl']],
                textposition='outside',
                marker_color="#39FF14"
            )
        ])
        # Configuração do layout e rótulos
        fig_compare.update_layout(
            title=dict(
                text="Comparação do Preço Médio Diário do Bitcoin em USD e BRL",
                font=dict(size=16, color="white"),
                x=0.5,
            ),
            xaxis=dict(
                title=dict(text="Data", font=dict(color="white")),
                tickfont=dict(color="white")
            ),
            yaxis=dict(
                title=dict(text="Preço Médio", font=dict(color="white")),
                tickfont=dict(color="white"),
                showgrid=True,
                gridcolor="#444444"
            ),
            barmode='group',
            paper_bgcolor="#2D2D2D",
            plot_bgcolor="#2D2D2D",
            font=dict(color="white"),
            height=450,
            margin=dict(l=40, r=40, t=60, b=40),
            legend=dict(
                title="Cotação",
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            )
        )
        # Exibir gráfico
        st.plotly_chart(fig_compare, use_container_width=True, config={'displayModeBar': False})








# ==============================================================================
# ABA 3
# ==============================================================================
with tab3:
    st.header("Em breve")





# =========================================================
# 🧠 ABA 4 - Sentimento e Notícias
# =========================================================
with tab4:
    st.markdown("## 🧠 Sentimento e Notícias do Mercado")
    # 🎯 SEÇÃO 1 - Sentimento (Fear & Greed Index)
    st.markdown("### 📊 Índice de Medo e Ganância (Fear & Greed)")
    try:
        # Assumindo que o df_sentiment já foi carregado e tem os timestamps corretos
        df_sentiment = load_data_api("sentiment")
        if not df_sentiment.empty:
            # Filtro usando as datas globais (start_date e end_date) que são UTC
            df_sentiment = df_sentiment[
                (df_sentiment["timestamp"] >= start_date) &
                (df_sentiment["timestamp"] <= end_date)
            ].reset_index(drop=True)
            # A conversão de pd.to_datetime é feita na load_data_api, mantido.
            if not df_sentiment.empty:
                # Última linha (sentimento mais recente)
                last_row = df_sentiment.iloc[-1]
                last_value = last_row["fear_greed_index"]
                last_text = last_row["sentiment_text"]
                # Formata a data: Converte o timestamp UTC para o horário local do Brasil (BRT)
                last_time = last_row["timestamp"].tz_convert('America/Sao_Paulo').strftime("%d/%m/%Y %H:%M:%S (BRT)") # Exemplo de conversão
                # Tradução automática e ícones do sentimento
                if last_value <= 25:
                    emoji = "😱"
                    level_pt = "Medo Extremo"
                    color = "#FF4C4C"
                elif last_value <= 50:
                    emoji = "😟"
                    level_pt = "Medo"
                    color = "#FFA500"
                elif last_value <= 75:
                    emoji = "😌"
                    level_pt = "Ganância"
                    color = "#39FF14"
                else:
                    emoji = "🚀"
                    level_pt = "Ganância Extrema"
                    color = "#00FF7F"

                # --- Card interpretativo (Mantido como você customizou) ---
                st.markdown(
                    f"""
                    <div style='background-color:{color}22; border: 1px solid {color};
                        border-radius:12px; padding:15px; text-align:center; margin-bottom:20px;'>
                        <h3 style='color:{color}; margin:0;'> {emoji} {level_pt} </h3>
                        <p style='color:white; margin:5px 0 0;'>
                            O índice atual é <b>{last_value:.0f}</b> ({last_text}).
                            <br>Atualizado em <b>{last_time}</b>.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # --- Gráfico de evolução ---
                fig_sentiment = px.line(
                    df_sentiment,
                    x="timestamp",
                    y="fear_greed_index",
                    markers=True,
                    title="Evolução do Índice de Sentimento"
                )

                # 1. Ajuste dos nomes dos EIXOS (títulos)
                fig_sentiment.update_layout(
                    # CORREÇÃO APLICADA AQUI: MUDAR O TÍTULO DO EIXO X PARA BRT
                    xaxis_title="Data e Hora (BRT)", 
                    # --- FIM DA CORREÇÃO ---
                    yaxis_title="Índice (0 = Medo, 100 = Ganância)", 
                    title_x=0.5,
                    title_font=dict(color="#00BFFF"), # Cor neon no título
                    plot_bgcolor="#2D2D2D",
                    paper_bgcolor="#2D2D2D",
                    font=dict(color="white"),
                    height=350,
                    margin=dict(l=20, r=20, t=60, b=40)
                )
                
                # 2. Ajuste na exibição do Eixo X (data/hora)
                fig_sentiment.update_xaxes(
                    tickformat="%d/%m/%Y %H:%M", # Formato de exibição mais claro
                    showgrid=True,
                    gridcolor='#444444'
                )
                
                # Adiciona as faixas de sentimento como fundo (cores mantidas)
                fig_sentiment.add_hrect(y0=0, y1=25, fillcolor="#8B0000", opacity=0.1, layer="below", line_width=0, annotation_text="Medo Extremo")
                fig_sentiment.add_hrect(y0=25, y1=50, fillcolor="#CC0000", opacity=0.1, layer="below", line_width=0, annotation_text="Medo")
                fig_sentiment.add_hrect(y0=50, y1=75, fillcolor="#009900", opacity=0.1, layer="below", line_width=0, annotation_text="Ganância")
                fig_sentiment.add_hrect(y0=75, y1=100, fillcolor="#006400", opacity=0.1, layer="below", line_width=0, annotation_text="Ganância Extrema")
                st.plotly_chart(fig_sentiment, use_container_width=True)
            else:
                st.warning("⚠️ Nenhum dado de sentimento disponível para o período selecionado.")
        else:
            st.warning("⚠️ Dados de sentimento não encontrados.")
    except Exception as e:
        st.error(f"Erro ao carregar sentimento: {e}")
    st.markdown("---")

    # 📰 SEÇÃO 2 - Últimas Notícias de Mercado
    st.markdown("### 📰 Últimas Notícias de Mercado")
    try:
        df_news = load_data_api("news_events")
        if not df_news.empty:
            df_news["date"] = pd.to_datetime(df_news["date"])
            df_news = df_news.sort_values("date", ascending=False).head(5)
            for _, row in df_news.iterrows():
                headline = row["headline"]
                source = row["source"]
                link = row["link"]
                date = row["date"].strftime("%d/%m/%Y")
                st.markdown(
                    f"""
                    <div style='background-color:#2F2F2F; padding:10px 15px; border-radius:8px; margin-bottom:8px;'>
                        <b style='color:#00BFFF;'>{source.upper()}</b>: 
                        <a href='{link}' target='_blank' style='color:#FFD700; text-decoration:none;'>{headline}</a><br>
                        <span style='color:#AAAAAA;'>📅 {date} | 🗞️ {source}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.warning("⚠️ Nenhuma notícia disponível no momento.")
    except Exception as e:
        st.error(f"Erro ao carregar notícias: {e}")



    
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
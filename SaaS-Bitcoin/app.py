import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px
import plotly.graph_objects as go
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
    <h1 class="neon-title">₿ SaaS Bitcoin</h1>
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
    "Últimos 90 Dias": 90
}
# --- BARRA LATERAL ---
st.sidebar.markdown("## 📊 Filtros de Análise")
# Seletor de Período
selected_period = st.sidebar.selectbox(
    "Selecione o Período:",
    options=list(DATE_OPTIONS.keys()),
    index=3,
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
    # Volume de Negociação (Gráfico de Barras) 
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
# ABA 3 - ADOÇÃO E USO (COMPATÍVEL COM SUAS COLUNAS REAIS)
# ==============================================================================
with tab3:
    st.markdown("### 🔗 3. Adoção e Uso do Bitcoin")
    st.markdown("---")

    # Carregando tabelas
    df_btc = load_data_api("prices_btc")
    df_global = load_data_api("market_global")
    df_sentiment = load_data_api("sentiment")
    if df_btc.empty or df_global.empty:
        st.warning("Dados insuficientes para montar esta aba.")
        st.stop()

    # Filtro por data
    df_btc_filtered = df_btc[(df_btc["timestamp"] >= start_date) &
                             (df_btc["timestamp"] <= end_date)].copy()
    df_global_filtered = df_global[(df_global["timestamp"] >= start_date) &
                                   (df_global["timestamp"] <= end_date)].copy()
    df_sentiment_filtered = df_sentiment[(df_sentiment["timestamp"] >= start_date) &
                                         (df_sentiment["timestamp"] <= end_date)].copy()

    # 1) VOLUME TOTAL DE NEGOCIAÇÃO
    st.subheader("📊 Volume Total de Negociação")
    if "total_volume" in df_global_filtered.columns:
        fig = px.line(
            df_global_filtered,
            x="timestamp",
            y="total_volume",
            title="Volume total de negociação",
            labels={"timestamp": "Data", "total_volume": "Volume"}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("A coluna 'total_volume' não existe em market_global.")
    st.markdown("---")

    # ==============================================================================
    # 2) MARKET CAP DO BITCOIN (total_market_cap)
    # ==============================================================================
    st.subheader("💰 Market Cap Total")
    if "total_market_cap" in df_global_filtered.columns:
        fig = px.line(
            df_global_filtered,
            x="timestamp",
            y="total_market_cap",
            title="Capitalização de Mercado (Market Cap)",
            labels={"timestamp": "Data", "total_market_cap": "Market Cap"}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("A coluna 'total_market_cap' não existe em market_global.")
    st.markdown("---")

    # 3) DOMINÂNCIA DO BITCOIN
    st.subheader("🟠 Dominância do Bitcoin (%)")
    if "btc_dominance" in df_global_filtered.columns:
        fig = px.area(
            df_global_filtered,
            x="timestamp",
            y="btc_dominance",
            title="Dominância do BTC no Mercado (%)",
            labels={"timestamp": "Data", "btc_dominance": "Dominância (%)"}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("A coluna 'btc_dominance' não existe em market_global.")
    st.markdown("---")
    
    # 4) FEAR & GREED INDEX
    st.subheader("😨 Fear & Greed Index")
    if "fear_greed_index" in df_sentiment_filtered.columns:
        fig = px.line(
            df_sentiment_filtered,
            x="timestamp",
            y="fear_greed_index",
            title="Índice de Sentimento (Fear & Greed)",
            labels={"timestamp": "Data", "fear_greed_index": "Índice"}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("A coluna 'fear_greed_index' não existe na tabela sentiment.")
    st.markdown("---")




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

    # SEÇÃO 2 - Últimas Notícias de Mercado
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
# ABA 5 - COMPARATIVOS (Versão Final e Corrigida)
# ==============================================================================
with tab5:
    st.markdown("## 🧭 Comparativos e Contexto de Mercado")
    st.markdown("O objetivo desta seção é contextualizar o Bitcoin em relação ao mercado cripto mais amplo e a ativos tradicionais.")
    # CORREÇÃO DE ESCOPO: Carrega dados diários do BTC para uso em toda a aba
    try:
        # Tenta carregar os dados do BTC
        df_btc_daily = load_data_api("prices_btc")
        # Garante que as colunas essenciais estejam no formato correto
        df_btc_daily['timestamp'] = pd.to_datetime(df_btc_daily['timestamp'], errors='coerce').dt.normalize()
        df_btc_daily['price_usd'] = pd.to_numeric(df_btc_daily['price_usd'], errors='coerce')
        df_btc_daily.dropna(subset=['timestamp', 'price_usd'], inplace=True)
    except Exception as e:
        # Fallback para evitar NameError
        df_btc_daily = pd.DataFrame({'timestamp': [], 'price_usd': []})
        st.error(f"FATAL: Não foi possível carregar 'df_btc_daily' para a Aba 5: {e}")
    # Inicializa um DataFrame vazio para a Seção 2, caso o carregamento falhe
    crypto_df = pd.DataFrame({'date': [], 'symbol': [], 'close': []})

    # 1. Dominância do Bitcoin no Mercado Cripto
    st.markdown("### 👑 1. Dominância do Bitcoin no Mercado Cripto")
    try:
        # Carrega dados de mercado global
        df_market = load_data_api("market_global")
        # Assegura que start_date e end_date estejam sem timezone para o filtro
        start_date_ts = pd.to_datetime(start_date).tz_localize(None)
        end_date_ts = pd.to_datetime(end_date).tz_localize(None)
        if not df_market.empty:
            df_market['timestamp'] = pd.to_datetime(df_market['timestamp'], errors='coerce').dt.tz_localize(None)
            df_dominance = df_market[
                (df_market["timestamp"] >= start_date_ts) &
                (df_market["timestamp"] <= end_date_ts)
            ].copy()
            if 'btc_dominance' in df_dominance.columns and not df_dominance.empty:
                latest_dominance = df_dominance['btc_dominance'].iloc[-1]
                if len(df_dominance) >= 2:
                    previous_dominance = df_dominance['btc_dominance'].iloc[-2]
                    delta_dominance = latest_dominance - previous_dominance
                    delta_str = f"{delta_dominance:+.2f} pts"
                else:
                    delta_str = "N/A"
                st.metric(
                    label="DOMINÂNCIA ATUAL DO BTC", 
                    value=f"{latest_dominance:.2f} %",
                    delta=delta_str,
                    delta_color="normal" 
                )
                fig_dominance = px.line(
                    df_dominance, x="timestamp", y="btc_dominance",
                    title="Evolução da Dominância do Bitcoin (BTC Dominance)",
                    labels={"timestamp": "Data e Hora", "btc_dominance": "Dominância (%)"}
                )
                fig_dominance.update_layout(title_x=0.5, title_font=dict(color="#00BFFF"), plot_bgcolor="#2D2D2D", paper_bgcolor="#2D2D2D", font=dict(color="white"), height=380, margin=dict(l=20, r=20, t=60, b=40))
                fig_dominance.update_traces(line=dict(color="#FFD700", width=2))
                fig_dominance.update_yaxes(range=[0, 100], tickformat=".2f", showgrid=True, gridcolor='#444444')
                st.plotly_chart(fig_dominance, use_container_width=True)
            else:
                st.warning("⚠️ Coluna 'btc_dominance' não encontrada ou dados insuficientes.")
        else:
            st.warning("⚠️ Dados de mercado global não encontrados.")
    except Exception as e:
        st.error(f"Erro ao carregar Dominância do BTC: {e}")
    st.markdown("---")
    # PREPARAÇÃO DE DADOS: Carregamento, Renomeação e Unificação (BTC + Altcoins)
    try:
        # 1. Carrega dados das Altcoins. Usa df_btc_daily carregado acima
        altcoins_df = load_data_api("altcoin_prices") 
        btc_df = df_btc_daily.copy() # Usa o DataFrame já carregado
        # --- Processamento BTC ---
        btc_df = btc_df.rename(columns={'price_usd': 'close', 'timestamp': 'date'})
        btc_df['symbol'] = 'BTC'
        btc_df = btc_df[['date', 'symbol', 'close']]
        # --- Processamento Altcoins ---
        if not altcoins_df.empty:
            altcoins_df = altcoins_df.rename(columns={'timestamp': 'date'})
            crypto_df_altcoins = pd.melt(
                altcoins_df,
                id_vars=['date'],
                value_vars=['eth_usd', 'bnb_usd', 'usdt_usd'],
                var_name='symbol',
                value_name='close'
            )
            crypto_df_altcoins['symbol'] = crypto_df_altcoins['symbol'].str.split('_').str[0].str.upper()
            crypto_df = pd.concat([btc_df, crypto_df_altcoins], ignore_index=True)
        else:
            crypto_df = btc_df.copy() 
    except Exception as e:
        st.warning(f"⚠️ Erro na preparação dos dados para o comparativo (Verifique as chaves 'altcoin_prices'): {e}")
        crypto_df = pd.DataFrame({'date': [], 'symbol': [], 'close': []}) 
    # 2. Bitcoin vs. Principais Altcoins (ETH, USDT, BNB)
    st.markdown("### 💰 2 Bitcoin vs. Principais Altcoins (ETH, USDT, BNB)")
    try:
        # Assegura que start_date e end_date estejam sem timezone para o filtro
        start_date_ts = pd.to_datetime(start_date).tz_localize(None)
        end_date_ts = pd.to_datetime(end_date).tz_localize(None)
        if not crypto_df.empty:
            crypto_df['date'] = pd.to_datetime(crypto_df['date'], errors='coerce').dt.tz_localize(None)
            # Filtragem inicial
            filtered_df = crypto_df[
                (crypto_df['date'] >= start_date_ts) & (crypto_df['date'] <= end_date_ts)
            ].copy() 
            
            # RE-AMOSTRAGEM (SUAVIZAÇÃO) DOS DADOS PARA FREQUÊNCIA DIÁRIA
            if not filtered_df.empty:
                filtered_df = filtered_df.set_index('date') 
                filtered_df_resampled = filtered_df.groupby('symbol')['close'].resample('D').last().reset_index()
                filtered_df = filtered_df_resampled.dropna(subset=['close'])
                filtered_df.sort_values(by=['symbol', 'date'], inplace=True) 
        else:
            filtered_df = pd.DataFrame()
        if filtered_df.empty:
            st.warning("⚠️ Não há dados suficientes no período selecionado para a comparação após a suavização dos dados.")
        else:
            # CÁLCULO: NORMALIZAÇÃO DOS DADOS PARA COMPARAR DESEMPENHO (Base 100)
            initial_prices = filtered_df.groupby('symbol')['close'].first().reset_index()
            initial_prices.rename(columns={'close': 'initial_close'}, inplace=True)
            df_normalized = filtered_df.merge(initial_prices, on='symbol')
            # Calcula o Retorno Normalizado (Base 100)
            df_normalized['normalized_price'] = (
                df_normalized['close'] / df_normalized['initial_close']
            ) * 100
            crypto_filtered = df_normalized
            # --- Gráfico de Desempenho Normalizado ---
            fig_altcoin = px.line(
                crypto_filtered,
                x='date',
                y='normalized_price',
                color='symbol',
                title='Comparativo de Desempenho: Bitcoin vs Altcoins (Base 100)',
                labels={'date': 'Data', 'normalized_price': 'Retorno Normalizado (Base 100)', 'symbol': 'Criptomoeda'}
            )
            fig_altcoin.update_layout(
                xaxis_title="Data",
                yaxis_title="Retorno Normalizado (Base 100)",
                legend_title="Criptomoeda"
            )
            st.plotly_chart(fig_altcoin, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao carregar comparação de Altcoins: {e}")

    # 🏛️ 3. Bitcoin vs. Ouro e S&P 500
    st.markdown("### 🏛️ 3. Bitcoin vs. Ouro e S&P 500")
    try:
        # 1. Função de busca e cache para Ativos Tradicionais
        @st.cache_data(ttl=600)
        def fetch_traditional_assets(_supabase_conn): 
            if not _supabase_conn:
                st.error("Conexão com Supabase indisponível.")
                return pd.DataFrame()
            response = _supabase_conn.table("traditional_assets_prices").select("timestamp, symbol, price_usd").execute()
            df = pd.DataFrame(response.data)
            # Limpeza e Preparação dos dados
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce').dt.normalize()
            df = df.rename(columns={'price_usd': 'price'})
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            # CORREÇÃO CRÍTICA: Limpa o símbolo para garantir que 'XAUUSD' seja reconhecido
            df['symbol'] = df['symbol'].astype(str).str.strip() 
            df.dropna(subset=['timestamp', 'price', 'symbol'], inplace=True) 
            return df[['timestamp', 'symbol', 'price']]
        # Busca os dados (Chama a função passando o objeto de conexão)
        df_traditional = fetch_traditional_assets(supabase)
        # 2. Prepara os dados do Bitcoin para a comparação
        if df_btc_daily.empty:
            st.warning("Dados do Bitcoin não carregados. Ignorando BTC.")
            df_btc_comparison = pd.DataFrame()
        else:
            df_btc_comparison = df_btc_daily[['timestamp', 'price_usd']].copy()
            df_btc_comparison = df_btc_comparison.rename(columns={'price_usd': 'price'})
            df_btc_comparison['symbol'] = 'BTC'
            df_btc_comparison['symbol'] = df_btc_comparison['symbol'].astype(str).str.strip()
        # 3. Combina todos os ativos (BTC, SPY, XAUUSD)
        df_all_assets = pd.concat([df_traditional, df_btc_comparison], ignore_index=True)
        df_all_assets.sort_values(by='timestamp', inplace=True)
        df_all_assets.dropna(subset=['price'], inplace=True)
        df_all_assets['timestamp'] = pd.to_datetime(df_all_assets['timestamp']).dt.tz_localize(None)
        # 3a. Ajusta a data de início do filtro para garantir que haja um ponto de partida para todos os ativos
        min_date_available = df_all_assets['timestamp'].min()
        start_date_ts = pd.to_datetime(start_date).tz_localize(None)
        end_date_ts = pd.to_datetime(end_date).tz_localize(None)
        # Garante que a data de início não seja anterior ao mínimo disponível
        if start_date_ts < min_date_available:
            start_date_ts = min_date_available
            
        # Filtra pelo período selecionado pelo usuário
        df_all_assets = df_all_assets[
            (df_all_assets['timestamp'] >= start_date_ts) & (df_all_assets['timestamp'] <= end_date_ts)
        ].copy()
        
        # CORREÇÃO DUPLICIDADE: Remove duplicatas pela chave (timestamp, symbol)
        df_all_assets.drop_duplicates(subset=['timestamp', 'symbol'], inplace=True)
        # 4. Normaliza os preços para comparar retornos (Base 100):
        # 4a. Agrupa e encontra o primeiro preço de cada ativo no período filtrado
        df_all_assets['initial_price'] = df_all_assets.groupby('symbol')['price'].transform('first')
        # 4b. Normaliza: (Preço Atual / Preço Inicial) * 100
        df_all_assets['Retorno Normalizado (Base 100)'] = (
            df_all_assets['price'] / df_all_assets['initial_price']
        ) * 100
        # 4c. Prepara para Plotly (DataFrame final)
        df_chart = df_all_assets.rename(columns={'symbol': 'Ativo', 'timestamp': 'Data'})
        df_chart = df_chart[['Data', 'Ativo', 'Retorno Normalizado (Base 100)']]
        
        # Garante que há dados para plotar
        if df_chart.empty or len(df_chart['Ativo'].unique()) < 3: 
            st.warning(f"⚠️ Não há dados suficientes. Apenas {len(df_chart['Ativo'].unique())} ativos encontrados no período selecionado. Verifique os filtros de data e limpe o cache.")
        else:
            # 5. Cria o Gráfico de Linhas
            fig = px.line(
                df_chart, 
                x="Data", 
                y="Retorno Normalizado (Base 100)", 
                color='Ativo',
                title="Performance Comparada: Bitcoin vs. Ouro e S&P 500",
                labels={"Data": "Data"},
                color_discrete_map={
                    'BTC': '#f7931a',
                    'SPY': '#008000',
                    'XAUUSD': '#FFD700'
                }
            )
            # CORREÇÃO DE VISUALIZAÇÃO: Força o Eixo Y para dar zoom (ajuste o range se necessário)
            # Este ajuste é crucial para que a linha do Ouro, menos volátil, não seja achatada.
            fig.update_yaxes(range=[90, 110])
            fig.update_layout(
                legend_title_text='Ativo',
                annotations=[
                    dict(
                        xref='paper', yref='paper',
                        x=0.0, y=-0.2,
                        text='*Base 100: Todos os ativos são comparados a partir do seu preço no dia inicial DENTRO do período filtrado.',
                        showarrow=False,
                        font=dict(size=10, color="grey")
                    )
                ]
            )
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao carregar comparação com Ativos Tradicionais: {e}")
    st.markdown("---")
    
    
# ==============================================================================
# ABA 6 - RESUMO GERAL
# ==============================================================================
with tab6:

    # BOTÃO PDF (somente visual, sem função ainda)
    st.markdown(
        """
        <style>
        /* Estilos do Botão Gerar PDF */
        .pdf-btn {
            position: absolute;
            top: 90px;
            right: 35px;
            background-color: #4CAF50;
            /* COR FORÇADA do texto → PRETO */
            color: #000 !important;
            padding: 8px 16px;
            border-radius: 8px;
            font-weight: bold;
            text-decoration: none !important;
            z-index: 999;
            transition: background-color 0.3s ease;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .pdf-btn:hover {
            background-color: #45a049;
            color: #000 !important; /* Mantém o texto PRETO no hover */
            box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
        }
        /* Remove cor padrão de links */
        .pdf-btn:visited,
        .pdf-btn:active,
        .pdf-btn:focus {
            color: #000 !important;
        }
        </style>
        <a class="pdf-btn" href="#">📄 Gerar PDF</a>
        """,
        unsafe_allow_html=True
    )
    st.markdown("## 📘 Resumo Geral do Mercado")
    st.markdown("Painel consolidado com os principais indicadores das abas anteriores.")
    st.markdown("---")

    # Carrega dados essenciais
    df_btc = load_data_api("prices_btc")
    df_global = load_data_api("market_global")
    df_sentiment = load_data_api("sentiment")
    df_news = load_data_api("news_events")
    if df_btc.empty or df_global.empty:
        st.warning("⚠️ Dados insuficientes para montar o resumo.")
        st.stop()

    # Ajustes de data
    df_btc["timestamp"] = pd.to_datetime(df_btc["timestamp"])
    df_global["timestamp"] = pd.to_datetime(df_global["timestamp"])
    df_sentiment["timestamp"] = pd.to_datetime(df_sentiment["timestamp"])
    df_btc_filtered = df_btc[
        (df_btc["timestamp"] >= start_date) & (df_btc["timestamp"] <= end_date)
    ].copy()
    df_global_filtered = df_global[
        (df_global["timestamp"] >= start_date) & (df_global["timestamp"] <= end_date)
    ].copy()
    df_sentiment_filtered = df_sentiment[
        (df_sentiment["timestamp"] >= start_date) & (df_sentiment["timestamp"] <= end_date)
    ].copy()

    # MÉTRICAS PRINCIPAIS (3 cards)
    st.markdown("### 📌 Indicadores Principais")
    col1, col2, col3 = st.columns(3)
    # --- Último preço BTC ---
    last_btc = df_btc_filtered.iloc[-1]["price_usd"]
    prev_btc = df_btc_filtered.iloc[-2]["price_usd"]
    delta_btc = last_btc - prev_btc

    col1.metric("Preço BTC (USD)", f"${last_btc:,.0f}", f"{delta_btc:+.0f}")

    # --- Market Cap ---
    if "total_market_cap" in df_global_filtered.columns:
        last_mc = df_global_filtered.iloc[-1]["total_market_cap"]
        prev_mc = df_global_filtered.iloc[-2]["total_market_cap"]
        delta_mc = last_mc - prev_mc
        col2.metric("Market Cap Cripto", f"${last_mc/1e12:.2f} T", f"{delta_mc/1e9:+.2f} B")
    else:
        col2.info("Sem Market Cap")
    # --- Dominância BTC ---
    if "btc_dominance" in df_global_filtered.columns:
        last_dom = df_global_filtered.iloc[-1]["btc_dominance"]
        prev_dom = df_global_filtered.iloc[-2]["btc_dominance"]
        delta_dom = last_dom - prev_dom
        col3.metric("Dominância BTC", f"{last_dom:.2f} %", f"{delta_dom:+.2f} pts")
    else:
        col3.info("Sem Dominância")
    st.markdown("---")

    # SENTIMENTO DO MERCADO
    st.markdown("### 😨 Sentimento Atual (Fear & Greed)")
    if not df_sentiment_filtered.empty:
        last_sent = df_sentiment_filtered.iloc[-1]
        value = last_sent["fear_greed_index"]
        text = last_sent["sentiment_text"]
        if value <= 25:
            emoji, level, color = "😱", "Medo Extremo", "#FF4444"
        elif value <= 50:
            emoji, level, color = "😟", "Medo", "#FFAA00"
        elif value <= 75:
            emoji, level, color = "🙂", "Ganância", "#33FF66"
        else:
            emoji, level, color = "🚀", "Ganância Extrema", "#00FF99"
        st.markdown(
            f"""
            <div style='background-color:{color}22; border-left:6px solid {color};
                border-radius:8px; padding:12px;'>
                <h3 style='color:{color};'>{emoji} {level}</h3>
                <p style='color:white'>
                    Índice atual: <b>{value}</b> <br>
                    Interpretação: <b>{text}</b>
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown("---")

    # MINI GRÁFICOS (Sparkline) — Preço, Dominância, Volume
    st.markdown("### 📈 Mini Gráficos Rápidos")
    colA, colB, colC = st.columns(3)
    # Preço BTC
    with colA:
        fig_price = px.line(
            df_btc_filtered.tail(50),
            x="timestamp", y="price_usd",
            title="Preço BTC (Últimos dias)"
        )
        fig_price.update_layout(height=250, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_price, use_container_width=True)
    # Dominância
    with colB:
        if "btc_dominance" in df_global_filtered.columns:
            fig_dom = px.line(
                df_global_filtered.tail(50),
                x="timestamp", y="btc_dominance",
                title="Dominância BTC"
            )
            fig_dom.update_layout(height=250, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_dom, use_container_width=True)
        else:
            st.info("Sem dados de dominância.")

    # Volume
    with colC:
        if "total_volume" in df_global_filtered.columns:
            fig_vol = px.area(
                df_global_filtered.tail(50),
                x="timestamp", y="total_volume",
                title="Volume de Mercado"
            )
            fig_vol.update_layout(height=250, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_vol, use_container_width=True)
        else:
            st.info("Sem volume.")
    st.markdown("---")

    # NOTÍCIAS RECENTES
    st.markdown("### 📰 Últimas Notícias")
    if not df_news.empty:
        df_news["date"] = pd.to_datetime(df_news["date"])
        df_news = df_news.sort_values("date", ascending=False).head(5)
        for _, row in df_news.iterrows():
            st.markdown(
                f"""
                <div style='background-color:#2d2d2d; padding:10px; margin-bottom:10px;
                    border-radius:8px;'>
                    <b style='color:#00BFFF'>{row['source'].upper()}</b><br>
                    <a href='{row['link']}' style='color:#FFD700' target='_blank'>
                        {row['headline']}
                    </a><br>
                    <span style='color:#ccc'>📅 {row['date'].strftime('%d/%m/%Y')}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("Nenhuma notícia disponível.")
    st.markdown("---")
    st.success("Resumo completo carregado com sucesso!")


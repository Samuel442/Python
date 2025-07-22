import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client
import pydeck as pdk
import plotly.graph_objects as go

# 🔑 Supabase configs
URL = "https://dvblfpbfozlcleuzedco.supabase.co"
KEY = "chave-supabase"  # substitua com sua chave

supabase: Client = create_client(URL, KEY)

# 📥 Função para carregar dados
@st.cache_data
def carregar_dados():
    try:
        resposta = supabase.table("vw_voos_formatados_oceania").select("*").execute()
        dados = pd.DataFrame(resposta.data)
        return dados
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

df = carregar_dados()

st.set_page_config(page_title="Dashboard de Voos na Oceania", layout="wide")

st.markdown(
    """
    <style>
    /* Aplica um gradiente azul no fundo do body da página */
    body {
        background: linear-gradient(135deg, #363636, #1C1C1C);
        color: white; /* Cor do texto padrão */
    }

    /* Aplica o mesmo gradiente ao fundo principal do aplicativo Streamlit */
    .stApp {
        background: linear-gradient(135deg, #B0B0B0, #2F2F2F);
    }

    /* Estiliza a barra de abas (tabs): cor de fundo levemente transparente, bordas arredondadas e espaçamento */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 0.5rem;
    }

    /* Estiliza cada aba (tab): cor clara, cantos arredondados, margens e animação de transição */
    .stTabs [data-baseweb="tab"] {
        padding: 0.5rem 1rem;
        border-radius: 10px;
        margin-right: 0.25rem;
        color: #dddddd;
        font-weight: 600;
        transition: all 0.3s ease-in-out;
    }

    /* Estiliza a aba atualmente selecionada: fundo cinza claro, texto escuro, borda clara */
    .stTabs [aria-selected="true"] {
        background-color: #cccccc;
        color: #000000;
        font-weight: bold;
        border: 2px solid #ffffff30;
    }

    /* Aplica cor branca aos títulos e métricas */
    h1, h2, h3, h4, h5, h6, .stMetricLabel, .stMetricValue {
        color: white;
    }

    /* Deixa o fundo dos gráficos Plotly transparente */
    .stPlotlyChart {
        background-color: transparent;
    }

    /* Estiliza a exibição de DataFrame (st.dataframe): fundo branco e cantos arredondados */
    .stDataFrame {
        background-color: #ffffff;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)



st.title("📡 Dashboard de Monitoramento de Voos - Oceania")


abas = st.tabs([
    "📄 Descrição",
    "✈️ Voos em Andamento",
    "📊 Distribuição por País",
    "🏁 Voos Mais Rápidos",
    "📈 Estatísticas Gerais",
    "🕒 Horários com Mais Voos",
    "🌍 Mapa de Localização"
])


# Aba 1
with abas[0]:
    st.markdown("<h1 style='text-align: center;'>🌏 Painel de Monitoramento Aéreo - Oceania</h1>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("""
    <div style="text-align: justify; font-size: 16px;">
        <p>Este painel apresenta dados públicos de voos obtidos por meio da API da <strong>OpenSky Network</strong>, uma organização sem fins lucrativos dedicada à pesquisa em aviação.</p>
        <p><strong>⚠️ Observação:</strong> Os dados não são atualizados em tempo real devido a limitações de custo na utilização da API pública gratuita.</p>
        <p>Os dados foram filtrados por <strong>latitude</strong> e <strong>longitude</strong> para representar voos na região da <strong>Oceania</strong>.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🌐 Região Geográfica de Foco")

    # Filtrando dados de latitude e longitude para Oceania
    df_oceania = df[
        (df["latitude"] >= -50) & (df["latitude"] <= 0) &
        (df["longitude"] >= 110) & (df["longitude"] <= 180)
    ][['latitude', 'longitude']].dropna()

    # Criando um container centralizado
    with st.container():
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.subheader("🗺️ Mapa de localização dos voos na Oceania")
        st.map(df_oceania)
        st.markdown("</div>", unsafe_allow_html=True)


# Aba 2
with abas[1]:
    st.subheader("✈️ Total de voos em andamento")
    st.metric("Voos ativos", len(df))

# Aba 3
with abas[2]:
    st.subheader("📊 Distribuição por país de origem")

    # Conta a quantidade de voos por país de origem
    df_origem = df['origin_country'].value_counts().reset_index()
    df_origem.columns = ['origin_country', 'count']

    # Cria o gráfico manualmente para controlar melhor a largura das barras
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_origem['origin_country'],       # Eixo X: países
        y=df_origem['count'],                # Eixo Y: quantidade de voos
        marker_color='#1f77b4',              # Cor azul escuro das barras
        width=[0.2]*len(df_origem),          # Define a largura das barras (0.4 mais fino que o normal)
    ))

    # Ajuste do layout para aparência escura e compacta
    fig.update_layout(
        title="Distribuição de voos por país de origem",
        template="plotly_dark",              # Tema escuro
        plot_bgcolor="#2c2c2c",              # Cor de fundo do gráfico
        paper_bgcolor="#2c2c2c",             # Cor de fundo geral
        font=dict(color="white"),            # Cor dos textos
        xaxis_title="País de Origem",        # Título do eixo X
        yaxis_title="Quantidade de Voos",    # Título do eixo Y
        height=350,                          # Altura mais baixa do gráfico
    )

    st.plotly_chart(fig, use_container_width=True)


# Aba 4
with abas[3]:
    # Classificação por categoria de velocidade
    def classificar_velocidade(v):
        if v < 150:
            return "Lento"
        elif v < 250:
            return "Médio"
        else:
            return "Rápido"

    df["categoria_velocidade"] = df["velocity"].apply(classificar_velocidade)

    # Contagem por categoria (forçando todas as categorias a aparecer)
    categorias = ["Lento", "Médio", "Rápido"]
    contagem_categorias = df["categoria_velocidade"].value_counts().reindex(categorias, fill_value=0).reset_index()
    contagem_categorias.columns = ["Categoria", "Quantidade"]

    st.subheader("📊 Quantidade de voos por categoria de velocidade")
    st.dataframe(contagem_categorias)

    # Gráfico de barras horizontal
    fig_cat = px.bar(
        contagem_categorias,
        x="Quantidade",
        y="Categoria",
        orientation='h',
        color="Categoria",
        title="Classificação dos Voos por Velocidade",
        color_discrete_map={
            "Lento": "#B0BEC5",
            "Médio": "#64B5F6",
            "Rápido": "#1E88E5"
        }
    )
    fig_cat.update_layout(
        xaxis_title="Quantidade de Voos",
        yaxis_title="Categoria",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False
    )
    st.plotly_chart(fig_cat, use_container_width=True)


# Aba 5
with abas[4]:
    st.subheader("📈 Média de velocidade e altitude")

    # Mostrar as métricas
    col1, col2 = st.columns(2)
    col1.metric("Velocidade Média (m/s)", f"{df['velocity'].mean():.2f}")
    col2.metric("Altitude Média (m)", f"{df['baro_altitude'].mean():.2f}")

    # Verificar se as colunas existem
    if 'velocity' in df.columns and 'baro_altitude' in df.columns:
        # Remover linhas com valores nulos
        df_corr = df[['velocity', 'baro_altitude']].dropna()

        st.markdown("### 🔄 Correlação entre Velocidade e Altitude")

        # Calcular o coeficiente de correlação de Pearson
        correlacao = df_corr['velocity'].corr(df_corr['baro_altitude'])

        st.write(f"**Coeficiente de correlação de Pearson:** `{correlacao:.2f}`")

        # Criar scatter plot
        fig = px.scatter(
            df_corr,
            x='velocity',
            y='baro_altitude',
            title="Dispersão: Velocidade vs Altitude",
            labels={'velocity': 'Velocidade (m/s)', 'baro_altitude': 'Altitude Barométrica (m)'},
            template='plotly_white',
            opacity=0.7,
            trendline='ols',  # Adiciona linha de tendência
        )

        fig.update_traces(marker=dict(size=6, line=dict(width=1, color='DarkSlateGrey')))
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=True, gridcolor='LightGray'),
            yaxis=dict(showgrid=True, gridcolor='LightGray'),
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("As colunas 'velocity' ou 'baro_altitude' não foram encontradas no DataFrame.")

#Aba 6
with abas[5]:
    st.subheader("🕒 Picos de captura por horário")

    if 'captured_at_br' in df.columns:
        # Converter para datetime e extrair hora
        df['hora'] = pd.to_datetime(df['captured_at_br'], errors='coerce').dt.hour

        # Contar capturas por hora
        hora_counts = df['hora'].value_counts().sort_values(ascending=False).head(5)

        st.markdown("### ⏰ Top 5 horários com mais voos capturados")

        # Layout em colunas para mostrar os cartões
        colunas = st.columns(5)

        for i, (hora, total) in enumerate(hora_counts.items()):
            with colunas[i]:
                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, #6EC1E4, #4F8EF7);
                                padding: 20px; border-radius: 15px; color: white; text-align: center;
                                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.2);">
                        <h2 style="margin: 0;">{hora:02d}h</h2>
                        <p style="font-size: 18px; margin: 5px 0 0;">{total} voos</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.warning("Coluna 'captured_at_br' não encontrada no dataframe.")


# Aba 7
with abas[6]:
    st.subheader("🌍 Localização dos voos")
    st.map(df[['latitude', 'longitude']].dropna())
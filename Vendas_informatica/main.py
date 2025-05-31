# Importa a biblioteca para conectar com o SQL Server
import pyodbc

# Importa o pandas para manipulação de dados
import pandas as pd

# Importa o Streamlit para criar a interface web
import streamlit as st

# Importa o Plotly para gráficos mais sofisticados
import plotly.graph_objects as go

# Cria uma conexão com o banco de dados usando pyodbc
conn = pyodbc.connect(
    'DRIVER={SQL Server};'              # Driver do SQL Server
    'SERVER=LAPTOP-U6GCBLFC;'           # Nome do servidor (pode ser o nome do seu PC)
    'DATABASE=DB_Vendas_Informatica;'  # Nome do banco de dados
    'Trusted_Connection=yes;'           # Usa autenticação do Windows (sem precisar de login e senha)
)

# Executa uma consulta SQL para pegar todos os dados da tabela "Vendas"
query = "SELECT * FROM Vendas"
df = pd.read_sql(query, conn)  # Carrega os dados em um DataFrame

# Converte a coluna 'data' para o tipo datetime (data/hora)
df['data'] = pd.to_datetime(df['data'])

# Cria um título bonito centralizado com HTML
st.markdown(
    "<h1 style='text-align: center; color: #4B8BBE;'>📊 Dashboard de Vendas - Loja de Informática</h1>",
    unsafe_allow_html=True
)

# Cria a seção de filtros no menu lateral esquerdo
st.sidebar.title("🔍 Filtros")

# Campo para escolher a data inicial (pega o menor valor da coluna 'data' como sugestão)
data_inicio = st.sidebar.date_input("Data inicial", df['data'].min())

# Campo para escolher a data final
data_fim = st.sidebar.date_input("Data final", df['data'].max())

# Filtra o DataFrame para mostrar só os dados entre as datas escolhidas
df = df[(df['data'] >= pd.to_datetime(data_inicio)) & (df['data'] <= pd.to_datetime(data_fim))]

# Calcula o total vendido
total_vendas = df['valor'].sum()

# Encontra o nome do produto mais vendido
produto_mais_vendido = df.groupby('produto')['valor'].sum().idxmax()

# Valor total do produto mais vendido
valor_top_produto = df.groupby('produto')['valor'].sum().max()

# Cria três colunas lado a lado para exibir os cartões
col1, col2, col3 = st.columns(3)

# Cartão 1 - Total Vendido
with col1:
    st.markdown(f"""
        <div style="border:2px solid #4B8BBE; padding:15px; border-radius:10px; text-align:center;">
            <h4>💰 Total Vendido</h4>
            <h2 style="color:#2E8B57;">R$ {total_vendas:,.2f}</h2>
        </div>
    """, unsafe_allow_html=True)

# Cartão 2 - Produto Campeão
with col2:
    st.markdown(f"""
        <div style="border:2px solid #4B8BBE; padding:15px; border-radius:10px; text-align:center;">
            <h4>🏆 Produto Campeão</h4>
            <h2 style="color:#2E8B57;">{produto_mais_vendido}</h2>
        </div>
    """, unsafe_allow_html=True)

# Cartão 3 - Valor do Produto Campeão
with col3:
    st.markdown(f"""
        <div style="border:2px solid #4B8BBE; padding:15px; border-radius:10px; text-align:center;">
            <h4>📦 Valor Top Produto</h4>
            <h2 style="color:#2E8B57;">R$ {valor_top_produto:,.2f}</h2>
        </div>
    """, unsafe_allow_html=True)

# Cria um subtítulo para o gráfico
st.subheader("🔹 Vendas por Produto")

# Agrupa os dados por produto e soma os valores vendidos
vendas_produto = df.groupby('produto')['valor'].sum().sort_values()

# Cria o gráfico de barras com o Streamlit (usa Altair por padrão)
st.bar_chart(vendas_produto)

# Subtítulo
st.subheader("🧭 Indicador de Vendas Totais")

# Cria um gráfico estilo velocímetro (gauge)
gauge = go.Figure(go.Indicator(
    mode="gauge+number",                        # Mostra o número e o ponteiro
    value=total_vendas,                         # Valor atual
    title={'text': "Vendas Totais"},            # Título
    gauge={'axis': {'range': [0, max(10000, total_vendas + 1000)]}}  # Define o limite máximo
))

# Mostra o gráfico na tela
st.plotly_chart(gauge)

# Mostra a tabela de dados como um DataFrame interativo
st.subheader("📋 Dados da Tabela")
st.dataframe(df)

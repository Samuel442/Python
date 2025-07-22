# 🛫 Painel Interativo de Voos na Oceania

Este projeto consiste em um painel interativo desenvolvido em **Streamlit** para visualização de voos na região da **Oceania**, com dados obtidos via requisição à **API OpenSky Network**, processados com **n8n** e armazenados no **Supabase**.

---

## 📡 Origem dos Dados

Os dados de tráfego aéreo foram obtidos a partir da [API OpenSky Network](https://opensky-network.org/), uma plataforma gratuita que fornece informações em tempo real sobre aeronaves.

- O acesso foi feito via requisição HTTP utilizando um fluxo no **n8n**
- Para fins de custo e desempenho, os dados não são atualizados em tempo real
- A região filtrada inclui apenas coordenadas de voos próximas à **Oceania**, utilizando **latitude e longitude**

---

## 🔧 Tecnologias Utilizadas

| Tecnologia  | Função                                              |
|-------------|-----------------------------------------------------|
| [n8n](https://n8n.io/)         | Requisição HTTP à API OpenSky e envio para banco |
| [Supabase](https://supabase.io/) | Armazenamento em banco de dados PostgreSQL       |
| [Streamlit](https://streamlit.io/) | Criação da interface visual interativa         |
| Python (pandas, plotly, etc) | Tratamento de dados e visualizações gráficas    |

---

## 🧠 Funcionalidades do Painel

- 🌍 Mapa com a localização atual dos voos (foco na Oceania)
- 📊 Gráfico interativo de países de origem das aeronaves
- ✈️ Informações detalhadas dos voos (altitude, país, velocidade etc.)
- 🖤 Design escuro moderno com experiência intuitiva

---

## ⚠️ Aviso

> Os dados não são atualizados em tempo real devido à limitação da API gratuita da OpenSky e custos de requisição. A atualização é feita periodicamente via fluxo automatizado no n8n.

---

## 🗂 Organização do Projeto


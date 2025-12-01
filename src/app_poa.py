import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np

DB_PATH = "violencia_poa.db"

st.set_page_config(page_title="♀️ SobreVIDA", layout="wide")
st.title("♀️ SobreVIDA — Violência entre Parceiros Íntimos (Dashboard)")

# -----------------------------------
# Função para carregar tabelas
# -----------------------------------
@st.cache_data
def load_table(name):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(f"SELECT * FROM {name}", conn)
    conn.close()
    return df

# -----------------------------------
# Carregar Dados
# -----------------------------------
categorias = load_table("categorias")
histograma = load_table("histograma")
heatmap = load_table("heatmap")

# Normalizações
categorias["BAIRRO"] = categorias["BAIRRO"].astype(str).str.upper().str.strip()
categorias["TIPOVIOLENCIA"] = categorias["TIPOVIOLENCIA"].astype(str).str.upper().str.strip()
categorias["COR_PELE"] = categorias["COR_PELE"].astype(str).str.upper().str.strip()

heatmap["X_val"] = heatmap["X_val"].astype(str).str.upper()
heatmap["Y_val"] = heatmap["Y_val"].astype(str).str.upper()

# -----------------------------------
# SIDEBAR
# -----------------------------------
st.sidebar.header("Filtros")

# Último ano como padrão
anos = sorted(categorias["ANOFATO"].dropna().unique())
ultimo_ano = max(anos)
ano_sel = st.sidebar.multiselect(
    "Ano",
    anos,
    default=[ultimo_ano]
)

# TOP 5 bairros por quantidade
top_bairros = (
    categorias.groupby("BAIRRO")["Quantidade"]
    .sum()
    .sort_values(ascending=False)
    .head(5)
    .index.tolist()
)

bairros = sorted(categorias["BAIRRO"].dropna().unique())
bairros_sel = st.sidebar.multiselect(
    "Bairros",
    bairros,
    default=top_bairros
)

# TOP 5 cores de pele
top_cores = (
    categorias.groupby("COR_PELE")["Quantidade"]
    .sum()
    .sort_values(ascending=False)
    .head(5)
    .index.tolist()
)

cores = sorted(categorias["COR_PELE"].dropna().unique())
cores_sel = st.sidebar.multiselect(
    "Cor da Pele",
    cores,
    default=top_cores
)

# Tipos de violência
tipos = sorted(categorias["TIPOVIOLENCIA"].dropna().unique())
tipo_sel = st.sidebar.multiselect(
    "Tipo de Violência",
    tipos,
    default=tipos
)

# ------------------------------------------------
# FILTROS DO HEATMAP
# ------------------------------------------------
st.sidebar.markdown("### Heatmap – Configuração")
colunas_heat = ["BAIRRO", "TIPOVIOLENCIA", "COR_PELE"]

eixo_x = st.sidebar.selectbox("Eixo X", colunas_heat, index=0)
default_y_index = (colunas_heat.index(eixo_x) + 1) % len(colunas_heat)
eixo_y = st.sidebar.selectbox("Eixo Y", colunas_heat, index=default_y_index)

# ------------------------------------------------
# FILTRO DO GRÁFICO DE BARRAS
# ------------------------------------------------
st.sidebar.markdown("### Gráfico de Barras – Configuração")
colunas_barra = ["BAIRRO", "TIPOVIOLENCIA", "COR_PELE"]
barra_eixo = st.sidebar.selectbox("Agrupar por", colunas_barra, index=1)

# -----------------------------------
# Aplicação dos filtros
# -----------------------------------
df = categorias[
    (categorias["ANOFATO"].isin(ano_sel)) &
    (categorias["TIPOVIOLENCIA"].isin(tipo_sel)) &
    (categorias["COR_PELE"].isin(cores_sel)) &
    (categorias["BAIRRO"].isin(bairros_sel))
]

# -----------------------------------
# GRÁFICOS
# -----------------------------------
col1, col2 = st.columns(2)

# -----------------------------------
# HEATMAP
# -----------------------------------
with col1:
    st.subheader("Heatmap")

    df_heat = heatmap[
        (heatmap["ANOFATO"].isin(ano_sel)) &
        (heatmap["EixoX"] == eixo_x) &
        (heatmap["EixoY"] == eixo_y)
    ]

    if df_heat.empty:
        st.info("Nenhum dado disponível para este Heatmap.")
    else:
        top_x = (
            df_heat.groupby("X_val")["Quantidade"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
            .index
        )

        top_y = (
            df_heat.groupby("Y_val")["Quantidade"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
            .index
        )

        df_heat = df_heat[
            (df_heat["X_val"].isin(top_x)) &
            (df_heat["Y_val"].isin(top_y))
        ]

        if df_heat.empty:
            st.info("Não há dados suficientes para compor um Heatmap com os Top 5.")
        else:
            pivot = df_heat.pivot_table(
                index="Y_val",
                columns="X_val",
                values="Quantidade",
                aggfunc="sum",
                fill_value=0
            )

            fig = go.Figure(go.Heatmap(
                z=pivot.values,
                x=pivot.columns,
                y=pivot.index,
                colorscale="RdPu"
            ))

            fig.update_layout(
                title=f"{eixo_x} × {eixo_y} — Top 5 por eixo",
                title_x=0.5
            )

            st.plotly_chart(fig, use_container_width=True)

# -----------------------------------
# BARRAS
# -----------------------------------
with col2:
    st.subheader("Casos por Categoria Selecionada")

    bar_df = df.groupby(barra_eixo)["Quantidade"].sum().reset_index()

    fig_bar = px.bar(
        bar_df,
        x=barra_eixo,
        y="Quantidade",
        color=barra_eixo,
        color_discrete_sequence=px.colors.sequential.RdPu
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# -----------------------------------
# PIZZA
# -----------------------------------
st.subheader("Distribuição por Cor da Pele")
pie_df = df.groupby("COR_PELE")["Quantidade"].sum().reset_index()

fig_pie = px.pie(
    pie_df,
    names="COR_PELE",
    values="Quantidade",
    hole=0.4,
    color_discrete_sequence=px.colors.sequential.RdPu
)
st.plotly_chart(fig_pie, use_container_width=True)

# -----------------------------------
# HISTOGRAMA
# -----------------------------------
st.subheader("Histograma de Idade")
hist_df = histograma[histograma["ANOFATO"].isin(ano_sel)]

fig_hist = px.histogram(
    hist_df,
    x="IDADE",
    nbins=20,
    color_discrete_sequence=["#cd6dbc"]
)
st.plotly_chart(fig_hist, use_container_width=True)

# -----------------------------------
# MAPA DE PORTO ALEGRE COM VALORES ALEATÓRIOS
# -----------------------------------
st.header("Mapa de Casos por Bairro — Porto Alegre")

with open("./data/bairros_poa.geojson", "r", encoding="utf-8") as f:
    geojson_map = json.load(f)

num_bairros = len(geojson_map["features"])
valores = np.random.randint(5, 101, size=num_bairros)  # valores aleatórios de casos

for feature, v in zip(geojson_map["features"], valores):
    feature["properties"]["TotalCasos"] = int(v)

ids = [f["properties"]["ID"] for f in geojson_map["features"]]
casos = [f["properties"]["TotalCasos"] for f in geojson_map["features"]]

fig_map = px.choropleth_mapbox(
    geojson=geojson_map,
    locations=ids,
    featureidkey="properties.ID",
    color=casos,
    mapbox_style="carto-positron",
    zoom=11,
    center={"lat": -30.03, "lon": -51.23},
    opacity=0.6,
    color_continuous_scale="RdPu",
    height=600,
    labels={'color': 'Número de casos'}
)

fig_map.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
    paper_bgcolor="rgba(0,0,0,0)"
)

st.plotly_chart(fig_map, use_container_width=True)

# -----------------------------------
# TOTAL FINAL
# -----------------------------------
st.markdown("---")
st.metric("Total de Registros nos Filtros", int(df["Quantidade"].sum()))

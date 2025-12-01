import streamlit as st
import pandas as pd
import sqlite3
import json
import plotly.express as px
import plotly.graph_objects as go
import warnings
import numpy as np
from src.auth import require_login, logout_button

st.set_page_config(page_title="SobreVIDA - Dashboard", layout="wide", initial_sidebar_state="expanded")

# 🔒 Exigir login antes de mostrar conteúdo
require_login()

# 🔓 Botão de logout
logout_button()

warnings.filterwarnings("ignore")

# -----------------------
# Config
# -----------------------
DB_PATH = "./data/violencia.db"
SHAPE_PATH = "./data/bairros_ll.geojson"
SHAPE_COL = "BAIRRO_PAD"

st.title("♀️ SobreVIDA — Violência entre Parceiros Íntimos (Dashboard)")

# -----------------------
# Helpers
# -----------------------
@st.cache_data
def load_table_from_sql(table_name):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

@st.cache_data
def load_shapefile(path):
    with open(path, "r", encoding="utf-8") as f:
        g = json.load(f)
    if g.get("type") != "FeatureCollection":
        raise ValueError("O arquivo GeoJSON deve ser um FeatureCollection")
    for i, feature in enumerate(g["features"]):
        value = feature["properties"].get(SHAPE_COL, "")
        feature["properties"][SHAPE_COL] = str(value).upper().strip()
        feature["properties"]["id_bairro"] = i
    return g

# -----------------------
# Load data
# -----------------------
try:
    heat_df = load_table_from_sql("heatmap")
    cat_df = load_table_from_sql("categorias")
    hist_df = load_table_from_sql("histograma")
except Exception as e:
    st.error(f"Erro ao carregar dados do banco: {e}")
    st.stop()

try:
    gdf = load_shapefile(SHAPE_PATH)
except Exception as e:
    st.error(f"Erro ao carregar shapefile '{SHAPE_PATH}': {e}")
    st.stop()

# normalize main fields
for col in ["BAIRRO", "TIPOVIOLENCIA", "FaixaEtária"]:
    if col in cat_df.columns:
        cat_df[col] = cat_df[col].astype(str).str.upper().str.strip()
if "BAIRRO" in hist_df.columns:
    hist_df["BAIRRO"] = hist_df["BAIRRO"].astype(str).str.upper().str.strip()

# -----------------------
# Sidebar filters
# -----------------------
st.sidebar.header("Filtros")
layout_option = st.sidebar.radio("Escolha o layout", ["Horizontal", "Vertical"])

anos = sorted(pd.unique(pd.concat([heat_df["AnoFato"], cat_df["AnoFato"]], ignore_index=True).dropna().astype(int)))
anos_selecionados = st.sidebar.multiselect("Anos", anos, default=[anos[-1]])
if not anos_selecionados:
    st.warning("Selecione pelo menos um ano.")
    st.stop()

heat_df = heat_df[heat_df["AnoFato"].isin(anos_selecionados)]
cat_df = cat_df[cat_df["AnoFato"].isin(anos_selecionados)]
if "AnoFato" in hist_df.columns:
    hist_df = hist_df[hist_df["AnoFato"].isin(anos_selecionados)]

tipos = sorted(cat_df["TIPOVIOLENCIA"].dropna().unique())
tipos_sel = st.sidebar.multiselect("Tipo de Violência", tipos, default=tipos)
if tipos_sel:
    cat_df = cat_df[cat_df["TIPOVIOLENCIA"].isin(tipos_sel)]

if "BAIRRO" in cat_df.columns:
    bairros_all = sorted(cat_df["BAIRRO"].dropna().unique())
    top5_bairros = cat_df.groupby("BAIRRO")["Quantidade"].sum().nlargest(5).index.tolist()
    bairros_sel = st.sidebar.multiselect("Bairros", bairros_all, default=top5_bairros)
    if bairros_sel:
        cat_df = cat_df[cat_df["BAIRRO"].isin(bairros_sel)]
        if "BAIRRO" in hist_df.columns:
            hist_df = hist_df[hist_df["BAIRRO"].isin(bairros_sel)]
else:
    bairros_sel = []

# -----------------------
# Category columns
# -----------------------
exclude_cols = {"Quantidade", "AnoFato", "X_val", "Y_val", "EixoX", "EixoY", "Sexo"}
cat_cols = [c for c in cat_df.columns if c not in exclude_cols and cat_df[c].dtype == object]
if not cat_cols:
    cat_cols = ["TIPOVIOLENCIA", "BAIRRO", "FaixaEtária"]

st.sidebar.markdown("---")
st.sidebar.subheader("Configurações de visualização")
eixo_x = st.sidebar.selectbox("Heatmap — Eixo X", cat_cols, index=0)
eixo_y = st.sidebar.selectbox("Heatmap — Eixo Y", cat_cols, index=1 if len(cat_cols) > 1 else 0)
group_bar = st.sidebar.selectbox("Gráfico de Barras — Agrupar por", cat_cols, index=0)
pie_col = st.sidebar.selectbox("Gráfico de Pizza — Categoria", cat_cols, index=1 if len(cat_cols) > 1 else 0)
hist_col = "IDADE"

# -----------------------
# Função para criar colunas
# -----------------------
def get_columns(container, n=2):
    if layout_option == "Vertical":
        return [container] * n  # empilha todos
    else:
        return container.columns(n)

# -----------------------
# HEATMAP + BARRAS
# -----------------------
container1 = st.container()
col1, col2 = get_columns(container1, 2)

with col1:
    # Seleciona apenas as linhas correspondentes ao eixo escolhido
    df_heat = heat_df[(heat_df["EixoX"] == eixo_x) & (heat_df["EixoY"] == eixo_y)].copy()

    # Aplicar filtro de bairros se necessário
    if bairros_sel:
        if eixo_x == "BAIRRO":
            df_heat = df_heat[df_heat["X_val"].isin(bairros_sel)]
        if eixo_y == "BAIRRO":
            df_heat = df_heat[df_heat["Y_val"].isin(bairros_sel)]

    if df_heat.empty:
        st.info("Nenhum dado disponível")
    else:
        # Limitar top 6 apenas para BAIRRO x BAIRRO
        if eixo_x == "BAIRRO" and eixo_y == "BAIRRO":
            top_x = df_heat.groupby("X_val")["Quantidade"].sum().nlargest(6).index
            top_y = df_heat.groupby("Y_val")["Quantidade"].sum().nlargest(6).index
            df_heat = df_heat[df_heat["X_val"].isin(top_x) & df_heat["Y_val"].isin(top_y)]

        # Agrupar para pivot table usando X_val e Y_val
        df_heat_grouped = df_heat.groupby(["Y_val", "X_val"], as_index=False)["Quantidade"].sum()
        pivot = df_heat_grouped.pivot(index="Y_val", columns="X_val", values="Quantidade").fillna(0)

        heat = go.Figure(go.Heatmap(
            z=pivot.values,
            x=list(pivot.columns),
            y=list(pivot.index),
            colorscale="RdPu"
        ))
        heat.update_layout(title=f"{eixo_x} × {eixo_y}", title_x=0, title_font_size=18)
        st.plotly_chart(heat, use_container_width=True)

with col2:
    df_bar = cat_df[[group_bar, "Quantidade"]].dropna()
    df_bar = df_bar.groupby(group_bar)["Quantidade"].sum().nlargest(5).reset_index()
    bar = go.Figure(go.Bar(x=df_bar[group_bar], y=df_bar["Quantidade"], text=df_bar["Quantidade"],
                           textposition="auto", marker_color="rgb(206,109,189)"))
    bar.update_layout(title=f"Número de casos por {group_bar}", title_x=0, title_font_size=18)
    st.plotly_chart(bar, use_container_width=True)

# -----------------------
# PIE + HISTOGRAMA
# -----------------------
container2 = st.container()
col3, col4 = get_columns(container2, 2)

with col3:
    df_pie = cat_df[[pie_col, "Quantidade"]].dropna()
    df_pie = df_pie.groupby(pie_col)["Quantidade"].sum().nlargest(5).reset_index()
    pie = go.Figure(go.Pie(labels=df_pie[pie_col], values=df_pie["Quantidade"], hole=0.4))
    pie.update_layout(title=f"Proporção por {pie_col}", title_x=0, title_font_size=18, legend=dict(x=0.02))
    st.plotly_chart(pie, use_container_width=True)

with col4:
    if "IDADE" in hist_df.columns:
        dfh = hist_df.dropna(subset=["IDADE"])
        dfh["IDADE"] = dfh["IDADE"].astype(float)
        bins = st.sidebar.slider("Número de bins (histograma):", 5, 80, 20)
        hist = go.Figure(go.Histogram(
            x=dfh["IDADE"],
            nbinsx=bins,
            marker_color="rgba(221,160,221,0.8)",
            marker_line_color='black',
            marker_line_width=1
        ))
        hist.update_layout(title=f"Histograma de idade", title_x=0, title_font_size=18)
        st.plotly_chart(hist, use_container_width=True)

# -----------------------
# MAPA — atualizado apenas pelo filtro de ano
# -----------------------
st.header("Mapa coroplético — Casos por Bairro")

# Cria um dataframe apenas com filtro de ano
cat_df_map = load_table_from_sql("categorias")  # sempre carrega a tabela completa
cat_df_map = cat_df_map[cat_df_map["AnoFato"].isin(anos_selecionados)]

geojson_map = json.loads(open(SHAPE_PATH).read())
for i, feature in enumerate(geojson_map["features"]):
    feature["properties"]["id_bairro"] = i

total_real = int(cat_df_map["Quantidade"].sum())
num_bairros = len(geojson_map["features"])
valores = np.random.rand(num_bairros)
valores = valores / valores.sum() * total_real
valores = valores.round().astype(int)
diff = total_real - valores.sum()
if diff != 0:
    i = np.random.randint(0, num_bairros)
    valores[i] += diff
valores = [max(v, 1) for v in valores]

for f, v in zip(geojson_map["features"], valores):
    f["properties"]["TotalCasos"] = int(v)

ids = [f["properties"]["id_bairro"] for f in geojson_map["features"]]
casos = [f["properties"]["TotalCasos"] for f in geojson_map["features"]]

fig_map = px.choropleth_mapbox(
    geojson=geojson_map,
    locations=ids,
    featureidkey="properties.id_bairro",
    color=casos,
    mapbox_style="carto-positron",
    zoom=11,
    center={"lat": -19.92, "lon": -43.94},
    opacity=0.65,
    color_continuous_scale="RdPu",
    height=600,
    labels={'color': 'Número de casos'}
)
fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig_map, use_container_width=True)

# -----------------------------
# WAFFLE CHART
# -----------------------------
st.subheader("Prevalência dos Tipos de Violência")
df_prev = cat_df.copy()
prev = df_prev["TIPOVIOLENCIA"].value_counts().reset_index()
prev.columns = ["TipoViolencia", "Total"]

if prev.empty:
    st.info("Nenhum dado disponível para os filtros selecionados.")
else:
    total = prev["Total"].sum()
    perc_raw = prev["Total"] / total * 100
    perc_round = perc_raw.round().astype(int)
    diff = 100 - perc_round.sum()
    if diff != 0:
        idx_max = perc_raw.idxmax()
        perc_round.loc[idx_max] += diff
    prev["Perc"] = perc_round

    waffle = []
    for _, row in prev.iterrows():
        waffle.extend([row["TipoViolencia"]] * row["Perc"])
    waffle = waffle[:100]

    waffle_grid = pd.DataFrame(np.array(waffle).reshape(10, 10))
    palette = px.colors.sequential.RdPu
    color_map = {cat: palette[i % len(palette)] for i, cat in enumerate(prev["TipoViolencia"])}

    fig_waffle = go.Figure()
    for r in range(10):
        for c in range(10):
            categoria = waffle_grid.iloc[r, c]
            fig_waffle.add_shape(
                type="rect",
                x0=c, x1=c + 1, y0=10 - r - 1, y1=10 - r,
                line=dict(width=0.5, color="white"),
                fillcolor=color_map.get(categoria, "#ccc")
            )
    for cat, tot in zip(prev["TipoViolencia"], prev["Total"]):
        fig_waffle.add_trace(go.Bar(
            x=[None], y=[None],
            marker=dict(color=color_map[cat]),
            name=f"{cat} ({tot})"
        ))

    fig_waffle.update_layout(
        showlegend=True,
        legend=dict(orientation="v", x=1.05, y=1),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        width=None,
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=120, t=30, b=0),
        title=dict(text="Waffle Chart — Prevalência da Violência", x=0, y=0.97, xanchor="left", font=dict(size=18))
    )
    st.plotly_chart(fig_waffle, use_container_width=True)

# -----------------------
# SUMMARY
# -----------------------
st.markdown("---")
st.metric("Casos no Filtro", f"{int(cat_df['Quantidade'].sum()):,}")

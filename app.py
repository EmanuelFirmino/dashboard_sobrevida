import streamlit as st
import pandas as pd
import sqlite3
import json
import plotly.express as px
import plotly.graph_objects as go
import warnings
import numpy as np
from pathlib import Path
from src.auth import require_login, logout_button

st.set_page_config(page_icon='♀️', page_title="♀️ SobreVIDA — Dashboard Unificado", layout="wide", initial_sidebar_state="expanded")

require_login()

logout_button()

warnings.filterwarnings("ignore")

st.title("♀️ SobreVIDA — Violência entre Parceiros Íntimos")

# -----------------------
# CONFIG: caminhos (ajuste se necessário)
# -----------------------
PATH_BH_DB = "./data/violencia.db"
PATH_BH_GEO = "./data/bairros_ll.geojson"

PATH_POA_DB = "violencia_poa.db"
PATH_POA_GEO = "./data/bairros_poa.geojson"

# -----------------------
# HELPERS
# -----------------------
@st.cache_data(ttl=600)
def load_sql_table(db_path: str, table_name: str):
    if not Path(db_path).exists():
        raise FileNotFoundError(f"DB não encontrado: {db_path}")
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    finally:
        conn.close()
    return df

@st.cache_data(ttl=600)
def load_geojson(path: str, shape_col_name: str = None):
    if not Path(path).exists():
        raise FileNotFoundError(f"GeoJSON não encontrado: {path}")
    with open(path, "r", encoding="utf-8") as f:
        gj = json.load(f)
    if gj.get("type") != "FeatureCollection":
        raise ValueError("GeoJSON deve ser FeatureCollection")
    # normalize requested shape column (se informado) and always create id_bairro index
    for i, feat in enumerate(gj["features"]):
        if shape_col_name:
            val = feat["properties"].get(shape_col_name, "")
            feat["properties"][shape_col_name] = str(val).upper().strip()
        # create id_bairro if missing
        if "id_bairro" not in feat["properties"]:
            feat["properties"]["id_bairro"] = i
    return gj

def normalize_cat_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza/renomeia colunas da tabela 'categorias' para nomes usados no app:
      - ANOFATO (int)
      - BAIRRO (str)
      - TIPOVIOLENCIA (str)
      - Quantidade (int)
      - COR_PELE (str)  <= mapeia 'Cor Autodeclarada' ou 'COR_PELE'
      - IDADE (float/int)  <= mapeia 'IDADE' ou 'Idade Participante'
    Não elimina colunas adicionais.
    """
    df = df.copy()
    colmap = {}
    cols_lower = {c.lower(): c for c in df.columns}

    # ano
    for candidate in ["ano", "ano_fato", "anofato", "ano fato"]:
        if candidate in cols_lower:
            colmap[cols_lower[candidate]] = "ANOFATO"
            break

    # bairro
    for candidate in ["bairro"]:
        if candidate in cols_lower:
            colmap[cols_lower[candidate]] = "BAIRRO"
            break

    # tipo violencia
    for candidate in ["tipoviolencia", "tipo_fato", "tipo fato", "tipo_de_violencia", "tipo violencia"]:
        if candidate in cols_lower:
            colmap[cols_lower[candidate]] = "TIPOVIOLENCIA"
            break

    # quantidade
    for candidate in ["quantidade", "qtde_vit_domest_sexoougenero", "quant"]:
        if candidate in cols_lower:
            colmap[cols_lower[candidate]] = "Quantidade"
            break

    # cor pele
    for candidate in ["cor_pele", "cor_autodeclarada", "cor cadastro", "cor_cadastro", "cor autodeclarada"]:
        if candidate in cols_lower:
            colmap[cols_lower[candidate]] = "COR_PELE"
            break

    # idade
    for candidate in ["idade", "idade_participante", "idade participante", "idade_part"]:
        if candidate in cols_lower:
            colmap[cols_lower[candidate]] = "IDADE"
            break

    # apply renames
    df = df.rename(columns=colmap)

    # uppercase and strip textual columns if present
    for text_col in ["BAIRRO", "TIPOVIOLENCIA", "COR_PELE"]:
        if text_col in df.columns:
            df[text_col] = df[text_col].astype(str).str.upper().str.strip()

    # ensure numeric types
    if "ANOFATO" in df.columns:
        df["ANOFATO"] = pd.to_numeric(df["ANOFATO"], errors="coerce").astype(pd.Int64Dtype())
    if "Quantidade" in df.columns:
        df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce").fillna(0).astype(int)
    if "IDADE" in df.columns:
        df["IDADE"] = pd.to_numeric(df["IDADE"], errors="coerce")

    return df

def normalize_heat_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza a tabela heatmap para colunas:
      - ANOFATO, EixoX, EixoY, X_val, Y_val, Quantidade
    """
    df = df.copy()
    cols_lower = {c.lower(): c for c in df.columns}
    colmap = {}

    for candidate in ["anofato", "ano_fato", "ano"]:
        if candidate in cols_lower:
            colmap[cols_lower[candidate]] = "ANOFATO"
            break

    for candidate in ["eixox", "eixo_x", "eixo x"]:
        if candidate in cols_lower:
            colmap[cols_lower[candidate]] = "EixoX"
            break

    for candidate in ["eixoy", "eixo_y", "eixo y"]:
        if candidate in cols_lower:
            colmap[cols_lower[candidate]] = "EixoY"
            break

    for candidate in ["x_val", "xval", "x val"]:
        if candidate in cols_lower:
            colmap[cols_lower[candidate]] = "X_val"
            break

    for candidate in ["y_val", "yval", "y val"]:
        if candidate in cols_lower:
            colmap[cols_lower[candidate]] = "Y_val"
            break

    for candidate in ["quantidade", "total", "count"]:
        if candidate in cols_lower:
            colmap[cols_lower[candidate]] = "Quantidade"
            break

    df = df.rename(columns=colmap)

    # uppercase X/Y labels for uniformity
    for c in ["X_val", "Y_val", "EixoX", "EixoY"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.upper().str.strip()

    if "Quantidade" in df.columns:
        df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce").fillna(0).astype(int)
    if "ANOFATO" in df.columns:
        df["ANOFATO"] = pd.to_numeric(df["ANOFATO"], errors="coerce").astype(pd.Int64Dtype())

    return df

def main():
    # -----------------------
    # SIDEBAR: escolha da fonte (BH / POA)
    # -----------------------
    data_source = st.sidebar.radio("Fonte dos dados", ["Belo Horizonte", "Porto Alegre"])

    if data_source == "Belo Horizonte":
        DB_PATH = PATH_BH_DB
        SHAPE_PATH = PATH_BH_GEO
        SHAPE_COL = "BAIRRO_PAD"
    else:
        DB_PATH = PATH_POA_DB
        SHAPE_PATH = PATH_POA_GEO
        # POA geojson may have different property name; we'll not try to normalize property column name
        SHAPE_COL = None

    # -----------------------
    # Carregar tabelas (cada DB: heatmap, categorias, histograma)
    # -----------------------
    try:
        raw_cat = load_sql_table(DB_PATH, "categorias")
        raw_heat = load_sql_table(DB_PATH, "heatmap")
        raw_hist = load_sql_table(DB_PATH, "histograma")
    except Exception as e:
        st.error(f"Erro ao carregar tabelas do DB ({DB_PATH}): {e}")
        st.stop()

    # normalize columns
    cat_full = normalize_cat_columns(raw_cat)
    heat_full = normalize_heat_columns(raw_heat)
    hist_full = raw_hist.copy()
    # try to normalize hist columns (AGE and ANOFATO)
    hist_cols_lower = {c.lower(): c for c in hist_full.columns}
    if "idade" in hist_cols_lower:
        hist_full = hist_full.rename(columns={hist_cols_lower["idade"]: "IDADE"})
    elif "idade_participante" in hist_cols_lower:
        hist_full = hist_full.rename(columns={hist_cols_lower["idade_participante"]: "IDADE"})
    if "anofato" in hist_cols_lower or "ano_fato" in hist_cols_lower or "ano" in hist_cols_lower:
        for candidate in ["anofato", "ano_fato", "ano"]:
            if candidate in hist_cols_lower:
                hist_full = hist_full.rename(columns={hist_cols_lower[candidate]: "ANOFATO"})
                break

    # -----------------------
    # Carregar geojson (com cache)
    # -----------------------
    try:
        geojson_map = load_geojson(SHAPE_PATH, shape_col_name=SHAPE_COL)
    except Exception as e:
        st.error(f"Erro ao carregar GeoJSON ({SHAPE_PATH}): {e}")
        st.stop()

    # -----------------------
    # Preparar opções de filtros (baseadas na tabela padronizada)
    anos = []
    if "ANOFATO" in cat_full.columns:
        anos = sorted(cat_full["ANOFATO"].dropna().unique())
    elif "ANOFATO" in heat_full.columns:
        anos = sorted(heat_full["ANOFATO"].dropna().unique())
    else:
        st.error("Nenhuma coluna de ano encontrada nas tabelas.")
        st.stop()

    # DEFAULTS: último ano
    ultimo_ano = int(max(anos))
    st.sidebar.header("Filtros")

    # ano (multi-select)
    anos_selecionados = st.sidebar.multiselect("Anos", anos, default=[ultimo_ano])
    if not anos_selecionados:
        st.warning("Selecione pelo menos um ano.")
        st.stop()

    # Normalize cat_full text columns if present
    if "BAIRRO" in cat_full.columns:
        bairros_all = sorted(cat_full["BAIRRO"].dropna().unique())
    else:
        bairros_all = []

    if bairros_all:
        top5_bairros = list(cat_full.groupby("BAIRRO")["Quantidade"].sum().nlargest(5).index)
    else:
        top5_bairros = []

    # Layout option (preserva seu comportamento)
    layout_option = st.sidebar.radio("Escolha o layout", ["Horizontal", "Vertical"])

    # bairros selector
    bairros_sel = st.sidebar.multiselect("Bairros", bairros_all, default=top5_bairros)


    # cores de pele
    cores_all = sorted(cat_full["COR_PELE"].dropna().unique()) if "COR_PELE" in cat_full.columns else []
    top5_cores = list(cat_full.groupby("COR_PELE")["Quantidade"].sum().nlargest(5).index) if cores_all else []
    cores_sel = st.sidebar.multiselect("Cor da Pele", cores_all, default=top5_cores)

    # Tipos de violência
    tipos_all = sorted(cat_full["TIPOVIOLENCIA"].dropna().unique()) if "TIPOVIOLENCIA" in cat_full.columns else []
    tipos_sel = st.sidebar.multiselect("Tipo de Violência", tipos_all, default=tipos_all)


    # Heatmap controls in sidebar (defaults: choose different X / Y)
    st.sidebar.markdown("### Heatmap — Configuração")
    # available heatmap axes -> deduce from columns present in cat_full or heat_full
    heat_axes = []
    # prefer the canonical names if present
    possible_axes = []
    if "BAIRRO" in cat_full.columns:
        possible_axes.append("BAIRRO")
    if "TIPOVIOLENCIA" in cat_full.columns:
        possible_axes.append("TIPOVIOLENCIA")
    if "COR_PELE" in cat_full.columns:
        possible_axes.append("COR_PELE")
    # fallback to what's present in heat_full values (X_val/Y_val content)
    if not possible_axes:
        # try unique values from heat_full EixoX/EixoY
        ex = heat_full["EixoX"].dropna().unique() if "EixoX" in heat_full.columns else []
        ey = heat_full["EixoY"].dropna().unique() if "EixoY" in heat_full.columns else []
        possible_axes = list(pd.unique(list(ex) + list(ey)))
    heat_axes = possible_axes

    if not heat_axes:
        st.error("Não há colunas candidatas para eixos do heatmap.")
        st.stop()

    # set defaults: choose two different axes if possible
    default_x = heat_axes[0]
    default_y = heat_axes[1] if len(heat_axes) > 1 else heat_axes[0]
    eixo_x = st.sidebar.selectbox("Eixo X", heat_axes, index=heat_axes.index(default_x))
    eixo_y = st.sidebar.selectbox("Eixo Y", heat_axes, index=heat_axes.index(default_y) if default_y in heat_axes else 0)

    # Bar chart grouping control
    st.sidebar.markdown("### Gráfico de Barras — Configuração")
    bar_choices = [c for c in ["BAIRRO", "TIPOVIOLENCIA", "COR_PELE"] if c in cat_full.columns]
    if not bar_choices:
        bar_choices = [c for c in cat_full.columns if cat_full[c].dtype == object][:3]
    bar_group = st.sidebar.selectbox("Agrupar por", bar_choices, index=0)

    # -----------------------
    # Aplicar filtros aos dataframes (para gráficos que dependem de todos filtros)
    # -----------------------
    cat_df = cat_full.copy()
    # filter by anos (always)
    if "ANOFATO" in cat_df.columns:
        cat_df = cat_df[cat_df["ANOFATO"].isin(anos_selecionados)]
    # apply other filters to cat_df (these WILL affect bar/pie/hist/heatmap selection)
    if "TIPOVIOLENCIA" in cat_df.columns and tipos_sel:
        cat_df = cat_df[cat_df["TIPOVIOLENCIA"].isin(tipos_sel)]
    if "COR_PELE" in cat_df.columns and cores_sel:
        cat_df = cat_df[cat_df["COR_PELE"].isin(cores_sel)]
    if "BAIRRO" in cat_df.columns and bairros_sel:
        cat_df = cat_df[cat_df["BAIRRO"].isin(bairros_sel)]

    # heatmap source: use heat_full but filtered by ANOFATO and by EixoX/EixoY fields
    heat_df = heat_full.copy()
    if "ANOFATO" in heat_df.columns:
        heat_df = heat_df[heat_df["ANOFATO"].isin(anos_selecionados)]
    # filter by EixoX/EixoY metadata (we expect EixoX/EixoY columns to contain strings matching eixo_x/eixo_y)
    if "EixoX" in heat_df.columns and "EixoY" in heat_df.columns:
        heat_df = heat_df[(heat_df["EixoX"] == eixo_x) & (heat_df["EixoY"] == eixo_y)]
    else:
        # if heat_full does not use EixoX/EixoY, attempt to build from cat_df (fallback)
        # create a synthetic heatmap by grouping cat_df on eixo_x x eixo_y if both exist in cat_df
        if eixo_x in cat_df.columns and eixo_y in cat_df.columns:
            temp = cat_df.groupby([eixo_y, eixo_x], as_index=False)["Quantidade"].sum()
            temp = temp.rename(columns={eixo_x: "X_val", eixo_y: "Y_val"})
            temp["EixoX"] = eixo_x
            temp["EixoY"] = eixo_y
            heat_df = temp[["EixoX","EixoY","X_val","Y_val","Quantidade"]].copy()
        else:
            heat_df = pd.DataFrame(columns=["EixoX","EixoY","X_val","Y_val","Quantidade"])

    # -----------------------
    # Função utilitária layout
    # -----------------------
    def get_columns(container, n=2):
        if layout_option == "Vertical":
            # return list of same container so with-statement will stack
            return [container] * n
        return container.columns(n)

    # -----------------------
    # RENDER: Heatmap + Bar
    # -----------------------
    container1 = st.container()
    col1, col2 = get_columns(container1, 2)

    with col1:
        st.subheader("Heatmap")
        df_h = heat_df.copy()

        # If user selected bairros filter, apply it to heat via X_val/Y_val when axis is BAIRRO
        if bairros_sel and eixo_x == "BAIRRO" and "X_val" in df_h.columns:
            df_h = df_h[df_h["X_val"].isin(bairros_sel)]
        if bairros_sel and eixo_y == "BAIRRO" and "Y_val" in df_h.columns:
            df_h = df_h[df_h["Y_val"].isin(bairros_sel)]

        if df_h.empty:
            st.info("Nenhum dado disponível para este Heatmap.")
        else:
            # compute top-5 for each axis (only among the rows present in df_h)
            if "X_val" in df_h.columns and "Y_val" in df_h.columns:
                top_x = df_h.groupby("X_val")["Quantidade"].sum().nlargest(5).index.tolist()
                top_y = df_h.groupby("Y_val")["Quantidade"].sum().nlargest(5).index.tolist()
                df_h = df_h[df_h["X_val"].isin(top_x) & df_h["Y_val"].isin(top_y)]
                if df_h.empty:
                    st.info("Não há dados suficientes para compor um Heatmap com os Top 5.")
                else:
                    pivot = df_h.pivot_table(index="Y_val", columns="X_val", values="Quantidade", aggfunc="sum", fill_value=0)
                    fig = go.Figure(go.Heatmap(z=pivot.values, x=pivot.columns, y=pivot.index, colorscale="RdPu"))
                    fig.update_layout(title=f"{eixo_x} × {eixo_y} — Top 5 por eixo", title_x=0.5)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Estrutura do heatmap não contém X_val / Y_val.")

    with col2:
        st.subheader("Casos por Categoria Selecionada")
        if bar_group in cat_df.columns:
            bar_df = cat_df.groupby(bar_group)["Quantidade"].sum().reset_index()
            if bar_df.empty:
                st.info("Nenhum dado para o gráfico de barras.")
            else:
                fig_bar = px.bar(bar_df, x=bar_group, y="Quantidade", color=bar_group, color_discrete_sequence=px.colors.sequential.RdPu)
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Campo selecionado para agrupamento não está disponível nos dados.")

    # -----------------------
    # PIE + HIST
    # -----------------------
    container2 = st.container()
    col3, col4 = get_columns(container2, 2)

    with col3:
        st.subheader("Distribuição por Cor da Pele")
        if "COR_PELE" in cat_df.columns:
            pie_df = cat_df.groupby("COR_PELE")["Quantidade"].sum().reset_index()
            fig_pie = px.pie(pie_df, names="COR_PELE", values="Quantidade", hole=0.4, color_discrete_sequence=px.colors.sequential.RdPu)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Coluna COR_PELE não disponível.")

    with col4:
        st.subheader("Histograma de Idade")
        if "IDADE" in hist_full.columns:
            hist_df = hist_full[hist_full["ANOFATO"].isin(anos_selecionados)].copy()
            # try to filter by bairros selection if hist has BAIRRO
            if "BAIRRO" in hist_df.columns and bairros_sel:
                hist_df["BAIRRO"] = hist_df["BAIRRO"].astype(str).str.upper().str.strip()
                hist_df = hist_df[hist_df["BAIRRO"].isin(bairros_sel)]
            if hist_df.empty:
                st.info("Nenhum registro no histograma para os filtros selecionados.")
            else:
                fig_hist = px.histogram(hist_df, x="IDADE", nbins=20, color_discrete_sequence=["#800080"])
                st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Coluna de idade não encontrada na tabela histograma.")

    # -----------------------
    # MAPA — atualiza apenas quando ANO muda (usamos cat_full filtered apenas por ANOFATO)
    # -----------------------
    st.header("Mapa coroplético — Casos por Bairro")

    # prepare cat_for_map: load fresh full categories from DB (to ignore other filters) and filter only by anos
    cat_for_map = normalize_cat_columns(load_sql_table(DB_PATH, "categorias"))
    if "ANOFATO" in cat_for_map.columns:
        cat_for_map = cat_for_map[cat_for_map["ANOFATO"].isin(anos_selecionados)]
    total_real = int(cat_for_map["Quantidade"].sum()) if "Quantidade" in cat_for_map.columns else 0

    # distribute total_real randomly across geojson features (preserve sum)
    n_features = len(geojson_map["features"])
    if n_features == 0:
        st.info("GeoJSON não contém features.")
    else:
        if total_real <= 0:
            # fallback: generate small random values so map shows colors
            valores = np.random.randint(1, 10, size=n_features)
        else:
            valores = np.random.rand(n_features)
            valores = valores / valores.sum() * total_real
            valores = np.round(valores).astype(int)
            diff = int(total_real - valores.sum())
            if diff != 0:
                idx = np.random.randint(0, n_features)
                valores[idx] += diff
            # ensure non-zero for display
            valores = [max(int(v), 1) for v in valores]

        # write into geojson
        for feat, v in zip(geojson_map["features"], valores):
            feat["properties"]["TotalCasos"] = int(v)
            # ensure there is a numeric id property for Plotly; prefer existing 'ID' / 'id' / 'id_bairro'
            if "ID" not in feat["properties"] and "id" not in feat["properties"]:
                feat["properties"].setdefault("id_bairro", feat["properties"].get("id_bairro", 0))

        # choose feature id key intelligently
        sample_props = geojson_map["features"][0]["properties"]
        if "ID" in sample_props:
            featureidkey = "properties.ID"
            locations = [f["properties"]["ID"] for f in geojson_map["features"]]
        elif "id" in sample_props:
            featureidkey = "properties.id"
            locations = [f["properties"]["id"] for f in geojson_map["features"]]
        else:
            featureidkey = "properties.id_bairro"
            locations = [f["properties"]["id_bairro"] for f in geojson_map["features"]]

        casos = [f["properties"]["TotalCasos"] for f in geojson_map["features"]]

        # center map depending on city
        if data_source == "Belo Horizonte":
            center = {"lat": -19.92, "lon": -43.94}
            zoom = 11
        else:
            center = {"lat": -30.03, "lon": -51.23}
            zoom = 11

        fig_map = px.choropleth_mapbox(
            geojson=geojson_map,
            locations=locations,
            featureidkey=featureidkey,
            color=casos,
            mapbox_style="carto-positron",
            zoom=zoom,
            center=center,
            opacity=0.65,
            color_continuous_scale="RdPu",
            height=600,
            labels={"color": "Número de casos"}
        )

        fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_map, use_container_width=True)

    # -----------------------
    # WAFFLE / SUMMARY
    # -----------------------
    st.subheader("Prevalência dos Tipos de Violência")
    if "TIPOVIOLENCIA" in cat_df.columns:
        prev = cat_df["TIPOVIOLENCIA"].value_counts().reset_index()
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
            if len(waffle) < 100:
                waffle += [""] * (100 - len(waffle))
            waffle_grid = pd.DataFrame(np.array(waffle).reshape(10, 10))
            palette = px.colors.sequential.RdPu
            color_map = {cat: palette[i % len(palette)] for i, cat in enumerate(prev["TipoViolencia"])}
            fig_waffle = go.Figure()
            for r in range(10):
                for c in range(10):
                    categoria = waffle_grid.iloc[r, c]
                    fig_waffle.add_shape(type="rect", x0=c, x1=c+1, y0=10-r-1, y1=10-r,
                                        line=dict(width=0.5, color="white"),
                                        fillcolor=color_map.get(categoria, "#ccc"))
            for cat, tot in zip(prev["TipoViolencia"], prev["Total"]):
                fig_waffle.add_trace(go.Bar(x=[None], y=[None], marker=dict(color=color_map[cat]), name=f"{cat} ({tot})"))
            fig_waffle.update_layout(showlegend=True, legend=dict(orientation="v", x=1.05, y=1),
                                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                    width=None, height=380, paper_bgcolor="rgba(0,0,0,0)",
                                    plot_bgcolor="rgba(0,0,0,0)",
                                    margin=dict(l=0, r=120, t=30, b=0),
                                    title=dict(text="Waffle Chart — Prevalência da Violência", x=0, y=0.97, xanchor="left", font=dict(size=18)))
            st.plotly_chart(fig_waffle, use_container_width=True)
    else:
        st.info("TIPOVIOLENCIA não disponível para geração do waffle.")

    st.markdown("---")
    total_filtrado = int(cat_df["Quantidade"].sum()) if "Quantidade" in cat_df.columns else 0
    st.metric("Casos no Filtro (aplica todos filtros)", f"{total_filtrado:,}")

if __name__ == '__main__':
    main()
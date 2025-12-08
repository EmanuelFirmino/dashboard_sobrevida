import sqlite3
import pandas as pd
import geopandas as gpd

# ===========================
# 1. CARREGAR SHAPEFILE
# ===========================
gdf = gpd.read_file("BAIRRO_POPULAR.shp")   # ajuste o nome se necessário
gdf["NOME"] = gdf["NOME"].str.upper().str.strip()

# ===========================
# 2. CARREGAR DADOS DO BANCO
# ===========================
DB_PATH = "violencia.db"

conn = sqlite3.connect(DB_PATH)

df = pd.read_sql("SELECT * FROM categorias", conn)

conn.close()

df["BAIRRO"] = df["BAIRRO"].astype(str).str.upper().str.strip()

casos_bairro = (
    df.groupby("BAIRRO")["Quantidade"]
      .sum()
      .reset_index()
      .rename(columns={"Quantidade": "N_CASOS"})
)

viol_bairro = (
    df.groupby(["BAIRRO", "TIPOVIOLENCIA"])["Quantidade"]
      .sum()
      .reset_index()
)

viol_bairro = (
    viol_bairro.loc[viol_bairro.groupby("BAIRRO")["Quantidade"].idxmax()]
               [["BAIRRO", "TIPOVIOLENCIA"]]
               .rename(columns={"TIPOVIOLENCIA": "TIPOVIOLENCIA_MAIS_FREQUENTE"})
)

gdf = gdf.merge(casos_bairro, how="left", left_on="NOME", right_on="BAIRRO")
gdf = gdf.merge(viol_bairro, how="left", left_on="NOME", right_on="BAIRRO")

gdf = gdf.drop(columns=["BAIRRO_x", "BAIRRO_y"], errors="ignore")

gdf["N_CASOS"] = gdf["N_CASOS"].fillna(0)
gdf["TIPOVIOLENCIA_MAIS_FREQUENTE"] = gdf["TIPOVIOLENCIA_MAIS_FREQUENTE"].fillna("Sem dados")

gdf.to_file("bairros_com_violencia.shp")

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

# Tabela que contém TIPOVIOLENCIA, BAIRRO e Quantidade
df = pd.read_sql("SELECT * FROM categorias", conn)

conn.close()

# Padronizar bairros
df["BAIRRO"] = df["BAIRRO"].astype(str).str.upper().str.strip()

# ===========================
# 3. CALCULAR NÚMERO DE CASOS POR BAIRRO
# ===========================
casos_bairro = (
    df.groupby("BAIRRO")["Quantidade"]
      .sum()
      .reset_index()
      .rename(columns={"Quantidade": "N_CASOS"})
)

# ===========================
# 4. CALCULAR TIPO MAIS FREQUENTE POR BAIRRO
# ===========================
viol_bairro = (
    df.groupby(["BAIRRO", "TIPOVIOLENCIA"])["Quantidade"]
      .sum()
      .reset_index()
)

# pegar o tipo mais frequente
viol_bairro = (
    viol_bairro.loc[viol_bairro.groupby("BAIRRO")["Quantidade"].idxmax()]
               [["BAIRRO", "TIPOVIOLENCIA"]]
               .rename(columns={"TIPOVIOLENCIA": "TIPOVIOLENCIA_MAIS_FREQUENTE"})
)

# ===========================
# 5. MERGE COM O SHAPEFILE
# ===========================
gdf = gdf.merge(casos_bairro, how="left", left_on="NOME", right_on="BAIRRO")
gdf = gdf.merge(viol_bairro, how="left", left_on="NOME", right_on="BAIRRO")

# Limpar colunas duplicadas
gdf = gdf.drop(columns=["BAIRRO_x", "BAIRRO_y"], errors="ignore")

# ===========================
# 6. TRATAR BAIRROS SEM REGISTROS
# ===========================
gdf["N_CASOS"] = gdf["N_CASOS"].fillna(0)
gdf["TIPOVIOLENCIA_MAIS_FREQUENTE"] = gdf["TIPOVIOLENCIA_MAIS_FREQUENTE"].fillna("Sem dados")

# ===========================
# 7. SALVAR SHAPEFILE ENRIQUECIDO
# ===========================
gdf.to_file("bairros_com_violencia.shp")

print("✔️ Shapefile criado: bairros_com_violencia.shp")

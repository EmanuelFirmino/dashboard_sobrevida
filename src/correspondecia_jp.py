import geopandas as gpd
import pandas as pd
import sqlite3
from rapidfuzz import process, fuzz

# ------------------------------------
# CONFIGURAÇÕES
# ------------------------------------
SHAPE_PATH = "BAIRRO_POPULAR.shp"  
OUT_PATH = "BAIRRO_PADRONIZADO.shp"
DB_PATH = "violencia.db"

SHAPE_COL = "NOME"     # coluna do shapefile com os nomes dos bairros
DATA_COL = "BAIRRO"     # coluna do banco contendo os bairros padronizados


# ------------------------------------
# 1. CARREGAR O SHAPEFILE
# ------------------------------------
print("🔍 Carregando shapefile...")
gdf = gpd.read_file(SHAPE_PATH)
gdf[SHAPE_COL] = gdf[SHAPE_COL].astype(str).str.upper().str.strip()


# ------------------------------------
# 2. CARREGAR LISTA DE BAIRROS DO BANCO
# ------------------------------------
print("🔍 Carregando bairros do banco...")

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql("SELECT DISTINCT BAIRRO FROM categorias", conn)
conn.close()

df["BAIRRO"] = df["BAIRRO"].astype(str).str.upper().str.strip()
bairros_pad = df["BAIRRO"].dropna().unique().tolist()

print(f"Total de bairros no banco: {len(bairros_pad)}")


# ------------------------------------
# 3. CORRESPONDÊNCIA FUZZY
# ------------------------------------
def melhor_correspondencia(nome_bairro):
    match, score, idx = process.extractOne(
        nome_bairro,
        bairros_pad,
        scorer=fuzz.WRatio
    )
    return match, score


print("\n🔧 Gerando correspondências (fuzzy matching)...")

matches = []
scores = []

for nome in gdf[SHAPE_COL]:
    match, score = melhor_correspondencia(nome)
    matches.append(match)
    scores.append(score)

gdf["BAIRRO_PAD"] = matches
gdf["SCORE_MATCH"] = scores


# ------------------------------------
# 4. LOG: verificar correspondências ruins
# ------------------------------------
ruins = gdf[gdf["SCORE_MATCH"] < 70]

print("\n⚠️ Correspondências fracas (score < 70):")
if len(ruins) == 0:
    print("Nenhuma correspondência ruim encontrada.")
else:
    print(ruins[[SHAPE_COL, "BAIRRO_PAD", "SCORE_MATCH"]])


# ------------------------------------
# 5. SALVAR SHAPEFILE PADRONIZADO
# ------------------------------------
print("\n💾 Salvando shapefile padronizado:", OUT_PATH)
gdf.to_file(OUT_PATH, encoding="utf-8")
print("🎉 Arquivo salvo com sucesso!")

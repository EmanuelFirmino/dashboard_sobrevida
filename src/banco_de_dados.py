import pandas as pd
import numpy as np
import sqlite3
from itertools import product

# =======================
# Configurações
# =======================
csv_path = "./PCMG/BH.csv"
db_path = "violencia.db"

# =======================
# Carregar os dados
# =======================
df = pd.read_csv(csv_path, sep=",", low_memory=False)

# Padronizar nomes das colunas
df = df.rename(columns={
    "TIPOVIOLÊNCIA": "TIPOVIOLENCIA",
    "Bairro_Atualizado": "BAIRRO",
    "CordaPele": "COR_PELE",
    "Idade_Atualizada": "IDADE"
})

# Converter datas
df["DataFato"] = pd.to_datetime(df["DataFato"], errors="coerce")
df["AnoFato"] = df["DataFato"].dt.year

# Remover registros sem ano
df = df.dropna(subset=["AnoFato"])
df["AnoFato"] = df["AnoFato"].astype(int)

# =======================
# Definir colunas para análises
# =======================
cat_cols = [
    "TIPOVIOLENCIA", "BAIRRO", "FaixaEtária", "Sexo",
    "COR_PELE", "Escolaridade", "RelaçãoVítimaAutor",
    "TipoEnvolvimento", "GrauLesão"
]

num_col = "IDADE"

# =======================
# Heatmap — pré agregação
# =======================
heat_records = []

for x, y in product(cat_cols, repeat=2):
    if x == y: 
        continue
    temp = df.groupby([x, y, "AnoFato"]).size().reset_index(name="Quantidade")
    temp["EixoX"] = x
    temp["EixoY"] = y
    temp = temp.rename(columns={x: "X_val", y: "Y_val"})
    heat_records.append(temp)

heat_df = pd.concat(heat_records, ignore_index=True)

# =======================
# Barras e Pizza — pré agregação
# =======================
bar_pie_df = df.groupby(cat_cols + ["AnoFato"]).size().reset_index(name="Quantidade")

# =======================
# Histograma — pré agregação
# =======================
hist_df = df[["AnoFato", num_col]].dropna()

# =======================
# Salvar no SQLite
# =======================
conn = sqlite3.connect(db_path)
heat_df.to_sql("heatmap", conn, if_exists="replace", index=False)
bar_pie_df.to_sql("categorias", conn, if_exists="replace", index=False)
hist_df.to_sql("histograma", conn, if_exists="replace", index=False)
conn.close()

print("✅ Banco criado com sucesso:", db_path)

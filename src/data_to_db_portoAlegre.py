import pandas as pd
import sqlite3
import numpy as np

df = pd.read_excel("../data/PortoAlegre_total/dados_corrigidos.xlsx", header=1)

domestic = ['LESAO CORPORAL', 'LESAO CORPORAL LEVE', 'AMEACA', 'ESTUPRO',
                'VIOLENCIA PSICOL CONTRA MULHER', 'FAVORECIMENTO DA PROSTITUICAO OU DE OUTRA FORMA DE EXPLORACAO SEXUAL',
                'FEMINICIDIO', 'OTR CRIMES CONTRA A FAMILIA', 'LESAO CORPORAL GRAVE', 'LESAO CORPORAL LEVE',
                'FAVORECIMENTO A PROSTITUICAO (*)', 'HOMICIDIO DOLOSO']

with open('atualCrimes.txt', 'w+') as file1:
    for crime in domestic:
        file1.write(crime)
        file1.write('\n')

with open('totalCrimes.txt', 'w+') as file2:
    for crime in df['Desc Fato'].unique():
        file2.write(crime)
        file2.write('\n')

df = df[df['Desc Fato'].isin(domestic)].reset_index(drop=True)

df.columns = (
    df.columns.str.strip()
    .str.lower()
    .str.replace(" ", "_")
    .str.replace("ç", "c")
    .str.replace("ã", "a")
    .str.replace("õ", "o")
    .str.replace("á", "a")
    .str.replace("é", "e")
    .str.replace("í", "i")
    .str.replace("ó", "o")
    .str.replace("ú", "u")
)


df["ano"] = df["ano_fato"].astype(int)
df["bairro"] = df["bairro"].astype(str).str.upper().str.strip()
df["tipo_fato"] = df["desc_fato"].astype(str).str.upper().str.strip()
df["genero"] = df["genero"].astype(str).str.upper().str.strip()
df["cor_autodeclarada"] = df["cor_autodeclarada"].astype(str).str.upper().str.strip()

faltantes = {
    "escolaridade": "",
    "relacaovitimaautor": "",
    "tipoenvolvimento": "",
    "graulesao": ""
}

for col, default_value in faltantes.items():
    if col not in df.columns:
        df[col] = default_value

df_categorias = df.rename(columns={
    "ano": "AnoFato",
    "tipo_fato": "TIPOVIOLENCIA",
    "idade_participante": "FaixaEtária",
    "genero": "Sexo",
    "cor_autodeclarada": "COR_PELE",
    "bairro": "BAIRRO",
    "qtde_vit_domest_sexoougenero": "Quantidade",
    "escolaridade": "Escolaridade",
    "relacaovitimaautor": "RelaçãoVítimaAutor",
    "tipoenvolvimento": "TipoEnvolvimento",
    "graulesao": "GrauLesão"
})

df_categorias["Quantidade"] = df_categorias["Quantidade"].fillna(1).astype(int)

df_categorias = df_categorias[
    ["TIPOVIOLENCIA", "BAIRRO", "FaixaEtária", "Sexo", "COR_PELE",
     "Escolaridade", "RelaçãoVítimaAutor", "TipoEnvolvimento",
     "GrauLesão", "AnoFato", "Quantidade"]
]

df_hist = df.rename(columns={
    "ano": "AnoFato",
    "idade_participante": "IDADE"
})[["AnoFato", "IDADE"]]

heat_rows = []

cat_cols = [
    "TIPOVIOLENCIA", "BAIRRO", "FaixaEtária",
    "Sexo", "COR_PELE"
]

df_base = df_categorias.copy()

for eixo_x in cat_cols:
    for eixo_y in cat_cols:

        if eixo_x == eixo_y:
            continue 

        temp = (
            df_base.groupby([eixo_x, eixo_y, "AnoFato"])["Quantidade"]
            .sum().reset_index()
            .rename(columns={
                eixo_x: "X_val",
                eixo_y: "Y_val"
            })
        )

        temp["EixoX"] = eixo_x
        temp["EixoY"] = eixo_y

        heat_rows.append(temp)

df_heatmap = pd.concat(heat_rows, ignore_index=True)

df_heatmap = df_heatmap[
    ["X_val", "Y_val", "AnoFato", "Quantidade", "EixoX", "EixoY"]
]

conn = sqlite3.connect("porto_alegre.db")

df_categorias.to_sql("categorias", conn, if_exists="replace", index=False)
df_hist.to_sql("histograma", conn, if_exists="replace", index=False)
df_heatmap.to_sql("heatmap", conn, if_exists="replace", index=False)

conn.close()

print("\n✔ Banco porto_alegre.db criado com sucesso!")
print("✔ Tabelas criadas: categorias, histograma, heatmap")
print("✔ Compatível com o app de BH (incluindo o HEATMAP)")

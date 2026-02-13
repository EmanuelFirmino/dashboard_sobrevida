import pandas as pd

# Ler arquivos
df_csv = pd.read_csv("PortoAlegre_total/violencia_total.csv")
df_xlsx = pd.read_excel("PortoAlegre_total/dadosViolenciaPadronizados.xlsx")

# Juntar as linhas (empilhar um abaixo do outro)
df_final = pd.concat([df_csv, df_xlsx], ignore_index=True)

# Salvar resultado
df_final.to_csv("resultado.csv", index=False)
# ou salvar em Excel
# df_final.to_excel("resultado.xlsx", index=False)

print("Arquivos unidos com sucesso!")

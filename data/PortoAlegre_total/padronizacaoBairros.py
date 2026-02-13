import pandas as pd
import difflib
import unicodedata
import re

def normalizar(texto):
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.encode('ascii', 'ignore').decode('utf-8')
    texto = texto.lower()
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def similaridade_percentual(str1, str2):
    n1 = normalizar(str1)
    n2 = normalizar(str2)
    return difflib.SequenceMatcher(None, n1, n2).ratio() * 100


corrigidos = ['NONOAI', 'TRISTEZA', 'SARANDI', 'SANTA ROSA DE LIMA', 'MORRO SANTANA', 'BELÉM NOVO', 'RUBEM BERTA', 'HUMAITÁ', 'HÍPICA', 'SANTO ANTÔNIO', 'CAVALHADA', 'SANTA TEREZA', 'CASCATA', 'JARDIM CARVALHO', 'RESTINGA', 'AUXILIADORA', 'CENTRO HISTÓRICO', 'N/I', 'VILA NOVA', 'ABERTA DOS MORROS', 'MÁRIO QUINTANA', 'RIO BRANCO', 'VILA SÃO JOSÉ', 'BOM JESUS', 'CRISTAL', 'SANTANA', 'LOMBA DO PINHEIRO', 'PASSO DAS PEDRAS', 'VILA JARDIM', 'INDEPENDÊNCIA', 'CEL. APARICIO BORGES', 'SANTA MARIA GORETTI', 'TERESÓPOLIS', 'JARDIM BOTÂNICO', 'SÃO SEBASTIÃO', 'PARTENON', 'PASSO DA AREIA', 'FLORESTA', 'JARDIM ITU', 'JARDIM FLORESTA', 'PETRÓPOLIS', 'LAMI', 'FARRAPOS', 'PONTA GROSSA', 'NAVEGANTES', 'MENINO DEUS', 'AZENHA', 'PRAIA DE BELAS', 'CAMPO NOVO', 'CIDADE BAIXA', 'BELA VISTA', 'VILA CONCEIÇÃO', 'MEDIANEIRA', 'ESPÍRITO SANTO', 'AGRONOMIA', 'CRISTO REDENTOR', 'IPANEMA', 'SANTA CECÍLIA', 'JARDIM LEOPOLDINA', 'TRÊS FIGUEIRAS', 'CAMAQUÃ', 'VILA IPIRANGA', 'ARQUIPÉLAGO', 'BELÉM VELHO', 'CHAPÉU DO SOL', 'JARDIM SABARÁ', 'VILA JOÃO PESSOA', 'GLÓRIA', 'SÃO JOÃO', 'JARDIM SÃO PEDRO', 'MONTSERRAT', 'ANCHIETA', 'FARROUPILHA', 'SERRARIA', 'BOA VISTA', 'COSTA E SILVA', 'GUARUJÁ', 'SÃO GERALDO', 'LAGEADO', 'BOM FIM', 'PEDRA REDONDA', 'VILA ASSUNÇÃO', 'PITINGA', 'PARQUE SANTA FÉ', 'CHÁCARA DAS PEDRAS', 'MOINHOS DE VENTO', 'JARDIM DO SALSO', 'JARDIM LINDÓIA', 'HIGIENÓPOLIS', 'JARDIM EUROPA', 'JARDIM ISABEL', 'EXTREMA', 'BOA VISTA DO SUL', 'SÃO CAETANO']

def main():
    df = pd.read_csv('remanescentes.csv')

    with open('scores.txt', 'w', encoding='utf-8') as f:  # abre uma vez só
        for idx, row in df.iterrows():

            if not isinstance(row['Bairro'], str):
                continue

            probs = []

            for corr in corrigidos:
                score = similaridade_percentual(row['Bairro'], corr)
                probs.append((score, corr))

            # ordena do maior para o menor
            probs_ordenado = sorted(probs, key=lambda x: x[0], reverse=True)

            best_score, best_corr = probs_ordenado[0]

            if best_score >= 70:
                df.at[idx, 'Bairro'] = best_corr 
                msg = f'Sucesso: {row["Bairro"]} ~= {best_corr} ({best_score:.2f}%)'
            else:
                msg = f'Score insuficiente: {row["Bairro"]} != {best_corr} ({best_score:.2f}%)'

            print(msg)
            f.write(msg + '\n')


    df.to_csv('resultadoPadronizacao.csv', index=False)

    
df = pd.read_csv('resultadoPadronizacao.csv')

df = df[~df['Bairro'].isin(corrigidos)]

df.to_excel('dadosNaoPadronizados.xlsx', index=False)



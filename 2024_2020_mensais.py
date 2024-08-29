import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import re
from fuzzywuzzy import fuzz
from collections import Counter

url_base = 'https://www.publishnews.com.br/ranking/mensal'

def coletar_dados(url, ano, mes):
    try:
        resposta = requests.get(url)
        resposta.raise_for_status()
        html = resposta.text
        sopa = BeautifulSoup(html, 'html.parser')

        blocos_livros = sopa.find_all('div', class_='pn-ranking-livro-dados')

        dados = []
        for bloco in blocos_livros:
            bloco_rank = bloco.find_previous('div', class_='pn-ranking-livros-posicao-numero')
            rank = bloco_rank.get_text(strip=True) if bloco_rank else "N/A"

            nome = bloco.find('div', class_='pn-ranking-livro-nome').get_text(strip=True)

            autor = bloco.find('div', class_='pn-ranking-livro-autor').get_text(strip=True)

            dados.append((mes, rank, nome, autor))

        return dados

    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        return []


def salvar_dados_em_arquivo(dados_totais, ano, diretorio):
    nome_arquivo = os.path.join(diretorio, f'livros_geral_{ano}.txt')

    df = pd.DataFrame(dados_totais, columns=['Mês', 'Colocação', 'Nome do Livro', 'Autor'])

    df['Mês'] = df['Mês'].astype(str).str.pad(width=5, side='right')
    df['Colocação'] = df['Colocação'].astype(str).str.pad(width=10, side='right')

    df.to_csv(nome_arquivo, sep='\t', index=False, header=True, mode='w')


def salvar_top_10_livros(dados_totais, ano, diretorio):
    nome_arquivo = os.path.join(diretorio, f'top_10_livros_{ano}.txt')

    livros = [dado[2] for dado in dados_totais]
    contador_livros = Counter(livros)

    top_10 = contador_livros.most_common(10)

    df = pd.DataFrame(top_10, columns=['Nome do Livro', 'Frequência'])
    df = df[['Frequência', 'Nome do Livro']]

    df.to_csv(nome_arquivo, sep='\t', index=False, header=True, mode='w')

diretorio = '2024_2020_mensais'
if not os.path.exists(diretorio):
    os.makedirs(diretorio)
    print(f"Diretório '{diretorio}' criado.")

for ano in range(2024, 2019, -1):
    dados_totais_ano = []
    for mes in range(1, 13):
        url = f'{url_base}/0/{ano}/{mes}/0'
        print(f"Coletando dados de: {url}")
        dados = coletar_dados(url, ano, mes)
        dados_totais_ano.extend(dados)

    salvar_dados_em_arquivo(dados_totais_ano, ano, diretorio)

    salvar_top_10_livros(dados_totais_ano, ano, diretorio)

print("Dados dos livros salvos no diretório '2024_2020_mensais'.")

def carregar_dados_txt(diretorio, anos):
    livros = []
    for ano in anos:
        caminho_arquivo = os.path.join(diretorio, f'livros_geral_{ano}.txt')
        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                for linha in f:
                    partes = linha.strip().split('\t')  # Usando tabulação como delimitador
                    if len(partes) == 4:
                        mes, colocacao, nome, autor = partes
                        livros.append((nome, autor))
    return livros

def normalizar_nome(nome):
    nome = nome.lower().strip()
    nome = re.sub(r'\s+', ' ', nome)  # Remover múltiplos espaços
    return nome

def comparar_nomes(nome1, nome2):
    return fuzz.ratio(normalizar_nome(nome1), normalizar_nome(nome2)) > 80  # Similaridade de 80%

def remover_duplicatas(livros):
    livros_unicos = []

    for nome, autor in livros:
        nome_normalizado = normalizar_nome(nome)
        if not any(comparar_nomes(nome_normalizado, normalizar_nome(nv)) for nv, _ in livros_unicos):
            livros_unicos.append((nome, autor))

    return livros_unicos

def salvar_livros_unicos_txt(livros_unicos, diretorio):
    caminho_arquivo = os.path.join(diretorio, 'livros_unicos.txt')
    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
        for nome, autor in livros_unicos:
            f.write(f"{nome} - {autor}\n")
    print(f"Lista de livros únicos salva em: {caminho_arquivo}")

diretorio = '2024_2020_mensais'
anos = range(2024, 2019, -1)

livros = carregar_dados_txt(diretorio, anos)
livros_unicos = remover_duplicatas(livros)

salvar_livros_unicos_txt(livros_unicos, diretorio)

# Import the required modules
import discord
from discord import app_commands
import os
from discord.ext import commands
from dotenv import load_dotenv
import sqlite3
import re
import random
import json
from flask import Flask
from threading import Thread
import psycopg2

# Create a Discord client instance and set the command prefix
intents = discord.Intents.all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!', intents=intents)

with open('movimentos_basicos.json', 'r', encoding='utf-8') as file:
    # Carrega o conteúdo do arquivo em um dicionário
    movimentos_basicos = json.load(file)


def obter_modificador(atributo):
    """
    Retorna o modificador de atributo baseado nas faixas fornecidas.

    Parâmetros:
    - atributo: valor do atributo para o qual o modificador deve ser calculado.

    Retorna:
    - Modificador inteiro para o atributo.
    """
    if atributo == None:
        return 0
    atributo = int(atributo)
    if atributo <= 3:
        return -3
    elif atributo <= 5:
        return -2
    elif atributo <= 8:
        return -1
    elif atributo <= 12:
        return 0
    elif atributo <= 15:
        return 1
    elif atributo <= 17:
        return 2
    else:
        return 3


def formatar_inventario(inventario):
    if inventario == None:
        inventario = "[]"
    inventario = json.loads(inventario)

    # Títulos das colunas
    cabecalho = "Item                              | Descrição                                    | Quantidade | Peso | Valor"
    separador = "-" * len(cabecalho)

    # Construindo cada linha do inventário
    linhas = []
    for item in inventario:
        linhas.append(
            f"{item['item']:<33} | {item['descricao']:<44} | {item['quantidade']:^10} | {item['peso']:^4} | {item['valor']:^5}"
        )

    # Juntando tudo
    tabela = f"```\n{cabecalho}\n{separador}\n" + "\n".join(linhas) + "\n```"

    return tabela


def formatar_vinculos(vinculos):
    if vinculos == None:
        vinculos = "[]"
    vinculos = json.loads(vinculos)
    # Títulos das colunas
    cabecalho = "Nome                              | Descrição                                                                | Valor"
    separador = "-" * len(cabecalho)

    # Construindo cada linha do inventário
    linhas = []
    for item in vinculos:
        linhas.append(
            f"{item['nome']:<33} | {item['descricao']:<72} | {item['valor']:^5}"
        )

    # Juntando tudo
    tabela = f"```\n{cabecalho}\n{separador}\n" + "\n".join(linhas) + "\n```"

    return tabela


def formatar_movimentos(movimentos):
    if movimentos == None:
        movimentos = "[]"
    movimentos = json.loads(movimentos)
    # Títulos das colunas

    linhas = []
    for item in movimentos:
        linhas.append(f"---> {item['nome']}")

    # Juntando tudo
    tabela = f"```" + "\n".join(linhas) + "\n```"

    return tabela


def calcular_peso_total(inventario_json):
    try:
        # Converte o inventário de JSON para uma lista de dicionários
        inventario = json.loads(inventario_json)

        # Soma o peso de todos os itens
        peso_total = sum(
            item.get('peso', 0) * item.get('quantidade', 0)
            for item in inventario)

        return peso_total
    except json.JSONDecodeError:
        # Caso haja um erro na decodificação do JSON
        print("Erro ao decodificar o inventário JSON.")
        return 0
    except Exception as e:
        # Captura outros erros
        print(f"Ocorreu um erro ao calcular o peso total: {e}")
        return 0


def formatar_dicionarios(lista_dicionarios):
    resultado = []

    for dicionario in lista_dicionarios:
        partes = []
        for chave, valor in dicionario.items():
            chave_formatada = chave.capitalize(
            )  # Capitaliza o primeiro caractere da chave
            partes.append(f"**{chave_formatada}**: {valor}")
        resultado.append("\n".join(partes))

    return "\n".join(resultado)


def formatar_json(json):
    novojson = {
        "nome": "",
        "aparencia": "",
        "classe": "",
        "xp": "",
        "nivel": "",
        "alinhamento": "",
        "alinhamento_detalhe": "",
        "raca": "",
        "raca_texto": "",
        "dado_dano": "",
        "hp_atual": "",
        "hp_max": "",
        "armadura": "",
        "str": "",
        "des": "",
        "con": "",
        "int": "",
        "sab": "",
        "car": "",
        "debilidades": "",
        "carga_max": "",
        "carga_atual": "",
        "inventario": "",
        "vinculos": "",
        "movimentos": "",
        "sorte": 0,
        "notas": ""
    }

    novojson["nome"] = json.get('characterName')
    novojson["aparencia"] = json.get('look').replace("\n", " ")
    novojson["classe"] = json.get('characterClass')
    novojson["xp"] = int(json.get('xp'))
    novojson["nivel"] = int(json.get('level'))
    novojson["alinhamento"] = json.get('alignment').split(" - ")[0]
    novojson["alinhamento_detalhe"] = json.get('alignment').split(" - ")[1]
    novojson["raca"] = json.get('race').split(" - ")[0]
    novojson["raca_texto"] = json.get('race').split(" - ")[1]
    novojson["dado_dano"] = json.get('otherDice')
    novojson["hp_atual"] = int(json.get('hitPoints'))
    novojson["hp_max"] = int(json.get('maxHitPoints'))
    novojson["armadura"] = int(json.get('armor'))
    novojson["str"] = int(json.get('strength'))
    novojson["des"] = int(json.get('dexterity'))
    novojson["con"] = int(json.get('constitution'))
    novojson["int"] = int(json.get('intelligence'))
    novojson["sab"] = int(json.get('wisdom'))
    novojson["car"] = int(json.get('charisma'))
    novojson["debilidades"] = ""
    novojson["carga_max"] = int(json.get('load'))
    novojson["carga_atual"] = int(json.get('maxLoad'))
    novojson["inventario"] = "[]"
    novojson["vinculos"] = "[]"
    novojson["movimentos"] = "[]"
    novojson["sorte"] = 0
    novojson["notas"] = ""

    return novojson


@bot.event
async def on_ready():
    print(f'Bot {bot.user} está pronto e funcionando!')

    # Sincronizando os comandos do bot
    try:
        # Sincroniza os comandos globais
        await bot.tree.sync()
        print("Comandos sincronizados com sucesso!")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")


# Set the commands for your bot

import json

# Conectar ao banco de dados

conn = psycopg2.connect('postgresql://postgres:rmZCpqXsuEhaZWmTvEbhCEiYkkjWZlbr@postgres.railway.internal:5432/railway')
cursor = conn.cursor()

# Criação da tabela de fichas
cursor.execute('''
CREATE TABLE IF NOT EXISTS fichas (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    nome TEXT,
    aparencia TEXT,
    classe TEXT,
    xp INTEGER,
    nivel INTEGER,
    alinhamento TEXT,
    alinhamento_detalhe TEXT,
    raca TEXT,
    raca_texto TEXT,
    dado_dano TEXT,
    hp_atual INTEGER,
    hp_max INTEGER,
    armadura INTEGER,
    str INTEGER,
    des INTEGER,
    con INTEGER,    
    int INTEGER,           
    sab INTEGER,
    car INTEGER,
    debilidades TEXT,
    carga_max INTEGER,
    carga_atual INTEGER,
    inventario TEXT,
    vinculos TEXT,
    movimentos TEXT,
    sorte INTEGER,
    notas TEXT
)
''')

# Criação da tabela de fichas ativas
cursor.execute('''
CREATE TABLE IF NOT EXISTS fichas_ativas (
    user_id BIGINT PRIMARY KEY,
    ficha_ativa_id INTEGER,
    FOREIGN KEY (ficha_ativa_id) REFERENCES fichas(id)
)
''')

conn.commit()


@bot.tree.command(name="criar_ficha",
                  description="Cria uma ficha vazia com um nome")
@app_commands.describe(nome="O nome do personagem a ser criado", )
async def criar_ficha(interaction: discord.Interaction, nome: str):
    user_id = interaction.user.id

    # Adiciona a ficha à tabela de fichas
    cursor.execute(
        '''
    INSERT INTO fichas (user_id, nome)
    VALUES (%s, %s)
    RETURNING id
    ''', (user_id, nome))
    conn.commit()

    # Recupera o ID da ficha recém-criada
    ficha_id = cursor.fetchone()[0]

    # Se o jogador não tiver uma ficha ativa, define a nova ficha como ativa
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ativo = cursor.fetchone()

    if ativo is None:
        cursor.execute(
            '''
        INSERT INTO fichas_ativas (user_id, ficha_ativa_id)
        VALUES (%s, %s)
        ''', (user_id, ficha_id))
        conn.commit()
        await interaction.response.send_message(
            f'Ficha "{nome}" criada com sucesso e marcada como ativa!')
    else:
        await interaction.response.send_message(
            f'Ficha "{nome}" criada com sucesso!')


@bot.tree.command(name="mudar_ficha",
                  description="Alterna a sua ficha ativa atual pelo ID")
@app_commands.describe(ficha_id="O ID da ficha a ser ativada", )
async def mudar_ficha(interaction: discord.Interaction, ficha_id: int):
    user_id = interaction.user.id

    # Verifica se a ficha existe
    cursor.execute(
        '''
    SELECT * FROM fichas WHERE id = %s AND user_id = %s
    ''', (ficha_id, user_id))
    ficha = cursor.fetchone()

    if ficha:
        # Atualiza a ficha ativa
        cursor.execute(
            '''
        UPDATE fichas_ativas SET ficha_ativa_id = %s WHERE user_id = %s
        ''', (ficha_id, user_id))
        conn.commit()
        await interaction.response.send_message(
            f'Ficha ativa alterada para: {ficha[0]}, ephemeral=True'
        )  # ficha[1] é o nome do personagem
    else:
        await interaction.response.send_message(
            'Ficha não encontrada ou não pertence a você.', ephemeral=True)


@bot.tree.command(name="listar_fichas",
                  description="Lista todas as suas fichas")
async def listar_fichas(interaction: discord.Interaction):
    user_id = interaction.user.id

    # Recupera todas as fichas do jogador
    cursor.execute(
        '''
    SELECT f.id, f.nome, 
           CASE 
               WHEN fa.ficha_ativa_id = f.id THEN 'Sim' 
               ELSE 'Não' 
           END AS ativa
    FROM fichas f
    LEFT JOIN fichas_ativas fa ON f.user_id = fa.user_id
    WHERE f.user_id = %s
    ''', (user_id, ))
    fichas = cursor.fetchall()

    if fichas:
        # Cria uma lista formatada para exibir as fichas
        resposta = "Suas fichas:\n"
        for ficha in fichas:
            ficha_id, nome, ativa = ficha
            resposta += f"ID: {ficha_id} | Nome: {nome} | Ativa: {ativa}\n"

        await interaction.response.send_message(resposta, ephemeral=True)
    else:
        await interaction.response.send_message(
            'Você não tem fichas criadas. Use /criar_ficha para começar.', ephemeral=True)


@bot.tree.command(name="definir",
                  description="Edita diretamente um valor em sua ficha ativa")
@app_commands.describe(parametro="O tipo de valor a ser mostrado",
                       valor="O novo valor")
@app_commands.choices(parametro=[
    app_commands.Choice(name="Nome", value="nome"),
    app_commands.Choice(name="Aparência", value="aparencia"),
    app_commands.Choice(name="Classe", value="classe"),
    app_commands.Choice(name="Experiência", value="xp"),
    app_commands.Choice(name="Nível", value="nivel"),
    app_commands.Choice(name="Alinhamento", value="alinhamento"),
    app_commands.Choice(name="Detalhe do Alinhamento",
                        value="alinhamento_detalhe"),
    app_commands.Choice(name="Raça", value="raca"),
    app_commands.Choice(name="Efeito da Raça", value="raca_texto"),
    app_commands.Choice(name="Dado de Dano", value="dado_dano"),
    app_commands.Choice(name="Vida Atual", value="hp_atual"),
    app_commands.Choice(name="Vida Máxima", value="hp_max"),
    app_commands.Choice(name="Armadura", value="armadura"),
    app_commands.Choice(name="Força", value="str"),
    app_commands.Choice(name="Destreza", value="des"),
    app_commands.Choice(name="Constituição", value="con"),
    app_commands.Choice(name="Inteligência", value="int"),
    app_commands.Choice(name="Sabedoria", value="sab"),
    app_commands.Choice(name="Carisma", value="car"),
    app_commands.Choice(name="Carga Máxima", value="carga_max"),
    app_commands.Choice(name="Carga Atual", value="carga_atual"),
    app_commands.Choice(name="Sorte", value="sorte"),
    app_commands.Choice(name="Notas", value="notas")
])
async def definir(interaction: discord.Interaction, parametro: str,
                  valor: str):

    if parametro in [
            "nivel", "hp_atual", "hp_max", "armadura", "str", "des", "con",
            "int", "sab", "car", "carga_max", "carga_atual", "sorte"
    ]:
        valor = int(valor)

    user_id = interaction.user.id

    # Recupera a ficha ativa do usuário
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()

    if ficha_ativa:
        ficha_id = ficha_ativa[0]

        # Atualiza o campo hp_max na tabela de fichas
        cursor.execute(
            f'''
        UPDATE fichas
        SET {parametro} = %s
        WHERE id = %s
        ''', (valor, ficha_id))
        conn.commit()

        await interaction.response.send_message(
            f'O valor {parametro} da sua ficha ativa foi alterado para {valor}.', ephemeral=True
        )
    else:
        await interaction.response.send_message(
            'Você não possui uma ficha ativa. Use /mudar_ficha para selecionar ou /criar_ficha para criar uma.', ephemeral=True
        )


@bot.tree.command(
    name="mostrar",
    description="Retorna diretamente um valor da sua ficha ativa")
@app_commands.describe(parametro="O tipo de valor a ser mostrado", )
@app_commands.choices(parametro=[
    app_commands.Choice(name="Nome", value="nome"),
    app_commands.Choice(name="Aparência", value="aparencia"),
    app_commands.Choice(name="Classe", value="classe"),
    app_commands.Choice(name="Experiência", value="xp"),
    app_commands.Choice(name="Nível", value="nivel"),
    app_commands.Choice(name="Alinhamento", value="alinhamento"),
    app_commands.Choice(name="Detalhe do Alinhamento",
                        value="alinhamento_detalhe"),
    app_commands.Choice(name="Raça", value="raca"),
    app_commands.Choice(name="Efeito da Raça", value="raca_texto"),
    app_commands.Choice(name="Dado de Dano", value="dado_dano"),
    app_commands.Choice(name="Vida Atual", value="hp_atual"),
    app_commands.Choice(name="Vida Máxima", value="hp_max"),
    app_commands.Choice(name="Armadura", value="armadura"),
    app_commands.Choice(name="Força", value="str"),
    app_commands.Choice(name="Destreza", value="des"),
    app_commands.Choice(name="Constituição", value="con"),
    app_commands.Choice(name="Inteligência", value="int"),
    app_commands.Choice(name="Sabedoria", value="sab"),
    app_commands.Choice(name="Carisma", value="car"),
    app_commands.Choice(name="Carga Máxima", value="carga_max"),
    app_commands.Choice(name="Carga Atual", value="carga_atual"),
    app_commands.Choice(name="Sorte", value="sorte"),
    app_commands.Choice(name="Debilidades", value="debilidades"),
    app_commands.Choice(name="Notas", value="notas")
])
async def mostrar(interaction: discord.Interaction, parametro: str):

    user_id = interaction.user.id

    cursor.execute(
        f'''
    SELECT f.{parametro}
    FROM fichas f
    JOIN fichas_ativas fa ON f.id = fa.ficha_ativa_id
    WHERE fa.user_id = %s
    ''', (user_id, ))
    ficha = cursor.fetchone()

    if ficha:
        valor = ficha[0]
        await interaction.response.send_message(
            f'O/A {parametro} da sua ficha ativa é: {valor}')
    else:
        await interaction.response.send_message(
            'Você não possui uma ficha ativa ou nenhuma ficha está definida como ativa.'
        )


@bot.tree.command(
    name="add_item",
    description="Adiciona um item ao inventário da sua ficha ativa")
@app_commands.describe(nome="Nome do item.",
                       descricao="Descrição detalhada do item.",
                       quantidade="Quantidade do item.",
                       peso="Peso do item.",
                       valor="Valor monetário do item.")
async def add_item(interaction: discord.Interaction,
                   nome: str,
                   descricao: str,
                   quantidade: int = 1,
                   peso: int = 1,
                   valor: int = 0):
    # Recuperar o ID do jogador (supondo que interaction: discord.Interaction.user.id seja o ID do jogador)
    user_id = interaction.user.id

    # Buscar a ficha do jogador pelo ID
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()

    if ficha_ativa:
        ficha_id = ficha_ativa[0]

        cursor.execute("SELECT inventario FROM fichas WHERE id = %s",
                       (ficha_id, ))
        inventario = cursor.fetchone()

        if inventario == (None, ):
            inventario = [None, None]

        inventario_json = inventario[0]

        if inventario_json == None:
            inventario_json = "[]"

        inventario = json.loads(
            inventario_json)  # Converter de JSON para um objeto Python

        novo_item = {
            "item": nome,
            "descricao": descricao,
            "quantidade": quantidade,
            "peso": peso,
            "valor": valor
        }

        item_existente = next(
            (item
             for item in inventario if item["item"].lower() == nome.lower()),
            None)

        if not item_existente:
            inventario.append(novo_item)
        else:
            opa = inventario.index(item_existente)
            inventario[inventario.index(
                item_existente)]["quantidade"] += quantidade

        inventario_json = json.dumps(inventario, ensure_ascii=False)

        cursor.execute(
            f'''
        UPDATE fichas
        SET inventario = %s
        WHERE id = %s
        ''', (inventario_json, ficha_id))
        conn.commit()

        await interaction.response.send_message(f'O item {nome} foi adicionado', ephemeral=True
                                                )

        novacarga = calcular_peso_total(inventario_json)

        cursor.execute(
            f'''
        UPDATE fichas
        SET carga_atual = %s
        WHERE id = %s
        ''', (novacarga, ficha_id))
        conn.commit()

        cursor.execute("SELECT carga_atual FROM fichas WHERE id = %s",
                       (ficha_id, ))
        cargaatual = cursor.fetchone()[0]

        cursor.execute("SELECT carga_max FROM fichas WHERE id = %s",
                       (ficha_id, ))
        cargamax = cursor.fetchone()[0]
        if cargamax == None: cargamax = 0

        if cargaatual > cargamax:
            await interaction.channel.send(
                f'{nome} está carregando itens demais!')

    else:
        await interaction.response.send_message(
            'Você não possui uma ficha ativa. Use /mudar_ficha para selecionar ou /criar_ficha para criar uma.', ephemeral=True
        )


@bot.tree.command(name="rem_item",
                  description="Exclui um item da sua ficha ativa")
@app_commands.describe(nome_item="Nome do item a ser excluído.", )
async def rem_item(interaction: discord.Interaction, nome_item: str):
    # Passo 1: Recuperar os movimentos atuais da ficha
    user_id = interaction.user.id
    # Buscar a ficha do jogador pelo ID
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()

    if ficha_ativa:
        ficha_id = ficha_ativa[0]
    else:
        await interaction.response.send_message(
            'Você não possui uma ficha ativa. Use /mudar_ficha para selecionar ou /criar_ficha para criar uma.', ephemeral=True
        )
        return

    cursor.execute("SELECT inventario FROM fichas WHERE id = %s", (ficha_id, ))
    resultado = cursor.fetchone()

    # Se a ficha não tiver movimentos, não há nada para remover
    if not resultado or not resultado[0]:
        await interaction.response.send_message("Não há itens para remover.", ephemeral=True)
        return

    # Passo 2: Converter o JSON armazenado no banco para uma lista de dicionários
    inventario = json.loads(resultado[0])

    # Passo 3: Buscar o movimento com o nome especificado
    item_existente = next(
        (item
         for item in inventario if item["item"].lower() == nome_item.lower()),
        None)

    # Se o movimento não existir, exibe uma mensagem e sai
    if not item_existente:
        await interaction.response.send_message(
            f"O item {nome_item} não foi encontrado", ephemeral=True)
        return

    # Passo 4: Remover o movimento da lista
    inventario.remove(item_existente)

    # Passo 5: Atualizar a coluna 'movimentos' com a lista de movimentos modificada
    inventario_json = json.dumps(inventario, ensure_ascii=False)
    cursor.execute(
        '''
        UPDATE fichas
        SET inventario = %s
        WHERE id = %s
    ''', (inventario_json, ficha_id))

    # Commit para garantir que as mudanças sejam salvas no banco de dados
    conn.commit()
    await interaction.response.send_message(f"O item {nome_item} foi excluído", ephemeral=True)

    novacarga = calcular_peso_total(inventario_json)

    cursor.execute(
        f'''
    UPDATE fichas
    SET carga_atual = %s
    WHERE id = %s
    ''', (novacarga, ficha_id))
    conn.commit()
    cursor.execute("SELECT nome FROM fichas WHERE id = %s", (ficha_id, ))
    nome = cursor.fetchone()[0]
    
    cursor.execute("SELECT carga_atual FROM fichas WHERE id = %s", (ficha_id, ))
    cargaatual = cursor.fetchone()[0]

    cursor.execute("SELECT carga_max FROM fichas WHERE id = %s", (ficha_id, ))
    cargamax = cursor.fetchone()[0]
    if cargamax == None: cargamax = 0

    if cargaatual > cargamax:
        await interaction.channel.send(f'{nome} está carregando itens demais!')


@bot.tree.command(name="usar_item",
                  description="Usa um item da sua ficha ativa")
@app_commands.describe(nome_item="Nome do item a ser usado.", )
async def usar_item(interaction: discord.Interaction, nome_item: str, quantidade: int = 1):
    # Passo 1: Recuperar os movimentos atuais da ficha
    user_id = interaction.user.id
    # Buscar a ficha do jogador pelo ID
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()

    if ficha_ativa:
        ficha_id = ficha_ativa[0]
    else:
        await interaction.response.send_message(
            'Você não possui uma ficha ativa. Use /mudar_ficha para selecionar ou /criar_ficha para criar uma.', ephemeral=True
        )
        return

    cursor.execute("SELECT inventario FROM fichas WHERE id = %s", (ficha_id, ))
    resultado = cursor.fetchone()

    # Se a ficha não tiver movimentos, não há nada para remover
    if not resultado or not resultado[0]:
        await interaction.response.send_message("Não há itens para usar.", ephemeral=True)
        return

    # Passo 2: Converter o JSON armazenado no banco para uma lista de dicionários
    inventario = json.loads(resultado[0])

    # Passo 3: Buscar o movimento com o nome especificado
    item_existente = next(
        (item
         for item in inventario if item["item"].lower() == nome_item.lower()),
        None)
    # Se o movimento não existir, exibe uma mensagem e sai
    if not item_existente:
        await interaction.response.send_message(
            f"O item {nome_item} não foi encontrado", ephemeral=True)
        return

    match = re.search(r'(\d+)\s+usos', item_existente['descricao'])
    if match:
        # Retorna o número e a palavra "usos"
        nova_quantidade = int(match.group(1)) - quantidade
        item_existente['descricao'] = item_existente['descricao'].replace(
            f"{match.group(1)} usos", f"{nova_quantidade} usos")
    else:
        nova_quantidade = item_existente['quantidade'] - quantidade
        inventario[inventario.index(
            item_existente)]['quantidade'] = nova_quantidade

    if nova_quantidade == 0:
        inventario.remove(item_existente)

    # Passo 5: Atualizar a coluna 'movimentos' com a lista de movimentos modificada
    inventario_json = json.dumps(inventario, ensure_ascii=False)
    cursor.execute(
        '''
        UPDATE fichas
        SET inventario = %s
        WHERE id = %s
    ''', (inventario_json, ficha_id))

    # Commit para garantir que as mudanças sejam salvas no banco de dados
    conn.commit()
    cursor.execute("SELECT nome FROM fichas WHERE id = %s", (ficha_id, ))
    nome = cursor.fetchone()[0]
    await interaction.response.send_message(
        f"{nome} usou {quantidade} {nome_item}")

    novacarga = calcular_peso_total(inventario_json)

    cursor.execute(
        f'''
    UPDATE fichas
    SET carga_atual = %s
    WHERE id = %s
    ''', (novacarga, ficha_id))
    conn.commit()

    cursor.execute("SELECT carga_atual FROM fichas WHERE id = %s", (ficha_id, ))
    cargaatual = cursor.fetchone()[0]

    cursor.execute("SELECT carga_max FROM fichas WHERE id = %s", (ficha_id, ))
    cargamax = cursor.fetchone()[0]
    if cargamax == None: cargamax = 0

    if cargaatual > cargamax:
        await interaction.channel.send(f'{nome} está carregando itens demais!')


@bot.tree.command(name="vender_item",
                  description="Vende item da sua ficha ativa")
@app_commands.describe(nome_item="Nome do item a ser usado.", )
async def vender_item(interaction: discord.Interaction,
                      nome_item: str,
                      quantidade: int = 1):
    # Passo 1: Recuperar os movimentos atuais da ficha
    user_id = interaction.user.id
    # Buscar a ficha do jogador pelo ID
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()

    if ficha_ativa:
        ficha_id = ficha_ativa[0]
    else:
        await interaction.response.send_message(
            'Você não possui uma ficha ativa. Use /mudar_ficha para selecionar ou /criar_ficha para criar uma.', ephemeral=True
        )
        return

    cursor.execute("SELECT inventario FROM fichas WHERE id = %s", (ficha_id, ))
    resultado = cursor.fetchone()

    # Se a ficha não tiver movimentos, não há nada para remover
    if not resultado or not resultado[0]:
        await interaction.response.send_message("Não há itens para vender.", ephemeral=True)
        return

    # Passo 2: Converter o JSON armazenado no banco para uma lista de dicionários
    inventario = json.loads(resultado[0])

    # Passo 3: Buscar o movimento com o nome especificado
    item_existente = next(
        (item
         for item in inventario if item["item"].lower() == nome_item.lower()),
        None)

    # Se o movimento não existir, exibe uma mensagem e sai
    if not item_existente:
        await interaction.response.send_message(
            f"O item {nome_item} não foi encontrado", ephemeral=True)
        return

    valor = quantidade * item_existente['valor']

    nova_quantidade = item_existente['quantidade'] - quantidade

    inventario[inventario.index(
        item_existente)]['quantidade'] = nova_quantidade

    if inventario[inventario.index(item_existente)]['quantidade'] == 0:
        inventario.remove(item_existente)

    moedas = next(
        (mov for mov in inventario if mov["nome"].lower() == 'moedas'), None)

    if not moedas:
        quantidade_de_moedas = 0

        moedas = {
            "item": "Moedas",
            "descricao": "Valor Monetário",
            "quantidade": 0,
            "peso": 0,
            "valor": 1
        }

        inventario.append(moedas)
    else:
        quantidade_de_moedas = moedas['quantidade']

    inventario[inventario.index(
        moedas)]['quantidade'] = quantidade_de_moedas + valor

    # Passo 5: Atualizar a coluna 'movimentos' com a lista de movimentos modificada
    inventario_json = json.dumps(inventario, ensure_ascii=False)
    cursor.execute(
        '''
        UPDATE fichas
        SET inventario = %s
        WHERE id = %s
    ''', (inventario_json, ficha_id))

    # Commit para garantir que as mudanças sejam salvas no banco de dados
    conn.commit()
    cursor.execute("SELECT nome FROM fichas WHERE id = %s", (ficha_id, ))
    nome = cursor.fetchone()[0]
    await interaction.response.send_message(
        f"{nome} vendeu {quantidade} {nome_item}, ganhando {valor} moedas")

    novacarga = calcular_peso_total(inventario_json)

    cursor.execute(
        f'''
    UPDATE fichas
    SET carga_atual = %s
    WHERE id = %s
    ''', (novacarga, ficha_id))
    conn.commit()

    cursor.execute("SELECT carga_atual FROM fichas WHERE id = %s", (ficha_id, ))
    cargaatual = cursor.fetchone()[0]

    cursor.execute("SELECT carga_max FROM fichas WHERE id = %s", (ficha_id, ))
    cargamax = cursor.fetchone()[0]
    if cargamax == None: cargamax = 0

    if cargaatual > cargamax:
        await interaction.channel.send(f'{nome} está carregando itens demais!')


@bot.tree.command(name="mostrar_item",
                  description="Mostra um vínculo da sua ficha ativa")
@app_commands.describe(nome_item="Nome do item a ser mostrado.", )
async def mostrar_item(interaction: discord.Interaction, nome_item: str):
    # Passo 1: Recuperar os movimentos atuais da ficha
    user_id = interaction.user.id
    # Buscar a ficha do jogador pelo ID
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()

    if ficha_ativa:
        ficha_id = ficha_ativa[0]
    else:
        await interaction.response.send_message(
            'Você não possui uma ficha ativa. Use /mudar_ficha para selecionar ou /criar_ficha para criar uma.', ephemeral=True
        )
        return

    cursor.execute("SELECT inventario FROM fichas WHERE id = %s", (ficha_id, ))
    resultado = cursor.fetchone()

    # Se a ficha não tiver movimentos, não há nada para remover
    if not resultado or not resultado[0]:
        await interaction.response.send_message("Não há itens para mostrar.", ephemeral=True)
        return

    # Passo 2: Converter o JSON armazenado no banco para uma lista de dicionários
    inventario = json.loads(resultado[0])

    # Passo 3: Buscar o movimento com o nome especificado
    item_existente = next(
        (item
         for item in inventario if item["item"].lower() == nome_item.lower()),
        None)

    # Se o movimento não existir, exibe uma mensagem e sai
    if not item_existente:
        await interaction.response.send_message(
            f"Item '{nome_item}' não encontrado.", ephemeral=True)
        return

    resposta = formatar_dicionarios([item_existente])

    await interaction.response.send_message(resposta)


@bot.tree.command(name="add_vinculo",
                  description="Adiciona um Vínculo à sua ficha ativa")
@app_commands.describe(nome="Nome do vínculo.",
                       descricao="Descrição do vínculo.",
                       valor="Valor do vínculo.")
async def add_vinculo(interaction: discord.Interaction,
                      nome: str,
                      descricao: str = "",
                      valor: int = 1):
    # Recuperar o ID do jogador (supondo que interaction: discord.Interaction.user.id seja o ID do jogador)
    user_id = interaction.user.id

    # Buscar a ficha do jogador pelo ID
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()

    if ficha_ativa:
        ficha_id = ficha_ativa[0]

        cursor.execute("SELECT vinculos FROM fichas WHERE id = %s",
                       (ficha_id, ))
        vinculos = cursor.fetchone()

        if vinculos == (None, ):
            vinculos = [None, None]

        vinculos_json = vinculos[0]

        if vinculos_json == None:
            vinculos_json = "[]"

        vinculos = json.loads(
            vinculos_json)  # Converter de JSON para um objeto Python

        novo_vinculo = {"nome": nome, "descricao": descricao, "valor": valor}

        vinculos.append(novo_vinculo)

        vinculos_json = json.dumps(vinculos, ensure_ascii=False)

        cursor.execute(
            f'''
        UPDATE fichas
        SET vinculos = %s
        WHERE id = %s
        ''', (vinculos_json, ficha_id))
        conn.commit()

        await interaction.response.send_message(
            f'O vínculo com {nome} foi adicionado', ephemeral=True)
    else:
        await interaction.response.send_message(
            'Você não possui uma ficha ativa. Use /mudar_ficha para selecionar ou /criar_ficha para criar uma.', ephemeral=True
        )


@bot.tree.command(name="rem_vinc",
                  description="Exclui um vínculo da sua ficha ativa")
@app_commands.describe(nome_vinculo="Nome do vínculo a ser excluído.", )
async def rem_vinc(interaction: discord.Interaction, nome_vinculo: str):
    # Passo 1: Recuperar os movimentos atuais da ficha
    user_id = interaction.user.id
    # Buscar a ficha do jogador pelo ID
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()

    if ficha_ativa:
        ficha_id = ficha_ativa[0]
    else:
        await interaction.response.send_message(
            'Você não possui uma ficha ativa. Use /mudar_ficha para selecionar ou /criar_ficha para criar uma.', ephemeral=True
        )
        return

    cursor.execute("SELECT vinculos FROM fichas WHERE id = %s", (ficha_id, ))
    resultado = cursor.fetchone()

    # Se a ficha não tiver movimentos, não há nada para remover
    if not resultado or not resultado[0]:
        await interaction.response.send_message("Não há vínculos para remover.", ephemeral=True
                                                )
        return

    # Passo 2: Converter o JSON armazenado no banco para uma lista de dicionários
    vinculos = json.loads(resultado[0])

    # Passo 3: Buscar o movimento com o nome especificado
    vinculo_existente = next(
        (mov
         for mov in vinculos if mov["nome"].lower() == nome_vinculo.lower()),
        None)

    # Se o movimento não existir, exibe uma mensagem e sai
    if not vinculo_existente:
        await interaction.response.send_message(
            f"O vínculo com {nome_vinculo} não foi encontrado", ephemeral=True)
        return

    # Passo 4: Remover o movimento da lista
    vinculos.remove(vinculo_existente)

    # Passo 5: Atualizar a coluna 'movimentos' com a lista de movimentos modificada
    vinculos_json = json.dumps(vinculos, ensure_ascii=False)
    cursor.execute(
        '''
        UPDATE fichas
        SET vinculos = %s
        WHERE id = %s
    ''', (vinculos_json, ficha_id))

    # Commit para garantir que as mudanças sejam salvas no banco de dados
    conn.commit()
    await interaction.response.send_message(
        f"O vínculo com {nome_vinculo} foi excluído", ephemeral=True)


@bot.tree.command(name="mostrar_vinculo",
                  description="Mostra um vínculo da sua ficha ativa")
@app_commands.describe(nome_vinculo="Nome do vínculo a ser mostrado.", )
async def mostrar_vinculo(interaction: discord.Interaction, nome_vinculo: str):
    # Passo 1: Recuperar os movimentos atuais da ficha
    user_id = interaction.user.id
    # Buscar a ficha do jogador pelo ID
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()

    if ficha_ativa:
        ficha_id = ficha_ativa[0]
    else:
        await interaction.response.send_message(
            'Você não possui uma ficha ativa. Use /mudar_ficha para selecionar ou /criar_ficha para criar uma.', ephemeral=True
        )
        return

    cursor.execute("SELECT vinculos FROM fichas WHERE id = %s", (ficha_id, ))
    resultado = cursor.fetchone()

    # Se a ficha não tiver movimentos, não há nada para remover
    if not resultado or not resultado[0]:
        await interaction.response.send_message("Não há vínculos para mostrar.", ephemeral=True
                                                )
        return

    # Passo 2: Converter o JSON armazenado no banco para uma lista de dicionários
    vinculos = json.loads(resultado[0])

    # Passo 3: Buscar o movimento com o nome especificado
    vinculo_existente = next(
        (vin
         for vin in vinculos if vin["nome"].lower() == nome_vinculo.lower()),
        None)

    # Se o movimento não existir, exibe uma mensagem e sai
    if not vinculo_existente:
        await interaction.response.send_message(
            f"Vínculo '{nome_vinculo}' não encontrado.", ephemeral=True)
        return

    resposta = formatar_dicionarios([vinculo_existente])

    await interaction.response.send_message(resposta)


@bot.tree.command(
    name="add_mov_roll",
    description="Adiciona um movimento com rolagem à sua ficha ativa")
@app_commands.describe(nome="Nome do movimento.",
                       gatilho="O que engatilha o movimento.",
                       atributo="Atributo usado na rolagem",
                       mod="Modificador da rolagem",
                       sucesso_total="O que acontece ao rolar 10+",
                       sucesso_parcial="O que acontece ao rolar 7-9",
                       fracasso="O que acontece ao rolar 6-",
                       detalhes="Detalhes adicionais")
async def add_mov_roll(interaction: discord.Interaction,
                       nome: str,
                       gatilho: str,
                       atributo: str = "",
                       mod: int = 0,
                       sucesso_total: str = "",
                       sucesso_parcial: str = "",
                       fracasso: str = "",
                       detalhes: str = "",
                       critico: str = ""):
    # Recuperar o ID do jogador (supondo que interaction: discord.Interaction.user.id seja o ID do jogador)
    user_id = interaction.user.id

    # Buscar a ficha do jogador pelo ID
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()

    if ficha_ativa:
        ficha_id = ficha_ativa[0]

        cursor.execute("SELECT movimentos FROM fichas WHERE id = %s",
                       (ficha_id, ))
        movimentos = cursor.fetchone()

        if movimentos == (None, ):
            movimentos = [None, None]

        movimentos_json = movimentos[0]

        if movimentos_json == None:
            movimentos_json = "[]"

        movimentos = json.loads(
            movimentos_json)  # Converter de JSON para um objeto Python
        if critico == "" or critico == None:
            critico = "**Crítico!**\n" + sucesso_total

        novo_movimento = {
            "nome": nome,
            "gatilho": gatilho.replace("  ","\n"),
            "atributo": atributo,
            "mod": mod,
            "sucesso_total": sucesso_total.replace("  ","\n"),
            "sucesso_parcial": sucesso_parcial.replace("  ","\n"),
            "fracasso": fracasso.replace("  ","\n"),
            "detalhes": detalhes.replace("  ","\n"),
            "critico": critico.replace("  ","\n")
        }

        movimento_existente = next(
            (mov for mov in movimentos if mov["nome"].lower() == nome.lower()),
            None)

        if movimento_existente:
            # Passo 3: Se o movimento existir, substituímos o movimento
            movimentos.remove(movimento_existente)

        movimentos.append(novo_movimento)

        movimentos_json = json.dumps(movimentos, ensure_ascii=False)

        cursor.execute(
            f'''
        UPDATE fichas
        SET movimentos = %s
        WHERE id = %s
        ''', (movimentos_json, ficha_id))
        conn.commit()

        await interaction.response.send_message(
            f'O movimento {nome} foi adicionado', ephemeral=True)
    else:
        await interaction.response.send_message(
            'Você não possui uma ficha ativa. Use /mudar_ficha para selecionar ou /criar_ficha para criar uma.', ephemeral=True
        )


@bot.tree.command(
    name="add_mov_tex",
    description="Adiciona um movimento descritivo à sua ficha ativa")
@app_commands.describe(nome="Nome do movimento.",
                       gatilho="O que engatilha o movimento.",
                       descricao="Descrição do movimento")
async def add_mov_tex(interaction: discord.Interaction,
                      nome: str,
                      gatilho: str = "",
                      descricao: str = ""):
    # Recuperar o ID do jogador (supondo que interaction: discord.Interaction.user.id seja o ID do jogador)
    user_id = interaction.user.id

    # Buscar a ficha do jogador pelo ID
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()

    if ficha_ativa:
        ficha_id = ficha_ativa[0]

        cursor.execute("SELECT movimentos FROM fichas WHERE id = %s",
                       (ficha_id, ))
        movimentos = cursor.fetchone()

        if movimentos == (None, ):
            movimentos = [None, None]

        movimentos_json = movimentos[0]

        if movimentos_json == None:
            movimentos_json = "[]"

        movimentos = json.loads(
            movimentos_json)  # Converter de JSON para um objeto Python

        novo_movimento = {
            "nome": nome.replace("  ","\n"),
            "gatilho": gatilho.replace("  ","\n"),
            "descricao": descricao.replace("  ","\n")
        }
        movimento_existente = next(
            (mov for mov in movimentos if mov["nome"].lower() == nome.lower()),
            None)

        if movimento_existente:
            # Passo 3: Se o movimento existir, substituímos o movimento
            movimentos.remove(movimento_existente)

        movimentos.append(novo_movimento)

        movimentos_json = json.dumps(movimentos, ensure_ascii=False)

        cursor.execute(
            f'''
        UPDATE fichas
        SET movimentos = %s
        WHERE id = %s
        ''', (movimentos_json, ficha_id))
        conn.commit()

        await interaction.response.send_message(
            f'O movimento {nome} foi adicionado', ephemeral=True)
    else:
        await interaction.response.send_message(
            'Você não possui uma ficha ativa. Use /mudar_ficha para selecionar ou /criar_ficha para criar uma.', ephemeral=True
        )


@bot.tree.command(name="mostrar_mov",
                  description="Mostra um movimento da sua ficha ativa")
@app_commands.describe(nome_movimento="Nome do movimento a ser mostrado.", )
async def mostrar_mov(interaction: discord.Interaction, nome_movimento: str):
    # Passo 1: Recuperar os movimentos atuais da ficha
    user_id = interaction.user.id
    # Buscar a ficha do jogador pelo ID
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()

    if ficha_ativa:
        ficha_id = ficha_ativa[0]
    else:
        await interaction.response.send_message(
            'Você não possui uma ficha ativa. Use /mudar_ficha para selecionar ou /criar_ficha para criar uma.', ephemeral=True
        )
        return

    cursor.execute("SELECT movimentos FROM fichas WHERE id = %s", (ficha_id, ))
    resultado = cursor.fetchone()

    # Se a ficha não tiver movimentos, não há nada para remover
    if not resultado or not resultado[0]:
        await interaction.response.send_message(
            "Não há movimentos para mostrar.", ephemeral=True)
        return

    # Passo 2: Converter o JSON armazenado no banco para uma lista de dicionários
    movimentos = json.loads(resultado[0])

    # Passo 3: Buscar o movimento com o nome especificado
    movimento_existente = next(
        (mov for mov in movimentos
         if mov["nome"].lower() == nome_movimento.lower()), None)

    # Se o movimento não existir, exibe uma mensagem e sai
    if not movimento_existente:
        await interaction.response.send_message(
            f"Movimento '{nome_movimento}' não encontrado.", ephemeral=True)
        return

    resposta = formatar_dicionarios([movimento_existente])

    await interaction.response.send_message(resposta)


@bot.tree.command(name="rem_mov",
                  description="Exclui um movimento da sua ficha ativa")
@app_commands.describe(nome_movimento="Nome do movimento a ser excluído.", )
async def rem_mov(interaction: discord.Interaction, nome_movimento: str):
    # Passo 1: Recuperar os movimentos atuais da ficha
    user_id = interaction.user.id
    # Buscar a ficha do jogador pelo ID
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()

    if ficha_ativa:
        ficha_id = ficha_ativa[0]
    else:
        await interaction.response.send_message(
            'Você não possui uma ficha ativa. Use /mudar_ficha para selecionar ou /criar_ficha para criar uma.', ephemeral=True
        )
        return

    cursor.execute("SELECT movimentos FROM fichas WHERE id = %s", (ficha_id, ))
    resultado = cursor.fetchone()

    # Se a ficha não tiver movimentos, não há nada para remover
    if not resultado or not resultado[0]:
        await interaction.response.send_message(
            "Não há movimentos para remover.", ephemeral=True)
        return

    # Passo 2: Converter o JSON armazenado no banco para uma lista de dicionários
    movimentos = json.loads(resultado[0])

    # Passo 3: Buscar o movimento com o nome especificado
    movimento_existente = next(
        (mov for mov in movimentos
         if mov["nome"].lower() == nome_movimento.lower()), None)

    # Se o movimento não existir, exibe uma mensagem e sai
    if not movimento_existente:
        await interaction.response.send_message(
            f"Movimento '{nome_movimento}' não encontrado.", ephemeral=True)
        return

    # Passo 4: Remover o movimento da lista
    movimentos.remove(movimento_existente)

    # Passo 5: Atualizar a coluna 'movimentos' com a lista de movimentos modificada
    movimentos_json = json.dumps(movimentos, ensure_ascii=False)
    cursor.execute(
        '''
        UPDATE fichas
        SET movimentos = %s
        WHERE id = %s
    ''', (movimentos_json, ficha_id))

    # Commit para garantir que as mudanças sejam salvas no banco de dados
    conn.commit()
    await interaction.response.send_message(
        f"O movimento {nome_movimento} foi excluído", ephemeral=True)


@bot.tree.command(
    name="mostrar_ficha",
    description="Mostra todos os dados da ficha ativa do jogador.")
async def mostrar_ficha(interaction: discord.Interaction):
    # Obter o ID do usuário
    user_id = interaction.user.id

    # Conectar ao banco de dados

    # Consultar a ficha ativa do usuário
    cursor.execute(
        '''SELECT * FROM fichas f
                    JOIN fichas_ativas fa ON f.id = fa.ficha_ativa_id
                    WHERE fa.user_id = %s''', (user_id, ))
    ficha = cursor.fetchone()

    if ficha is None:
        resposta = "Você não tem uma ficha ativa no momento."
    else:
        # Extrair dados da ficha
        colunas = [desc[0] for desc in cursor.description
                   ]  # Obter os nomes das colunas
        dados_ficha = dict(zip(
            colunas, ficha))  # Combinar nomes das colunas com os valores

        dados_ficha.pop('user_id', None)
        dados_ficha.pop('ficha_ativa_id', None)

        # Formatar os dados da ficha em um texto
        resposta = "**Dados da sua ficha ativa:**\n\n"
        for key, value in dados_ficha.items():
            if key == 'inventario':
                resposta += "\n**Inventário**\n" + formatar_inventario(
                    value) + "\n"
            elif key == 'movimentos':
                resposta += "\n**Movimentos**\n" + formatar_movimentos(
                    value) + "\n"
            elif key == 'vinculos':
                resposta += "\n**Vínculos**\n" + formatar_vinculos(
                    value) + "\n"
            else:
                resposta += f"**{key.replace('_', ' ').capitalize()}:** {value}\n"

    # Enviar a resposta
    if len(resposta) > 2000:
        await interaction.response.defer()
        partes = [resposta[i:i + 2000] for i in range(0, len(resposta), 2000)]
        for parte in partes:
            await interaction.followup.send(parte)
    else:
        await interaction.response.send_message(resposta)


@bot.tree.command(name="exportar_ficha",
                  description="Exporta uma ficha como um arquivo json")
@app_commands.describe(ficha_id="ID da ficha a ser exportada", )
async def exportar_ficha(interaction: discord.Interaction,
                         ficha_id: int = None):

    if ficha_id == None:
        user_id = interaction.user.id
        cursor.execute(
            '''
        SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
        ''', (user_id, ))
        ficha_ativa = cursor.fetchone()

        if ficha_ativa:
            ficha_id = ficha_ativa[0]
        else:
            await interaction.response.send_message(
                'Você não possui uma ficha ativa e nem especificou o id da ficha a ser exportada', ephemeral=True
            )
            return

    cursor.execute(
        '''
            SELECT * FROM fichas WHERE id = %s
        ''', (ficha_id, ))

    ficha = cursor.fetchone()

    # Verifica se a ficha foi encontrada
    if ficha:
        # Cria um dicionário com os dados da ficha
        ficha_dict = {
            'nome': ficha[2],
            'aparencia': ficha[3],
            'classe': ficha[4],
            'xp': ficha[5],
            'nivel': ficha[6],
            'alinhamento': ficha[7],
            'alinhamento_detalhe': ficha[8],
            'raca': ficha[9],
            'raca_texto': ficha[10],
            'dado_dano': ficha[11],
            'hp_atual': ficha[12],
            'hp_max': ficha[13],
            'armadura': ficha[14],
            'str': ficha[15],
            'des': ficha[16],
            'con': ficha[17],
            'int': ficha[18],
            'sab': ficha[19],
            'car': ficha[20],
            'carga_max': ficha[21],
            'carga_atual': ficha[22],
            'inventario': ficha[23],
            'vinculos': ficha[24],
            'movimentos': ficha[25],
            'sorte': ficha[26],
            'debilidades': ficha[27],
            'notas': ficha[28]
        }

        # Converte o dicionário para JSON
        ficha_json = json.dumps(ficha_dict, ensure_ascii=False)

        # Salva o JSON em um arquivo
        with open(f'ficha_{ficha[2]}.json', 'w', encoding='utf-8') as f:
            f.write(ficha_json)

        # Envia o arquivo JSON para o usuário
        await interaction.response.send_message(
            f"A ficha {ficha[2]} foi exportada com sucesso! Aqui está o arquivo.",
            file=discord.File(f'ficha_{ficha[2]}.json', ephemeral=True))

        if os.path.exists(f'ficha_{ficha[2]}.json'):
            os.remove(f'ficha_{ficha[2]}.json')
            print(f"Arquivo {f'ficha_{ficha[2]}.json'} excluído com sucesso.")
        else:
            print(f"O arquivo {f'ficha_{ficha[2]}.json'} não foi encontrado.")

        # Fecha a conexão com o banco de dados

    else:
        # Caso a ficha não exista
        await interaction.response.send_message(
            f"Nenhuma ficha encontrada com o ID {ficha_id}.", ephemeral=True)


@bot.tree.command(
    name="deletar_ficha",
    description="Deleta uma ficha do banco de dados pelo ID da ficha")
async def deletar_ficha(interaction: discord.Interaction, ficha_id: int):
    try:

        user_id = interaction.user.id

        # Buscar a ficha do jogador pelo ID
        cursor.execute(
            '''
        SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
        ''', (user_id, ))
        ficha_ativa = cursor.fetchone()
        if ficha_ativa:
            ficha_ativa_id = ficha_ativa[0]
        else:
            ficha_ativa_id = -1
        
        if ficha_id == ficha_ativa_id:
            await interaction.response.send_message(
                f"Você não pode deletar sua ficha ativa! Crie outra e ative ela antes de deletar esta!", ephemeral=True)
            return

        # Verificar se a ficha com o ID fornecido existe
        cursor.execute('SELECT * FROM fichas WHERE id = %s', (ficha_id, ))
        ficha = cursor.fetchone()

        if ficha is None:
            await interaction.response.send_message(
                f"Ficha com ID {ficha_id} não encontrada.", ephemeral=True)
            return

        # Deletar a ficha
        cursor.execute('DELETE FROM fichas WHERE id = %s', (ficha_id, ))
        conn.commit()

        # Mensagem de confirmação
        await interaction.response.send_message(
            f"Ficha com ID {ficha_id} foi deletada com sucesso!", ephemeral=True)
    except Exception as e:
        # Mensagem de erro
        await interaction.response.send_message(
            f"Ocorreu um erro ao tentar deletar a ficha: {e}", ephemeral=True)


@bot.tree.command(name="importar_ficha",
                  description="Importa uma ficha a partir de um arquivo json")
async def importar_ficha(interaction: discord.Interaction,
                         json_ficha: discord.Attachment):
    # Abrir o arquivo JSON enviado pelo usuário
    ficha_json = json.loads(await json_ficha.read())

    if "characterName" in ficha_json:
        ficha_json = formatar_json(ficha_json)

    # A partir do JSON, vamos preencher o dicionário ficha_dict com os dados
    ficha_dict = {
        'nome': ficha_json.get('nome'),
        'aparencia': ficha_json.get('aparencia'),
        'classe': ficha_json.get('classe'),
        'xp': ficha_json.get('xp'),
        'nivel': ficha_json.get('nivel'),
        'alinhamento': ficha_json.get('alinhamento'),
        'alinhamento_detalhe': ficha_json.get('alinhamento_detalhe'),
        'raca': ficha_json.get('raca'),
        'raca_texto': ficha_json.get('raca_texto'),
        'dado_dano': ficha_json.get('dado_dano'),
        'hp_atual': ficha_json.get('hp_atual'),
        'hp_max': ficha_json.get('hp_max'),
        'armadura': ficha_json.get('armadura'),
        'str': ficha_json.get('str'),
        'des': ficha_json.get('des'),
        'con': ficha_json.get('con'),
        'int': ficha_json.get('int'),
        'sab': ficha_json.get('sab'),
        'car': ficha_json.get('car'),
        'carga_max': ficha_json.get('carga_max'),
        'carga_atual': ficha_json.get('carga_atual'),
        'inventario': ficha_json.get('inventario', []),
        'vinculos': ficha_json.get('vinculos', []),
        'movimentos': ficha_json.get('movimentos', []),
        'sorte': ficha_json.get('sorte'),
        'debilidades': ficha_json.get('debilidades'),
        'notas': ficha_json.get('notas')
    }

    # Vamos usar o user_id para saber qual ficha editar, você pode pegar isso a partir de interaction.user.id
    user_id = interaction.user.id
    cursor.execute(
        '''
    INSERT INTO fichas (user_id, nome, aparencia, classe, xp, nivel, alinhamento, 
            alinhamento_detalhe, raca, raca_texto, dado_dano, hp_atual, 
            hp_max, armadura, str, des, con, int, sab, car, 
            carga_max, carga_atual, inventario, vinculos, movimentos, 
            sorte, debilidades, notas)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id
    ''', (user_id, ficha_dict['nome'], ficha_dict['aparencia'],
          ficha_dict['classe'], ficha_dict['xp'], ficha_dict['nivel'],
          ficha_dict['alinhamento'], ficha_dict['alinhamento_detalhe'],
          ficha_dict['raca'], ficha_dict['raca_texto'],
          ficha_dict['dado_dano'], ficha_dict['hp_atual'],
          ficha_dict['hp_max'], ficha_dict['armadura'], ficha_dict['str'],
          ficha_dict['des'], ficha_dict['con'], ficha_dict['int'],
          ficha_dict['sab'], ficha_dict['car'], ficha_dict['carga_max'],
          ficha_dict['carga_atual'], ficha_dict['inventario'],
          ficha_dict['vinculos'], ficha_dict['movimentos'],
          ficha_dict['sorte'], ficha_dict['debilidades'], ficha_dict['notas']))
    conn.commit()

    ficha_id = cursor.fetchone()[0]
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ativo = cursor.fetchone()


    if ativo is None:
        cursor.execute(
            '''
        INSERT INTO fichas_ativas (user_id, ficha_ativa_id)
        VALUES (%s, %s)
        ''', (user_id, ficha_id))
        conn.commit()
        await interaction.response.send_message(
            f'Ficha "{ficha_dict["nome"]}" importada com sucesso e marcada como ativa!', ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f'Ficha "{ficha_dict["nome"]}" importada com sucesso!')

    # Mensagem de confirmação
    await interaction.response.send_message(
        f"Ficha importada com sucesso para {interaction.user.mention}!", ephemeral=True)


@bot.tree.command(name="roll", description="Simule uma rolagem de dados")
@app_commands.describe(
    expressao="Expressão da rolagem de dados (ex: 2d6+2, 5d4-1, 1d20*4)")
async def roll(interaction: discord.Interaction, expressao: str = "2d6"):
    try:
        # Regex para capturar a expressão do dado
        match = re.fullmatch(r'(\d*)d(\d+)([+\-*/]\d+)?', expressao)
        if not match:
            await interaction.response.send_message(
                "Expressão inválida! Use o formato XdY+Z.", ephemeral=True)
            return

        # Extrair partes da expressão
        n_dados = int(match.group(1)) if match.group(
            1) else 1  # Número de dados, default 1
        tipo_dado = int(match.group(2))  # Tipo de dado (ex: 6 para d6)
        modificador = match.group(3)  # Modificador aritmético (ex: +2, -1, *4)

        # Realizar as rolagens
        rolagens = [random.randint(1, tipo_dado) for _ in range(n_dados)]
        soma_rolagens = sum(rolagens)

        # Aplicar o modificador, se existir
        resultado_final = soma_rolagens
        if modificador:
            resultado_final = eval(f"{soma_rolagens}{modificador}")

        # Construir a mensagem de resultado
        rolagens_str = ' + '.join(map(str, rolagens))
        if modificador:
            resposta = f"**Rolagem: {expressao}**\nRolagens: {rolagens_str} = {soma_rolagens}\nModificador: {modificador}\n**Resultado Final: {resultado_final}**"
        else:
            resposta = f"**Rolagem: {expressao}**\nRolagens: {rolagens_str} = {resultado_final}"

        await interaction.response.send_message(resposta)

    except Exception as e:
        await interaction.response.send_message(
            "Ocorreu um erro ao processar a rolagem. Verifique a expressão e tente novamente.", ephemeral=True
        )


@bot.tree.command(
    name="atributo",
    description="Simule uma rolagem de dados usando um atributo só")
@app_commands.describe(atributo="Qual atributo usar",
                       modificador="Modificador na rolagem")
@app_commands.choices(atributo=[
    app_commands.Choice(name="Força", value="str"),
    app_commands.Choice(name="Destreza", value="des"),
    app_commands.Choice(name="Constituição", value="con"),
    app_commands.Choice(name="Inteligência", value="int"),
    app_commands.Choice(name="Sabedoria", value="sab"),
    app_commands.Choice(name="Carisma", value="car"),
])
async def atributo(interaction: discord.Interaction,
                   atributo: str,
                   modificador: int = 0):

    user_id = interaction.user.id

    # Buscar a ficha do jogador pelo ID
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()

    if ficha_ativa:
        ficha_id = ficha_ativa[0]
    else:
        await interaction.response.send_message(
            'Você não possui uma ficha ativa. Use /mudar_ficha para selecionar ou /criar_ficha para criar uma.', ephemeral=True
        )
        return

    n_dados = 2
    tipo_dado = 6  # Tipo de dado (ex: 6 para d6)
    mod = modificador  # Modificador aritmético (ex: +2, -1, *4)

    if atributo in ["str", "des", "con", "int", "sab", "car"]:
        cursor.execute(f"SELECT {atributo} FROM fichas WHERE id = %s",
                       (ficha_id, ))
        atributomod = cursor.fetchone()[0]
        atributomod = obter_modificador(atributomod)
    else:
        atributomod = 0
    if atributo:
        cursor.execute(f"SELECT debilidades FROM fichas WHERE id = %s",
                    (ficha_id, ))
        debilidades = cursor.fetchone()[0]
        if debilidades == None:
            debilidades = ""
        debilidades = debilidades.lower()
        if atributo == "str" and "fraco" in debilidades:
            mod = mod - 1
        elif atributo == "des" and "trêmulo" in debilidades:
            mod = mod - 1
        elif atributo == "con" and "doente" in debilidades:
            mod = mod - 1
        elif atributo == "int" and "atordoado" in debilidades:
            mod = mod - 1
        elif atributo == "sab" and "confuso" in debilidades:
            mod = mod - 1
        elif atributo == "car" and "marcado" in debilidades:
            mod = mod - 1

    modificador = mod

    # Realizar as rolagens
    rolagens = [random.randint(1, tipo_dado) for _ in range(n_dados)]
    soma_rolagens = sum(rolagens)

    # Aplicar o modificador, se existir
    resultado_final = soma_rolagens
    if modificador:
        resultado_final = eval(f"{soma_rolagens}{modificador}")

    # Construir a mensagem de resultado
    rolagens_str = ' + '.join(map(str, rolagens))
    if modificador:
        resposta = f"**Rolagem: 2d6+{atributo.upper()} ({atributomod})**\nRolagens: {rolagens_str} + {atributomod} = {soma_rolagens}\nModificador: {modificador}\n**Resultado Final: {resultado_final}**"
    else:
        resposta = f"**Rolagem: 2d6+{atributo.upper()} ({atributomod})**\nRolagens: {rolagens_str} + {atributomod} = {resultado_final}"

    await interaction.response.send_message(resposta)


@bot.tree.command(
    name="debilidade",
    description="Adiciona ou remove uma debilidade da sua ficha ativa")
@app_commands.describe(debilidade="Nome da debilidade", )
@app_commands.choices(debilidade=[
    app_commands.Choice(name="Fraco (FOR)", value="fraco"),
    app_commands.Choice(name="Trêmulo (DES)", value="trêmulo"),
    app_commands.Choice(name="Doente (CON)", value="doente"),
    app_commands.Choice(name="Atordoado (INT)", value="atordoado"),
    app_commands.Choice(name="Confuso (SAB)", value="confuso"),
    app_commands.Choice(name="Marcado (CAR)", value="marcado"),
])
async def debilidade(interaction: discord.Interaction, debilidade: str):
    # Recuperar o ID do jogador (supondo que interaction: discord.Interaction.user.id seja o ID do jogador)
    user_id = interaction.user.id

    # Buscar a ficha do jogador pelo ID
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()

    if ficha_ativa:
        ficha_id = ficha_ativa[0]

        cursor.execute("SELECT debilidades FROM fichas WHERE id = %s",
                       (ficha_id, ))
        debilidades = cursor.fetchone()[0]

        if debilidades == None:
            debilidades = ""

        if debilidade not in debilidades:
            debilidades = debilidades + " " + debilidade
            await interaction.response.send_message(
                f'A debilidade {debilidade.capitalize()} foi adicionada.')
        else:
            debilidades = debilidades.replace(debilidade, "")
            await interaction.response.send_message(
                f'A debilidade {debilidade.capitalize()} foi removida.')

        cursor.execute(
            f'''
        UPDATE fichas
        SET debilidades = %s
        WHERE id = %s
        ''', (debilidades, ficha_id))
        conn.commit()

    else:
        await interaction.response.send_message(
            'Você não possui uma ficha ativa. Use /mudar_ficha para selecionar ou /criar_ficha para criar uma.', ephemeral=True
        )


@bot.tree.command(name="sorte",
                  description="Usa um ponto de sorte da sua ficha ativa")
async def sorte(interaction: discord.Interaction):
    # Recuperar o ID do jogador (supondo que interaction: discord.Interaction.user.id seja o ID do jogador)
    user_id = interaction.user.id

    # Buscar a ficha do jogador pelo ID
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()
    if ficha_ativa:
        ficha_id = ficha_ativa[0]

        cursor.execute("SELECT nome FROM fichas WHERE id = %s", (ficha_id, ))
        nome = cursor.fetchone()[0]

        cursor.execute("SELECT sorte FROM fichas WHERE id = %s", (ficha_id, ))
        sorte = cursor.fetchone()[0]

        if sorte == None:
            sorte = 0

        if sorte > 0:
            sorte = sorte - 1
            await interaction.response.send_message(
                f'{nome} usou um ponto de Sorte!\nSó lhe restam {sorte} pontos de Sorte agora.'
            )
        else:
            await interaction.response.send_message(
                f'{nome} não tem mais Sorte pra gastar...')

        cursor.execute(
            f'''
        UPDATE fichas
        SET sorte = %s
        WHERE id = %s
        ''', (sorte, ficha_id))
        conn.commit()

    else:
        await interaction.response.send_message(
            'Você não possui uma ficha ativa. Use /mudar_ficha para selecionar ou /criar_ficha para criar uma.', ephemeral=True
        )


@bot.tree.command(name="db", description="Rola o seu dano básico")
@app_commands.describe(modificador_extra="Algum modificador adicional")
async def db(interaction: discord.Interaction, modificador_extra: int = 0):
    try:
        user_id = interaction.user.id

        cursor.execute(
            f'''
        SELECT f.dado_dano
        FROM fichas f
        JOIN fichas_ativas fa ON f.id = fa.ficha_ativa_id
        WHERE fa.user_id = %s
        ''', (user_id, ))
        ficha = cursor.fetchone()

        if ficha:
            valor = ficha[0]
        else:
            await interaction.response.send_message(
                'Você não possui uma ficha ativa ou nenhuma ficha está definida como ativa.', ephemeral=True
            )
        if valor == None: valor = ""
        # Regex para capturar a expressão do dado
        match = re.fullmatch(r'(\d*)d(\d+)([+\-*/]\d+)?', valor)
        if not match:
            await interaction.response.send_message(
                "Expressão inválida! Use o formato XdY+Z.", ephemeral=True)
            return

        # Extrair partes da expressão
        n_dados = int(match.group(1)) if match.group(
            1) else 1  # Número de dados, default 1
        tipo_dado = int(match.group(2))  # Tipo de dado (ex: 6 para d6)
        modificador = match.group(3)  # Modificador aritmético (ex: +2, -1, *4)
        if modificador == None: modificador = 0
        # Realizar as rolagens
        rolagens = [random.randint(1, tipo_dado) for _ in range(n_dados)]
        soma_rolagens = sum(rolagens)

        # Aplicar o modificador, se existir
        resultado_final = soma_rolagens
        if modificador:
            resultado_final = eval(f"{soma_rolagens}{modificador}")
        if modificador_extra:
            resultado_final = resultado_final + modificador_extra

        # Construir a mensagem de resultado
        rolagens_str = ' + '.join(map(str, rolagens))
        resposta = f"**Rolagem: {valor}**\nRolagens: {rolagens_str} = {soma_rolagens}\nModificador: {modificador}+{modificador_extra}\n**Resultado Final: {resultado_final}**"

        await interaction.response.send_message(resposta)

    except Exception as e:
        await interaction.response.send_message(
            "Ocorreu um erro ao processar a rolagem. Verifique a expressão e tente novamente.", ephemeral=True
        )


@bot.tree.command(name="mov",description="Use um movimento da sua ficha ativa")
@app_commands.describe(movimento="O nome exato do movimento", modificador ="Modificador na rolagem")
async def mov(interaction: discord.Interaction, movimento: str, modificador: int = 0):
    user_id = interaction.user.id
    # Buscar a ficha do jogador pelo ID
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()
    if ficha_ativa:
        ficha_id = ficha_ativa[0]

        cursor.execute("SELECT movimentos FROM fichas WHERE id = %s",
                       (ficha_id, ))
        movimentos = cursor.fetchone()

        if movimentos == (None, ):
            movimentos = [None, None]

        movimentos_json = movimentos[0]

        if movimentos_json == None:
            movimentos_json = "[]"

        movimentos = json.loads(movimentos_json)

        movimento_especifico = next(
            (x for x in movimentos if x["nome"].lower() == movimento.lower()),
            None)
        movimento = movimento_especifico
        if "atributo" in movimento_especifico:
            atributo = movimento_especifico['atributo']
            if atributo in ["str", "des", "con", "int", "sab", "car"]:
                cursor.execute(f"SELECT {atributo} FROM fichas WHERE id = %s",
                               (ficha_id, ))
                atributo = cursor.fetchone()[0]
                atributo = obter_modificador(atributo)
            else:
                atributo = 0
            mod = movimento_especifico['mod']
            if atributo:
                cursor.execute(f"SELECT debilidades FROM fichas WHERE id = %s",
                            (ficha_id, ))
                debilidades = cursor.fetchone()[0]
                if debilidades == None:
                    debilidades = ""
                debilidades = debilidades.lower()
                if movimento['atributo'] == "str" and "fraco" in debilidades:
                    mod = mod - 1
                elif movimento['atributo'] == "des" and "trêmulo" in debilidades:
                    mod = mod - 1
                elif movimento['atributo'] == "con" and "doente" in debilidades:
                    mod = mod - 1
                elif movimento['atributo'] == "int" and "atordoado" in debilidades:
                    mod = mod - 1
                elif movimento['atributo'] == "sab" and "confuso" in debilidades:
                    mod = mod - 1
                elif movimento['atributo'] == "car" and "marcado" in debilidades:
                    mod = mod - 1

            n_dados = 2  # Número de dados, default 1
            tipo_dado = 6  # Tipo de dado (ex: 6 para d6)
            modificador = modificador + mod + atributo  # Modificador aritmético (ex: +2, -1, *4)

            # Realizar as rolagens
            rolagens = [random.randint(1, tipo_dado) for _ in range(n_dados)]
            soma_rolagens = sum(rolagens)

            # Aplicar o modificador, se existir
            resultado_final = soma_rolagens
            if modificador:
                resultado_final = eval(f"{soma_rolagens}+{modificador}")

            # Construir a mensagem de resultado

            cursor.execute("SELECT nome FROM fichas WHERE id = %s",
                           (ficha_id, ))
            nome = cursor.fetchone()[0]

            resposta = f"**{nome}** usou o movimento **{movimento_especifico['nome']}**:\n**{movimento_especifico['gatilho']}**\n"

            rolagens_str = ' + '.join(map(str, rolagens))
            if modificador and atributo:
                resposta += f"**Rolagem: 2d6 **\nRolagens: {rolagens_str} = {soma_rolagens}\nModificadores: {movimento_especifico['atributo']}: {atributo} + Modificador: {mod}\n**Resultado Final: {resultado_final}**"
            elif modificador:
                resposta += f"**Rolagem: 2d6 **\nRolagens: {rolagens_str} = {soma_rolagens}\nModificador: {mod}\n**Resultado Final: {resultado_final}**"
            elif atributo:
                resposta += f"**Rolagem: 2d6 **\nRolagens: {rolagens_str} = {soma_rolagens}\nModificador: {movimento_especifico['atributo']}: {atributo}\n**Resultado Final: {resultado_final}**"
            else:
                resposta += f"**Rolagem: 2d6 **\nRolagens: {rolagens_str} = {resultado_final}"

            if resultado_final <= 6:
                resposta += "\nFracasso!\n" + movimento_especifico['fracasso']
            elif resultado_final <= 9:
                resposta += "\nSucesso Parcial!\n" + movimento_especifico[
                    'sucesso_parcial']
            elif resultado_final <= 11:
                resposta += "\nSucesso Total!\n" + movimento_especifico[
                    'sucesso_total']
            elif resultado_final >= 12:
                resposta += "\nCrítico!\n" + movimento_especifico['critico']
            if movimento_especifico['detalhes'] != "":
                resposta += f"\n{movimento_especifico['detalhes']}"
        else:
            cursor.execute("SELECT nome FROM fichas WHERE id = %s",
                           (ficha_id, ))
            nome = cursor.fetchone()[0]
            resposta = f"**{nome}** usou o movimento **{movimento_especifico['nome']}**:\n{movimento_especifico['gatilho']}\n{movimento_especifico['descricao']}"

        await interaction.response.send_message(resposta)

        if resultado_final <= 6:
            cursor.execute("SELECT xp FROM fichas WHERE id = %s", (ficha_id, ))
            xp = cursor.fetchone()[0]

            if xp == None:
                xp = 0

            xp = int(xp) + 1

            cursor.execute(
            f'''
            UPDATE fichas
            SET xp = %s
            WHERE id = %s
            ''', (xp, ficha_id))

            cursor.execute("SELECT nivel FROM fichas WHERE id = %s",
                           (ficha_id, ))
            nivel = cursor.fetchone()

            cursor.execute("SELECT nome FROM fichas WHERE id = %s",
                           (ficha_id, ))
            nome = cursor.fetchone()[0]

            if nivel == None or nivel[0] == None:
                nivel = 0

            if xp >= nivel + 7:
                await interaction.channel.send(
                    f'{nome} Já pode subir de nível!')

            cursor.execute(
                f'''
            UPDATE fichas
            SET xp = %s
            WHERE id = %s
            ''', (xp, ficha_id))
            conn.commit()

    else:
        await interaction.response.send_message(
            'Você não tem fichas criadas. Use /criar_ficha para começar.', ephemeral=True)


@bot.tree.command(name="calamidade",
                  description="Role na tabela de Calamidade")
async def calamidade(interaction: discord.Interaction):

    user_id = interaction.user.id

    # Buscar a ficha do jogador pelo ID
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()

    if ficha_ativa:
        ficha_id = ficha_ativa[0]
    else:
        await interaction.response.send_message(
            'Você não tem fichas criadas. Use /criar_ficha para começar.', ephemeral=True)
        return
    # Extrair partes da expressão
    n_dados = 2  # Número de dados, default 1
    tipo_dado = 6  # Tipo de dado (ex: 6 para d6)

    # Realizar as rolagens
    rolagens = [random.randint(1, tipo_dado) for _ in range(n_dados)]
    soma_rolagens = sum(rolagens)

    # Aplicar o modificador, se existir
    resultado_final = soma_rolagens

    if resultado_final == 2:
        resultado = "Dê seu Último Suspiro"
    if resultado_final == 3:
        resultado = "Seu pior pesadelo surge para te levar"
    if resultado_final == 4:
        resultado = "Tudo dá errado e é culpa sua"
    if resultado_final == 5:
        resultado = "Uma decisão terrível precisa ser tomad"
    if resultado_final == 6:
        resultado = "As luzes se apagam"
    if resultado_final == 7:
        resultado = "Você perde algo importante"
    if resultado_final == 8:
        resultado = "Uma nova ameaça aparece"
    if resultado_final == 9:
        resultado = "Você é marcado com um destino sombrio"
    if resultado_final == 10:
        resultado = "Tudo ao seu redor cai em ruína"
    if resultado_final == 11:
        resultado = "Você é traído por quem menos esperava"
    if resultado_final == 12:
        resultado = "Uma força absoluta trará o Fim"

    cursor.execute("SELECT nome FROM fichas WHERE id = %s", (ficha_id, ))
    nome = cursor.fetchone()[0]

    # Construir a mensagem de resultado
    rolagens_str = ' + '.join(map(str, rolagens))

    resposta = f"**Uma Calamidade cai sobre {nome}!**\nRolagens: {rolagens_str} = {soma_rolagens}\nResultado Final: **{resultado_final}** - **{resultado}**"

    cursor.execute("SELECT sorte FROM fichas WHERE id = %s", (ficha_id, ))
    sorte = cursor.fetchone()[0]

    if sorte == None:
        sorte = 0

    sorte = sorte + 1

    cursor.execute(
        f'''
    UPDATE fichas
    SET sorte = %s
    WHERE id = %s
    ''', (sorte, ficha_id))
    conn.commit()

    await interaction.response.send_message(resposta)


@bot.tree.command(name="mb", description="Use um movimento básico")
@app_commands.describe(movimento="O nome exato do movimento", modificador = "Modificador da rolagem")
async def mb(interaction: discord.Interaction, movimento: str, modificador: int = 0):
    user_id = interaction.user.id
    # Buscar a ficha do jogador pelo ID
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()
    try:
        movimento = movimentos_basicos[movimento.lower()]
    except KeyError:
        await interaction.response.send_message(
            'Esse movimento básico não existe! Use /help_mb para ver todos os movimentos básicos disponíveis.', ephemeral=True
        )
        return
    if ficha_ativa:
        ficha_id = ficha_ativa[0]

        if "atributo" in movimento:
            atributo = movimento['atributo']
            if atributo in ["str", "des", "con", "int", "sab", "car"]:
                cursor.execute(f"SELECT {atributo} FROM fichas WHERE id = %s",
                               (ficha_id, ))
                atributo = cursor.fetchone()[0]
                atributo = obter_modificador(atributo)
            else:
                atributo = 0
            mod = movimento['mod']
            mod = mod+modificador
            if atributo:
                cursor.execute(f"SELECT debilidades FROM fichas WHERE id = %s",
                            (ficha_id, ))
                debilidades = cursor.fetchone()[0]
                if debilidades == None:
                    debilidades = ""
                debilidades = debilidades.lower()
                if movimento['atributo'] == "str" and "fraco" in debilidades:
                    mod = mod - 1
                elif movimento['atributo'] == "des" and "trêmulo" in debilidades:
                    mod = mod - 1
                elif movimento['atributo'] == "con" and "doente" in debilidades:
                    mod = mod - 1
                elif movimento['atributo'] == "int" and "atordoado" in debilidades:
                    mod = mod - 1
                elif movimento['atributo'] == "sab" and "confuso" in debilidades:
                    mod = mod - 1
                elif movimento['atributo'] == "car" and "marcado" in debilidades:
                    mod = mod - 1

            n_dados = 2  # Número de dados, default 1
            tipo_dado = 6  # Tipo de dado (ex: 6 para d6)
            modificador = mod + atributo  # Modificador aritmético (ex: +2, -1, *4)

            # Realizar as rolagens
            rolagens = [random.randint(1, tipo_dado) for _ in range(n_dados)]
            soma_rolagens = sum(rolagens)

            # Aplicar o modificador, se existir
            resultado_final = soma_rolagens
            if modificador:
                resultado_final = eval(f"{soma_rolagens}+{modificador}")

            # Construir a mensagem de resultado

            cursor.execute("SELECT nome FROM fichas WHERE id = %s",
                           (ficha_id, ))
            nome = cursor.fetchone()[0]

            resposta = f"**{nome}** usou o movimento **{movimento['nome']}**:\n**{movimento['gatilho']}**\n"

            rolagens_str = ' + '.join(map(str, rolagens))
            if modificador and atributo:
                resposta += f"**Rolagem: 2d6 **\nRolagens: {rolagens_str} = {soma_rolagens}\nModificadores: {movimento['atributo']}: {atributo} + Modificador: {mod}\n**Resultado Final: {resultado_final}**"
            elif modificador:
                resposta += f"**Rolagem: 2d6 **\nRolagens: {rolagens_str} = {soma_rolagens}\nModificador: {mod}\n**Resultado Final: {resultado_final}**"
            elif atributo:
                resposta += f"**Rolagem: 2d6 **\nRolagens: {rolagens_str} = {soma_rolagens}\nModificador: {movimento['atributo']}: {atributo}\n**Resultado Final: {resultado_final}**"
            else:
                resposta += f"**Rolagem: 2d6 **\nRolagens: {rolagens_str} = {resultado_final}"

            if resultado_final <= 6:
                resposta += "\nFracasso!\n" + movimento['fracasso']
            elif resultado_final <= 9:
                resposta += "\nSucesso Parcial!\n" + movimento[
                    'sucesso_parcial']
            elif resultado_final <= 11:
                resposta += "\nSucesso Total!\n" + movimento['sucesso_total']
            elif resultado_final >= 12:
                resposta += "\nCrítico!\n" + movimento['critico']
            if movimento['detalhes'] != "":
                resposta += f"\n{movimento['detalhes']}"
        else:
            cursor.execute("SELECT nome FROM fichas WHERE id = %s",
                           (ficha_id, ))
            nome = cursor.fetchone()[0]
            resposta = f"**{nome}** usou o movimento **{movimento['nome']}**:\n{movimento['gatilho']}\n{movimento['descricao']}"

        await interaction.response.send_message(resposta)

        if resultado_final <= 6:
            cursor.execute("SELECT xp FROM fichas WHERE id = %s", (ficha_id, ))
            xp = cursor.fetchone()[0]


            if xp == None:
                xp = 0

            xp = int(xp) + 1

            cursor.execute(
                f'''
                UPDATE fichas
                SET xp = %s
                WHERE id = %s
                ''', (xp, ficha_id))

            cursor.execute("SELECT nivel FROM fichas WHERE id = %s",
                           (ficha_id, ))
            nivel = cursor.fetchone()

            cursor.execute("SELECT nome FROM fichas WHERE id = %s",
                           (ficha_id, ))
            nome = cursor.fetchone()[0]

            if nivel == None or nivel[0] == None:
                nivel = 0

            if xp >= nivel + 7:
                await interaction.channel.send(
                    f'{nome} Já pode subir de nível!')

            cursor.execute(
                f'''
            UPDATE fichas
            SET xp = %s
            WHERE id = %s
            ''', (xp, ficha_id))
            conn.commit()
    else:
        await interaction.response.send_message(
            'Você não tem fichas criadas. Use /criar_ficha para começar.', ephemeral=True)


@bot.tree.command(name="dano", description="Causa dano à sua ficha ativa")
@app_commands.describe(quantidade="Quantidade de dano a ser recebido", perfurante="Pontos de armadura a se ignorar")
async def dano(interaction: discord.Interaction, quantidade: int, perfurante: int = 0):
    # Recuperar o ID do jogador (supondo que interaction: discord.Interaction.user.id seja o ID do jogador)
    user_id = interaction.user.id
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()
    if ficha_ativa:
        ficha_id = ficha_ativa[0]
        cursor.execute("SELECT hp_atual FROM fichas WHERE id = %s", (ficha_id, ))
        vida_atual = cursor.fetchone()[0]
        if vida_atual == None:
            vida_atual = 0
        cursor.execute("SELECT armadura FROM fichas WHERE id = %s", (ficha_id, ))
        armadura = cursor.fetchone()[0]
        if armadura == None:
            armadura = 0
        armaduraefetiva = armadura - perfurante
        if armaduraefetiva < 0:
            armaduraefetiva = 0
        damage = quantidade - armaduraefetiva
        if damage < 0: 
            damage = 0
        vida_atual = vida_atual - damage
        if vida_atual < 0:
            vida_atual = 0

        cursor.execute("SELECT nome FROM fichas WHERE id = %s", (ficha_id, ))
        nome = cursor.fetchone()[0]

        cursor.execute(
            f'''
        UPDATE fichas
        SET hp_atual = %s
        WHERE id = %s
        ''', (vida_atual, ficha_id))
        conn.commit()

        resposta = f'{nome},'
        if armadura:
            resposta += f' que tem {armadura} de armadura,'
        
        resposta += f" recebeu {quantidade} de dano"

        if armadura and perfurante:
            resposta += f", mas o ataque ignora {perfurante} de armadura."
        else:
            resposta += f"."

        resposta += f" Sua vida atual agora é {vida_atual}."

        await interaction.response.send_message(
            resposta
        )
    else:
        await interaction.response.send_message(
            'Você não possui uma ficha ativa. Use /mudar_ficha para selecionar ou /criar_ficha para criar uma.', ephemeral=True
        )



@bot.tree.command(name="cura", description="Recupera HP da sua ficha ativa")
@app_commands.describe(quantidade="Quantidade de dano a ser curado")
async def cura(interaction: discord.Interaction, quantidade: int = 0):
    # Recuperar o ID do jogador (supondo que interaction: discord.Interaction.user.id seja o ID do jogador)
    user_id = interaction.user.id
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()
    if ficha_ativa:
        ficha_id = ficha_ativa[0]
        
        cursor.execute("SELECT hp_atual FROM fichas WHERE id = %s", (ficha_id, ))
        vida_atual = cursor.fetchone()[0]
        if vida_atual == None:
            vida_atual = 0
        
        cursor.execute("SELECT hp_max FROM fichas WHERE id = %s", (ficha_id, ))
        vida_max = cursor.fetchone()[0]
        if vida_max == None:
            vida_max = 0
        
        if quantidade == 0:
            quantidade = vida_max/2
            quantidade = int(quantidade)
        
        vida_atual += quantidade

        if vida_atual > vida_max:
            vida_atual = vida_max

        cursor.execute("SELECT nome FROM fichas WHERE id = %s", (ficha_id, ))
        nome = cursor.fetchone()[0]

        cursor.execute(
            f'''
        UPDATE fichas
        SET hp_atual = %s
        WHERE id = %s
        ''', (vida_atual, ficha_id))
        conn.commit()

        await interaction.response.send_message(
            f"{nome} se curou de {quantidade} pontos de dano, ficando com {vida_atual} de vida atual"
        )
    else:
        await interaction.response.send_message(
            'Você não possui uma ficha ativa. Use /mudar_ficha para selecionar ou /criar_ficha para criar uma.', ephemeral=True
        )



@bot.tree.command(name="xp", description="Adiciona xp à sua ficha ativa")
@app_commands.describe(quantidade="Quantidade de xp a ser adicionada")
async def xp(interaction: discord.Interaction, quantidade: int = 1):
    # Recuperar o ID do jogador (supondo que interaction: discord.Interaction.user.id seja o ID do jogador)
    user_id = interaction.user.id

    # Buscar a ficha do jogador pelo ID
    cursor.execute(
        '''
    SELECT ficha_ativa_id FROM fichas_ativas WHERE user_id = %s
    ''', (user_id, ))
    ficha_ativa = cursor.fetchone()

    if ficha_ativa:
        ficha_id = ficha_ativa[0]

        cursor.execute("SELECT xp FROM fichas WHERE id = %s", (ficha_id, ))
        xp = cursor.fetchone()[0]

        
        if xp == None:
            xp = 0

        xp = int(xp) + quantidade

        cursor.execute("SELECT nivel FROM fichas WHERE id = %s", (ficha_id, ))
        nivel = cursor.fetchone()

        if nivel == None or nivel[0] == None:
            nivel = 0

        cursor.execute("SELECT nome FROM fichas WHERE id = %s", (ficha_id, ))
        nome = cursor.fetchone()[0]

        if xp >= nivel + 7:
            await interaction.response.send_message(
                f'{nome} ganhou {quantidade} de xp.')
            await interaction.channel.send(f'{nome} Já pode subir de nível!')
        else:
            await interaction.response.send_message(
                f'{nome} ganhou {quantidade} de xp.')

        cursor.execute(
            f'''
        UPDATE fichas
        SET xp = %s
        WHERE id = %s
        ''', (xp, ficha_id))
        conn.commit()

    else:
        await interaction.response.send_message(
            'Você não possui uma ficha ativa. Use /mudar_ficha para selecionar ou /criar_ficha para criar uma.', ephemeral=True
        )















@bot.tree.command(name="help", description="Lista os comandos")
async def help(interaction: discord.Interaction):
    # Mensagem de ajuda
    help_message = """
    **Comandos Disponíveis:**

    `/roll` - Simula uma rolagem de dados.  
    `/criar_ficha` - Cria uma ficha vazia com um nome.  
    `/mudar_ficha` - Muda qual é a sua ficha ativa.  
    `/listar_fichas` - Lista todas as fichas de um usuário.  
    `/mostrar_ficha` - Mostra os detalhes da ficha ativa do jogador.  
    `/mostrar` - Mostra uma informação específica da ficha ativa do jogador.
    `/definir` - Edita um dado específico da ficha ativa do jogador.    
    `/add_item` - Adiciona um item ao inventário da ficha ativa do jogador.
    `/rem_item` - Remove um item do inventário da ficha ativa do jogador.
    `/mostrar_item` - Mostra um item do inventário da ficha ativa do jogador.
    `/usar_item` - Usa um item do inventário da ficha ativa do jogador.
    `/vender_item` - Vende um item do inventário da ficha ativa do jogador.
    `/add_vinculo` - Adiciona um vínculo à ficha ativa do jogador.
    `/rem_vinculo` - Remove um vínculo à ficha ativa do jogador.
    `/mostrar_vínculo` - Mostra um vínculo da ficha ativa do jogador.
    `/add_mov_roll` - Adiciona um movimento com rolagem à ficha ativa do jogador.
    `/add_mov_text` - Adiciona  um movimento descritivo à ficha ativa do jogador.
    `/mov` - Usa um movimento da ficha ativa do jogador
    `/mb` - Usa um movimento básico
    `/rem_mov` - Remove um movimento da ficha ativa do jogador.
    `/mostrar_mov` - Mostra um movimento da ficha ativa do jogador.
    `/atributo` - Faz uma rolagem simples de atributo.
    `/debilidade` - Adiciona ou remove uma debilidade.
    `/sorte` - Usa um ponto de sorte.
    `/calamidade` - Rola na tabela de calamidades.
    `/xp` - Adiciona um de xp.
    `/importar ficha` - Importa uma ficha em formato json 
    `/exportar ficha` - Exporta uma ficha em formato json 
    `/deletar ficha` - Deleta uma ficha
    `/help_mb` - Lista todos os movimentos básicos
    
    """

    # Envia a mensagem de ajuda
    await interaction.response.send_message(help_message)


@bot.tree.command(name="help_mb", description="Lista os movimentos básicos")
async def help_mb(interaction: discord.Interaction):
    # Mensagem de ajuda

    lista = list(movimentos_basicos.keys())

    help_message = ""

    for movi in lista:
        help = help + f"`{movi}`\n"

    # Envia a mensagem de ajuda
    await interaction.response.send_message(help_message)


load_dotenv()
token = os.getenv('TOKEN')

app = Flask(__name__)


@app.route("/")
def home():
    return "O bot está ativo!"


def manter_vivo():
    app.run(host="0.0.0.0", port=4213)


def run():
    # Inicia o servidor Flask em uma thread separada
    flask_thread = Thread(target=manter_vivo)
    flask_thread.daemon = True
    flask_thread.start()

    # Inicia o bot Discord
    bot.run(token)  # Aqui o token do seu bot Discord


if __name__ == "__main__":
    run()
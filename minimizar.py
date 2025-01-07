import json

with open('movimentos_basicos.json', 'r', encoding='utf-8') as file:
    # Carrega o conteúdo do arquivo em um dicionário
    movimentos_basicos = json.load(file)


dicionario_minusculo = {chave.lower(): valor for chave, valor in movimentos_basicos.items()}


chaves = list((movimentos_basicos.keys()))

print(chaves)


with open('saida.json', 'w', encoding='utf-8') as file:
    json.dump(dicionario_minusculo, file, ensure_ascii=False, indent=4)
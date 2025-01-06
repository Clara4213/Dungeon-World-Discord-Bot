def formatar_dicionarios(lista_dicionarios):
    resultado = []
    
    for dicionario in lista_dicionarios:
        partes = []
        for chave, valor in dicionario.items():
            chave_formatada = chave.capitalize()  # Capitaliza o primeiro caractere da chave
            partes.append(f"{chave_formatada}: {valor}")
        resultado.append(", ".join(partes))
    
    return "\n".join(resultado)

# Exemplo de uso
lista = [
    {"nome": "Espada Larga", "descricao": "Duas Mãos, Pesada", "peso": 2},
    {"nome": "Poção de Cura", "descricao": "Cura 10 PV", "peso": 0},
]

string_formatada = formatar_dicionarios(lista)
print(string_formatada)

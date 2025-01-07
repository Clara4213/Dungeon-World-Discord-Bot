
import json


def formatar_json(json):
    novojson = {
    "nome" : "",
    "aparencia" : "",
    "classe" : "",
    "xp" : "",
    "nivel"  : "",
    "alinhamento"  : "",
    "alinhamento_detalhe"  : "",
    "raca"  : "",
    "raca_texto"  : "",
    "dado_dano"  : "",
    "hp_atual"  : "",
    "hp_max"  : "",
    "armadura"  : "",
    "for"  : "",
    "des"  : "",
    "con"  : "",
    "int"  : "",
    "sab"  : "",
    "car"  : "",
    "debilidades"  : "",
    "carga_max"  : "",
    "carga_atual"  : "",
    "inventario"  : "",
    "vinculos"  : "",
    "movimentos"  : "",
    "sorte"  : "",
    "notas" : ""
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
    novojson["for"] = int(json.get('strenght'))
    novojson["des"] = int(json.get('dexterity'))
    novojson["con"] = int(json.get('constitution'))
    novojson["int"] = int(json.get('intelligence'))
    novojson["sab"] = int(json.get('wisdom'))
    novojson["car"] = int(json.get('carisma'))
    novojson["debilidades"] = ""
    novojson["carga_max"] = int(json.get('load'))
    novojson["carga_atual"] = int(json.get('maxLoad'))
    novojson["inventario"] = "[]"
    novojson["vinculos"] = "[]"
    novojson["movimentos"] = "[]"
    novojson["sorte"] = ""
    novojson["notas"] = ""

    return novojson

print("opa")
import sqlite3
import json

# Conectar ao banco de dados
conn = sqlite3.connect('rpg.db')
cursor = conn.cursor()

# Criação da tabela
cursor.execute('''
CREATE TABLE IF NOT EXISTS fichas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    aparencia TEXT,
    classe TEXT,
    nivel INTEGER,
    alinhamento TEXT,
    alinhamento_detalhe TEXT,
    raca TEXT,
    raca_texto TEXT,
    dado_dano TEXT,
    hp_atual INTEGER,
    hp_max INTEGER,
    armadura INTEGER,
    for INTEGER,
    des INTEGER,
    con INTEGER,    
    int INTEGER,           
    sab INTEGER,
    car INTEGER,
    carga_max INTEGER,
    carga_atual INTEGER,
    inventario TEXT,
    notas TEXT,
    movimentos TEXT
)
''')


cursor.execute('''
CREATE TABLE IF NOT EXISTS fichas_ativas (
    user_id BIGINT PRIMARY KEY,
    ficha_ativa_id INTEGER,
    FOREIGN KEY (ficha_ativa_id) REFERENCES fichas(id)
)
''')

# Exemplo de dados para inserir na tabela
ficha = {
    "nome": "Aragorn",
    "aparencia": "Homem alto, cabelo escuro, barba curta.",
    "classe": "Guerreiro",
    "nivel": 5,
    "alinhamento": "Neutro Bom",
    "alinhamento_detalhe": "Protege os inocentes, mas não hesita em agir para o bem maior.",
    "raca": "Humano",
    "raca_texto": "Humano de linhagem nobre, com grande resistência e liderança.",
    "dado_dano": "2d6+3",
    "hp_atual": 38,
    "hp_max": 50,
    "armadura": 16,
    "for": 18,
    "des": 14,
    "con": 16,
    "int": 10,
    "sab": 12,
    "car": 15,
    "carga_max": 50,
    "carga_atual": 30,
    "inventario": 
        [
            {"item": "espada", "quantidade": 1, "peso": 3},
            {"item": "escudo", "quantidade": 1, "peso": 5},
            {"item": "poção de cura", "quantidade": 3, "peso": 0.5}
        ],
    "notas": "Líder do grupo.",
    "movimentos": "Atacar, Defender, Liderar."
}

# Inserção na tabela
cursor.execute('''
INSERT INTO fichas (
    nome, aparencia, classe, nivel, alinhamento, alinhamento_detalhe,
    raca, raca_texto, dado_dano, hp_atual, hp_max, armadura, for, des,
    con, int, sab, car, carga_max, carga_atual, inventario, notas, movimentos
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    ficha["nome"],
    ficha["aparencia"],
    ficha["classe"],
    ficha["nivel"],
    ficha["alinhamento"],
    ficha["alinhamento_detalhe"],
    ficha["raca"],
    ficha["raca_texto"],
    ficha["dado_dano"],
    ficha["hp_atual"],
    ficha["hp_max"],
    ficha["armadura"],
    ficha["for"],
    ficha["des"],
    ficha["con"],
    ficha["int"],
    ficha["sab"],
    ficha["car"],
    ficha["carga_max"],
    ficha["carga_atual"],
    json.dumps(ficha["inventario"]),  # Convertendo o inventário para JSON
    ficha["notas"],
    ficha["movimentos"]
))

# Salvar as mudanças
conn.commit()

# Consultar dados inseridos
cursor.execute('SELECT * FROM fichas')
fichas = cursor.fetchall()

# Exemplo de leitura e conversão dos dados
for ficha in fichas:
    inventario = json.loads(ficha[21])  # Reconverte o JSON de inventário para lista de dicionários
    print(f"Nome: {ficha[1]}, Classe: {ficha[3]}, Inventário: {inventario}")

# Fechar a conexão
conn.close()

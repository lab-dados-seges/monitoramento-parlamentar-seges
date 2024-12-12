import requests
import json
from datetime import datetime, timedelta

# Carrega verbetes de um arquivo externo TXT
def carregar_verbetes(caminho):
    with open(caminho, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file if line.strip()]

# Caminho para o verbetes.txt
caminho_verbetes = 'verbetes.txt'
TEMAS = carregar_verbetes(caminho_verbetes)

# API da Câmara
url_proposicoes = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"
params = {
    "dataInicio": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
    "dataFim": datetime.now().strftime("%Y-%m-%d"),
    "ordenarPor": "id",
    "itens": 100,
    "pagina": 1,
}

proposicoes_filtradas = []

# Buscar proposições com temas relevantes
while True:
    response = requests.get(url_proposicoes, params=params)
    if response.status_code != 200:
        print(f"Erro na API da Câmara: {response.status_code}")
        break

    dados = response.json().get("dados", [])
    if not dados:
        break

    # Filtrar proposições pelos temas
    for proposicao in dados:
        if any(tema in proposicao.get("ementa", "").lower() for tema in TEMAS):
            proposicoes_filtradas.append(proposicao)

    # Avançar para a próxima página
    params["pagina"] += 1

# Adicionar detalhes às proposições
proposicoes_completas = []
for proposicao in proposicoes_filtradas:
    detalhes_response = requests.get(proposicao["uri"])
    if detalhes_response.status_code != 200:
        print(f"Erro ao acessar detalhes da proposição {proposicao['id']}: {detalhes_response.status_code}")
        continue

    try:
        detalhes = detalhes_response.json().get("dados", {})
    except ValueError:
        print(f"Erro ao decodificar detalhes da proposição {proposicao['id']}.")
        continue

    # Obter informações adicionais
    situacao_tramitacao = detalhes.get("statusProposicao", {}).get("descricaoTramitacao", "Não informado")
    sigla_orgao = detalhes.get("statusProposicao", {}).get("siglaOrgao", "Não informado")
    link_inteiro_teor = detalhes.get("urlInteiroTeor", "Não disponível")
    despacho = detalhes.get("statusProposicao", {}).get("despacho", "Não informado")
    link_tramitacao = f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={proposicao['id']}"

    # Montar objeto completo
    proposicao_completa = {
        "Sigla Tipo": proposicao["siglaTipo"],
        "Número": proposicao["numero"],
        "Ano": proposicao["ano"],
        "Ementa": proposicao["ementa"],
        "Situação Tramitação": situacao_tramitacao,
        "Despacho": despacho,
        "Órgão Última Tramitação (Sigla)": sigla_orgao,
        "Link para Inteiro Teor": link_inteiro_teor,
        "Link para Tramitação": link_tramitacao,
    }
    proposicoes_completas.append(proposicao_completa)

# Salvar os dados completos no arquivo JSON
with open("./data-json/dados_camara.json", "w") as f:
    json.dump(proposicoes_completas, f, ensure_ascii=False, indent=4)

print(f"Proposições salvas com informações detalhadas: {len(proposicoes_completas)}")
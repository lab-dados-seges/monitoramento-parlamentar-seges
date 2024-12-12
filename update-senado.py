import requests
import json
import xmltodict
from datetime import datetime, timedelta

# Carrega verbetes de um arquivo externo TXT
def carregar_verbetes(caminho):
    with open(caminho, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file if line.strip()]

# Caminho para o verbetes.txt
caminho_verbetes = 'verbetes.txt'
TEMAS = carregar_verbetes(caminho_verbetes)

# API do Senado
url_materias = "https://legis.senado.leg.br/dadosabertos/materia/atualizadas"
params = {"numdias": 30}

# Buscar matérias atualizadas
response = requests.get(url_materias, params=params)
if response.status_code != 200:
    print(f"Erro na API do Senado: {response.status_code}")
    materias = []
else:
    try:
        dados = xmltodict.parse(response.text)
        materias = dados.get("ListaMateriasAtualizadas", {}).get("Materias", {}).get("Materia", [])
        if isinstance(materias, dict):  # Se for um único item, transformar em lista
            materias = [materias]
    except Exception as e:
        print(f"Erro ao processar dados do Senado: {e}")
        materias = []

materias_filtradas = []

# Processar cada matéria
for materia in materias:
    ementa = materia.get("DadosBasicosMateria", {}).get("EmentaMateria", "").lower()
    if any(tema in ementa for tema in TEMAS):  # Filtro por temas
        id_materia = materia.get("IdentificacaoMateria", {}).get("CodigoMateria")

        # Links de tramitação e movimentação
        link_tramitacao = f"https://www25.senado.leg.br/web/atividade/materias/-/materia/{id_materia}"
        link_movimentacao = f"https://legis.senado.leg.br/dadosabertos/materia/movimentacoes/{id_materia}"

        # Buscar movimentações
        sigla_colegiado = "Não informado"
        descricao_informe = "Não informado"
        movimentacoes_response = requests.get(link_movimentacao)
        if movimentacoes_response.status_code == 200:
            try:
                movimentacoes = xmltodict.parse(movimentacoes_response.text)
                movimentacoes_lista = movimentacoes.get("MovimentacaoMateria", {}).get("Materia", {}).get("Autuacoes", {}).get("Autuacao", [])

                if isinstance(movimentacoes_lista, dict):  # Garantir que seja uma lista
                    movimentacoes_lista = [movimentacoes_lista]

                for movimentacao in movimentacoes_lista:
                    informe_legislativo = movimentacao.get("InformesLegislativos", {}).get("InformeLegislativo", [])
                    if isinstance(informe_legislativo, dict):  # Garantir que seja uma lista
                        informe_legislativo = [informe_legislativo]

                    if informe_legislativo:
                        sigla_colegiado = informe_legislativo[0].get("Colegiado", {}).get("SiglaColegiado", "Não informado")
                        descricao_informe = informe_legislativo[0].get("Descricao", "Não informado")
                        break  # Pegar apenas o primeiro informeLegislativo
            except Exception as e:
                print(f"Erro ao processar movimentações para a matéria {id_materia}: {e}")

        # Adicionar dados filtrados
        materias_filtradas.append({
            "Tipo": materia.get("IdentificacaoMateria", {}).get("SiglaSubtipoMateria", "Não informado"),
            "Número": materia.get("IdentificacaoMateria", {}).get("NumeroMateria", "Não informado"),
            "Ano": materia.get("IdentificacaoMateria", {}).get("AnoMateria", "Não informado"),
            "Ementa": materia.get("DadosBasicosMateria", {}).get("EmentaMateria", "Não informado"),
            "Sigla Colegiado": sigla_colegiado,
            "Descrição Informe Legislativo": descricao_informe,
            "Link para Tramitação": link_tramitacao,
        })

# Salvar os dados filtrados no arquivo JSON
with open("./data-json/dados_senado.json", "w") as f:
    json.dump(materias_filtradas, f, ensure_ascii=False, indent=4)

print(f"Matérias filtradas e salvas: {len(materias_filtradas)}")
import requests
import pandas as pd
import streamlit as st
import io
import xmltodict  # Adicionado para processar XML

# Título da aplicação
st.title('Monitoramento de Proposições Legislativas - Senado Federal')
st.write("""
Este aplicativo exibe as proposições legislativas relacionadas aos temas de interesse
que tiveram movimentação nos últimos 30 dias no Senado Federal.
""")

# Temas de interesse
temas = ["inovação", "gestão", "energia", "compras", "administração pública"]

# Parâmetros da API do Senado
url_materias = "https://legis.senado.leg.br/dadosabertos/materia/atualizadas"
params = {
    "numdias": 30,
}

# Lista para armazenar resultados
materias_filtradas = []

# Requisição inicial
st.info("Buscando dados das proposições...")
response = requests.get(url_materias, params=params)

if response.status_code != 200:
    st.error(f"Erro na requisição: {response.status_code}")
else:
    try:
        # Processar XML da resposta
        dados = xmltodict.parse(response.text)
        materias = dados.get("ListaMateriasAtualizadas", {}).get("Materias", {}).get("Materia", [])

        # Garantir que materias seja uma lista
        if isinstance(materias, dict):
            materias = [materias]

    except Exception as e:
        st.error("Erro ao processar a resposta da API.")
        st.write("Erro:", str(e))
        materias = []

    # Filtrando proposições por temas
    for materia in materias:
        ementa = materia.get("DadosBasicosMateria", {}).get("EmentaMateria", "").lower()
        if any(tema in ementa for tema in temas):
            materias_filtradas.append(materia)

# Se nenhum dado for encontrado
if not materias_filtradas:
    st.warning("Nenhuma proposição encontrada para os temas de interesse.")
else:
    # Criar tabela para exibição
    rows = []

    for materia in materias_filtradas:
        # Obter detalhes da matéria
        id_materia = materia.get("IdentificacaoMateria", {}).get("CodigoMateria")
        detalhes_url = f"https://legis.senado.leg.br/dadosabertos/materia/{id_materia}"
        detalhes_response = requests.get(detalhes_url)

        if detalhes_response.status_code != 200:
            st.warning(f"Erro ao acessar detalhes da matéria {id_materia}: {detalhes_response.status_code}")
            continue

        try:
            # Processar XML dos detalhes
            detalhes = xmltodict.parse(detalhes_response.text)
            detalhes_materia = detalhes.get("DetalheMateria", {}).get("Materia", {})
        except Exception as e:
            st.warning(f"Erro ao processar detalhes da matéria {id_materia}.")
            st.write("Erro:", str(e))
            continue

        # Construir link para a tramitação
        link_tramitacao = f"https://www25.senado.leg.br/web/atividade/materias/-/materia/{id_materia}"

        # Construir link para a movimentação
        link_movimentacao = f"https://legis.senado.leg.br/dadosabertos/materia/movimentacoes/{id_materia}"

        # Buscar movimentações para obter o primeiro informeLegislativo
        sigla_colegiado = "Não informado"
        descricao_informe = "Não informado"

        movimentacoes_response = requests.get(link_movimentacao)
        if movimentacoes_response.status_code == 200:
            try:
                movimentacoes = xmltodict.parse(movimentacoes_response.text)
                movimentacoes_lista = movimentacoes.get("MovimentacaoMateria", {}).get("Materia", {}).get("Autuacoes", {}).get("Autuacao", [])

                # Garantir que movimentacoes_lista seja uma lista
                if isinstance(movimentacoes_lista, dict):
                    movimentacoes_lista = [movimentacoes_lista]

                for movimentacao in movimentacoes_lista:
                    informe_legislativo = movimentacao.get("InformesLegislativos", {}).get("InformeLegislativo", [])

                    # Garantir que informe_legislativo seja uma lista
                    if isinstance(informe_legislativo, dict):
                        informe_legislativo = [informe_legislativo]

                    if informe_legislativo:
                        sigla_colegiado = informe_legislativo[0].get("Colegiado", {}).get("SiglaColegiado", "Não informado")
                        descricao_informe = informe_legislativo[0].get("Descricao", "Não informado")
                        break  # Pegar apenas o primeiro informeLegislativo
            except Exception as e:
                st.warning(f"Erro ao processar movimentações para a matéria {id_materia}.")
                st.write("Erro:", str(e))
                continue

        rows.append({
            "Tipo": materia.get("IdentificacaoMateria", {}).get("SiglaSubtipoMateria"),
            "Número": f'<a href="{link_tramitacao}" target="_blank">{materia.get("IdentificacaoMateria", {}).get("NumeroMateria")}</a>',
            "Ano": materia.get("IdentificacaoMateria", {}).get("AnoMateria"),
            "Ementa": materia.get("DadosBasicosMateria", {}).get("EmentaMateria"),
            "Sigla Colegiado": sigla_colegiado,
            "Descrição Informe Legislativo": descricao_informe,
        })

    # Criar DataFrame para exibição no Streamlit
    df = pd.DataFrame(rows)

    # Criar DataFrame limpo para exportação
    df_excel = df.copy()

    # Remover HTML do "Número" na exportação
    df_excel["Número"] = df_excel["Número"].str.extract(r'>(.*?)<')

    # Botão para exportar para Excel (no topo da página)
    st.subheader("Exportar Dados")
    buffer = io.BytesIO()
    df_excel.to_excel(buffer, index=False, engine='openpyxl')
    st.download_button(
        label="📥 Baixar como Excel",
        data=buffer,
        file_name="materias_senado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Exibir resultados no Streamlit (apenas com a coluna com link)
    st.subheader("Resultados")
    st.write(
        df.to_html(escape=False, index=False),
        unsafe_allow_html=True
    )

# Rodapé
st.write("Fonte: [Dados Abertos - Senado Federal](https://dadosabertos.senado.leg.br/)")
import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import io

# Título da aplicação
st.title('Monitoramento de Proposições Legislativas - Câmara dos Deputados')
st.write("""
Este aplicativo exibe as proposições legislativas relacionadas aos temas de interesse
que tiveram movimentação nos últimos 30 dias.
""")

# Temas de interesse
temas = ["inovação", "gestão", "energia", "compras"]

# Configuração de datas
data_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
data_fim = datetime.now().strftime("%Y-%m-%d")

# Parâmetros da API
url_proposicoes = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"
params = {
    "dataInicio": data_inicio,
    "dataFim": data_fim,
    "ordenarPor": "id",
    "itens": 100,
    "pagina": 1
}

# Lista para armazenar resultados
proposicoes_filtradas = []
alertas = []  # Lista para coletar alertas

# Requisição inicial
st.info("Buscando dados das proposições...")
while True:
    response = requests.get(url_proposicoes, params=params)
    if response.status_code != 200:
        st.error(f"Erro na requisição: {response.status_code}")
        break

    try:
        dados = response.json().get("dados", [])
    except ValueError:
        st.error("Erro ao decodificar a resposta JSON.")
        st.write("Resposta recebida:", response.text)
        break

    if not dados:
        break

    # Filtrando proposições por temas
    for proposicao in dados:
        if any(tema in proposicao["ementa"].lower() for tema in temas):
            proposicoes_filtradas.append(proposicao)

    # Avançar para a próxima página
    params["pagina"] += 1

# Se nenhum dado for encontrado
if not proposicoes_filtradas:
    st.warning("Nenhuma proposição encontrada para os temas de interesse.")
else:
    # Criar tabela para exibição
    rows = []

    for proposicao in proposicoes_filtradas:
        # Obter detalhes da proposição
        detalhes_response = requests.get(proposicao["uri"])
        if detalhes_response.status_code != 200:
            st.warning(f"Erro ao acessar detalhes da proposição {proposicao['id']}: {detalhes_response.status_code}")
            continue

        try:
            detalhes = detalhes_response.json().get("dados", {})
        except ValueError:
            st.warning(f"Resposta inválida para detalhes da proposição {proposicao['id']}.")
            st.write("Conteúdo recebido:", detalhes_response.text)
            continue

        situacao_tramitacao = detalhes.get("statusProposicao", {}).get("descricaoTramitacao", "Não informado")
        sigla_orgao = detalhes.get("statusProposicao", {}).get("siglaOrgao", "Não informado")
        link_inteiro_teor = detalhes.get("urlInteiroTeor", "Não disponível")
        despacho = detalhes.get("statusProposicao", {}).get("despacho", "Não informado")

        # Construir o link para a ficha de tramitação
        link_tramitacao = f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={proposicao['id']}"

        # Formatar a situação da tramitação
        situacao_formatada = (
            f'<b><span style="color:red;">{situacao_tramitacao}</span></b>'
            if "pauta" in situacao_tramitacao.lower() else situacao_tramitacao
        )
        if "pauta" in situacao_tramitacao.lower():
            alertas.append({
                "Sigla": proposicao["siglaTipo"],
                "Número": proposicao["numero"],
                "Link": link_tramitacao,
                "Situação": situacao_tramitacao
            })

        # Formatar ementa para destacar palavras específicas
        ementa = proposicao["ementa"]
        for termo in ["Esther Dweck", "MGI"]:
            ementa = ementa.replace(
                termo,
                f'<b><span style="color:red;">{termo}</span></b>'
            )

        # Adicionar à tabela
        rows.append({
            "Sigla Tipo": proposicao["siglaTipo"],
            "Número (Link)": f'<a href="{link_tramitacao}" target="_blank">{proposicao["numero"]}</a>',
            "Ano": proposicao["ano"],
            "Ementa": ementa,
            "Situação Tramitação": situacao_formatada,
            "Despacho": despacho,
            "Órgão Última Tramitação (Sigla)": sigla_orgao,
            "Link para o Inteiro Teor": f'<a href="{link_inteiro_teor}" target="_blank">Clique aqui</a>' if link_inteiro_teor != "Não disponível" else "Não disponível"
        })

    # Mostrar alertas no topo
    if alertas:
        st.warning("⚠️ Atenção: Algumas proposições estão em pauta! Verifique abaixo:")
        for alerta in alertas:
            st.write(
                f"- **{alerta['Sigla']} {alerta['Número']}** - "
                f"[Link para tramitação]({alerta['Link']}) - "
                f"Situação: {alerta['Situação']}"
            )

    # Criar DataFrame para exibição no Streamlit
    df = pd.DataFrame(rows)

    # Criar DataFrame para exportação no Excel (sem HTML e colunas desnecessárias)
    df_excel = df.drop(columns=["Número (Link)", "Link para o Inteiro Teor"])

    # Botão para exportar para Excel (no topo da página)
    st.subheader("Exportar Dados")
    buffer = io.BytesIO()
    df_excel.to_excel(buffer, index=False, engine='openpyxl')
    st.download_button(
        label="📥 Baixar como Excel",
        data=buffer,
        file_name="proposicoes_legislativas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Exibir resultados no Streamlit (apenas com a coluna com link)
    st.subheader("Resultados")
    st.write(
        df.to_html(escape=False, index=False),
        unsafe_allow_html=True
    )

# Rodapé
st.write("Fonte: [Dados Abertos - Câmara dos Deputados](https://dadosabertos.camara.leg.br/)")
import os
import json
import pandas as pd
import streamlit as st
import io

# Caminhos locais dos arquivos JSON
file_camara = "./data-json/dados_camara.json"
file_senado = "./data-json/dados_senado.json"

# Configuração do Streamlit
st.set_page_config(page_title="Monitoramento Legislativo", layout="wide")

# Menu de navegação
opcao = st.sidebar.selectbox("Navegação:", ["Home", "Câmara dos Deputados", "Senado Federal"])

# Palavras-chave para destacar
PALAVRAS_CHAVE = ["pauta", "MGI", "Esther Dweck", "Ministra da Gestão e da Inovação em Serviços Públicos", "Ministra da Gestão e da Inovação em Serviços Públicos"]

# Função para carregar os dados do JSON
def carregar_dados(caminho):
    if os.path.exists(caminho):
        with open(caminho, "r") as f:
            return json.load(f)
    else:
        st.error(f"Arquivo {caminho} não encontrado!")
        return []

# Função para destacar palavras-chave
def destacar_texto(texto, palavras_chave):
    if not texto:
        return texto
    for palavra in palavras_chave:
        texto = texto.replace(
            palavra,
            f'<b><span style="color:red;">{palavra}</span></b>'
        )
    return texto

# Função para exibir dados com formatação e alertas
def exibir_dados(titulo, dados, campo_alerta):
    if not dados:
        st.warning(f"Nenhuma proposição encontrada em {titulo}.")
    else:
        df = pd.DataFrame(dados)

        # Destacar palavras-chave no DataFrame
        for col in ["Ementa", "Despacho", "Descrição Informe Legislativo"]:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: destacar_texto(x, PALAVRAS_CHAVE))

        # Criar lista de alertas para "pauta"
        alertas = df[df[campo_alerta].str.contains("pauta", case=False, na=False)]
        if not alertas.empty:
            st.warning("⚠️ **Atenção: Algumas proposições tiveram tramitação relacionada à pauta!**")
            for _, row in alertas.iterrows():
                st.write(
                    f"- **{row.get('Tipo', row.get('Sigla Tipo'))} {row['Número']}** - "
                    f"{row[campo_alerta]}",
                    unsafe_allow_html=True
                )

        # Garantir que os links sejam exibidos como hiperlinks
        for col in ["Link para Tramitação", "Link para Inteiro Teor"]:
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda url: f'<a href="{url}" target="_blank">Clique aqui</a>' if pd.notnull(url) and url != "Não disponível" else "Não disponível"
                )

        # Criar DataFrame para exportação (removendo HTML dos links)
        df_excel = df.copy()
        for col in ["Link para Tramitação", "Link para Inteiro Teor"]:
            if col in df_excel.columns:
                df_excel[col] = df_excel[col].str.extract(r'href="(.*?)"', expand=False).fillna("Não disponível")

        # Botão para exportar para Excel
        st.subheader("Exportar Dados")
        buffer = io.BytesIO()
        df_excel.to_excel(buffer, index=False, engine="openpyxl")
        st.download_button(
            label="📥 Baixar como Excel",
            data=buffer,
            file_name=f"proposicoes_{titulo.lower().replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Exibir resultados no Streamlit com links clicáveis
        st.subheader(f"Resultados - {titulo}")
        st.write(
            df.to_html(escape=False, index=False),
            unsafe_allow_html=True  # Permitir HTML nos links
        )

# Função para criar botão "Voltar ao Início" no topo
def botao_voltar_ao_inicio():
    st.markdown(
        """
        <div style="text-align: right; margin-bottom: 1em;">
            <form action="/" method="get">
                <button style="
                    background-color: #f63366;
                    color: white;
                    border: none;
                    padding: 0.5em 1em;
                    font-size: 1em;
                    border-radius: 5px;
                    cursor: pointer;">
                    Voltar ao Início
                </button>
            </form>
        </div>
        """,
        unsafe_allow_html=True
    )

# Página inicial (Home)
if opcao == "Home":
    st.title("Monitoramento Legislativo SEGES/MGI")
    st.write("""
    Este aplicativo permite consultar proposições legislativas que tiveram tramitação nos últimos **60 dias** na **Câmara dos Deputados** e nos últimos **30 dias** no **Senado Federal**.

    As proposições exibidas são relacionadas a temas de interesse específicos, tais como:
    - **Gestão pública**
    - **Inovação da gestão pública**
    - **Central de compras**
    - **Programa de gestão e desempenho**
    """)

# Página da Câmara dos Deputados
elif opcao == "Câmara dos Deputados":
    botao_voltar_ao_inicio()  # Botão no início
    dados = carregar_dados(file_camara)
    exibir_dados("Câmara dos Deputados", dados, campo_alerta="Despacho")

# Página do Senado Federal
elif opcao == "Senado Federal":
    botao_voltar_ao_inicio()  # Botão no início
    dados = carregar_dados(file_senado)
    exibir_dados("Senado Federal", dados, campo_alerta="Descrição Informe Legislativo")

# Rodapé
st.markdown("""
<hr style="height:1px;border:none;color:#ccc;background-color:#ccc;" />
<p style="text-align: center; font-size: 0.9em;">
Este aplicativo foi desenvolvido pelo <b>Núcleo de Gestão da Informação e do Conhecimento</b> da <b>SEGES/MGI</b>.
</p>
""", unsafe_allow_html=True)
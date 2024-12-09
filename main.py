import streamlit as st

# Configuração da página principal
st.set_page_config(page_title="Consultas Legislativas", layout="wide")

# Título da aplicação
st.title("Portal de Consultas Legislativas")
st.write("""
Este portal permite realizar consultas legislativas na Câmara dos Deputados e no Senado Federal.
Escolha a consulta desejada no menu abaixo.
""")

# Opções de consulta
consulta = st.selectbox(
    "Escolha o local da consulta:",
    ("Selecione...", "Câmara dos Deputados", "Senado Federal")
)

# Redirecionar para o script escolhido
if consulta == "Câmara dos Deputados":
    st.info("Carregando consulta na Câmara dos Deputados...")
    exec(open("consulta-cam.py").read())  # Executa o script da Câmara
elif consulta == "Senado Federal":
    st.info("Carregando consulta no Senado Federal...")
    exec(open("consulta-sf.py").read())  # Executa o script do Senado
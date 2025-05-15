import streamlit as st
from agent_api.client import RagflowClient
from agent_api.config import AGENT_EXPLANATOR_ID

st.set_page_config(page_title="Análise de Matéria - Ragflow", layout="centered")
st.title("Análise de Matéria Jornalística")

materia = st.text_area("Cole a matéria jornalística para análise:", height=300)

# Inicializa variáveis de estado
if "resposta_agente" not in st.session_state:
    st.session_state.resposta_agente = None
if "mostrar_detalhes" not in st.session_state:
    st.session_state.mostrar_detalhes = False
if "detalhes_agente" not in st.session_state:
    st.session_state.detalhes_agente = None

if st.button("Analisar"):
    if not materia.strip():
        st.warning("Por favor, cole uma matéria para análise.")
    else:
        with st.spinner("Analisando..."):
            try:
                client = RagflowClient()
                session_id = client.start_session()
                result = client.analyze_materia(materia, session_id)

                if result.get("code") == 0:
                    resposta = result["data"]["answer"]
                    st.session_state.resposta_agente = resposta
                    st.session_state.detalhes_agente = None  # Limpa caso nova análise
                    st.session_state.mostrar_detalhes = "FAKE" in resposta.upper()

                    st.success("Resposta do agente:")
                    st.write(resposta)
                else:
                    st.error(f"Erro da API: {result.get('message')}")

            except Exception as e:
                st.error(f"Erro ao conectar com o agente: {e}")

# Exibe botão de detalhes se apropriado
if st.session_state.resposta_agente and st.session_state.mostrar_detalhes:
    if st.button("Obter detalhes"):
        with st.spinner("Consultando agente explicador..."):
            try:
                explicador = RagflowClient(agent_id=AGENT_EXPLANATOR_ID)
                explicador_session = explicador.start_session()
                detalhamento = explicador.analyze_materia(materia, explicador_session)

                if detalhamento.get("code") == 0:
                    detalhes = detalhamento["data"]["answer"]
                    st.session_state.detalhes_agente = detalhes
                else:
                    st.error(f"Erro no agente explicador: {detalhamento.get('message')}")
            except Exception as e:
                st.error(f"Erro ao conectar com o agente explicador: {e}")

# Exibe explicação se já foi carregada
if st.session_state.detalhes_agente:
    st.info("Explicação detalhada do agente:")
    st.write(st.session_state.detalhes_agente)

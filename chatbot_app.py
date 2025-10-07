import streamlit as st
import google.generativeai as genai
import os

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Chatbot con Gemini",
    page_icon="🤖",
    layout="centered"
)

# --- Título de la Aplicación ---
st.title("🤖 Chatbot con IA de Gemini")
st.caption("Una aplicación para conversar con el modelo de IA de Google.")

# --- Lógica del Chatbot ---
def get_gemini_response(question, chat_history):
    """
    Obtiene una respuesta del modelo Gemini.
    """
    try:
        # Configura el modelo con la API Key
        model = genai.GenerativeModel('gemini-pro')
        
        # Inicia una sesión de chat con el historial
        chat = model.start_chat(history=chat_history)
        
        # Envía la pregunta del usuario
        response = chat.send_message(question)
        
        return response.text
    except Exception as e:
        # Manejo de errores (ej. API Key inválida)
        st.error(f"Ocurrió un error: {e}")
        return None

# --- Interfaz de la Aplicación ---

# Sidebar para la API Key
with st.sidebar:
    st.header("Configuración")
    # Pide la API Key de Gemini
    api_key = st.text_input("Ingresa tu API Key de Gemini:", type="password", key="api_key_input")
    
    # Botón para configurar la API Key
    if st.button("Guardar Clave", key="save_api_key"):
        if api_key:
            genai.configure(api_key=api_key)
            st.session_state.api_key_configured = True
            st.success("¡API Key configurada correctamente!")
        else:
            st.warning("Por favor, ingresa una API Key.")

# Inicializa el historial del chat en el estado de la sesión si no existe
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'api_key_configured' not in st.session_state:
    st.session_state.api_key_configured = False

# Muestra el historial del chat
for message in st.session_state.chat_history:
    role = "Tú" if message['role'] == 'user' else "Gemini"
    with st.chat_message(role):
        st.markdown(message['parts'][0])

# Input para la pregunta del usuario
user_prompt = st.chat_input("Escribe tu pregunta aquí...")

if user_prompt:
    # Asegúrate de que la API Key esté configurada antes de chatear
    if not st.session_state.api_key_configured:
        st.warning("Por favor, configura tu API Key en la barra lateral antes de chatear.")
    else:
        # Añade el mensaje del usuario al historial y a la pantalla
        st.session_state.chat_history.append({"role": "user", "parts": [user_prompt]})
        with st.chat_message("Tú"):
            st.markdown(user_prompt)

        # Muestra un indicador de carga mientras se obtiene la respuesta
        with st.spinner("Gemini está pensando..."):
            # Obtiene la respuesta de Gemini
            response_text = get_gemini_response(user_prompt, st.session_state.chat_history)
        
        # Añade la respuesta de Gemini al historial y a la pantalla
        if response_text:
            st.session_state.chat_history.append({"role": "model", "parts": [response_text]})
            with st.chat_message("Gemini"):
                st.markdown(response_text)

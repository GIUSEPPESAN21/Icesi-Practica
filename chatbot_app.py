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
st.caption("Una aplicación segura para conversar con el modelo de IA de Google.")

# --- Configuración de la API Key desde Streamlit Secrets ---
try:
    # Intenta obtener la clave desde los secretos de Streamlit
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    st.session_state.api_key_configured = True
except (KeyError, AttributeError):
    # Si la clave no se encuentra, muestra un mensaje de error
    st.error("🔑 La API Key de Gemini no está configurada. Por favor, crea un archivo .streamlit/secrets.toml y añade tu clave.")
    st.session_state.api_key_configured = False

# --- Lógica del Chatbot ---
def get_gemini_response(question, chat_history):
    """
    Obtiene una respuesta del modelo Gemini.
    """
    try:
        model = genai.GenerativeModel('gemini-pro')
        chat = model.start_chat(history=chat_history)
        response = chat.send_message(question)
        return response.text
    except Exception as e:
        st.error(f"Ocurrió un error al contactar a Gemini: {e}")
        return None

# --- Interfaz de la Aplicación ---

# Inicializa el historial del chat
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Muestra el historial del chat
for message in st.session_state.chat_history:
    role = "Tú" if message['role'] == 'user' else "Gemini"
    with st.chat_message(role):
        st.markdown(message['parts'][0])

# Input para la pregunta del usuario
user_prompt = st.chat_input("Escribe tu pregunta aquí...")

if user_prompt:
    # Solo procede si la API Key fue configurada exitosamente
    if not st.session_state.get('api_key_configured', False):
        st.warning("No se puede chatear hasta que la API Key esté configurada correctamente en los secretos.")
    else:
        # Añade el mensaje del usuario al historial y a la pantalla
        st.session_state.chat_history.append({"role": "user", "parts": [user_prompt]})
        with st.chat_message("Tú"):
            st.markdown(user_prompt)

        # Muestra un indicador de carga
        with st.spinner("Gemini está pensando..."):
            response_text = get_gemini_response(user_prompt, st.session_state.chat_history)
        
        # Añade la respuesta de Gemini al historial y a la pantalla
        if response_text:
            st.session_state.chat_history.append({"role": "model", "parts": [response_text]})
            with st.chat_message("Gemini"):
                st.markdown(response_text)

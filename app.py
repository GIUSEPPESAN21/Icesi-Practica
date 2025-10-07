import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import warnings
import os

# --- 1. Configuración General de la Página ---
st.set_page_config(
    page_title="Dashboard Inteligente",
    page_icon="🧠",
    layout="wide",
)
warnings.filterwarnings('ignore')

# --- 2. Lógica del Analizador de Datos ---

@st.cache_data
def load_and_clean_data(uploaded_file):
    """Carga y limpia los datos desde un archivo CSV."""
    try:
        df = pd.read_csv(uploaded_file)
        df['value'] = df['value'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df['value'].fillna(0, inplace=True)
        for col in ['parameter', 'mode', 'region', 'powertrain']:
             df[col] = df[col].astype(str)
        df['year'] = pd.to_numeric(df['year'], errors='coerce').dropna().astype(int)
        return df
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        return pd.DataFrame()

def page_segment_trends(df):
    st.header("📈 Tendencias por Segmento de Vehículo")
    metric = st.selectbox("Selecciona la Métrica", options=sorted(df['parameter'].unique()), key='trends_metric')
    segment_data = df[(df['region'] == 'World') & (df['parameter'] == metric) & (df['powertrain'] == 'EV') & (df['mode'] != 'EV')].groupby(['year', 'mode'])['value'].sum().reset_index()
    if not segment_data.empty:
        fig = px.line(segment_data, x='year', y='value', color='mode', title=f"Tendencia Mundial de '{metric}' por Segmento", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay datos mundiales para esta métrica.")

def page_regional_comparison(df):
    st.header("🌍 Comparativa Regional por Segmento")
    segments = sorted([m for m in df['mode'].unique() if m != 'EV'])
    selected_segment = st.selectbox("Selecciona un Segmento", options=segments)
    metric = st.selectbox("Selecciona la Métrica", options=sorted(df['parameter'].unique()), key='comparison_metric')
    regional_data = df[(df['mode'] == selected_segment) & (df['parameter'] == metric) & (df['powertrain'] == 'EV') & (df['region'] != 'World')].groupby('region')['value'].sum().nlargest(15).sort_values()
    if not regional_data.empty:
        fig = px.bar(regional_data, x='value', y=regional_data.index, orientation='h', title=f"Top 15 Regiones para '{selected_segment}'")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"No hay datos para el segmento '{selected_segment}'.")

def page_market_composition(df):
    st.header("📊 Composición del Mercado")
    metric = st.selectbox("Selecciona la Métrica", options=[p for p in sorted(df['parameter'].unique()) if 'share' not in p], key='composition_metric')
    year = st.slider("Selecciona un Año", min_value=int(df['year'].min()), max_value=int(df['year'].max()), value=int(df['year'].max() - 1))
    composition_data = df[(df['year'] == year) & (df['parameter'] == metric) & (df['region'] == 'World') & (df['powertrain'] == 'EV') & (df['mode'] != 'EV')].groupby('mode')['value'].sum()
    if not composition_data.empty:
        fig = px.pie(composition_data, names=composition_data.index, values='value', title=f"Distribución del Mercado Mundial en {year}", hole=0.3)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"No hay datos de composición para el año {year}.")

def run_analyzer():
    """Ejecuta la lógica completa del analizador de datos."""
    st.sidebar.title("Panel del Analizador 📊")
    uploaded_file = st.sidebar.file_uploader("Sube tu archivo CSV de datos", type=["csv"], key="analyzer_uploader")
    if uploaded_file is None:
        st.title("Bienvenido al Analizador de Datos")
        st.info("👈 Sube un archivo CSV para comenzar.")
        return
    df = load_and_clean_data(uploaded_file)
    if df.empty: return
    page = st.sidebar.radio("Selecciona un análisis", ["Tendencias", "Comparativa Regional", "Composición del Mercado"])
    if page == "Tendencias": page_segment_trends(df)
    elif page == "Comparativa Regional": page_regional_comparison(df)
    elif page == "Composición del Mercado": page_market_composition(df)

# --- 3. Lógica del Chatbot con Gemini ---

def get_gemini_response(question, chat_history):
    """
    Obtiene una respuesta del modelo Gemini, probando una lista de modelos disponibles
    para asegurar la robustez del servicio.
    """
    # Lista de modelos a probar, ordenados por preferencia (del más potente al más básico)
    modelos_disponibles = [
        "gemini-1.5-pro-latest",
        "gemini-1.5-flash-latest",
        "gemini-pro", # Modelo más antiguo, pero estable como fallback
    ]
    
    last_error = None
    
    for model_name in modelos_disponibles:
        try:
            # Intenta inicializar el modelo
            model = genai.GenerativeModel(model_name)
            chat = model.start_chat(history=chat_history)
            response = chat.send_message(question)
            
            # Si la respuesta es exitosa, la retornamos y salimos de la función
            return response.text
        
        except Exception as e:
            # Guarda el error para informarlo si todos los modelos fallan
            last_error = e
            # Opcional: Imprime en la consola del servidor para depuración
            print(f"Advertencia: El modelo '{model_name}' no está disponible. Intentando con el siguiente. Error: {e}")
            continue # Pasa al siguiente modelo de la lista
            
    # Si el bucle termina sin haber retornado una respuesta, significa que todos los modelos fallaron.
    return f"Ocurrió un error al contactar la API de Gemini. Todos los modelos probados fallaron. Último error: {last_error}"

def run_chatbot():
    """Ejecuta la lógica completa del Chatbot."""
    st.title("🤖 Chatbot con IA de Gemini")
    st.caption("Conversa con el modelo de IA de Google.")
    
    # Configuración de la API Key desde Streamlit Secrets
    try:
        # Asegurarse de que la clave de API está en st.secrets
        if "GEMINI_API_KEY" not in st.secrets:
            st.error("🔑 La API Key de Gemini no está configurada. Añádela a tus secretos de Streamlit.")
            st.code("GEMINI_API_KEY = 'TU_API_KEY'")
            return

        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)

    except Exception as e:
        st.error(f"Error al configurar la API Key: {e}")
        return

    # Lógica del historial de chat
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    for message in st.session_state.chat_history:
        role = "Tú" if message['role'] == 'user' else "Gemini"
        with st.chat_message(role):
            st.markdown(message['parts'][0])

    user_prompt = st.chat_input("Escribe tu pregunta aquí...")

    if user_prompt:
        st.session_state.chat_history.append({"role": "user", "parts": [user_prompt]})
        with st.chat_message("Tú"):
            st.markdown(user_prompt)

        with st.spinner("Gemini está pensando..."):
            response_text = get_gemini_response(user_prompt, st.session_state.chat_history)
        
        st.session_state.chat_history.append({"role": "model", "parts": [response_text]})
        with st.chat_message("Gemini"):
            st.markdown(response_text)

# --- 4. Aplicación Principal (Router) ---
def main():
    st.sidebar.title("Navegación Principal")
    app_choice = st.sidebar.radio(
        "Elige la aplicación",
        ["Analizador de Datos", "Chatbot con Gemini"]
    )
    
    if app_choice == "Analizador de Datos":
        run_analyzer()
    elif app_choice == "Chatbot con Gemini":
        run_chatbot()

if __name__ == "__main__":
    main()


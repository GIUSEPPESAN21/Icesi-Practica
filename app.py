import streamlit as st
import pandas as pd
import plotly.express as px
import warnings

# --- 1. Configuración de la Página y Carga de Datos ---
# Configura el título, ícono y layout de la página de Streamlit.
st.set_page_config(
    page_title="Análisis por Segmento de Vehículos",
    page_icon="📊",
    layout="wide",
)

warnings.filterwarnings('ignore')

# Usa el caché de Streamlit para no tener que cargar y limpiar los datos cada vez que se cambia un filtro.
@st.cache_data
def load_and_clean_data(uploaded_file):
    """
    Carga y limpia los datos desde un archivo CSV subido por el usuario.
    """
    try:
        df = pd.read_csv(uploaded_file)
        # Limpieza de la columna 'value'
        df['value'] = df['value'].astype(str).str.replace('.', '', regex=False)
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df['value'].fillna(0, inplace=True)
        # Limpieza de columnas categóricas y de año
        df['parameter'] = df['parameter'].astype(str)
        df['mode'] = df['mode'].astype(str)
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df.dropna(subset=['year'], inplace=True)
        df['year'] = df['year'].astype(int)
        return df
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        return pd.DataFrame()

# --- 2. Páginas de Análisis ---

def page_segment_trends(df):
    """
    Página para analizar las tendencias de diferentes segmentos de vehículos a lo largo del tiempo.
    """
    st.header("📈 Tendencias por Segmento de Vehículo")
    st.markdown("Observa cómo ha crecido cada segmento de vehículo (Coches, Buses, Furgonetas) a nivel mundial.")

    metric = st.selectbox(
        "Selecciona la Métrica",
        options=sorted(df['parameter'].unique()),
        key='trends_metric'
    )

    st.subheader("Visión General: Crecimiento de cada Segmento en el Mundo")
    
    # Filtra los datos para la métrica seleccionada a nivel mundial y por segmento
    segment_data = df[
        (df['region'] == 'World') &
        (df['parameter'] == metric) &
        (df['powertrain'] == 'EV') &
        (df['mode'] != 'EV') # Excluir valores genéricos
    ].groupby(['year', 'mode'])['value'].sum().reset_index()

    if not segment_data.empty:
        fig = px.line(segment_data, x='year', y='value', color='mode',
                      title=f"Tendencia Mundial de '{metric}' por Segmento de Vehículo",
                      labels={'year': 'Año', 'value': 'Valor', 'mode': 'Segmento'},
                      markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay datos mundiales disponibles para esta métrica y segmentos.")

def page_regional_comparison(df):
    """
    Página para comparar el rendimiento de las regiones dentro de un segmento específico.
    """
    st.header("🌍 Comparativa Regional por Segmento")
    st.markdown("Selecciona un segmento de vehículo y descubre qué regiones son líderes en el mercado.")

    # El usuario primero elige el segmento
    segments = sorted([m for m in df['mode'].unique() if m != 'EV'])
    selected_segment = st.selectbox("Selecciona un Segmento de Vehículo", options=segments)

    metric = st.selectbox(
        "Selecciona la Métrica",
        options=sorted(df['parameter'].unique()),
        key='comparison_metric'
    )

    st.subheader(f"Visión General: Top 15 Regiones para el Segmento '{selected_segment}'")
    
    # Filtra por el segmento y métrica seleccionados
    regional_data = df[
        (df['mode'] == selected_segment) &
        (df['parameter'] == metric) &
        (df['powertrain'] == 'EV') &
        (df['region'] != 'World')
    ].groupby('region')['value'].sum().nlargest(15).sort_values()

    if not regional_data.empty:
        fig = px.bar(regional_data, x='value', y=regional_data.index, orientation='h',
                     title=f"Top 15 Regiones por '{metric}' en el segmento '{selected_segment}' (Total Histórico)",
                     labels={'value': 'Valor Total Acumulado', 'y': 'Región'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"No hay datos disponibles para el segmento '{selected_segment}' con la métrica seleccionada.")

def page_market_composition(df):
    """
    Página para analizar la composición del mercado, enfocada en segmentos.
    """
    st.header("📊 Composición del Mercado")
    st.markdown("Entiende qué porcentaje del mercado representa cada segmento de vehículo.")

    metric = st.selectbox(
        "Selecciona la Métrica",
        options=[p for p in sorted(df['parameter'].unique()) if 'share' not in p],
        key='composition_metric'
    )

    year = st.slider(
        "Selecciona un Año para el Análisis",
        min_value=int(df['year'].min()),
        max_value=int(df['year'].max()),
        value=int(df['year'].max()) - 1
    )

    st.subheader(f"Visión General: Composición del Mercado Mundial por Segmento en {year}")

    # Filtra por año, métrica y agrupa por segmento
    composition_data = df[
        (df['year'] == year) &
        (df['parameter'] == metric) &
        (df['region'] == 'World') &
        (df['powertrain'] == 'EV') &
        (df['mode'] != 'EV')
    ].groupby('mode')['value'].sum()

    if not composition_data.empty:
        fig = px.pie(composition_data, names=composition_data.index, values='value',
                     title=f"Distribución del Mercado Mundial por Segmento ({metric}, {year})",
                     hole=0.3)
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"No hay datos de composición mundial para el año {year}.")

# --- 3. Lógica Principal de la Aplicación ---
def main():
    """
    Función principal que organiza la interfaz de usuario y la navegación entre páginas.
    """
    st.sidebar.title("Panel de Control 🚗")
    
    uploaded_file = st.sidebar.file_uploader("Sube tu archivo CSV", type=["csv"])

    if uploaded_file is None:
        st.title("Bienvenido al Analizador de Datos por Segmento")
        st.info("👈 Por favor, sube un archivo CSV para comenzar el análisis.")
        return

    df = load_and_clean_data(uploaded_file)
    if df.empty:
        return

    page = st.sidebar.radio(
        "Selecciona una página de análisis",
        ["Tendencias por Segmento", "Comparativa Regional", "Composición del Mercado"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("Esta aplicación te permite analizar el mercado de Vehículos Eléctricos, enfocándose en los diferentes segmentos como coches, buses y camiones.")

    if page == "Tendencias por Segmento":
        page_segment_trends(df)
    elif page == "Comparativa Regional":
        page_regional_comparison(df)
    elif page == "Composición del Mercado":
        page_market_composition(df)

if __name__ == "__main__":
    main()


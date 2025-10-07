import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import warnings

# --- Page Configuration ---
st.set_page_config(
    page_title="Analizador de Datos Interactivo",
    page_icon="📂",
    layout="wide",
)

warnings.filterwarnings('ignore')

# --- Cached Data Loading and Cleaning ---
@st.cache_data
def load_and_clean_data(uploaded_file):
    """
    Loads and cleans data from an uploaded file. Results are cached.
    Args:
        uploaded_file: The file-like object from st.file_uploader.
    Returns:
        pd.DataFrame: A cleaned and prepared pandas DataFrame.
    """
    try:
        df = pd.read_csv(uploaded_file)
        # Data Cleaning Logic remains the same
        df['value'] = df['value'].astype(str).str.replace('.', '', regex=False)
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df['value'].fillna(0, inplace=True)
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df.dropna(subset=['year'], inplace=True)
        df['year'] = df['year'].astype(int)
        return df
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        return pd.DataFrame()

# --- Main Application Logic ---
def main():
    st.title("📂 Analizador de Datos Interactivo")
    
    # --- Sidebar for Controls ---
    st.sidebar.header("Panel de Control")
    
    # --- 1. File Uploader ---
    st.sidebar.subheader("1. Carga tus Datos")
    uploaded_file = st.sidebar.file_uploader(
        "Sube tu archivo CSV aquí", 
        type=["csv"]
    )

    # If no file is uploaded, show a welcome message
    if uploaded_file is None:
        st.info("👈 Por favor, sube un archivo CSV para comenzar el análisis.")
        st.markdown("### ¿Cómo funciona?")
        st.markdown("""
        1.  **Arrastra y suelta** un archivo CSV en el área de carga a la izquierda, o haz clic para seleccionarlo.
        2.  Una vez cargado, la aplicación **analizará los datos automáticamente**.
        3.  Usa los **filtros y selectores de gráficos** que aparecerán en el panel lateral para explorar tus datos.
        """)
        return # Stop the app execution until a file is uploaded

    # If a file IS uploaded, proceed with the analysis
    df = load_and_clean_data(uploaded_file)

    if df.empty:
        st.warning("El archivo está vacío o no se pudo procesar. Por favor, verifica el formato del CSV.")
        return

    # --- 2. Chart and Data Filters ---
    st.sidebar.subheader("2. Configura tu Análisis")
    
    chart_types = [
        "Gráfico de Barras", "Gráfico Lineal", "Diagrama de Cajas",
        "Mapa de Calor", "Gráfico Circular (Sunburst)", "Diagrama de Dispersión",
        "Gráfico de Burbujas", "Gráfico de Barras Apiladas", "Diagrama de Pareto",
    ]
    chart_type = st.sidebar.selectbox("Selecciona un Tipo de Gráfico", chart_types)
    
    # Common filters
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros Generales")
    
    metric_options = sorted(df['parameter'].unique())
    selected_metric = st.sidebar.selectbox("Selecciona la Métrica Principal", metric_options)

    min_year, max_year = int(df['year'].min()), int(df['year'].max())
    year_range = st.sidebar.slider("Selecciona un Rango de Años", min_year, max_year, (min_year, max_year))

    # Filter the DataFrame based on common filters
    filtered_df = df[
        (df['parameter'] == selected_metric) &
        (df['year'] >= year_range[0]) &
        (df['year'] <= year_range[1])
    ]

    # --- Visualization Logic (remains mostly the same) ---
    st.header(f"Visualización: {chart_type}")
    
    if chart_type == "Gráfico de Barras":
        st.info("**Propósito:** Comparar una métrica entre diferentes categorías.")
        year_to_show = st.slider("Selecciona un año para comparar", min_year, max_year, max_year - 1)
        data = filtered_df[(filtered_df['year'] == year_to_show) & (filtered_df['region'] != 'World') & (filtered_df['powertrain'] == 'EV')].groupby('region')['value'].sum().nlargest(15)
        fig = px.bar(data, x=data.index, y='value', title=f'Top 15 Regiones por "{selected_metric}" en {year_to_show}', labels={'value': 'Valor', 'region': 'Región'})
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Gráfico Lineal":
        st.info("**Propósito:** Mostrar cómo una métrica cambia a lo largo del tiempo.")
        region_options = ['World'] + sorted(filtered_df['region'].unique())
        selected_region = st.selectbox("Selecciona una Región", region_options)
        data = filtered_df[(filtered_df['region'] == selected_region) & (filtered_df['powertrain'] == 'EV')].groupby('year')['value'].sum()
        fig = px.line(data, x=data.index, y='value', title=f'Tendencia de "{selected_metric}" en {selected_region}', markers=True, labels={'value': 'Valor', 'year': 'Año'})
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Diagrama de Cajas":
        st.info("**Propósito:** Entender la distribución de una métrica a través de diferentes categorías.")
        data = filtered_df[(filtered_df['powertrain'] == 'EV') & (filtered_df['region'] != 'World')]
        fig = px.box(data, x='region', y='value', title=f'Distribución de "{selected_metric}" por Región', labels={'value': 'Valor', 'region': 'Región'})
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Mapa de Calor":
        st.info("**Propósito:** Visualizar la magnitud de una métrica en una matriz de dos dimensiones (Región vs. Año).")
        data = filtered_df[(filtered_df['powertrain'] == 'EV') & (filtered_df['region'] != 'World')].pivot_table(index='region', columns='year', values='value', aggfunc='sum')
        fig = px.imshow(data, title=f'Mapa de Calor de "{selected_metric}" (Región vs. Año)', labels=dict(x="Año", y="Región", color="Valor"))
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Gráfico Circular (Sunburst)":
        st.info("**Propósito:** Mostrar la proporción de cada parte sobre un todo, de forma jerárquica.")
        year_to_show = st.slider("Selecciona un año para la jerarquía", min_year, max_year, max_year - 1)
        data = df[(df['year'] == year_to_show) & (df['parameter'] == selected_metric) & (df['region'] == 'World') & (df['powertrain'].isin(['BEV', 'PHEV']))]
        fig = px.sunburst(data, path=['mode', 'powertrain'], values='value', title=f'Composición del Mercado Mundial en {year_to_show}')
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Diagrama de Dispersión":
        st.info("**Propósito:** Investigar la relación entre dos variables numéricas.")
        year_to_show = st.slider("Selecciona un año para la dispersión", min_year, max_year, max_year-1)
        df_stock = df[(df['parameter'] == 'EV stock') & (df['year'] == year_to_show) & (df['region'] != 'World')]
        df_sales = df[(df['parameter'] == 'EV sales') & (df['year'] == year_to_show) & (df['region'] != 'World')]
        merged_df = pd.merge(df_stock, df_sales, on='region', suffixes=('_stock', '_sales'))
        fig = px.scatter(merged_df, x='value_sales', y='value_stock', text='region', title=f'Ventas vs. Stock de EVs por Región en {year_to_show}', labels={'value_sales': 'Ventas de EVs', 'value_stock': 'Stock de EVs'})
        fig.update_traces(textposition='top center')
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Gráfico de Burbujas":
        st.info("**Propósito:** Añade una tercera dimensión (tamaño de la burbuja) al diagrama de dispersión.")
        year_to_show = st.slider("Selecciona un año para las burbujas", min_year, max_year, max_year-1)
        df_stock = df[(df['parameter'] == 'EV stock') & (df['year'] == year_to_show) & (df['region'] != 'World')]
        df_sales = df[(df['parameter'] == 'EV sales') & (df['year'] == year_to_show) & (df['region'] != 'World')]
        df_share = df[(df['parameter'] == 'EV sales share') & (df['year'] == year_to_show) & (df['region'] != 'World')]
        merged_df = pd.merge(df_stock, df_sales, on='region', suffixes=('_stock', '_sales'))
        merged_df = pd.merge(merged_df, df_share, on='region')
        fig = px.scatter(merged_df, x='value_sales', y='value_stock', size='value', color='region', hover_name='region', size_max=60, title=f'Ventas vs. Stock vs. Cuota de Mercado en {year_to_show}', labels={'value_sales': 'Ventas', 'value_stock': 'Stock', 'value': 'Cuota de Mercado (%)'})
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Diagrama de Pareto":
        st.info("**Propósito:** Identificar las contribuciones más importantes a un total (Principio 80/20).")
        year_to_show = st.slider("Selecciona un año para el análisis de Pareto", min_year, max_year, max_year - 1)
        data = filtered_df[(filtered_df['year'] == year_to_show) & (filtered_df['region'] != 'World') & (filtered_df['powertrain'] == 'EV')].groupby('region')['value'].sum().sort_values(ascending=False)
        data = data.to_frame()
        data['cumulative_sum'] = data['value'].cumsum()
        data['cumulative_perc'] = 100 * data['cumulative_sum'] / data['value'].sum()
        fig = go.Figure()
        fig.add_trace(go.Bar(x=data.index, y=data['value'], name=selected_metric))
        fig.add_trace(go.Scatter(x=data.index, y=data['cumulative_perc'], name='Porcentaje Acumulado', yaxis='y2', mode='lines+markers'))
        fig.update_layout(title=f'Análisis de Pareto para "{selected_metric}" en {year_to_show}', yaxis=dict(title='Valor'), yaxis2=dict(title='Porcentaje Acumulado (%)', overlaying='y', side='right', range=[0, 100]), legend=dict(x=0.1, y=0.9))
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()


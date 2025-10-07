import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import warnings

# --- Page Configuration ---
st.set_page_config(
    page_title="Dashboard Multi-Página de EVs",
    page_icon="🚗",
    layout="wide",
)

warnings.filterwarnings('ignore')

# --- Cached Data Loading and Cleaning ---
@st.cache_data
def load_and_clean_data(uploaded_file):
    """
    Loads and cleans data from an uploaded file. Results are cached.
    """
    try:
        df = pd.read_csv(uploaded_file)
        df['value'] = df['value'].astype(str).str.replace('.', '', regex=False)
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df.fillna(0, inplace=True)
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df.dropna(subset=['year'], inplace=True)
        df['year'] = df['year'].astype(int)
        return df
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        return pd.DataFrame()

# --- Page 1: Análisis de Tendencias Temporales ---
def page_trends(df):
    st.header("📈 Análisis de Tendencias Temporales")
    st.markdown("Esta sección muestra cómo han evolucionado las métricas a lo largo del tiempo.")

    metric = st.selectbox(
        "Selecciona la Métrica de Tendencia",
        options=sorted(df['parameter'].unique()),
        key='trends_metric'
    )

    st.subheader("Visión General: Tendencia Mundial")
    world_data = df[(df['region'] == 'World') & (df['parameter'] == metric) & (df['powertrain'] == 'EV')].groupby('year')['value'].sum()
    if not world_data.empty:
        fig_world = px.line(world_data, x=world_data.index, y='value', title=f"Tendencia Mundial de '{metric}'", markers=True)
        st.plotly_chart(fig_world, use_container_width=True)
    else:
        st.warning("No hay datos mundiales para la métrica seleccionada.")

    with st.expander("🔍 Exploración Detallada por Región"):
        st.markdown("Selecciona una o varias regiones para comparar sus tendencias.")
        regions = sorted([r for r in df['region'].unique() if r != 'World'])
        selected_regions = st.multiselect("Selecciona Regiones", options=regions, default=regions[:3])

        if selected_regions:
            detailed_data = df[
                (df['region'].isin(selected_regions)) &
                (df['parameter'] == metric) &
                (df['powertrain'] == 'EV')
            ].groupby(['year', 'region'])['value'].sum().reset_index()
            
            fig_detailed = px.line(detailed_data, x='year', y='value', color='region', title=f"Tendencia de '{metric}' por Región", markers=True)
            st.plotly_chart(fig_detailed, use_container_width=True)

# --- Page 2: Comparativa Entre Regiones ---
def page_comparison(df):
    st.header("🌍 Comparativa Regional")
    st.markdown("Compara el rendimiento de diferentes regiones en un año específico.")

    metric = st.selectbox(
        "Selecciona la Métrica de Comparación",
        options=sorted(df['parameter'].unique()),
        key='comparison_metric'
    )
    
    year = st.slider(
        "Selecciona un Año",
        min_value=int(df['year'].min()),
        max_value=int(df['year'].max()),
        value=int(df['year'].max()) - 1,
        key='comparison_year'
    )

    st.subheader(f"Visión General: Top 15 Regiones en {year}")
    
    general_data = df[
        (df['year'] == year) &
        (df['parameter'] == metric) &
        (df['powertrain'] == 'EV') &
        (df['region'] != 'World')
    ].groupby('region')['value'].sum().nlargest(15).sort_values()

    if not general_data.empty:
        fig_general = px.bar(general_data, x='value', y=general_data.index, orientation='h', title=f"Top 15 Regiones por '{metric}' en {year}")
        st.plotly_chart(fig_general, use_container_width=True)
    else:
        st.warning(f"No hay datos para '{metric}' en {year}.")
        
    with st.expander("🔍 Análisis de Pareto (Principio 80/20)"):
        st.markdown("Este gráfico identifica las regiones que contribuyen al 80% del total de la métrica, ayudando a enfocar los esfuerzos.")
        pareto_data = df[
            (df['year'] == year) &
            (df['parameter'] == metric) &
            (df['powertrain'] == 'EV') &
            (df['region'] != 'World')
        ].groupby('region')['value'].sum().sort_values(ascending=False).to_frame()

        if not pareto_data.empty:
            pareto_data['cumulative_perc'] = 100 * pareto_data['value'].cumsum() / pareto_data['value'].sum()
            fig_pareto = go.Figure()
            fig_pareto.add_trace(go.Bar(x=pareto_data.index, y=pareto_data['value'], name=metric))
            fig_pareto.add_trace(go.Scatter(x=pareto_data.index, y=pareto_data['cumulative_perc'], name='Porcentaje Acumulado', yaxis='y2', mode='lines+markers'))
            fig_pareto.update_layout(title=f'Análisis de Pareto para "{metric}" en {year}', yaxis2=dict(title='Porcentaje Acumulado (%)', overlaying='y', side='right', range=[0, 100]))
            st.plotly_chart(fig_pareto, use_container_width=True)

# --- Page 3: Composición del Mercado ---
def page_composition(df):
    st.header("📊 Composición del Mercado")
    st.markdown("Analiza la distribución del mercado por tipo de vehículo y tecnología.")

    metric = st.selectbox(
        "Selecciona la Métrica de Composición",
        options=[p for p in sorted(df['parameter'].unique()) if 'share' not in p], # Filter out share metrics for value-based composition
        key='composition_metric'
    )

    year = st.slider(
        "Selecciona un Año",
        min_value=int(df['year'].min()),
        max_value=int(df['year'].max()),
        value=int(df['year'].max()) - 1,
        key='composition_year'
    )
    
    st.subheader(f"Visión General: Composición Mundial en {year}")
    
    world_composition = df[
        (df['year'] == year) &
        (df['parameter'] == metric) &
        (df['region'] == 'World') &
        (df['powertrain'].isin(['BEV', 'PHEV']))
    ]

    if not world_composition.empty:
        fig_sunburst = px.sunburst(world_composition, path=['mode', 'powertrain'], values='value', title=f'Composición Jerárquica del Mercado Mundial ({metric}, {year})')
        st.plotly_chart(fig_sunburst, use_container_width=True)
    else:
        st.warning(f"No hay datos de composición mundial para '{metric}' en {year}.")
        
    with st.expander("🔍 Exploración Detallada por Región"):
        st.markdown("Selecciona una región para ver su composición de mercado específica.")
        regions = sorted([r for r in df['region'].unique() if r != 'World'])
        selected_region = st.selectbox("Selecciona una Región", options=regions, index=regions.index('USA'))

        if selected_region:
            region_composition = df[
                (df['year'] == year) &
                (df['parameter'] == metric) &
                (df['region'] == selected_region) &
                (df['powertrain'].isin(['BEV', 'PHEV']))
            ].groupby('powertrain')['value'].sum()

            if not region_composition.empty:
                fig_pie = px.pie(region_composition, names=region_composition.index, values='value', title=f"Distribución BEV vs. PHEV en {selected_region} ({metric}, {year})")
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                 st.warning(f"No hay datos de composición para '{selected_region}' en {year}.")


# --- Main Application Logic ---
def main():
    st.sidebar.title("Navegación del Dashboard")
    
    # --- 1. File Uploader ---
    uploaded_file = st.sidebar.file_uploader(
        "Sube tu archivo CSV",
        type=["csv"]
    )

    if uploaded_file is None:
        st.title("Bienvenido al Analizador de Datos de Vehículos Eléctricos 🚗")
        st.info("👈 Por favor, sube un archivo CSV para comenzar.")
        st.markdown("""
        Esta aplicación te permite explorar datos sobre el mercado de EVs a través de diferentes análisis.
        - **Análisis de Tendencias:** Observa el crecimiento a lo largo del tiempo.
        - **Comparativa Regional:** Compara el rendimiento entre países.
        - **Composición del Mercado:** Entiende la cuota de cada tipo de vehículo.
        
        Sube tu archivo para habilitar el menú de navegación y comenzar el análisis.
        """)
        return

    df = load_and_clean_data(uploaded_file)
    if df.empty:
        return

    # --- Page Selector ---
    page = st.sidebar.radio("Selecciona una página de análisis", 
                            ["Análisis de Tendencias", "Comparativa Regional", "Composición del Mercado"])
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("Creado con Streamlit y Plotly.")

    # --- Page Routing ---
    if page == "Análisis de Tendencias":
        page_trends(df)
    elif page == "Comparativa Regional":
        page_comparison(df)
    elif page == "Composición del Mercado":
        page_composition(df)

if __name__ == "__main__":
    main()


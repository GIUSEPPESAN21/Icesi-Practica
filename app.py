import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import warnings
import os

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Motor de Visualización de Datos de EVs",
    page_icon="📊",
    layout="wide",
)

warnings.filterwarnings('ignore')

# --- Carga de Datos en Caché ---
@st.cache_data
def load_and_clean_data(filepath):
    """Carga y limpia los datos desde un archivo CSV. Los resultados se guardan en caché."""
    try:
        df = pd.read_csv(filepath)
        df['value'] = df['value'].astype(str).str.replace('.', '', regex=False)
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df['value'].fillna(0, inplace=True)
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df.dropna(subset=['year'], inplace=True)
        df['year'] = df['year'].astype(int)
        return df
    except FileNotFoundError:
        st.error(f"Error: El archivo de datos '{filepath}' no fue encontrado.")
        return pd.DataFrame()

# --- Aplicación Principal ---
def main():
    st.title("📊 Motor de Visualización de Datos de EVs")
    st.markdown("Selecciona un tipo de gráfico en el panel lateral para analizar el mercado de vehículos eléctricos desde diferentes perspectivas.")

    # --- Carga de Datos ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'Practica ICESI.csv')
    df = load_and_clean_data(file_path)

    if df.empty:
        return

    # --- Panel Lateral de Controles (Sidebar) ---
    st.sidebar.header("Panel de Control")
    
    chart_types = [
        "Gráfico de Barras", "Gráfico Lineal", "Diagrama de Cajas",
        "Mapa de Calor", "Gráfico Circular (Sunburst)", "Diagrama de Dispersión",
        "Gráfico de Burbujas", "Gráfico de Barras Apiladas", "Diagrama de Pareto",
        "Gráfico en Cascada", "Gráfico de Embudo", "Cuadro de Manómetros", "Carta Radar"
    ]
    chart_type = st.sidebar.selectbox("Selecciona un Tipo de Gráfico", chart_types)
    
    # Filtros comunes
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros Generales")
    
    # Usar 'parameter' como métrica principal
    metric_options = ['EV stock', 'EV sales', 'EV stock share', 'EV sales share']
    selected_metric = st.sidebar.selectbox("Selecciona la Métrica Principal", metric_options)

    # Filtro de año
    min_year, max_year = int(df['year'].min()), int(df['year'].max())
    year_range = st.sidebar.slider("Selecciona un Rango de Años", min_year, max_year, (min_year, max_year))

    # Filtrar el DataFrame según los filtros comunes
    filtered_df = df[
        (df['parameter'] == selected_metric) &
        (df['year'] >= year_range[0]) &
        (df['year'] <= year_range[1])
    ]

    # --- Lógica de Visualización ---
    if chart_type == "Gráfico de Barras":
        st.subheader("Gráfico de Barras: Comparación de Magnitudes")
        st.info("**Propósito:** Comparar una métrica entre diferentes categorías. Ideal para ver qué regiones o tipos de vehículos lideran en un año específico.")
        
        year_to_show = st.slider("Selecciona un año para comparar", min_year, max_year, max_year - 1)
        data = filtered_df[(filtered_df['year'] == year_to_show) & (filtered_df['region'] != 'World') & (filtered_df['powertrain'] == 'EV')].groupby('region')['value'].sum().nlargest(15)
        
        fig = px.bar(data, x=data.index, y='value', title=f'Top 15 Regiones por "{selected_metric}" en {year_to_show}', labels={'value': 'Valor', 'region': 'Región'})
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Gráfico Lineal":
        st.subheader("Gráfico Lineal: Evolución en el Tiempo")
        st.info("**Propósito:** Mostrar cómo una métrica cambia a lo largo del tiempo. Perfecto para visualizar tendencias de crecimiento.")

        region_options = ['World'] + sorted(filtered_df['region'].unique())
        selected_region = st.selectbox("Selecciona una Región", region_options)

        data = filtered_df[(filtered_df['region'] == selected_region) & (filtered_df['powertrain'] == 'EV')].groupby('year')['value'].sum()
        
        fig = px.line(data, x=data.index, y='value', title=f'Tendencia de "{selected_metric}" en {selected_region}', markers=True, labels={'value': 'Valor', 'year': 'Año'})
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Diagrama de Cajas":
        st.subheader("Diagrama de Cajas (Box Plot): Distribución de Datos")
        st.info("**Propósito:** Entender la distribución de una métrica a través de diferentes categorías, mostrando la mediana, los cuartiles y los valores atípicos.")

        data = filtered_df[(filtered_df['powertrain'] == 'EV') & (filtered_df['region'] != 'World')]
        
        fig = px.box(data, x='region', y='value', title=f'Distribución de "{selected_metric}" por Región', labels={'value': 'Valor', 'region': 'Región'})
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Mapa de Calor":
        st.subheader("Mapa de Calor: Correlación entre Variables")
        st.info("**Propósito:** Visualizar la magnitud de una métrica en una matriz de dos dimensiones. Excelente para ver cómo la métrica varía entre regiones y a lo largo de los años simultáneamente.")

        data = filtered_df[(filtered_df['powertrain'] == 'EV') & (filtered_df['region'] != 'World')].pivot_table(index='region', columns='year', values='value', aggfunc='sum')
        
        fig = px.imshow(data, title=f'Mapa de Calor de "{selected_metric}" (Región vs. Año)', labels=dict(x="Año", y="Región", color="Valor"))
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Gráfico Circular (Sunburst)":
        st.subheader("Gráfico Sunburst: Visualización Jerárquica")
        st.info("**Propósito:** Mostrar la proporción de cada parte sobre un todo, de forma jerárquica. Aquí lo usamos para ver la composición del mercado por tipo de vehículo y tipo de motor (BEV/PHEV).")

        year_to_show = st.slider("Selecciona un año para la jerarquía", min_year, max_year, max_year - 1)
        data = df[(df['year'] == year_to_show) & (df['parameter'] == selected_metric) & (df['region'] == 'World') & (df['powertrain'].isin(['BEV', 'PHEV']))]
        
        fig = px.sunburst(data, path=['mode', 'powertrain'], values='value', title=f'Composición del Mercado Mundial en {year_to_show}')
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Diagrama de Dispersión":
        st.subheader("Diagrama de Dispersión: Relación entre dos Métricas")
        st.info("**Propósito:** Investigar la relación entre dos variables numéricas. Aquí comparamos el stock de EVs contra las ventas de EVs para identificar tendencias entre regiones.")
        
        year_to_show = st.slider("Selecciona un año para la dispersión", min_year, max_year, max_year-1)
        df_stock = df[(df['parameter'] == 'EV stock') & (df['year'] == year_to_show) & (df['region'] != 'World')]
        df_sales = df[(df['parameter'] == 'EV sales') & (df['year'] == year_to_show) & (df['region'] != 'World')]
        
        merged_df = pd.merge(df_stock, df_sales, on='region', suffixes=('_stock', '_sales'))
        
        fig = px.scatter(merged_df, x='value_sales', y='value_stock', text='region', title=f'Ventas vs. Stock de EVs por Región en {year_to_show}',
                         labels={'value_sales': 'Ventas de EVs', 'value_stock': 'Stock de EVs'})
        fig.update_traces(textposition='top center')
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Gráfico de Burbujas":
        st.subheader("Gráfico de Burbujas: Relación entre Tres Métricas")
        st.info("**Propósito:** Similar al de dispersión, pero añade una tercera dimensión representada por el tamaño de la burbuja. Aquí, el tamaño representa la cuota de mercado.")
        
        year_to_show = st.slider("Selecciona un año para las burbujas", min_year, max_year, max_year-1)
        df_stock = df[(df['parameter'] == 'EV stock') & (df['year'] == year_to_show) & (df['region'] != 'World')]
        df_sales = df[(df['parameter'] == 'EV sales') & (df['year'] == year_to_show) & (df['region'] != 'World')]
        df_share = df[(df['parameter'] == 'EV sales share') & (df['year'] == year_to_show) & (df['region'] != 'World')]
        
        merged_df = pd.merge(df_stock, df_sales, on='region', suffixes=('_stock', '_sales'))
        merged_df = pd.merge(merged_df, df_share, on='region')
        
        fig = px.scatter(merged_df, x='value_sales', y='value_stock', size='value', color='region',
                         hover_name='region', size_max=60, title=f'Ventas vs. Stock vs. Cuota de Mercado en {year_to_show}',
                         labels={'value_sales': 'Ventas', 'value_stock': 'Stock', 'value': 'Cuota de Mercado (%)'})
        st.plotly_chart(fig, use_container_width=True)
    
    # ... (Se añadirán más gráficos aquí) ...
    elif chart_type == "Diagrama de Pareto":
        st.subheader("Diagrama de Pareto: Principio 80/20")
        st.info("**Propósito:** Identificar los 'pocos vitales' que contribuyen a la mayoría del efecto. Aquí, vemos qué regiones representan el 80% de la métrica seleccionada.")

        year_to_show = st.slider("Selecciona un año para el análisis de Pareto", min_year, max_year, max_year - 1)
        data = filtered_df[(filtered_df['year'] == year_to_show) & (filtered_df['region'] != 'World') & (filtered_df['powertrain'] == 'EV')].groupby('region')['value'].sum().sort_values(ascending=False)
        
        data = data.to_frame()
        data['cumulative_sum'] = data['value'].cumsum()
        data['cumulative_perc'] = 100 * data['cumulative_sum'] / data['value'].sum()

        fig = go.Figure()
        fig.add_trace(go.Bar(x=data.index, y=data['value'], name=selected_metric))
        fig.add_trace(go.Scatter(x=data.index, y=data['cumulative_perc'], name='Porcentaje Acumulado', yaxis='y2', mode='lines+markers'))

        fig.update_layout(
            title=f'Análisis de Pareto para "{selected_metric}" en {year_to_show}',
            yaxis=dict(title='Valor'),
            yaxis2=dict(title='Porcentaje Acumulado (%)', overlaying='y', side='right', range=[0, 100]),
            legend=dict(x=0.1, y=0.9)
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning(f"El gráfico '{chart_type}' aún no está implementado.")


if __name__ == "__main__":
    main()


import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import os

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# --- Page Configuration ---
# Set the page configuration. This must be the first Streamlit command.
st.set_page_config(
    page_title="Análisis Interactivo de Vehículos Eléctricos",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Caching Data Loading and Cleaning ---
@st.cache_data
def load_and_clean_data(filepath):
    """
    Loads and cleans data from a CSV file. The results are cached to improve performance.
    Args:
        filepath (str): The path to the CSV file.
    Returns:
        pd.DataFrame: A cleaned and prepared pandas DataFrame.
    """
    try:
        df = pd.read_csv(filepath)
        # Clean the 'value' column
        df['value'] = df['value'].astype(str).str.replace('.', '', regex=False)
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df['value'].fillna(0, inplace=True)
        # Clean the 'year' column
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df.dropna(subset=['year'], inplace=True)
        df['year'] = df['year'].astype(int)
        return df
    except FileNotFoundError:
        st.error(f"Error: The data file '{filepath}' was not found. Please make sure it's in the same directory as the app.")
        return pd.DataFrame()

# --- Plotting Functions ---
def set_plot_style():
    """Sets a professional and aesthetically pleasing style for all generated plots."""
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (10, 6)
    plt.rcParams['axes.titlesize'] = 16
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10
    plt.rcParams['legend.fontsize'] = 10
    plt.rcParams['figure.dpi'] = 100

def plot_global_trends(df, parameter, region):
    """Plots historical and projected trends for a given parameter."""
    fig, ax = plt.subplots()
    data_to_plot = df[(df['parameter'] == parameter) & (df['region'] == region) & (df['powertrain'] == 'EV')]
    
    for category, style in [('Historical', '-'), ('Projection-APS', '--'), ('Projection-STEPS', ':')]:
        subset = data_to_plot[data_to_plot['category'] == category].groupby('year')['value'].sum()
        if not subset.empty:
            ax.plot(subset.index, subset.values, linestyle=style, marker='o', markersize=4, label=category)

    ax.set_title(f'Evolución de "{parameter}" en "{region}"', fontweight='bold')
    ax.set_xlabel('Año')
    ax.set_ylabel('Cantidad (en millones)')
    ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))
    ax.legend(title='Categoría')
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.tight_layout()
    return fig

def plot_powertrain_distribution(df, parameter, year, region):
    """Creates a pie chart showing the distribution between BEV and PHEV."""
    fig, ax = plt.subplots()
    data_to_plot = df[(df['parameter'] == parameter) & (df['year'] == year) & (df['region'] == region) & (df['powertrain'].isin(['BEV', 'PHEV']))]
    powertrain_summary = data_to_plot.groupby('powertrain')['value'].sum()
    
    if powertrain_summary.empty or powertrain_summary.sum() == 0:
        ax.text(0.5, 0.5, 'No hay datos disponibles', horizontalalignment='center', verticalalignment='center')
    else:
        ax.pie(powertrain_summary.values, labels=powertrain_summary.index, autopct='%1.1f%%',
               colors=sns.color_palette('pastel'), startangle=90, wedgeprops={'edgecolor': 'black'})
    
    ax.set_title(f'Distribución BEV vs. PHEV para "{parameter}" en {year} ({region})', fontweight='bold')
    return fig

# --- Main Application Logic ---
def main():
    # Set plot style
    set_plot_style()

    # --- Header ---
    st.title("⚡ Dashboard de Análisis del Mercado de Vehículos Eléctricos")
    st.markdown("""
    Esta aplicación interactiva permite explorar datos históricos y proyecciones sobre el stock y las ventas 
    de vehículos eléctricos (EVs) a nivel mundial. Utiliza los filtros en el panel lateral para personalizar los gráficos.
    """)

    # --- Data Loading ---
    # Construct the path to the data file relative to the script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'Practica ICESI.csv')
    df = load_and_clean_data(file_path)

    if df.empty:
        return

    # --- Sidebar for Filters ---
    st.sidebar.header("Filtros de Visualización")
    
    # Get unique values for filters
    sorted_regions = sorted(df['region'].unique())
    selected_region = st.sidebar.selectbox("Selecciona una Región", sorted_regions, index=sorted_regions.index('World'))
    
    min_year, max_year = int(df['year'].min()), int(df['year'].max())
    selected_year = st.sidebar.slider("Selecciona un Año", min_year, max_year, value=2022)

    selected_parameter_stock = "EV stock"
    selected_parameter_sales = "EV sales"

    # --- Body ---
    st.header(f"Análisis para: {selected_region}")
    
    # Create columns for layout
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Tendencia del Stock de EVs")
        fig_stock = plot_global_trends(df, selected_parameter_stock, selected_region)
        st.pyplot(fig_stock)

    with col2:
        st.subheader("Tendencia de las Ventas de EVs")
        fig_sales = plot_global_trends(df, selected_parameter_sales, selected_region)
        st.pyplot(fig_sales)
        
    st.markdown("---") # Visual separator
    
    st.header(f"Análisis Detallado para el año {selected_year}")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader(f"Distribución (Stock) BEV vs PHEV")
        fig_pie_stock = plot_powertrain_distribution(df, selected_parameter_stock, selected_year, selected_region)
        st.pyplot(fig_pie_stock)

    with col4:
        st.subheader(f"Distribución (Ventas) BEV vs PHEV")
        fig_pie_sales = plot_powertrain_distribution(df, selected_parameter_sales, selected_year, selected_region)
        st.pyplot(fig_pie_sales)
        
    # --- Data Explorer ---
    st.markdown("---")
    st.header("Explorador de Datos")
    if st.checkbox("Mostrar datos crudos"):
        st.dataframe(df)

if __name__ == "__main__":
    main()

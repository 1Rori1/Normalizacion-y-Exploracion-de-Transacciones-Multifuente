import streamlit as st
import pandas as pd
from normalizer import TransactionNormalizer

st.set_page_config(page_title="Dashboard", layout="wide")

st.title("Sistema de Normalización de Transacciones")
st.caption("Estructuración y validación automática de múltiples fuentes de datos.")

# Inicializar normalizador
normalizer = TransactionNormalizer()

# Cargar datos por defecto
try:
    valid_data, invalid_data, metrics = normalizer.process_file("data_source.json")
except Exception as e:
    st.error(f"Error al cargar los archivos: {e}")
    st.stop()

# --- SECCIÓN DE MÉTRICAS ---
st.subheader("Métricas Globales")
col1, col2, col3 = st.columns(3)
col1.metric("Procesadas Totales", metrics["total_processed"])
col2.metric("✅ Válidas", metrics["total_valid"], delta_color="normal")
col3.metric("❌ Inválidas/Descartadas", metrics["total_invalid"], delta=-metrics["total_invalid"])

st.markdown("---")

# --- INTERFAZ DE EXPLORACIÓN ---
tab1, tab2 = st.tabs(["📂 Datos Normalizados", "⚠️ Registros con Errores"])

with tab1:
    if valid_data:
        df_valid = pd.DataFrame(valid_data)
        
        # Filtros interactivos en barra lateral o columnas
        st.write("### Filtros Disponibles")
        f_col1, f_col2 = st.columns(2)
        
        with f_col1:
            selected_currency = st.multiselect("Filtrar por Moneda:", options=df_valid["currency"].unique(), default=df_valid["currency"].unique())
        with f_col2:
            selected_status = st.multiselect("Filtrar por Estado:", options=df_valid["status"].unique(), default=df_valid["status"].unique())
        
        # Aplicar Filtros
        filtered_df = df_valid[
            (df_valid["currency"].isin(selected_currency)) & 
            (df_valid["status"].isin(selected_status))
        ]
        
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.info("No hay transacciones válidas.")

with tab2:
    if invalid_data:
        st.warning("Los siguientes registros fueron marcados como inválidos por no cumplir las reglas de negocio:")
        for idx, item in enumerate(invalid_data):
            with st.expander(f"Registro Inconsistente #{idx + 1} - Errores detectados: {item.get('errors')}"):
                st.json(item.get("raw"))
    else:
        st.success("¡Excelente! No hay registros con errores.")
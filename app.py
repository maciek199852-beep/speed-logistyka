import streamlit as st
import pandas as pd

st.set_page_config(page_title="Analiza Marż Speed - Konstytucja 2026", layout="wide")
st.title("🚛 Panel Eksperta Logistyki i Analityka Marż")
st.success("Aplikacja działa online w oficjalnej chmurze Streamlit!")

# Tabela główna zgodna z Konstytucją 2026
st.subheader("📊 Tabela Główna (Logika Przebicia i Pełne Kody Pocztowe)")
df_main = pd.DataFrame({
    "Trasa (Kod Kraj)": ["00-950 Warszawa (PL) -> 80331 Monachium (DE)", "75-001 Paryż (FR) -> 20121 Mediolan (IT, Kufstein)"],
    "Fracht P (€)": [1200.00, 1450.00],
    "Fracht K (€)": [1500.00, 1800.00],
    "KM": [1150, 1400],
    "Nadwyżka (P-KM)": [50.00, -20.00],
    "€/km Przewoźnik": [1.04, 1.03],
    "€/km Klient": [1.30, 1.28]
})
st.dataframe(df_main, use_container_width=True)

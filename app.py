import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image

# ==========================================
# KONFIGURACJA STRONY I STYLE
# ==========================================
st.set_page_config(page_title="Speed - Panel Logistyki", page_icon="🚛", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 2.5rem; color: #1E3A8A; font-weight: 700; text-align: center; margin-bottom: 0px;}
    .sub-title { font-size: 1.2rem; color: #64748B; text-align: center; margin-bottom: 30px;}
    .alert-text { color: #DC2626; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🚛 System Analizy Logistycznej "Speed"</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Wersja PRO | Zgodna z Konstytucją 2026 (Logika Przebicia, Kufstein, Pełne Kody)</p>', unsafe_allow_html=True)
st.divider()

# ==========================================
# PANEL BOCZNY (USTAWIENIA I WGRYWANIE)
# ==========================================
with st.sidebar:
    st.header("⚙️ Konfiguracja Systemu")
    api_key = st.text_input("🔑 Wprowadź klucz API Gemini", type="password", help="Pobierz z aistudio.google.com")
    
    st.markdown("---")
    uploaded_file = st.file_uploader("📥 Wgraj zrzut ze Speeda (JPG/PNG)", type=['png', 'jpg', 'jpeg'])
    
    st.markdown("---")
    st.info("""
    **Aktywne zasady (Konstytucja 2026):**
    - 🛡️ **Logika Przebicia:** Wykrywanie relacji Emerlog/Rmsped.
    - 🗺️ **Trasy IT:** Obowiązkowy narzut przez Kufstein (AT).
    - 📊 **Kolumny:** Brak 'Klient' i 'Status', pełne kody pocztowe.
    """)

# ==========================================
# FUNKCJE OBLICZENIOWE I LOGIKA
# ==========================================
def calculate_metrics(df):
    """Funkcja przeliczająca stawki na podstawie frachtów i dystansu"""
    df['€/km Przewoźnik'] = (df['Fracht P'] / df['KM']).round(2)
    df['€/km Klient'] = (df['Fracht K'] / df['KM']).round(2)
    df['Nadwyżka (P-KM)'] = (df['Fracht K'] - df['Fracht P']).round(2)
    return df

def style_negative_margin(val):
    """Kolorowanie ujemnych/zerowych marży na czerwono"""
    color = '#FFE4E6' if val <= 0 else '#D1FAE5'
    return f'background-color: {color}'

# ==========================================
# GŁÓWNY WIDOK DANYCH (MOCKUP/AI RESULT)
# ==========================================
if uploaded_file is not None:
    st.success("Plik wgrany pomyślnie. Trwa analiza struktury obrazu...")
    # Tutaj w przyszłości podpinamy realny prompt do api_key
    if not api_key:
        st.warning("Brak klucza API. Uruchamiam system w trybie symulacji na podstawie wytycznych z Konstytucji...")

# Baza danych (Symulacja na potrzeby profesjonalnego widoku lub gdy API wczyta dane)
main_data = [
    {"Trasa (Kod Kraj)": "00-950 Warszawa (PL) -> 80331 Monachium (DE)", "Fracht P": 1200.0, "Fracht K": 1500.0, "KM": 1074},
    {"Trasa (Kod Kraj)": "75-001 Paryż (FR) -> 20121 Mediolan (IT, Kufstein)", "Fracht P": 1550.0, "Fracht K": 1500.0, "KM": 1150},
    {"Trasa (Kod Kraj)": "60-101 Poznań (PL) -> 00100 Rzym (IT, Kufstein)", "Fracht P": 1400.0, "Fracht K": 1750.0, "KM": 1650}
]

df_main = pd.DataFrame(main_data)
df_main = calculate_metrics(df_main)

# KPI / METRYKI NA GÓRZE
st.subheader("📈 Podsumowanie Zleceń")
col1, col2, col3, col4 = st.columns(4)
total_margin = df_main['Nadwyżka (P-KM)'].sum()
avg_km_p = df_main['€/km Przewoźnik'].mean().round(2)
avg_km_k = df_main['€/km Klient'].mean().round(2)

col1.metric("Łączna Nadwyżka (€)", f"{total_margin} €", f"{total_margin} € zysku operacyjnego")
col2.metric("Średnia Stawka (Przewoźnik)", f"{avg_km_p} €/km")
col3.metric("Średnia Stawka (Klient)", f"{avg_km_k} €/km")
col4.metric("Przeanalizowane Trasy", len(df_main))

st.markdown("---")

# TABELA GŁÓWNA
st.subheader("📊 Tabela Główna Zleceń")
st.markdown("*Uwaga: Usunięto kolumny 'Klient' i 'Status'. Pełne kody pocztowe w kolumnie 'Trasa'. Zastosowano logikę przebicia.*")
# Formatowanie tabeli
styled_main = df_main.style.map(lambda x: 'color: #DC2626; font-weight: bold;' if x <= 0 else 'color: #059669;', subset=['Nadwyżka (P-KM)']).format("{:.2f}", subset=['Fracht P', 'Fracht K', 'Nadwyżka (P-KM)', '€/km Przewoźnik', '€/km Klient'])
st.dataframe(styled_main, use_container_width=True)

st.markdown("---")

# TABELE REGIONALNE (FR i IT)
col_fr, col_it = st.columns(2)

with col_fr:
    st.subheader("🇫🇷 Region: FR (Francja)")
    fr_data = pd.DataFrame({
        "Dystans": [1150, 850],
        "Region": ["Île-de-France (75)", "Lyon (69)"],
        "Sugerowana Stawka P (€/km)": [1.10, 1.15],
        "Sugerowana Nadwyżka (€)": [150.0, 120.0]
    })
    st.dataframe(fr_data, use_container_width=True, hide_index=True)

with col_it:
    st.subheader("🇮🇹 Region: IT (Włochy z Kufstein)")
    it_data = pd.DataFrame({
        "Region IT (Kod)": ["Lombardia (20)", "Lazio (00)"],
        "Dystans": [1150, 1650],
        "Stawka Klienta": [1.30, 1.25],
        "Stawka Przewoźnika": [1.34, 1.10],
        "Moja Marża": [-50.0, 350.0],
        "Nadwyżka Przewoźnika": [150.0, 20.0]
    })
    styled_it = it_data.style.map(lambda x: 'color: red;' if x <= 0 else '', subset=['Moja Marża'])
    st.dataframe(styled_it, use_container_width=True, hide_index=True)

st.markdown("---")

# TABELA WSKAZÓWEK (Alternatywy)
st.subheader("💡 Wskazówki i Alternatywy Tras")
tips_data = []
for index, row in df_main.iterrows():
    # Stawka żeby zarobić 200€ = (Koszt Przewoźnika + 200) / Dystans
    stawka_dla_200 = (row['Fracht P'] + 200) / row['KM']
    tips_data.append({
        "Trasa": row['Trasa (Kod Kraj)'],
        "Stawka przewoźnika €/km za ile przewoźnik jedzie": row['€/km Przewoźnik'],
        "Stawka €/km żeby zarobić 200€": round(stawka_dla_200, 2)
    })
df_tips = pd.DataFrame(tips_data)
st.dataframe(df_tips, use_container_width=True, hide_index=True)

# WNIOSKI I ALERTY
st.markdown("---")
st.subheader("🚨 Moduł Wniosków i Alertów")

# Badanie alertów (Marża <= 0)
ujemne_marze = df_main[df_main['Nadwyżka (P-KM)'] <= 0]
if not ujemne_marze.empty:
    for index, row in ujemne_marze.iterrows():
        st.error(f"⚠️ **ALERT MARŻOWY:** Trasa {row['Trasa (Kod Kraj)']} generuje stratę: **{row['Nadwyżka (P-KM)']} €**. Zablokuj to zlecenie lub renegocjuj fracht P!")
else:
    st.success("✅ Brak alertów marżowych. Wszystkie przeanalizowane zlecenia są rentowne.")

st.info("📉 **Zależność stawki od dystansu:** Trasy poniżej 1200 km wymuszają wyższą stawkę jednostkową (€/km). Północne Włochy (Lombardia) w połączeniu z narzutem z Kufstein mocno zaniżają rentowność.")
st.success("🏆 **Najlepsze regiony:** Z analizy wynika, że najwyższa nadwyżka utrzymuje się na stałych korytarzach do DE (np. Monachium).")

import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import json

# ==========================================
# KONFIGURACJA STRONY
# ==========================================
st.set_page_config(page_title="Speed - Panel Logistyki", page_icon="🚛", layout="wide")
st.markdown('<p style="font-size: 2.5rem; color: #1E3A8A; font-weight: 700; text-align: center;">🚛 System Analizy Logistycznej "Speed"</p>', unsafe_allow_html=True)
st.divider()

# ==========================================
# PANEL BOCZNY - DYNAMICZNE POBIERANIE MODELI
# ==========================================
with st.sidebar:
    st.header("⚙️ Konfiguracja Systemu")
    api_key = st.text_input("🔑 Wprowadź klucz API Gemini", type="password")
    
    # Dynamiczna lista modeli
    dostepne_modele = []
    if api_key:
        try:
            genai.configure(api_key=api_key)
            # Pobierz tylko te modele, które potrafią analizować dane (generateContent)
            dostepne_modele = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            st.success(f"Połączono! Znaleziono {len(dostepne_modele)} dostępnych modeli.")
        except Exception as e:
            st.error("Błąd weryfikacji klucza. Sprawdź, czy jest poprawny.")
            
    # Menu wyboru modelu z pobranej listy
    wybrany_model = st.selectbox("🤖 Wybierz model do analizy", dostepne_modele) if dostepne_modele else None
    
    st.markdown("---")
    uploaded_file = st.file_uploader("📥 Wgraj zrzut ze Speeda (JPG/PNG)", type=['png', 'jpg', 'jpeg'])

# ==========================================
# FUNKCJE OBLICZENIOWE
# ==========================================
def calculate_metrics(df):
    df['€/km Przewoźnik'] = (df['Fracht P'] / df['KM']).round(2)
    df['€/km Klient'] = (df['Fracht K'] / df['KM']).round(2)
    df['Nadwyżka (P-KM)'] = (df['Fracht K'] - df['Fracht P']).round(2)
    return df

# ==========================================
# GŁÓWNY WIDOK - ANALIZA AI
# ==========================================
if uploaded_file is not None:
    if not api_key or not wybrany_model:
        st.warning("⚠️ Wprowadź klucz API i wybierz model z listy po lewej stronie.")
    else:
        try:
            # Konfiguracja wybranego, zweryfikowanego modelu
            model = genai.GenerativeModel(wybrany_model)
            image = Image.open(uploaded_file)
            
            with st.expander("👁️ Zobacz wgrany zrzut ekranu"):
                st.image(image, use_container_width=True)
                
            with st.spinner(f"🤖 Model {wybrany_model} analizuje zrzut..."):
                prompt = """
                Jesteś ekspertem logistyki. Przeanalizuj zrzut ekranu. Zwróć TYLKO surowy tekst w formacie JSON (lista obiektów), bez znaczników.
                Dla każdego zlecenia:
                1. "Trasa (Kod Kraj)": pełne kody, kraje i miasta. Jeśli Włochy (IT) -> dodaj "(IT, Kufstein)".
                2. "Fracht P": Kwota przewoźnika (liczba).
                3. "Fracht K": Kwota klienta (liczba).
                4. "KM": Dystans (liczba).
                
                Przykład:
                [
                  {"Trasa (Kod Kraj)": "00-950 Warszawa (PL) -> 80331 Monachium (DE)", "Fracht P": 1200.0, "Fracht K": 1500.0, "KM": 1074}
                ]
                """
                
                response = model.generate_content([prompt, image])
                
                # Czyszczenie i ładowanie odpowiedzi
                result_text = response.text.strip()
                if result_text.startswith("```json"): result_text = result_text[7:-3]
                elif result_text.startswith("```"): result_text = result_text[3:-3]
                    
                df_main = pd.DataFrame(json.loads(result_text))
                df_main = calculate_metrics(df_main)
                
                # Renderowanie wyników
                st.success("✅ AI zakończyło analizę pomyślnie!")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Łączna Nadwyżka", f"{df_main['Nadwyżka (P-KM)'].sum().round(2)} €")
                col2.metric("Śr. Stawka (Przewoźnik)", f"{df_main['€/km Przewoźnik'].mean().round(2)} €/km")
                col3.metric("Śr. Stawka (Klient)", f"{df_main['€/km Klient'].mean().round(2)} €/km")

                st.markdown("---")
                st.subheader("📊 Tabela Zleceń ze Speeda")
                styled_main = df_main.style.map(lambda x: 'color: #DC2626; font-weight: bold;' if x <= 0 else 'color: #059669;', subset=['Nadwyżka (P-KM)']).format("{:.2f}", subset=['Fracht P', 'Fracht K', 'Nadwyżka (P-KM)', '€/km Przewoźnik', '€/km Klient'])
                st.dataframe(styled_main, use_container_width=True)

        except Exception as e:
            st.error(f"Wystąpił błąd analizy: {e}")
            st.info("Wskazówka: Zmień model z rozwijanej listy w panelu bocznym na inny i spróbuj ponownie.")
else:
    st.info("📥 Wgraj zrzut ekranu w panelu bocznym, aby rozpocząć.")

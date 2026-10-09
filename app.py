import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import json

# ==========================================
# KONFIGURACJA STRONY I STYLE
# ==========================================
st.set_page_config(page_title="Speed - Panel Logistyki", page_icon="🚛", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 2.5rem; color: #1E3A8A; font-weight: 700; text-align: center; margin-bottom: 0px;}
    .sub-title { font-size: 1.2rem; color: #64748B; text-align: center; margin-bottom: 30px;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🚛 System Analizy Logistycznej "Speed"</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Wersja PRO z modułem AI | Zgodna z Konstytucją 2026</p>', unsafe_allow_html=True)
st.divider()

# ==========================================
# PANEL BOCZNY (USTAWIENIA I WGRYWANIE)
# ==========================================
with st.sidebar:
    st.header("⚙️ Konfiguracja Systemu")
    api_key = st.text_input("🔑 Wprowadź klucz API Gemini", type="password")
    st.markdown("---")
    uploaded_file = st.file_uploader("📥 Wgraj zrzut ze Speeda (JPG/PNG)", type=['png', 'jpg', 'jpeg'])

# ==========================================
# FUNKCJE OBLICZENIOWE I LOGIKA
# ==========================================
def calculate_metrics(df):
    df['€/km Przewoźnik'] = (df['Fracht P'] / df['KM']).round(2)
    df['€/km Klient'] = (df['Fracht K'] / df['KM']).round(2)
    df['Nadwyżka (P-KM)'] = (df['Fracht K'] - df['Fracht P']).round(2)
    return df

# ==========================================
# GŁÓWNY WIDOK - INTEGRACJA Z AI (GEMINI)
# ==========================================
if uploaded_file is not None:
    if not api_key:
        st.warning("⚠️ Wprowadź klucz API Gemini w panelu po lewej stronie, aby AI mogło przeczytać dane ze zrzutu.")
    else:
        # Inicjalizacja AI
        genai.configure(api_key=api_key)
        
        try:
            # Automatyczne wykrywanie modelu dostępnego dla Twojego klucza (Kuloodporne rozwiązanie)
            dostepne_modele = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            wybrany_model = "gemini-1.5-flash-latest" # Opcja domyślna
            for m in dostepne_modele:
                if '1.5-flash' in m:
                    wybrany_model = m.replace('models/', '')
                    break
            
            model = genai.GenerativeModel(wybrany_model)
            image = Image.open(uploaded_file)
            
            with st.expander("👁️ Zobacz wgrany zrzut ekranu"):
                st.image(image, use_container_width=True)
                
            with st.spinner(f"🤖 Sztuczna inteligencja ({wybrany_model}) skanuje dane ze Speeda..."):
                # Prompt wymuszający strukturę Konstytucji 2026
                prompt = """
                Jesteś ekspertem logistyki. Przeanalizuj ten zrzut ekranu z systemu transportowego. 
                Zwróć TYLKO surowy tekst w formacie JSON (lista obiektów), bez znaczników markdown.
                Dla każdego rozpoznanego zlecenia wyciągnij:
                1. "Trasa (Kod Kraj)": pełne kody pocztowe, kraje i nazwy miast (np. "00-950 Warszawa (PL) -> 80331 Monachium (DE)"). Jeśli Włochy (IT), obowiązkowo dopisz "(IT, Kufstein)".
                2. "Fracht P": Kwota frachtu przewoźnika (tylko liczba, bez waluty).
                3. "Fracht K": Kwota frachtu klienta (tylko liczba).
                4. "KM": Dystans (tylko liczba całkowita, pobierz z obrazu lub oszacuj jeśli brak).
                
                Przykładowy poprawny output:
                [
                  {"Trasa (Kod Kraj)": "00-950 Warszawa (PL) -> 80331 Monachium (DE)", "Fracht P": 1200.0, "Fracht K": 1500.0, "KM": 1074}
                ]
                """
                
                response = model.generate_content([prompt, image])
                
                # Czyszczenie odpowiedzi
                result_text = response.text.strip()
                if result_text.startswith("```json"):
                    result_text = result_text[7:-3]
                elif result_text.startswith("```"):
                    result_text = result_text[3:-3]
                    
                data = json.loads(result_text)
                df_main = pd.DataFrame(data)
                df_main = calculate_metrics(df_main)
                
                st.success("✅ AI zakończyło analizę!")
                
                st.subheader("📈 Podsumowanie Zleceń (Z tego zrzutu)")
                col1, col2, col3, col4 = st.columns(4)
                total_margin = df_main['Nadwyżka (P-KM)'].sum().round(2)
                avg_km_p = df_main['€/km Przewoźnik'].mean().round(2)
                avg_km_k = df_main['€/km Klient'].mean().round(2)

                col1.metric("Łączna Nadwyżka (€)", f"{total_margin} €", f"{total_margin} € czystego zysku")
                col2.metric("Średnia Stawka (Przewoźnik)", f"{avg_km_p} €/km")
                col3.metric("Średnia Stawka (Klient)", f"{avg_km_k} €/km")
                col4.metric("Znalezione Trasy na Zrzucie", len(df_main))

                st.markdown("---")
                st.subheader("📊 Tabela Zleceń ze Speeda")
                styled_main = df_main.style.map(lambda x: 'color: #DC2626; font-weight: bold;' if x <= 0 else 'color: #059669;', subset=['Nadwyżka (P-KM)']).format("{:.2f}", subset=['Fracht P', 'Fracht K', 'Nadwyżka (P-KM)', '€/km Przewoźnik', '€/km Klient'])
                st.dataframe(styled_main, use_container_width=True)

                st.markdown("---")
                st.subheader("🚨 Raport i Alerty Marżowe")
                ujemne_marze = df_main[df_main['Nadwyżka (P-KM)'] <= 0]
                if not ujemne_marze.empty:
                    for index, row in ujemne_marze.iterrows():
                        st.error(f"⚠️ **ALERT MARŻOWY:** Trasa {row['Trasa (Kod Kraj)']} ma zerową lub ujemną nadwyżkę (**{row['Nadwyżka (P-KM)']} €**). Zweryfikuj koszty przewoźnika!")
                else:
                    st.success("✅ Brak alertów! Wszystkie zlecenia widoczne na zrzucie generują dodatnią marżę operacyjną.")

        except Exception as e:
            st.error(f"Wystąpił błąd podczas analizy obrazu przez sztuczną inteligencję: {e}")
            st.info("💡 Wskazówka: Upewnij się, że wpisany klucz API jest poprawny.")
else:
    st.info("📥 Aby rozpocząć prawdziwą analizę, wgraj zdjęcie lub zrzut ekranu zleceń ze Speeda w panelu bocznym.")

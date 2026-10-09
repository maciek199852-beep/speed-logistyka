import streamlit as st
import pandas as pd
import google.generativeai as genai
import googlemaps
from PIL import Image
import json

# ==========================================
# KONFIGURACJA STRONY
# ==========================================
st.set_page_config(page_title="Speed - Panel Logistyki", page_icon="🚛", layout="wide")
st.markdown('<p style="font-size: 2.5rem; color: #1E3A8A; font-weight: 700; text-align: center;">🚛 System Analizy Logistycznej "Speed"</p>', unsafe_allow_html=True)
st.markdown('<p style="font-size: 1.2rem; color: #64748B; text-align: center; margin-bottom: 30px;">Pełna automatyzacja: AI + Google Maps (Tryb Diagnostyczny)</p>', unsafe_allow_html=True)
st.divider()

# ==========================================
# PANEL BOCZNY 
# ==========================================
with st.sidebar:
    st.header("⚙️ Konfiguracja Systemu")
    api_key_gemini = st.text_input("🔑 Klucz API Gemini (AI)", type="password")
    
    dostepne_modele = []
    if api_key_gemini:
        try:
            genai.configure(api_key=api_key_gemini)
            dostepne_modele = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        except:
            pass
            
    wybrany_model = st.selectbox("🤖 Wybierz model do analizy", dostepne_modele) if dostepne_modele else None
    
    st.markdown("---")
    api_key_maps = st.text_input("📍 Klucz API Google Maps", type="password")
    
    st.markdown("---")
    uploaded_file = st.file_uploader("📥 Wgraj zrzut ze Speeda (JPG/PNG)", type=['png', 'jpg', 'jpeg'])

# ==========================================
# OBLICZANIE KILOMETRÓW Z OBSŁUGĄ BŁĘDÓW
# ==========================================
def oblicz_realne_km(zaladunek, rozladunek, kod_kraju_rozladunku, maps_client):
    try:
        punkty_posrednie = ["Kufstein, Austria"] if "IT" in kod_kraju_rozladunku.upper() else None
        
        directions = maps_client.directions(
            zaladunek,
            rozladunek,
            waypoints=punkty_posrednie
        )
        
        if directions:
            dystans_metry = sum([leg['distance']['value'] for leg in directions[0]['legs']])
            return int(dystans_metry / 1000)
        else:
            st.warning(f"Mapy nie znalazły trasy dla: {zaladunek} -> {rozladunek}")
            return 1
    except Exception as e:
        # TUTAJ WYŚWIETLIMY DOKŁADNY BŁĄD OD GOOGLE MAPS
        st.error(f"❌ Błąd klucza Google Maps: {e}")
        return 1

def calculate_metrics(df):
    df['€/km Przewoźnik'] = (df['Fracht P'] / df['KM']).round(2)
    df['€/km Klient'] = (df['Fracht K'] / df['KM']).round(2)
    df['Nadwyżka (P-KM)'] = (df['Fracht K'] - df['Fracht P']).round(2)
    return df

# ==========================================
# GŁÓWNY WIDOK - ANALIZA AI + MAPY
# ==========================================
if uploaded_file is not None:
    if not api_key_gemini or not api_key_maps or not wybrany_model:
        st.warning("⚠️ Wprowadź OBA klucze API i wybierz model.")
    else:
        try:
            gmaps = googlemaps.Client(key=api_key_maps)
            model = genai.GenerativeModel(wybrany_model)
            image = Image.open(uploaded_file)
            
            with st.expander("👁️ Zobacz wgrany zrzut ekranu"):
                st.image(image, use_container_width=True)
                
            with st.spinner(f"🤖 Krok 1/2: AI analizuje zrzut..."):
                prompt = """
                Jesteś ekspertem logistyki. Zwróć JSON (lista obiektów), bez znaczników.
                Dla każdego zlecenia wyciągnij:
                1. "Zaladunek": Pełny kod pocztowy, miasto i kraj (np. "00-950 Warszawa, PL").
                2. "Rozladunek": Pełny kod pocztowy, miasto i kraj (np. "20121 Mediolan, IT").
                3. "Kraj Rozladunku": Tylko dwuliterowy kod kraju (np. "IT", "DE").
                4. "Fracht P": Kwota przewoźnika (liczba).
                5. "Fracht K": Kwota klienta (liczba).
                
                Przykład:
                [{"Zaladunek": "00-950 Warszawa, PL", "Rozladunek": "80331 Monachium, DE", "Kraj Rozladunku": "DE", "Fracht P": 1200, "Fracht K": 1500}]
                """
                response = model.generate_content([prompt, image])
                
                result_text = response.text.strip()
                if result_text.startswith("```json"): result_text = result_text[7:-3]
                elif result_text.startswith("```"): result_text = result_text[3:-3]
                
                zlecenia = json.loads(result_text)
            
            with st.spinner(f"🗺️ Krok 2/2: Obliczanie precyzyjnych tras przez Google Maps..."):
                gotowe_dane = []
                for z in zlecenia:
                    km = oblicz_realne_km(z["Zaladunek"], z["Rozladunek"], z["Kraj Rozladunku"], gmaps)
                    
                    dopisek = " (przez Kufstein)" if "IT" in z["Kraj Rozladunku"].upper() else ""
                    trasa = f"{z['Zaladunek']} -> {z['Rozladunek']}{dopisek}"
                    
                    gotowe_dane.append({
                        "Trasa (Kod Kraj)": trasa,
                        "Fracht P": float(z["Fracht P"]),
                        "Fracht K": float(z["Fracht K"]),
                        "KM": km
                    })
                    
                df_main = pd.DataFrame(gotowe_dane)
                df_main = calculate_metrics(df_main)
                
                st.success("✅ Zakończono!")
                
                st.subheader("📊 Tabela Zleceń")
                styled_main = df_main.style.map(lambda x: 'color: #DC2626; font-weight: bold;' if x <= 0 else 'color: #059669;', subset=['Nadwyżka (P-KM)']).format("{:.2f}", subset=['Fracht P', 'Fracht K', 'Nadwyżka (P-KM)', '€/km Przewoźnik', '€/km Klient'])
                st.dataframe(styled_main, use_container_width=True)

        except Exception as e:
            st.error(f"Wystąpił błąd: {e}")
else:
    st.info("📥 Wgraj zrzut ekranu w panelu bocznym, aby rozpocząć.")

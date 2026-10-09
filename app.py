import streamlit as st
import pandas as pd
import google.generativeai as genai
import requests
from PIL import Image
import json

# ==========================================
# KONFIGURACJA STRONY
# ==========================================
st.set_page_config(page_title="Speed - Panel Logistyki", page_icon="🚛", layout="wide")
st.markdown('<p style="font-size: 2.5rem; color: #1E3A8A; font-weight: 700; text-align: center;">🚛 System Analizy Logistycznej "Speed"</p>', unsafe_allow_html=True)
st.markdown('<p style="font-size: 1.2rem; color: #64748B; text-align: center; margin-bottom: 30px;">Pełna automatyzacja: AI + Nowe Google Routes API</p>', unsafe_allow_html=True)
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
# OBLICZANIE KILOMETRÓW (NOWE ROUTES API)
# ==========================================
def oblicz_realne_km(zaladunek, rozladunek, kod_kraju_rozladunku, api_key):
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "routes.distanceMeters"
    }
    payload = {
        "origin": {"address": zaladunek},
        "destination": {"address": rozladunek},
        "travelMode": "DRIVE"
    }
    
    # Kufstein dla Włoch (Konstytucja 2026)
    if "IT" in kod_kraju_rozladunku.upper():
        payload["intermediates"] = [{"address": "Kufstein, Austria"}]
        
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if 'routes' in data and len(data['routes']) > 0:
                metry = data['routes'][0].get('distanceMeters', 0)
                return int(metry / 1000)
        else:
            st.error(f"Błąd Google Routes API: {response.text}")
            return 1
    except Exception as e:
        st.error(f"Błąd połączenia: {e}")
        return 1
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
            
            with st.spinner(f"🗺️ Krok 2/2: Obliczanie tras przez Google Routes API..."):
                gotowe_dane = []
                for z in zlecenia:
                    km = oblicz_realne_km(z["Zaladunek"], z["Rozladunek"], z["Kraj Rozladunku"], api_key_maps)
                    
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
                
                st.subheader("📊 Tabela Zleceń (100% precyzyjne kilometry)")
                styled_main = df_main.style.map(lambda x: 'color: #DC2626; font-weight: bold;' if x <= 0 else 'color: #059669;', subset=['Nadwyżka (P-KM)']).format("{:.2f}", subset=['Fracht P', 'Fracht K', 'Nadwyżka (P-KM)', '€/km Przewoźnik', '€/km Klient'])
                st.dataframe(styled_main, use_container_width=True)

        except Exception as e:
            st.error(f"Wystąpił błąd: {e}")
else:
    st.info("📥 Wgraj zrzut ekranu w panelu bocznym, aby rozpocząć.")

import streamlit as st
import google.generativeai as genai
import pdfplumber
from PIL import Image
import io
import json

# --- KONFIGURATION ---
st.set_page_config(page_title="Gemini Inköpslista", page_icon="🛒")
st.title("🛒 Inköpslista (Powered by Gemini)")

# Hämta API-nyckel från Secrets
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("Ingen API-nyckel hittades. Lägg in GOOGLE_API_KEY i Streamlit Secrets.")
    st.stop()

# --- FUNKTIONER ---

def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def analyze_fridge_gemini(image_bytes, diet_text, days):
    # Gemini vill ha bilden som ett PIL-objekt, inte base64
    image = Image.open(io.BytesIO(image_bytes))
    
    # Välj modell (Flash är snabb och bra, Pro är ännu smartare)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Du är en expert på kost och logistik.
    1. Titta på bilden av kylskåpet.
    2. Läs kostschemat nedan.
    3. Räkna ut vad som saknas för {days} dagar.
    
    KOSTSCHEMA:
    {diet_text}
    
    INSTRUKTIONER:
    - Ignorera basvaror som kryddor och olja.
    - Svara ENDAST med ett JSON-objekt. Inget annat prat.
    - Format: {{"Kategori": ["Vara 1", "Vara 2"]}}
    """

    # Skicka bild och text till modellen
    # generation_config tvingar svaret att vara JSON
    response = model.generate_content(
        [prompt, image],
        generation_config={"response_mime_type": "application/json"}
    )
    
    # Returnera som Python-dictionary
    return json.loads(response.text)

# --- APPENS LOGIK ---

if 'shopping_list' not in st.session_state:
    st.session_state.shopping_list = None

st.subheader("1. Ladda upp Kostschema")
uploaded_pdf = st.file_uploader("PDF-fil", type="pdf")

if uploaded_pdf:
    diet_text = extract_text_from_pdf(uploaded_pdf)
    st.success("✅ Schema inläst")
    
    days = st.slider("Antal dagar", 1, 7, 3)

    st.subheader("2. Fota Kylen")
    camera_image = st.camera_input("Ta bild")

    if camera_image:
        if st.button("Skapa lista med Gemini ✨"):
            with st.spinner("Gemini tittar i kylen..."):
                try:
                    bytes_data = camera_image.getvalue()
                    st.session_state.shopping_list = analyze_fridge_gemini(bytes_data, diet_text, days)
                    st.rerun()
                except Exception as e:
                    st.error(f"Ett fel uppstod: {e}")

    # Visa resultat
    if st.session_state.shopping_list:
        st.write("---")
        st.header("Din Checklista")
        
        if st.button("Rensa"):
            st.session_state.shopping_list = None
            st.rerun()

        data = st.session_state.shopping_list
        for category, items in data.items():
            if items:
                st.subheader(category)
                for item in items:
                    st.checkbox(item, key=f"{category}-{item}")

else:
    st.info("Ladda upp PDF först.")

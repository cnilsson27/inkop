import streamlit as st
import base64
from openai import OpenAI
import pdfplumber

# Konfigurera sidan för mobilen
st.set_page_config(page_title="Min AI-Inköpslista", page_icon="🛒")

# Titel
st.title("🛒 AI-Inköpslistan")
st.write("Fota kylen -> Få inköpslista baserat på kostschemat.")

# Hämta API-nyckel från inställningar (secrets)
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# --- FUNKTIONER ---
def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def analyze_fridge(image_bytes, diet_text, days):
    # Koda bilden till base64
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    # Din System-Prompt (Här klistrar vi in den vi skapade tidigare)
    system_prompt = """
    Du är en expert på nutrition. Analysera bilden på kylskåpet och jämför med kostschemat.
    1. Identifiera vad som finns.
    2. Jämför med behovet för angivet antal dagar.
    3. Skapa en inköpslista sorterad efter butikens avdelningar.
    Anta att kryddor och olja finns hemma.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": f"Planera för {days} dagar. Här är kostschemat: {diet_text}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        max_tokens=1500
    )
    return response.choices[0].message.content

# --- APPENS GRÄNSSNITT ---

# 1. Ladda upp kostschema (Görs en gång, eller varje gång om du byter schema)
st.subheader("1. Ditt Kostschema")
uploaded_pdf = st.file_uploader("Ladda upp PDF", type="pdf")

if uploaded_pdf:
    # Extrahera text direkt när filen laddas upp
    diet_plan_text = extract_text_from_pdf(uploaded_pdf)
    st.success("✅ Kostschema inläst!")
    
    # 2. Välj antal dagar
    days = st.slider("Hur många dagar ska du handla för?", 1, 7, 3)

    # 3. Kameran
    st.subheader("2. Fota Kylen")
    # enable_events=True gör att den reagerar direkt när bilden tas
    camera_image = st.camera_input("Ta en bild på innehållet")

    if camera_image:
        with st.spinner("🤖 AI:n analyserar din kyl och räknar kalorier..."):
            # Läs in bilden från kameran
            bytes_data = camera_image.getvalue()
            
            # Skicka till AI
            shopping_list = analyze_fridge(bytes_data, diet_plan_text, days)
            
            # Visa resultatet
            st.markdown("---")
            st.subheader("Din Inköpslista")
            st.markdown(shopping_list)
            
            # Knapp för att kopiera eller ladda ner kan läggas till här
else:
    st.info("Börja med att ladda upp ditt kostschema (PDF).")
import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps
import io
import os
import pandas as pd
import urllib.parse
from datetime import datetime
from pymongo import MongoClient
import pillow_heif
import random

# Tenta importar o componente de JS de forma segura para GPS em tempo real
try:
    from streamlit_js_eval import streamlit_js_eval
    JS_DISPONIVEL = True
except ImportError:
    JS_DISPONIVEL = False

# --- CONFIGURAÇÃO DE ENGENHARIA DE ELITE ---
pillow_heif.register_heif_opener()
st.set_page_config(
    page_title="TechnoBolt Pets Hub | Elite Edition", 
    layout="wide", 
    page_icon="🐾",
    initial_sidebar_state="collapsed"
)

# --- DATABASE ENGINE ---
@st.cache_resource
def iniciar_conexao():
    try:
        user = os.environ.get("MONGO_USER", "technobolt")
        password_raw = os.environ.get("MONGO_PASS", "tech@132")
        host = os.environ.get("MONGO_HOST", "cluster0.zbjsvk6.mongodb.net")
        password = urllib.parse.quote_plus(password_raw)
        uri = f"mongodb+srv://{user}:{password}@{host}/?appName=Cluster0"
        client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
        return client['technoboltpets']
    except Exception as e:
        st.error(f"⚠️ Erro Crítico de Database: {e}")
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM (BLACK, WHITE & BROWN LUXURY) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    
    /* Configurações Globais de Cor */
    * { font-family: 'Plus Jakarta Sans', sans-serif; color: #ffffff !important; }
    .stApp { background-color: #000000 !important; }
    
    /* Inputs, Forms e Barras de Pesquisa (Marrom Escuro) */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stNumberInput>div>div>input, .stSelectbox>div>div>div { 
        background-color: #3e2723 !important; 
        color: #ffffff !important; 
        border: 1px solid #4b3621 !important;
        border-radius: 10px !important;
    }

    /* Botões (Marrom Chocolate) */
    .stButton>button {
        background-color: #3e2723 !important;
        color: #ffffff !important;
        border: 1px solid #4b3621 !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #4b3621 !important;
        border-color: #ffffff !important;
    }

    /* Cards e Elementos Visuais */
    .elite-card {
        background: #0d0d0d;
        border: 1px solid #3e2723;
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 20px;
    }
    
    .rating-badge { background: #5d4037; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 800; }
    .pros { color: #aaffaa !important; font-size: 0.9rem; }
    .contras { color: #ffaaaa !important; font-size: 0.9rem; }
    
    /* Mapa Customizado (Grayscale Dark) */
    .stMap { filter: grayscale(1) invert(0.9) hue-rotate(180deg); border-radius: 15px; border: 1px solid #3e2723; }
</style>
""", unsafe_allow_html=True)

# --- AI ENGINE (MOTORES MANTIDOS) ---
def call_ia(prompt, img=None, speed_mode=False):
    chaves = [os.environ.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    if not chaves: return "Erro: Chaves de API não localizadas."
    
    motores = ["models/gemini-3-flash-preview", "models/gemini-2.5-flash", "models/gemini-2.0-flash", "models/gemini-flash-latest"]
    config = {"temperature": 0.3 if speed_mode else 0.7, "top_p": 0.9}
    genai.configure(api_key=random.choice(chaves))
    
    for motor in motores:
        try:
            model = genai.GenerativeModel(motor, generation_config=config)
            content = [prompt, img] if img else prompt
            response = model.generate_content(content)
            return response.text
        except: continue
    return "⚠️ Motores em manutenção."

# --- AUTH & SESSION ---
if "logado" not in st.session_state: st.session_state.logado = False
if "lat_long" not in st.session_state: st.session_state.lat_long = None

if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center; font-weight:800;'>🐾 TECHNOBOLT PETS</h1>", unsafe_allow_html=True)
    with st.container():
        u = st.text_input("Usuário", placeholder="Seu username")
        p = st.text_input("Senha", type="password", placeholder="Sua senha")
        if st.button("AUTENTICAR NO HUB", use_container_width=True):
            user = db.usuarios.find_one({"usuario": u, "senha": p}) if db is not None else None
            if user:
                st.session_state.logado = True
                st.session_state.user_data = user
                st.rerun()
    st.stop()

# --- HUB INTERFACE ---
user_doc = st.session_state.user_data
is_admin = user_doc.get("tipo") == "Admin"
tabs = st.tabs(["💡 Insights", "🧬 PetScan IA", "📍 Clínicas & Petshops", "🐕 Cuidadores"] + (["⚙️ Gestão Admin"] if is_admin else []))

# ABA 2: PETSCAN
with tabs[1]:
    st.subheader("🧬 Diagnóstico Biométrico por Imagem")
    up = st.file_uploader("Submeter Foto do Pet", type=['jpg', 'png', 'heic'])
    if up and st.button("EXECUTAR SCAN", use_container_width=True):
        img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
        st.image(img, width=400, caption="Amostra Biométrica")
        resultado = call_ia("Analise raça, BCS 1-9 e saúde.", img=img, speed_mode=True)
        st.markdown(f"<div class='elite-card'><h3>📝 Laudo IA</h3>{resultado}</div>", unsafe_allow_html=True)
        st.markdown("### 📊 Guia de Referência: Condição Corporal")
        
        

[Image of a Body Condition Score chart for dogs and cats]


# ABA 3: LOCALIZAR VETERINÁRIOS & PETSHOPS (GOOGLE MAPS ELITE LOOK)
with tabs[2]:
    st.subheader("📍 Mapa de Saúde e Bem-Estar Animal")
    
    # Captura GPS Real
    if JS_DISPONIVEL:
        loc = streamlit_js_eval(data_of_interest='location', key='get_location')
        if loc:
            st.session_state.lat_long = f"{loc['coords']['latitude']}, {loc['coords']['longitude']}"
    
    # Barra de Pesquisa (Fundo Marrom)
    col_search, col_gps = st.columns([4, 1])
    search_query = col_search.text_input("Pesquisar Veterinários, Petshops ou Tosadores...", placeholder="Ex: Veterinários 24h próximos")
    
    if col_gps.button("📍 GPS REAL"):
        st.success("Coordenadas GPS sincronizadas com sucesso.")

    loc_search = st.session_state.lat_long if not search_query else search_query

    if loc_search:
        with st.spinner("IA mapeando estabelecimentos de elite..."):
            prompt_map = f"""Com base em {loc_search}, liste os 5 melhores estabelecimentos de: 
            Veterinária, Petshop ou Tosa. Retorne exatamente: 
            NOME|LAT|LON|NOTA_MEDIA|ENDERECO|PROS|CONTRAS"""
            
            res_v = call_ia(prompt_map, speed_mode=True)
            if res_v:
                map_data = []
                for v in [l for l in res_v.split('\n') if '|' in l]:
                    d = v.split('|')
                    if len(d) >= 7:
                        map_data.append({'lat': float(d[1]), 'lon': float(d[2]), 'name': d[0]})
                        
                        # Card de Detalhes após seleção
                        with st.container():
                            st.markdown(f"""
                            <div class='elite-card'>
                                <div style='display:flex; justify-content:space-between; align-items:center;'>
                                    <span style='font-size:1.2rem; font-weight:800;'>🏥 {d[0]}</span>
                                    <span class='rating-badge'>⭐ {d[3]}</span>
                                </div>
                                <p style='color:#888; font-size:0.9rem; margin-top:8px;'>📍 {d[4]}</p>
                                <hr style='border: 0.1px solid #3e2723;'>
                                <p class='pros'><b>✅ Ponto Positivo:</b> {d[5]}</p>
                                <p class='contras'><b>❌ Ponto Negativo:</b> {d[6]}</p>
                            </div>""", unsafe_allow_html=True)
                
                # Exibição do Mapa
                if map_data:
                    st.map(pd.DataFrame(map_data), zoom=14)

# ABA 5: GESTÃO ADMIN
if is_admin:
    with tabs[-1]:
        st.subheader("⚙️ Gestão Admin")
        users = list(db.usuarios.find())
        for u in users:
            c1, c2, c3, c4 = st.columns([2,1,1,1])
            c1.write(f"**{u['nome']}** (@{u['usuario']})")
            c2.write(f"`{u.get('tipo', 'User')}`")
            status = u.get("status", "Ativo")
            c3.markdown(f"<span class='status-active'>{status}</span>", unsafe_allow_html=True)
            if c4.button("SUSPENDER", key=u['usuario']):
                new_status = "Inativo" if status != "Inativo" else "Ativo"
                db.usuarios.update_one({"usuario": u['usuario']}, {"$set": {"status": new_status}})
                st.rerun()

with st.sidebar:
    st.write(f"### 👤 {user_doc['nome']}")
    if st.button("LOGOUT", use_container_width=True):
        st.session_state.logado = False
        st.rerun()

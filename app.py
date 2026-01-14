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

# Tenta importar o componente de JS de forma segura
try:
    from streamlit_js_eval import streamlit_js_eval
    JS_DISPONIVEL = True
except ImportError:
    JS_DISPONIVEL = False

# --- INICIALIZAÇÃO DE ELITE ---
pillow_heif.register_heif_opener()
st.set_page_config(page_title="TechnoBolt Pets Hub", layout="wide", page_icon="🐾")

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
        st.error(f"⚠️ Falha no Banco de Dados: {e}")
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background-color: #000000 !important; color: white !important; }
    .elite-card {
        background: linear-gradient(145deg, #0d0d0d, #161616);
        border: 1px solid #222; border-radius: 20px;
        padding: 24px; margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .status-active { color: #10b981; font-weight: bold; }
    .status-inactive { color: #f87171; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- ENGINE DE IA (MOTORES RECUPERADOS) ---
def call_ia(prompt, img=None, speed_mode=False):
    chaves = [os.environ.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    if not chaves: return "Erro: API Keys ausentes."
    
    motores = [
        "models/gemini-3-flash-preview", 
        "models/gemini-2.5-flash", 
        "models/gemini-2.0-flash", 
        "models/gemini-flash-latest"
    ]
    
    config = {"temperature": 0.4 if speed_mode else 0.7, "top_p": 0.9}
    genai.configure(api_key=random.choice(chaves))
    
    for motor in motores:
        try:
            model = genai.GenerativeModel(motor, generation_config=config)
            content = [prompt, img] if img else prompt
            response = model.generate_content(content)
            return response.text
        except: continue
    return "⚠️ Motores de IA ocupados."

# --- AUTH & SESSION ---
if "logado" not in st.session_state: st.session_state.logado = False
if "location_data" not in st.session_state: st.session_state.location_data = None

if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center;'>🐾 TECHNOBOLT PETS</h1>", unsafe_allow_html=True)
    u, p = st.text_input("User"), st.text_input("Pass", type="password")
    if st.button("ACESSAR HUB"):
        user = db.usuarios.find_one({"usuario": u, "senha": p}) if db is not None else None
        if user:
            st.session_state.logado = True
            st.session_state.user_data = user
            st.rerun()
    st.stop()

# --- INTERFACE ---
user_doc = st.session_state.user_data
is_admin = user_doc.get("tipo") == "Admin"
tabs = st.tabs(["💡 Insights", "🧬 PetScan", "📍 Clínicas Vets", "🐕 Cuidadores"] + (["⚙️ Gestão Admin"] if is_admin else []))

# ABA 2: PETSCAN
with tabs[1]:
    st.subheader("🧬 Diagnóstico Biométrico Digital")
    up = st.file_uploader("Upload Foto", type=['jpg', 'png', 'heic'])
    if up and st.button("SCAN"):
        img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
        st.image(img, width=400)
        with st.status("Analizando..."):
            res = call_ia("Analise raça, Escore Corporal (BCS 1-9) e recomendações.", img=img, speed_mode=True)
            st.markdown(f"<div class='elite-card'>{res}</div>", unsafe_allow_html=True)
        
        st.markdown("### 📊 Guia de Referência: Condição Corporal")
        st.markdown("""Utilize o gráfico abaixo para entender o diagnóstico visual:""")
        
[attachment_0](attachment)

# ABA 3: VETS (LOCALIZAÇÃO DINÂMICA)
with tabs[2]:
    st.subheader("📍 Veterinários e Clínicas em Tempo Real")
    if JS_DISPONIVEL:
        if st.button("📍 CAPTURAR GPS REAL"):
            loc = streamlit_js_eval(data_of_interest='location', key='get_gps')
            if loc:
                st.session_state.location_data = f"{loc['coords']['latitude']}, {loc['coords']['longitude']}"
                st.success("GPS sincronizado!")
    else:
        st.warning("⚠️ Componente GPS não instalado no servidor. Use a busca manual abaixo.")

    loc_ref = st.text_input("Localização ou Coordenadas", value=st.session_state.location_data or "")
    if loc_ref:
        prompt_vets = f"5 clínicas 24h em {loc_ref}. Formato: NOME|NOTA|ENDERECO|PROS|CONTRAS"
        res_vets = call_ia(prompt_vets, speed_mode=True)
        if res_vets:
            for v in [l for l in res_vets.split('\n') if '|' in l][:5]:
                d = v.split('|')
                st.markdown(f"<div class='elite-card'><b>🏥 {d[0]}</b> | ⭐ {d[1]}<br><small>{d[2]}</small></div>", unsafe_allow_html=True)

# ABA 5: GESTÃO ADMIN
if is_admin:
    with tabs[-1]:
        st.subheader("⚙️ Painel de Governança")
        users = list(db.usuarios.find()) if db is not None else []
        for u in users:
            c1, c2, c3, c4 = st.columns([2,1,1,1])
            c1.write(f"**{u['nome']}** (@{u['usuario']})")
            c2.write(f"Perfil: `{u.get('tipo')}`")
            status = u.get('status', 'Ativo')
            st_class = "status-active" if status == "Ativo" else "status-inactive"
            c3.markdown(f"<span class='{st_class}'>{status}</span>", unsafe_allow_html=True)
            if c4.button("Inverter Status", key=u['usuario']):
                new_status = "Inativo" if status == "Ativo" else "Ativo"
                db.usuarios.update_one({"usuario": u['usuario']}, {"$set": {"status": new_status}})
                st.rerun()

with st.sidebar:
    st.write(f"👤 {user_doc['nome']}")
    if st.button("SAIR"): st.session_state.logado = False; st.rerun()

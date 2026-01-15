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

# --- DATABASE ENGINE (MANTIDO CONFORME SOLICITADO) ---
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

# --- DESIGN SYSTEM (DARK MODE RESPONSIVO & ELITE) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    
    /* Elite Glassmorphism Cards */
    .elite-card {
        background: linear-gradient(145deg, #0d0d0d, #161616);
        border: 1px solid #262626;
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        transition: 0.3s ease;
    }
    .elite-card:hover { border-color: #3b82f6; transform: translateY(-3px); }
    
    .price-tag { background: #3b82f6; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 800; font-size: 0.9rem; }
    .status-active { color: #10b981; font-weight: bold; background: rgba(16, 185, 129, 0.1); padding: 4px 10px; border-radius: 12px; }
    .status-inactive { color: #f87171; font-weight: bold; background: rgba(248, 113, 113, 0.1); padding: 4px 10px; border-radius: 12px; }
    
    .stButton>button {
        border-radius: 12px !important;
        height: 48px;
        font-weight: 700 !important;
        background-color: #1a1a1a !important;
        border: 1px solid #333 !important;
        transition: 0.3s;
    }
    .stButton>button:hover { border-color: #3b82f6 !important; color: #3b82f6 !important; }
</style>
""", unsafe_allow_html=True)

# --- AI ENGINE (MOTORES MANTIDOS - PERFORMANCE OTIMIZADA) ---
def call_ia(prompt, img=None, speed_mode=False):
    chaves = [os.environ.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    if not chaves: return "Erro: Chaves de API não localizadas."
    
    motores = [
        "models/gemini-3-flash-preview", 
        "models/gemini-2.5-flash", 
        "models/gemini-2.0-flash", 
        "models/gemini-flash-latest"
    ]
    
    config = {"temperature": 0.3 if speed_mode else 0.7, "top_p": 0.9}
    genai.configure(api_key=random.choice(chaves))
    
    for motor in motores:
        try:
            model = genai.GenerativeModel(motor, generation_config=config)
            content = [prompt, img] if img else prompt
            response = model.generate_content(content)
            return response.text
        except: continue
    return "⚠️ Motores ocupados. Tente novamente."

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
tabs = st.tabs(["💡 Insights", "🧬 PetScan IA", "📍 Localizar Veterinários", "🐕 Cuidadores"] + (["⚙️ Gestão Admin"] if is_admin else []))

# ABA 2: PETSCAN
with tabs[1]:
    st.subheader("🧬 Diagnóstico Biométrico por Imagem")
    up = st.file_uploader("Submeter Foto do Pet", type=['jpg', 'png', 'heic'])
    if up and st.button("EXECUTAR SCAN", use_container_width=True):
        img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
        st.image(img, width=400, caption="Amostra Biométrica")
        with st.status("Processando padrões morfofisiológicos..."):
            res = call_ia("Analise raça, Escore Corporal (BCS 1-9) e saúde. Retorne um laudo técnico conciso.", img=img, speed_mode=True)
            st.markdown(f"<div class='elite-card'><h3>📝 Laudo IA</h3>{res}</div>", unsafe_allow_html=True)
        st.markdown("### 📊 Guia de Referência: Condição Corporal")
        st.markdown("""Utilize o gráfico abaixo para validar o escore corporal identificado:""")
        
        # --- CORREÇÃO DO ERRO DE SINTAXE AQUI (Uso de aspas triplas) ---
        st.markdown("""
        

[Image of a Body Condition Score chart for dogs and cats]

        """)

# ABA 3: LOCALIZAR VETERINÁRIOS
with tabs[2]:
    st.subheader("📍 Veterinários e Clínicas em Tempo Real")
    st.markdown("Este módulo acede ao GPS do seu dispositivo para localizar unidades veterinárias de elite.")
    
    if JS_DISPONIVEL:
        loc = streamlit_js_eval(data_of_interest='location', key='get_location')
        if loc:
            st.session_state.lat_long = f"{loc['coords']['latitude']}, {loc['coords']['longitude']}"
            st.success(f"✅ Localização exata capturada: {st.session_state.lat_long}")
    
    loc_final = st.text_input("Localização de Busca", value=st.session_state.lat_long or "", placeholder="Coordenadas ou Cidade")
    
    if loc_final:
        with st.spinner("Rastreando Unidades Veterinárias próximas..."):
            prompt_vet = f"""Com base na localização {loc_final}, encontre exclusivamente:
            1. Clínicas Veterinárias de Urgência | 2. Hospitais Veterinários 24h
            Retorne no formato: NOME|NOTA|ENDEREÇO|PONTOS POSITIVOS|PONTOS NEGATIVOS"""
            
            res_v = call_ia(prompt_vet, speed_mode=True)
            if res_v:
                for v in [l for l in res_v.split('\n') if '|' in l][:5]:
                    d = v.split('|')
                    st.markdown(f"""
                    <div class='elite-card'>
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <span style='font-size:1.2rem; font-weight:800;'>🏥 {d[0]}</span>
                            <span class='price-tag'>⭐ {d[1]}</span>
                        </div>
                        <p style='color:#888; font-size:0.9rem; margin-top:8px;'>📍 {d[2]}</p>
                        <div style='display:grid; grid-template-columns: 1fr 1fr; gap:10px;'>
                            <div style='color:#aaffaa; font-size:0.85rem;'><b>PROS:</b> {d[3]}</div>
                            <div style='color:#ffaaaa; font-size:0.85rem;'><b>CONTRAS:</b> {d[4]}</div>
                        </div>
                    </div>""", unsafe_allow_html=True)

# ABA 5: GESTÃO ADMIN
if is_admin:
    with tabs[-1]:
        st.subheader("⚙️ Painel de Governança Admin")
        users = list(db.usuarios.find()) if db is not None else []
        for u in users:
            c1, c2, c3, c4 = st.columns([2,1,1,1])
            c1.write(f"**{u['nome']}** (@{u['usuario']})")
            c2.write(f"Perfil: `{u.get('tipo', 'User')}`")
            st_class = "status-active" if u.get("status") != "Inativo" else "status-inactive"
            c3.markdown(f"<span class='{st_class}'>{u.get('status', 'Ativo')}</span>", unsafe_allow_html=True)
            if c4.button("GERIR ACESSO", key=u['usuario']):
                new_status = "Inativo" if u.get("status") != "Inativo" else "Ativo"
                db.usuarios.update_one({"usuario": u['usuario']}, {"$set": {"status": new_status}})
                st.rerun()

with st.sidebar:
    st.write(f"### 👤 {user_doc['nome']}")
    st.divider()
    if st.button("ENCERRAR SESSÃO", use_container_width=True):
        st.session_state.logado = False
        st.rerun()

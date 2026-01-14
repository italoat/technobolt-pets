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

# --- INICIALIZAÇÃO ---
pillow_heif.register_heif_opener()
st.set_page_config(page_title="TechnoBolt Pets Hub", layout="wide", page_icon="🐾")

# --- CONEXÃO MONGODB ---
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
        st.error(f"Erro no Banco de Dados: {e}")
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM: BLACK, WHITE & GRAY ---
st.markdown("""
<style>
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    h1, h2, h3, p, span, label { color: #ffffff !important; }
    .stTextInput>div>div>input { background-color: #333333 !important; color: #ffffff !important; border: 1px solid #555555 !important; }
    .stButton>button { background-color: #555555 !important; color: #ffffff !important; border-radius: 8px; font-weight: bold; width: 100%; }
    .clinic-card { background-color: #1a1a1a; border: 1px solid #333333; border-radius: 12px; padding: 20px; margin-bottom: 25px; }
    .pros { color: #aaffaa; font-size: 0.85rem; margin-bottom: 5px; }
    .contras { color: #ffaaaa; font-size: 0.85rem; }
    /* Ajuste para o mapa não ficar muito alto */
    .stMap { filter: grayscale(1) invert(1); border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- MOTOR DE IA ---
def call_ia(prompt, model_name="models/gemini-2.0-flash", img=None):
    chaves = [os.environ.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    if not chaves: return "Erro: API Key"
    genai.configure(api_key=random.choice(chaves))
    try:
        model = genai.GenerativeModel(model_name)
        if img:
            response = model.generate_content([prompt, img])
        else:
            response = model.generate_content(prompt)
        return response.text
    except: return "Serviço Indisponível"

# --- LOGIN ---
if "logado" not in st.session_state: st.session_state.logado = False
if "ultimo_scan" not in st.session_state: st.session_state.ultimo_scan = None

if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center;'>🐾 TechnoBolt Pets</h1>", unsafe_allow_html=True)
    u, p = st.text_input("Usuário"), st.text_input("Senha", type="password")
    if st.button("ACESSAR HUB"):
        user = db.usuarios.find_one({"usuario": u, "senha": p}) if db else None
        if user: 
            st.session_state.logado = True
            st.session_state.user_data = user
            st.rerun()
    st.stop()

# --- TABS ---
tab_dicas, tab_scan, tab_vets = st.tabs(["💡 Insights", "🧬 PetScan", "📍 Localizar Vets"])

# --- ABA 1: DICAS (MOTOR FLASH-LATEST) ---
with tab_dicas:
    st.markdown("### Dicas de Performance Pet")
    p_dicas = f"4 dicas curtas pet. Verão 2026. Contexto: {st.session_state.ultimo_scan or 'Geral'}. Formato: TAG|DICA"
    res = call_ia(p_dicas, model_name="models/gemini-flash-latest")
    cols = st.columns(4)
    if res:
        for i, linha in enumerate([l for l in res.split('\n') if '|' in l][:4]):
            tag, texto = linha.split('|')
            cols[i].markdown(f"<div style='background:#1a1a1a; padding:15px; border-radius:10px; border:1px solid #333; height:150px;'><small style='color:#888;'>{tag}</small><br>{texto}</div>", unsafe_allow_html=True)

# --- ABA 2: SCAN ---
with tab_scan:
    st.subheader("🧬 Diagnóstico Biométrico")
    up = st.file_uploader("Foto", type=['jpg', 'png', 'heic'])
    if up and st.button("EXECUTAR SCAN"):
        img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
        st.image(img, width=300)
        resultado = call_ia("Analise raça, score corporal (BCS) e pelagem.", img=img)
        st.session_state.ultimo_scan = resultado
        st.markdown(f"<div class='clinic-card'>{resultado}</div>", unsafe_allow_html=True)
        

[Image of a body condition score chart for dogs and cats]


# --- ABA 3: VETS (COM MAPA DINÂMICO) ---
with tab_vets:
    st.subheader("📍 Encontrar Melhores Clínicas")
    loc_user = st.text_input("Sua localização (ex: Lapa, SP)", key="loc_vets")
    
    if st.button("BUSCAR 5 MELHORES CLÍNICAS") and loc_user:
        with st.spinner("IA localizando unidades hospitalares..."):
            prompt_vets = f"""
            Liste as 5 melhores clínicas veterinárias 24h em {loc_user}. 
            Retorne EXATAMENTE este formato por linha:
            NOME|LATITUDE|LONGITUDE|ENDERECO|PRÓS|CONTRAS
            Exemplo: Hospital Vet|-23.55|-46.63|Rua X, 10|Equipe PhD|Preço alto
            """
            res_vets = call_ia(prompt_vets)
            
            if res_vets:
                for vet in [l for l in res_vets.split('\n') if '|' in l][:5]:
                    dados = vet.split('|')
                    if len(dados) >= 6:
                        with st.container():
                            st.markdown(f"<div class='clinic-card'>", unsafe_allow_html=True)
                            st.markdown(f"### 🏥 {dados[0]}") # Nome
                            
                            # MINI MAPA (Abaixo do nome, acima do endereço)
                            try:
                                lat, lon = float(dados[1]), float(dados[2])
                                map_df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
                                st.map(map_df, zoom=15, size=20)
                            except: st.warning("Mapa indisponível para esta unidade.")
                            
                            st.markdown(f"<p style='color:#888; margin-top:10px;'>📍 {dados[3]}</p>", unsafe_allow_html=True) # Endereço
                            st.markdown(f"<p class='pros'><b>✅ Prós:</b> {dados[4]}</p>", unsafe_allow_html=True)
                            st.markdown(f"<p class='contras'><b>❌ Contras:</b> {dados[5]}</p>", unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)

with st.sidebar:
    st.write(f"**Tutor:** {user_doc.get('nome', 'User')}")
    if st.button("LOGOUT"): st.session_state.logado = False; st.rerun()

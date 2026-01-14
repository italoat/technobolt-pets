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

    .stTextInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #333333 !important; color: #ffffff !important; border: 1px solid #555555 !important;
    }
    
    .stButton>button {
        background-color: #555555 !important; color: #ffffff !important; 
        border-radius: 8px; border: 1px solid #777777; font-weight: bold; width: 100%;
    }
    .stButton>button:hover { background-color: #777777 !important; border-color: #ffffff !important; }

    .tip-card, .clinic-card {
        background-color: #1a1a1a; border: 1px solid #333333;
        border-radius: 12px; padding: 20px; margin-bottom: 15px;
    }
    .tip-tag { color: #888888; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
    
    .pros { color: #aaffaa; font-size: 0.85rem; }
    .contras { color: #ffaaaa; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# --- MOTOR DE IA ---
def call_ia(prompt, model_name="models/gemini-2.0-flash", img=None):
    chaves = [os.environ.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    if not chaves: return "Erro: Chave API não configurada."
    
    genai.configure(api_key=random.choice(chaves))
    
    # Rotação automática de modelos caso o principal falhe
    motores = [model_name, "models/gemini-2.0-flash", "models/gemini-1.5-flash"]
    
    for motor in motores:
        try:
            model = genai.GenerativeModel(motor)
            if img:
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')
                blob = {"mime_type": "image/jpeg", "data": img_byte_arr.getvalue()}
                response = model.generate_content([prompt, blob])
            else:
                response = model.generate_content(prompt)
            return response.text
        except:
            continue
    return "Serviço de IA temporariamente indisponível."

# --- LOGIN ---
if "logado" not in st.session_state: st.session_state.logado = False
if "ultimo_scan" not in st.session_state: st.session_state.ultimo_scan = None

if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center;'>🐾 TechnoBolt Pets</h1>", unsafe_allow_html=True)
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("ACESSAR HUB"):
        user = db.usuarios.find_one({"usuario": u, "senha": p}) if db else None
        if user:
            st.session_state.logado = True
            st.session_state.user_data = user
            st.rerun()
    st.stop()

user_doc = st.session_state.user_data
tab_dicas, tab_scan, tab_vets = st.tabs(["💡 Insights", "🧬 PetScan", "📍 Localizar Vets"])

# --- ABA 1: DICAS ---
with tab_dicas:
    st.markdown("### Dicas de Performance Pet")
    clima = "Janeiro 2026 (Verão)"
    contexto = st.session_state.ultimo_scan if st.session_state.ultimo_scan else "Geral"
    
    res_dicas = call_ia(f"4 dicas curtas para pet. Contexto: {clima}, Pet: {contexto}. Formato: TAG|DICA", model_name="models/gemini-flash-latest")
    
    cols = st.columns(4)
    if res_dicas:
        linhas = [l for l in res_dicas.split('\n') if '|' in l][:4]
        for i, linha in enumerate(linhas):
            tag, texto = linha.split('|')
            cols[i].markdown(f"<div class='tip-card'><span class='tip-tag'>{tag}</span><br>{texto}</div>", unsafe_allow_html=True)

# --- ABA 2: SCAN (COM CORREÇÃO DE SINTAXE) ---
with tab_scan:
    st.subheader("🧬 Diagnóstico Biométrico")
    up = st.file_uploader("Foto do pet", type=['jpg', 'png', 'heic'])
    if up and st.button("EXECUTAR SCAN"):
        img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
        st.image(img, width=300)
        # Corrigido: Passando apenas um modelo por vez
        resultado = call_ia("Analise raça, score corporal e pelagem.", model_name="models/gemini-2.0-flash", img=img)
        st.session_state.ultimo_scan = resultado
        st.markdown(f"<div class='clinic-card'>{resultado}</div>", unsafe_allow_html=True)

# --- ABA 3: VETS (LOCALIZAÇÃO DINÂMICA) ---
with tab_vets:
    st.subheader("📍 Encontrar Melhores Clínicas")
    
    # Campo de localização em cinza
    loc_user = st.text_input("Digite sua cidade ou bairro (ex: Pompéia, SP)", key="loc_user")
    
    if st.button("BUSCAR 5 MELHORES CLÍNICAS"):
        if loc_user:
            with st.spinner(f"Analisando clínicas em {loc_user}..."):
                # IA simula a busca baseada em dados reais de treino e fornece Prós/Contras
                prompt_vets = f"""
                Liste as 5 melhores clínicas veterinárias em {loc_user}. 
                Para cada uma, retorne exatamente neste formato:
                NOME_CLINICA|ENDERECO|PRÓS (em uma frase)|CONTRAS (em uma frase)
                Use apenas informações reais conhecidas.
                """
                res_vets = call_ia(prompt_vets)
                
                if res_vets:
                    linhas_vets = [l for l in res_vets.split('\n') if '|' in l][:5]
                    for vet in linhas_vets:
                        dados = vet.split('|')
                        if len(dados) >= 4:
                            with st.container():
                                st.markdown(f"""
                                <div class="clinic-card">
                                    <h3 style='margin-top:0;'>🏥 {dados[0]}</h3>
                                    <p style='font-size:0.8rem; color:#888;'>📍 {dados[1]}</p>
                                    <p class="pros"><b>✅ Prós:</b> {dados[2]}</p>
                                    <p class="contras"><b>❌ Contras:</b> {dados[3]}</p>
                                </div>
                                """, unsafe_allow_html=True)
        else:
            st.warning("Por favor, digite uma localização.")

with st.sidebar:
    st.write(f"**Tutor:** {user_doc['nome']}")
    if st.button("LOGOUT"):
        st.session_state.logado = False
        st.rerun()

import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps
import io
import os
import re
import pandas as pd
import urllib.parse
from datetime import datetime
from fpdf import FPDF
from pymongo import MongoClient
import pillow_heif

# --- INICIALIZAÇÃO ---
pillow_heif.register_heif_opener()
st.set_page_config(page_title="TechnoBolt Pets Hub", layout="wide", page_icon="🐾")

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
        st.error(f"Erro de conexão: {e}")
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM TECHNOBOLT ---
st.markdown("""
<style>
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    .clinic-title { color: #3b82f6; font-size: 1.5rem; font-weight: bold; margin-bottom: 5px; }
    .clinic-address { color: #888; font-size: 0.9rem; margin-top: 5px; margin-bottom: 20px; }
    .result-card-unificado { 
        background-color: #0d0d0d !important; border-left: 5px solid #3b82f6;
        border-radius: 12px; padding: 25px; border: 1px solid #1a1a1a;
    }
    .stButton>button { background-color: #3b82f6 !important; color: white !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- MOTOR DE IA ---
def realizar_scan_ia(prompt, img_pil=None):
    chaves = [os.environ.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    motores = ["models/gemini-3-flash-preview", "models/gemini-2.5-flash", "models/gemini-2.0-flash", "models/gemini-flash-latest"]
    for key in chaves:
        try:
            genai.configure(api_key=key)
            for m in motores:
                try:
                    model = genai.GenerativeModel(m)
                    cont = [prompt, img_pil] if img_pil else [prompt]
                    response = model.generate_content(cont)
                    if response.text: return response.text, m
                except: continue
        except: continue
    return None, "OFFLINE"

# --- INTERFACE DE LOGIN (SIMPLIFICADA PARA O EXEMPLO) ---
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🐾 TechnoBolt Pets Hub")
    if st.button("ENTRAR (DEMO)"): st.session_state.logado = True; st.session_state.user_atual = "admin"; st.rerun()
    st.stop()

# --- DASHBOARD ---
user_doc = db.usuarios.find_one({"usuario": st.session_state.user_atual})
tab1, tab2, tab3 = st.tabs(["🧬 PetScan IA", "📍 Vets & Clínicas", "🐕 Marketplace"])

with tab2:
    st.subheader("📍 Geolocalização Inteligente: Top 5 Clínicas")
    
    # Dados das 5 principais clínicas de São Paulo (Exemplo Real)
    clinicas = [
        {"nome": "Veros Hospital Veterinário 24h", "lat": -23.5819, "lon": -46.6661, "end": "Av. Brigadeiro Luís Antônio, 4643 - Jardim Paulista", "url": "https://veros.vet/"},
        {"nome": "WeVets Hospital Veterinário - Pompéia", "lat": -23.5302, "lon": -46.6848, "end": "Av. Pompéia, 633 - Pompeia", "url": "https://wevets.com.br/"},
        {"nome": "Hospital Veterinário Medeiros 24h", "lat": -23.5313, "lon": -46.7001, "end": "Rua Catão, 1157 Vila Romana - Lapa", "url": "https://hvmedeiros.com.br/"},
        {"nome": "SaveVet Centro Veterinário 24h", "lat": -23.4926, "lon": -46.6178, "end": "Av. Leôncio de Magalhães, 1005 - Jd. São Paulo", "url": "http://www.savevet.com.br/"},
        {"nome": "Provet Diagnóstico - Unidade Aratãs", "lat": -23.6111, "lon": -46.6509, "end": "Av. Indianópolis, 1465 - Indianópolis", "url": "http://www.provet.com.br/"}
    ]

    for clinica in clinicas:
        st.markdown(f'<div class="clinic-title">{clinica["nome"]}</div>', unsafe_allow_html=True)
        
        # Mapa em Miniatura
        map_data = pd.DataFrame({'lat': [clinica['lat']], 'lon': [clinica['lon']]})
        st.map(map_data, zoom=14, use_container_width=True)
        
        # Endereço e Link
        st.markdown(f'<div class="clinic-address">📍 {clinica["end"]}</div>', unsafe_allow_html=True)
        st.link_button("Ver no Google Maps", clinica['url'])
        st.divider()

    if st.button("🪄 IA: ANALISAR REPUTAÇÃO DESTAS CLÍNICAS"):
        prompt_reputacao = f"Analise as clínicas: {[c['nome'] for l in clinicas]}. Resuma o diferencial tecnológico de cada uma em 2 linhas."
        res, _ = realizar_scan_ia(prompt_reputacao)
        st.info(res)

with tab1: st.write("Módulo PetScan ativo.")
with tab3: st.write("Módulo Marketplace ativo.")

st.caption("TechnoBolt Pets v2.0 | IA & Geolocalização")

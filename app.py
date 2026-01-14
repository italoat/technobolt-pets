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
import random

# --- INICIALIZAÇÃO DE SUPORTE HEIC ---
# Permite o processamento de fotos de iPhone diretamente no sistema
pillow_heif.register_heif_opener()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="TechnoBolt Pets Hub", layout="wide", page_icon="🐾")

# --- CONEXÃO MONGODB ---
# Utiliza as variáveis de ambiente configuradas no Render para segurança
@st.cache_resource
def iniciar_conexao():
    try:
        user = os.environ.get("MONGO_USER", "technobolt")
        password_raw = os.environ.get("MONGO_PASS", "tech@132")
        host = os.environ.get("MONGO_HOST", "cluster0.zbjsvk6.mongodb.net")
        password = urllib.parse.quote_plus(password_raw)
        uri = f"mongodb+srv://{user}:{password}@{host}/?appName=Cluster0"
        client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
        client.admin.command('ping')
        return client['technoboltpets'] 
    except Exception as e:
        st.error(f"Erro de conexão com o Banco de Dados: {e}")
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM ---
# Estética Dark Mode com acentos em azul para o padrão TechnoBolt
st.markdown("""
<style>
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    [data-testid="stHeader"], [data-testid="stSidebar"] { background-color: #000000 !important; }
    
    .welcome-card {
        background: linear-gradient(145deg, #0d0d0d, #1a1a1a);
        border: 1px solid #333; border-radius: 20px; padding: 40px;
        margin-bottom: 30px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .welcome-title { color: #3b82f6; font-size: 2.5rem; font-weight: 800; margin-bottom: 10px; }
    
    .tip-card {
        background: rgba(59, 130, 246, 0.05); border: 1px solid #3b82f6;
        border-radius: 15px; padding: 20px; height: 180px; transition: 0.3s;
    }
    .tip-tag { color: #3b82f6; font-weight: bold; font-size: 0.8rem; text-transform: uppercase; }
    
    .result-card-unificado { 
        background-color: #0d0d0d !important; border-left: 5px solid #3b82f6;
        border-radius: 12px; padding: 25px; margin-top: 15px; border: 1px solid #1a1a1a;
        line-height: 1.7; color: #e0e0e0;
    }
    .result-card-unificado b { color: #3b82f6; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #3b82f6 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- UTILITÁRIOS PDF ---
class TechnoBoltPDF(FPDF):
    def header(self):
        self.set_fill_color(10, 10, 10); self.rect(0, 0, 210, 40, 'F')
        self.set_xy(15, 12); self.set_font("Helvetica", "B", 24); self.set_text_color(59, 130, 246)
        self.cell(0, 10, "TECHNOBOLT PETS", ln=True)
        self.ln(20)

def gerar_pdf(nome, conteudo, data):
    pdf = TechnoBoltPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 12)
    pdf.multi_cell(0, 10, conteudo.encode('latin-1', 'replace').decode('latin-1'))
    return bytes(pdf.output(dest='S'))

# --- MOTOR DE IA (MOTORES SOLICITADOS) ---
# Implementação do rodízio de chaves e motores de última geração
def realizar_scan_ia(prompt, img_pil=None):
    chaves = [os.environ.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    motores = ["models/gemini-3-flash-preview", "models/gemini-2.5-flash", "models/gemini-2.0-flash", "models/gemini-flash-latest"]
    
    img_blob = None
    if img_pil:
        img_byte_arr = io.BytesIO()
        img_pil.save(img_byte_arr, format='JPEG')
        img_blob = {"mime_type": "image/jpeg", "data": img_byte_arr.getvalue()}

    for key in chaves:
        try:
            genai.configure(api_key=key)
            for m in motores:
                try:
                    model = genai.GenerativeModel(m)
                    cont = [prompt, img_blob] if img_blob else [prompt]
                    response = model.generate_content(cont)
                    if response.text: return response.text, m
                except: continue
        except: continue
    return None, "OFFLINE"

# --- LOGIN / TELA INICIAL ---
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.markdown("""
    <div class="welcome-card">
        <div class="welcome-title">🐾 TechnoBolt Pets Hub</div>
        <div class="welcome-subtitle">IA de Elite para a Longevidade do seu Melhor Amigo</div>
    </div>
    """, unsafe_allow_html=True)

    # 4 Cards Gratuitos de Dicas (Sempre mudam via IA)
    dica_prompt = "Gere 4 dicas curtas para tutores de pets: TAG|TITULO|DICA. Uma por linha."
    res_dicas, _ = realizar_scan_ia(dica_prompt)
    cols = st.columns(4)
    if res_dicas:
        linhas = [l for l in res_dicas.split('\n') if '|' in l][:4]
        for i, linha in enumerate(linhas):
            p = linha.split('|')
            if len(p) >= 3:
                cols[i].markdown(f'<div class="tip-card"><span class="tip-tag">{p[0]}</span><br><b>{p[1]}</b><br><small>{p[2]}</small></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔐 Acesso ao Hub", "📝 Novo Cadastro"])
    with t1:
        u_log = st.text_input("Usuário").lower().strip()
        p_log = st.text_input("Senha", type="password")
        if st.button("AUTENTICAR"):
            udata = db.usuarios.find_one({"usuario": u_log, "senha": p_log})
            if udata:
                st.session_state.logado = True; st.session_state.user_atual = u_log; st.rerun()
            else: st.error("Acesso negado.")
    with t2:
        u_reg = st.text_input("Escolha um Login").lower().strip()
        p_reg = st.text_input("Escolha uma Senha", type="password")
        tipo_reg = st.selectbox("Plano", ["Pet Lite", "Pet PRO", "Partner"])
        if st.button("CADASTRAR"):
            db.usuarios.insert_one({"usuario": u_reg, "senha": p_reg, "tipo": tipo_reg, "avaliacoes_restantes": 5 if "PRO" in tipo_reg else 0, "historico": []})
            st.success("Cadastro realizado!")
    st.stop()

# --- DASHBOARD LOGADO ---
user_doc = db.usuarios.find_one({"usuario": st.session_state.user_atual})

with st.sidebar:
    st.header(f"Olá, {user_doc.get('usuario')}")
    st.write(f"Plano: **{user_doc.get('tipo')}**")
    if st.button("LOGOUT"): st.session_state.logado = False; st.rerun()
    st.divider()
    p_nome = st.text_input("Nome do Pet", "Rex")
    p_peso = st.number_input("Peso (kg)", 0.5, 100.0, 10.0)
    up = st.file_uploader("📸 PetScan IA", type=['jpg', 'jpeg', 'png', 'heic'])

# --- MÓDULOS DE INTELIGÊNCIA ---
tab1, tab2, tab3 = st.tabs(["🧬 PetScan IA", "📍 Vets Próximos", "🐕 Caregiver Marketplace"])

with tab1:
    if up and st.button("🚀 INICIAR ANÁLISE"):
        if user_doc.get('avaliacoes_restantes', 0) > 0 or user_doc.get('tipo') == "Pet PRO":
            with st.status("🧬 Analisando biometria animal..."):
                img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
                prompt_scan = f"""
                ATUE COMO UM CONSELHO VETERINÁRIO PHD. PET: {p_nome}, PESO: {p_peso}KG.
                1. IDENTIFICAÇÃO: Raça e Mix.
                2. SCORE CORPORAL (BCS): Avalie visualmente de 1 a 9.
                3. RECOMENDAÇÃO: Calorias/dia e nível de atividade.
                4. INSIGHT TECHNOBOLT: Sugestão técnica de longevidade.
                """
                res, eng = realizar_scan_ia(prompt_scan, img)
                if res:
                    st.markdown(f"<div class='result-card-unificado'>{res}</div>", unsafe_allow_html=True)
                    db.usuarios.update_one({"usuario": st.session_state.user_atual}, {"$push": {"historico": {"data": datetime.now(), "relatorio": res}}, "$inc": {"avaliacoes_restantes": -1} if user_doc.get('tipo') != "Pet PRO" else {}})
        else:
            st.warning("Assine o Pet PRO para scans ilimitados.")

with tab2:
    st.subheader("📍 Geolocalização Inteligente")
    loc = st.text_input("Sua Localização", "Bairro, Cidade")
    if st.button("BUSCAR CLÍNICAS"):
        prompt_geo = f"Liste 3 clínicas veterinárias em {loc}. Resuma pontos positivos e alertas baseados em avaliações reais."
        res_geo, _ = realizar_scan_ia(prompt_geo)
        st.write(res_geo)

with tab3:
    st.subheader("🐕 Caregiver Marketplace")
    st.info("Cuidadores validados pelo TechnoBolt Confidence Score.")
    # Exemplo de exibição do marketplace
    col_a, col_b = st.columns([3, 1])
    col_a.markdown("**Ana Clara (Dog Walker)** - Especialista em Cães Senior\n\n⭐ Score: **98%**")
    if col_b.button("VER PERFIL"): st.write("Perfil em desenvolvimento.")

st.markdown("<br><br>", unsafe_allow_html=True)
st.caption(f"TechnoBolt Pets © 2026 | Engine: {motores[0] if 'motores' in locals() else 'Gemini'}")

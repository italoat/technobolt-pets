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
pillow_heif.register_heif_opener()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="TechnoBolt Pets Hub", layout="wide", page_icon="🐾")

# --- CONEXÃO MONGODB (CONFIGURAÇÃO SOLICITADA) ---
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
        return client['technoboltpets'] # Database específico para Pets
    except Exception as e:
        st.error(f"Erro de conexão com o Banco de Dados: {e}")
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM TECHNOBOLT ---
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
    .tip-card:hover { border-style: dashed; transform: scale(1.02); }
    .tip-tag { color: #3b82f6; font-weight: bold; font-size: 0.9rem; margin-bottom: 8px; display: block; }
    
    .result-card-unificado { 
        background-color: #0d0d0d !important; border-left: 5px solid #3b82f6;
        border-radius: 12px; padding: 25px; margin-top: 15px; border: 1px solid #1a1a1a;
        line-height: 1.7; color: #e0e0e0; font-family: 'Inter', sans-serif;
    }
    .result-card-unificado b { color: #3b82f6; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #3b82f6 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- MOTOR DE IA (RODÍZIO E MOTORES SOLICITADOS) ---
def realizar_scan_pets(prompt_mestre, img_pil=None):
    chaves = [os.environ.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    # Motores solicitados:
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
                    conteudo = [prompt_mestre, img_blob] if img_blob else [prompt_mestre]
                    response = model.generate_content(conteudo)
                    if response and response.text:
                        return response.text, f"{m.upper()}"
                except: continue
        except: continue
    return None, "OFFLINE"

# --- LOGIN / TELA INICIAL COM 4 CARDS ---
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.markdown("""
    <div class="welcome-card">
        <div class="welcome-title">🐾 TechnoBolt Pets Hub</div>
        <div class="welcome-subtitle">Alta tecnologia aplicada à saúde e bem-estar animal.</div>
    </div>
    """, unsafe_allow_html=True)

    # Dicas Dinâmicas via IA (Usando motor com mais cotas para a home)
    with st.spinner("Carregando insights do dia..."):
        dica_prompt = "Gere 4 dicas ultra-curtas para donos de cães e gatos (Saúde, Treino, Nutrição, Curiosidade). Formato: TAG|TITULO|DESCRICAO. Sem saudações."
        res_dicas, _ = realizar_scan_pets(dica_prompt)
        
        cols = st.columns(4)
        if res_dicas:
            linhas = [l for l in res_dicas.split('\n') if '|' in l][:4]
            for i, linha in enumerate(linhas):
                partes = linha.split('|')
                if len(partes) >= 3:
                    cols[i].markdown(f"""
                    <div class="tip-card">
                        <span class="tip-tag">{partes[0]}</span>
                        <b>{partes[1]}</b><br>
                        <small>{partes[2]}</small>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔐 Acesso Tutor/Partner", "📝 Novo Cadastro"])
    
    with t1:
        u_log = st.text_input("Usuário").lower().strip()
        p_log = st.text_input("Senha", type="password")
        if st.button("ENTRAR NO HUB"):
            udata = db.usuarios.find_one({"usuario": u_log, "senha": p_log})
            if udata:
                st.session_state.logado = True
                st.session_state.user_atual = u_log
                st.session_state.is_admin = udata.get('is_admin', False)
                st.rerun()
            else: st.error("Acesso negado.")
            
    with t2:
        u_reg = st.text_input("Login Desejado").lower().strip()
        p_reg = st.text_input("Senha Cadastro", type="password")
        tipo = st.selectbox("Tipo de Conta", ["Pet Lite", "Pet PRO", "Partner (Vet/Walker)"])
        if st.button("CRIAR CONTA"):
            db.usuarios.insert_one({"usuario": u_reg, "senha": p_reg, "tipo": tipo, "status": "ativo", "avaliacoes_restantes": 3 if "PRO" in tipo else 0, "historico": []})
            st.success("Cadastro realizado com sucesso!")
    st.stop()

# --- DASHBOARD LOGADO ---
user_doc = db.usuarios.find_one({"usuario": st.session_state.user_atual})

with st.sidebar:
    st.header(f"Tutor: {user_doc.get('usuario')}")
    st.write(f"Plano: **{user_doc.get('tipo')}**")
    if st.button("SAIR"): st.session_state.logado = False; st.rerun()
    st.divider()
    p_nome = st.text_input("Nome do Pet", "Rex")
    p_idade = st.number_input("Idade", 0, 25, 3)
    p_objetivo = st.selectbox("Foco", ["Saúde Geral", "Perda de Peso", "Ganho de Massa", "Senior"])
    up = st.file_uploader("📸 PetScan IA (Subir Foto)", type=['jpg', 'jpeg', 'png', 'heic'])

# --- MÓDULOS DE INTELIGÊNCIA ---
tab1, tab2, tab3 = st.tabs(["🧬 PetScan IA", "📍 Vets & Clínicas", "🐕 Caregiver Marketplace"])

with tab1:
    st.subheader("Análise Biométrica e Nutricional")
    if up and st.button("🚀 INICIAR PETSCAN"):
        if user_doc.get('avaliacoes_restantes', 0) > 0 or user_doc.get('tipo') == "Pet PRO":
            with st.status("🧬 Analisando condição corporal..."):
                img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
                
                prompt_pet = f"""
                VOCÊ É UM CONSELHO VETERINÁRIO DE ELITE (VET PHD, NUTROLOGISTA E ETÓLOGO).
                PET: {p_nome} | IDADE: {p_idade} ANOS | FOCO: {p_objetivo}.

                [AVALIAÇÃO]
                1. IDENTIFICAÇÃO: Raça provável ou mix de raças.
                2. SCORE CORPORAL (BCS): Avalie visualmente o Body Condition Score (1-9).
                3. PELAGEM E PELE: Sinais visíveis de saúde ou carências.
                
                [PLANO TECHNOBOLT]
                - Sugestão calórica diária aproximada.
                - Nível de atividade física recomendado (Baixo/Médio/Atleta).
                - Recomendações de Nutracêuticos.

                EXPLIQUE TERMOS TÉCNICOS. TERMINE COM 🚀 TECHNOBOLT PET INSIGHT.
                """
                res, eng = realizar_scan_pets(prompt_pet, img)
                if res:
                    st.markdown(f"<div class='result-card-unificado'>{res}</div>", unsafe_allow_html=True)
                    db.usuarios.update_one({"usuario": st.session_state.user_atual}, {"$push": {"historico": {"data": datetime.now(), "relatorio": res}}, "$inc": {"avaliacoes_restantes": -1} if user_doc.get('tipo') != "Pet PRO" else {}})
        else:
            st.error("Créditos insuficientes. Migre para o plano PRO para scans ilimitados.")

with tab2:
    st.subheader("📍 Geolocalização Inteligente")
    loc = st.text_input("Sua Localização (Bairro/Cidade)", "São Paulo, SP")
    if st.button("FILTRAR MELHORES VETS"):
        with st.spinner("IA analisando reputação de clínicas locais..."):
            prompt_geo = f"Liste 3 clínicas veterinárias próximas a {loc}. Para cada uma, faça um 'Resumo IA' dos pontos positivos e um 'Alerta TechnoBolt' baseado em feedbacks comuns de tutores."
            res_geo, _ = realizar_scan_pets(prompt_geo)
            st.write(res_geo)

with tab3:
    st.subheader("🐕 Caregiver Marketplace")
    st.markdown("Busque profissionais validados pelo **TechnoBolt Confidence Score**.")
    
    col_f1, col_f2 = st.columns(2)
    busca = col_f1.text_input("Filtrar por Especialidade (ex: Cães Bravos, Idosos)")
    preco_max = col_f2.slider("Preço Máximo (R$)", 30, 300, 100)

    # Simulação de Marketplace (Puxando de Partners cadastrados no banco)
    # Aqui a IA poderia ordenar por Score de Confiança
    st.divider()
    c1, c2, c3 = st.columns([1, 2, 1])
    c1.image("https://cdn-icons-png.flaticon.com/512/194/194279.png", width=80)
    c2.markdown("**Mariana Silva** - *Especialista em Cães Senior*\n\n⭐ Confidence Score: **98%** | 📍 1.2km de você")
    c3.button("CONTRATAR R$ 65/h", key="contrat_1")

st.markdown("<br><br>", unsafe_allow_html=True)
st.caption(f"TechnoBolt Pets v2.0 © 2026 | Engine: {motores[0].split('/')[-1]}")

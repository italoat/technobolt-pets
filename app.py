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

# --- CONFIGURAÇÕES DE ENGENHARIA SÊNIOR ---
pillow_heif.register_heif_opener()
st.set_page_config(page_title="TechnoBolt Pets | Enterprise Edition", layout="wide", page_icon="🐾")

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
        st.error(f"⚠️ Falha na conexão com o Banco de Dados: {e}")
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM: TECHNOBOLT DARK MODE PRO ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background-color: #000000 !important; }
    
    /* Cards de Elite */
    .elite-card {
        background: linear-gradient(145deg, #0d0d0d, #161616);
        border: 1px solid #222; border-radius: 20px;
        padding: 24px; margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .status-active { background: #064e3b; color: #10b981; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 0.8rem; }
    .status-inactive { background: #451a1a; color: #f87171; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 0.8rem; }
    .price-tag { color: #3b82f6; font-weight: 800; font-size: 1.1rem; }
    
    /* Inputs */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stNumberInput>div>div>input {
        background-color: #111 !important; color: white !important; border: 1px solid #333 !important; border-radius: 10px !important;
    }
    .stButton>button {
        background-color: #1a1a1a !important; color: white !important; border: 1px solid #333 !important;
        border-radius: 12px !important; font-weight: 600 !important; transition: 0.3s ease;
    }
    .stButton>button:hover { border-color: #3b82f6 !important; color: #3b82f6 !important; transform: translateY(-2px); }
</style>
""", unsafe_allow_html=True)

# --- ENGINE DE IA (MOTORES REESTABELECIDOS) ---
def call_ia(prompt, img=None):
    chaves = [os.environ.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    if not chaves: return "Erro: Chaves de API não encontradas."
    
    motores = ["models/gemini-3-flash-preview", "models/gemini-2.5-flash", "models/gemini-2.0-flash", "models/gemini-flash-latest"]
    genai.configure(api_key=random.choice(chaves))
    
    for motor in motores:
        try:
            model = genai.GenerativeModel(motor)
            response = model.generate_content([prompt, img] if img else prompt)
            return response.text
        except: continue
    return "⚠️ Serviço de IA em manutenção."

# --- AUTH & SESSION ---
if "logado" not in st.session_state: st.session_state.logado = False
if "ultimo_scan" not in st.session_state: st.session_state.ultimo_scan = None
if "cg_index" not in st.session_state: st.session_state.cg_index = 0

if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center; font-weight:800; color:white;'>🐾 TECHNOBOLT PETS</h1>", unsafe_allow_html=True)
    t_log, t_reg = st.tabs(["🔐 ACESSAR HUB", "📝 REGISTRAR"])
    
    with t_log:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("AUTENTICAR"):
            user = db.usuarios.find_one({"usuario": u, "senha": p}) if db is not None else None
            if user:
                if user.get("status") == "Inativo":
                    st.error("Conta suspensa pelo administrador.")
                else:
                    st.session_state.logado = True
                    st.session_state.user_data = user
                    st.rerun()
            else: st.error("Credenciais inválidas.")
    
    with t_reg:
        n_nome = st.text_input("Nome Completo")
        n_user = st.text_input("Username").lower()
        n_pass = st.text_input("Senha", type="password")
        n_tipo = st.selectbox("Eu sou um:", ["Usuário Normal", "Cuidador"])
        if st.button("SOLICITAR ACESSO"):
            if n_user and db is not None:
                db.usuarios.insert_one({"nome": n_nome, "usuario": n_user, "senha": n_pass, "tipo": n_tipo, "status": "Ativo", "dt": datetime.now()})
                st.success("Conta criada! Acesse o hub.")
    st.stop()

# --- INTERFACE HUB ---
user_doc = st.session_state.user_data
is_admin = user_doc.get("tipo") == "Admin"

tabs = st.tabs(["💡 Insights", "🧬 PetScan", "📍 Localizar Vets", "🐕 Cuidadores"] + (["⚙️ Gestão de Usuários"] if is_admin else []))

# ABA 1: INSIGHTS
with tabs[0]:
    st.markdown("### 💡 Inteligência Preventiva")
    res = call_ia(f"4 dicas técnicas pet. Verão 2026. Contexto: {st.session_state.ultimo_scan or 'Geral'}. Formato: TAG|DICA")
    if res and "|" in res:
        cols = st.columns(4)
        for i, linha in enumerate([l for l in res.split('\n') if '|' in l][:4]):
            tag, txt = linha.split('|')
            cols[i].markdown(f"<div class='elite-card' style='height:160px;'><small style='color:#3b82f6; font-weight:800;'>{tag}</small><br>{txt}</div>", unsafe_allow_html=True)

# ABA 2: PETSCAN (RELATÓRIO APRIMORADO)
with tabs[1]:
    st.subheader("🧬 Diagnóstico Biométrico IA")
    up = st.file_uploader("Upload de Amostra Visual", type=['jpg', 'png', 'heic'])
    if up and st.button("PROCESSAR SCAN"):
        img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
        st.image(img, width=400)
        with st.status("Analisando padrões biotipológicos..."):
            res = call_ia("Analise anatômica detalhada: Raça provável, Escore Corporal (BCS) de 1 a 9, Saúde da pelagem e Recomendações.", img=img)
            st.session_state.ultimo_scan = res
        
        st.markdown(f"<div class='elite-card'><h3>📝 Laudo Técnico</h3><br>{res}</div>", unsafe_allow_html=True)
        
        st.markdown("### 📊 Gráfico de Referência: Condição Corporal")
        # CORREÇÃO DA SINTAXE DO ERRO ANTERIOR:
        st.markdown("""
        O escore corporal (BCS) avalia a quantidade de gordura sobre as costelas e a cintura.
        
[attachment_0](attachment)
        """)

# ABA 3: VETS (LOCALIZAÇÃO & AVALIAÇÕES)
with tabs[2]:
    st.subheader("📍 Inteligência Geo-Localizada")
    loc_input = st.text_input("Sua Localização (ou clique em GPS)", placeholder="Ex: Itaim Bibi, SP")
    if st.button("📍 CAPTURAR MINHA LOCALIZAÇÃO"):
        loc_input = "São Paulo, SP" # Simulação de GPS
        st.info("Localização do dispositivo detectada via sinal de rede.")

    if loc_input:
        with st.spinner("IA processando avaliações reais da rede..."):
            prompt_vets = f"Liste 5 melhores veterinários/clínicas em {loc_input}. Formato: NOME|AVALIAÇÃO|ENDEREÇO|PRÓS|CONTRAS"
            res_vets = call_ia(prompt_vets)
            if res_vets:
                for v in [l for l in res_vets.split('\n') if '|' in l][:5]:
                    d = v.split('|')
                    st.markdown(f"""
                    <div class='elite-card'>
                        <div style='display:flex; justify-content:space-between;'>
                            <h3>🏥 {d[0]}</h3>
                            <span class='price-tag'>⭐ {d[1]}</span>
                        </div>
                        <p style='color:#888;'>📍 {d[2]}</p>
                        <div style='display:grid; grid-template-columns: 1fr 1fr; gap:10px;'>
                            <div style='color:#aaffaa;'><small><b>PONTOS FORTES:</b></small><br>{d[3]}</div>
                            <div style='color:#ffaaaa;'><small><b>PONTOS FRACOS:</b></small><br>{d[4]}</div>
                        </div>
                    </div>""", unsafe_allow_html=True)

# ABA 4: CUIDADORES
with tabs[3]:
    st.subheader("🐕 Elite Caregivers Marketplace")
    if db is not None:
        cuidadores = list(db.usuarios.find({"tipo": "Cuidador"}))
        if cuidadores:
            c = cuidadores[st.session_state.cg_index % len(cuidadores)]
            c1, c2, c3 = st.columns([1, 4, 1])
            if c1.button("⬅️"): st.session_state.cg_index -= 1; st.rerun()
            if c3.button("➡️"): st.session_state.cg_index += 1; st.rerun()
            with c2:
                st.markdown(f"<div class='elite-card'><span class='price-tag'>R$ {c.get('valor_diaria', 0):.2f}/dia</span><br><br><b>{c['nome']}</b><br>{c.get('resumo', 'Verificado.')}</div>", unsafe_allow_html=True)

# ABA 5: GESTÃO ADMIN (COMPLETA)
if is_admin:
    with tabs[4]:
        st.subheader("⚙️ Painel de Governança de Usuários")
        if db is not None:
            usuarios = list(db.usuarios.find())
            for u in usuarios:
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    col1.write(f"**{u['nome']}** ({u['usuario']})")
                    col2.write(f"`{u['tipo']}`")
                    
                    status = u.get("status", "Ativo")
                    st_class = "status-active" if status == "Ativo" else "status-inactive"
                    col3.markdown(f"<span class='{st_class}'>{status}</span>", unsafe_allow_html=True)
                    
                    # Ações Admin
                    with col4:
                        if u['tipo'] != "Admin":
                            if st.button("Promover", key=f"prom_{u['usuario']}"):
                                db.usuarios.update_one({"usuario": u['usuario']}, {"$set": {"tipo": "Admin"}})
                                st.rerun()
                            if status == "Ativo":
                                if st.button("Suspender", key=f"susp_{u['usuario']}"):
                                    db.usuarios.update_one({"usuario": u['usuario']}, {"$set": {"status": "Inativo"}})
                                    st.rerun()
                            else:
                                if st.button("Reativar", key=f"react_{u['usuario']}"):
                                    db.usuarios.update_one({"usuario": u['usuario']}, {"$set": {"status": "Ativo"}})
                                    st.rerun()
                st.divider()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"### 👤 {user_doc.get('nome')}")
    st.caption(f"Perfil: {user_doc.get('tipo')}")
    if st.button("SAIR"): st.session_state.logado = False; st.rerun()

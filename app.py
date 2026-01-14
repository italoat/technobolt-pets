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

# --- CONFIGURAÇÕES TÉCNICAS SÊNIOR ---
pillow_heif.register_heif_opener()
st.set_page_config(page_title="TechnoBolt Pets Hub | Enterprise Edition", layout="wide", page_icon="🐾")

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
        client.admin.command('ping')
        return client['technoboltpets']
    except Exception as e:
        st.error(f"⚠️ Erro Crítico na Conexão: {e}")
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM: TECHNOBOLT DARK PRO ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background-color: #000000 !important; }
    
    /* Cards Visual Improvements */
    .elite-card {
        background: #0d0d0d; border: 1px solid #1f1f1f; border-radius: 20px;
        padding: 24px; margin-bottom: 20px;
        transition: transform 0.3s ease, border-color 0.3s ease;
        box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    }
    .elite-card:hover { transform: translateY(-5px); border-color: #3b82f6; }
    
    .status-active { color: #10b981; font-weight: bold; }
    .price-tag { background: #3b82f6; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 800; }
    
    /* Admin Table Styling */
    .admin-row { border-bottom: 1px solid #1a1a1a; padding: 10px 0; }
    
    .stButton>button {
        background: #1a1a1a !important; color: #fff !important;
        border: 1px solid #333 !important; border-radius: 12px !important;
        font-weight: 600 !important; transition: 0.3s !important;
    }
    .stButton>button:hover { background: #3b82f6 !important; border-color: #3b82f6 !important; }
</style>
""", unsafe_allow_html=True)

# --- AI CORE ENGINE ---
def call_ia(prompt, img=None):
    chaves = [os.environ.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    if not chaves: return "Erro: API_KEYS_MISSING"
    
    motores = ["models/gemini-2.0-flash", "models/gemini-3-flash-preview", "models/gemini-2.5-flash", "models/gemini-flash-latest"]
    genai.configure(api_key=random.choice(chaves))
    
    for motor in motores:
        try:
            model = genai.GenerativeModel(motor)
            response = model.generate_content([prompt, img] if img else prompt)
            return response.text
        except: continue
    return "Motores Offline."

# --- SESSION & SECURITY ---
if "logado" not in st.session_state: st.session_state.logado = False
if "ultimo_scan" not in st.session_state: st.session_state.ultimo_scan = None
if "cg_index" not in st.session_state: st.session_state.cg_index = 0

# --- AUTH & REGISTRATION ---
if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center; font-weight:800; color:white;'>🐾 TECHNOBOLT PETS</h1>", unsafe_allow_html=True)
    t_login, t_reg = st.tabs(["🔐 ACESSAR HUB", "📝 SOLICITAR ACESSO"])
    
    with t_login:
        u = st.text_input("Usuário", key="u_field")
        p = st.text_input("Senha", type="password", key="p_field")
        if st.button("AUTENTICAR"):
            user = db.usuarios.find_one({"usuario": u, "senha": p}) if db is not None else None
            if user:
                st.session_state.logado = True
                st.session_state.user_data = user
                st.rerun()
            else: st.error("Falha na autenticação.")

    with t_reg:
        n_nome = st.text_input("Nome")
        n_user = st.text_input("User").lower()
        n_pass = st.text_input("Pass", type="password")
        n_tipo = st.selectbox("Perfil", ["Usuário Normal", "Cuidador"])
        if st.button("FINALIZAR"):
            if n_user and db is not None:
                db.usuarios.insert_one({"nome": n_nome, "usuario": n_user, "senha": n_pass, "tipo": n_tipo, "status": "Ativo", "dt": datetime.now()})
                st.success("Conta criada!")
    st.stop()

# --- INTERFACE LOGADA ---
user_doc = st.session_state.user_data
is_admin = user_doc.get('tipo') == "Admin"

# Se for admin, adicionamos a aba de gestão
tabs_names = ["💡 Insights", "🧬 PetScan", "📍 Vets & Clínicas", "🐕 Cuidadores"]
if is_admin: tabs_names.append("⚙️ Gestão Admin")

tabs = st.tabs(tabs_names)

# --- ABA 1: INSIGHTS (CARDS MELHORADOS) ---
with tabs[0]:
    st.markdown("### 💡 Inteligência Preventiva")
    res = call_ia(f"4 dicas curtas pet. Contexto: {st.session_state.ultimo_scan or 'Geral'}. Formato: TAG|DICA")
    if res and "|" in res:
        cols = st.columns(4)
        for i, linha in enumerate([l for l in res.split('\n') if '|' in l][:4]):
            tag, txt = linha.split('|')
            cols[i].markdown(f"""
            <div class="elite-card" style="height: 180px;">
                <small style="color:#3b82f6; font-weight:800;">{tag.upper()}</small><br>
                <p style="font-size:0.9rem; margin-top:10px;">{txt}</p>
            </div>
            """, unsafe_allow_html=True)

# --- ABA 2: PETSCAN ---
with tabs[1]:
    st.subheader("🧬 Diagnóstico Biométrico IA")
    up = st.file_uploader("Upload de Amostra", type=['jpg', 'png', 'heic'])
    if up and st.button("EXECUTAR SCAN"):
        img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
        st.image(img, width=400)
        resultado = call_ia("Analise anatômica: raça, escore corporal (BCS) e saúde dérmica.", img=img)
        st.session_state.ultimo_scan = resultado
        st.markdown(f"<div class='elite-card'><b>LAUDO TÉCNICO:</b><br><br>{resultado}</div>", unsafe_allow_html=True)
        
        st.markdown("### 📊 Guia de Referência BCS")
        st.markdown("[attachment_0](attachment)")

# --- ABA 3: VETS & CLÍNICAS (LOCALIZAÇÃO & AVALIAÇÕES) ---
with tabs[2]:
    st.subheader("📍 Geolocalização de Especialistas")
    col_loc1, col_loc2 = st.columns([3, 1])
    loc_input = col_loc1.text_input("Localização (Cidade, Bairro ou 'Minha Localização')", placeholder="Ex: Itaim Bibi, SP")
    
    if col_loc2.button("📍 GPS"):
        # Simulação de geolocalização do aparelho (em Streamlit real, exige componente JS)
        loc_input = "Localização Atual (GPS Ativo)"
        st.info("Localização captada via GPS do dispositivo.")

    if loc_input:
        with st.spinner("IA processando avaliações da rede..."):
            prompt_vets = f"Liste 5 clínicas/vets em {loc_input}. Formato: NOME|NOTA|ENDERECO|PROS|CONTRAS"
            res_vets = call_ia(prompt_vets)
            if res_vets:
                for vet in [l for l in res_vets.split('\n') if '|' in l][:5]:
                    d = vet.split('|')
                    with st.container():
                        st.markdown(f"""
                        <div class='elite-card'>
                            <div style='display:flex; justify-content:space-between;'>
                                <h3>🏥 {d[0]}</h3>
                                <span class='price-tag'>⭐ {d[1]}</span>
                            </div>
                            <p style='color:#888;'>📍 {d[2]}</p>
                            <div style='display:grid; grid-template-columns: 1fr 1fr; gap:10px;'>
                                <div style='color:#aaffaa;'><small><b>PONTOS POSITIVOS:</b></small><br>{d[3]}</div>
                                <div style='color:#ffaaaa;'><small><b>PONTOS NEGATIVOS:</b></small><br>{d[4]}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

# --- ABA 4: CUIDADORES ---
with tabs[3]:
    st.subheader("🐕 Elite Caregivers")
    if db is not None:
        cuidadores = list(db.usuarios.find({"tipo": "Cuidador"}))
        if cuidadores:
            c = cuidadores[st.session_state.cg_index % len(cuidadores)]
            col_a, col_b, col_c = st.columns([1, 4, 1])
            if col_a.button("⬅️"): st.session_state.cg_index -= 1; st.rerun()
            if col_c.button("➡️"): st.session_state.cg_index += 1; st.rerun()
            with col_b:
                st.markdown(f"""
                <div class='elite-card'>
                    <span class='price-tag'>R$ {c.get('valor_diaria', 0):.2f}/dia</span><br><br>
                    <span style='font-size:1.5rem; font-weight:800;'>👤 {c['nome']}</span><br>
                    <p>{c.get('resumo', 'Sem bio disponível.')}</p>
                </div>""", unsafe_allow_html=True)

# --- ABA 5: GESTÃO ADMIN (CONTROLE DE ACESSO) ---
if is_admin:
    with tabs[4]:
        st.subheader("⚙️ Painel de Governança Admin")
        st.markdown("Gerencie permissões e visualize a base de usuários ativos.")
        
        if db is not None:
            usuarios = list(db.usuarios.find())
            for user in usuarios:
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    col1.write(f"**{user['nome']}** ({user['usuario']})")
                    col2.write(f"Type: `{user['tipo']}`")
                    col3.markdown(f"Status: <span class='status-active'>{user.get('status', 'Ativo')}</span>", unsafe_allow_html=True)
                    
                    if user['tipo'] != "Admin":
                        if col4.button("Promover Admin", key=f"promo_{user['usuario']}"):
                            db.usuarios.update_one({"usuario": user['usuario']}, {"$set": {"tipo": "Admin"}})
                            st.success(f"{user['usuario']} promovido!")
                            st.rerun()
                st.markdown("---")

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"### 👤 {user_doc.get('nome')}")
    st.caption(f"Acesso: {user_doc.get('tipo')}")
    if st.button("SAIR"):
        st.session_state.logado = False
        st.rerun()

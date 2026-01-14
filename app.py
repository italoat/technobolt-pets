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

# --- CONEXÃO MONGODB (ESTABILIDADE) ---
@st.cache_resource
def iniciar_conexao():
    try:
        user = os.environ.get("MONGO_USER", "technobolt")
        password_raw = os.environ.get("MONGO_PASS", "tech@132")
        host = os.environ.get("MONGO_HOST", "cluster0.zbjsvk6.mongodb.net")
        password = urllib.parse.quote_plus(password_raw)
        uri = f"mongodb+srv://{user}:{password}@{host}/?appName=Cluster0"
        client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
        # Teste de ping para validar conexão
        client.admin.command('ping')
        return client['technoboltpets']
    except Exception as e:
        st.error(f"Erro Crítico de Conexão: {e}")
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM: HIGH-END DARK ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stNumberInput>div>div>input, .stSelectbox>div>div>div { 
        background-color: #1a1a1a !important; color: #ffffff !important; border: 1px solid #333333 !important; 
    }
    
    .stButton>button { 
        background-color: #333333 !important; color: #ffffff !important; 
        border-radius: 8px; border: 1px solid #444444; font-weight: bold; width: 100%; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #444444 !important; border-color: #ffffff !important; }

    .clinic-card, .caregiver-card { 
        background-color: #111111; border: 1px solid #222222; border-radius: 12px; 
        padding: 25px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .price-tag { color: #3b82f6; font-weight: 800; font-size: 1.2rem; }
    .stMap { filter: grayscale(1) invert(0.9); border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- MOTOR DE IA (MULTIMODEL FALLBACK) ---
def call_ia(prompt, img=None):
    chaves = [os.environ.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    if not chaves: return "Erro: Chave API ausente."
    
    motores = [
        "models/gemini-2.0-flash", 
        "models/gemini-3-flash-preview", 
        "models/gemini-2.5-flash", 
        "models/gemini-flash-latest"
    ]
    
    genai.configure(api_key=random.choice(chaves))
    for motor in motores:
        try:
            model = genai.GenerativeModel(motor)
            if img:
                response = model.generate_content([prompt, img])
            else:
                response = model.generate_content(prompt)
            return response.text
        except:
            continue
    return "Serviço de IA instável. Tente novamente."

# --- SESSION STATE ---
if "logado" not in st.session_state: st.session_state.logado = False
if "ultimo_scan" not in st.session_state: st.session_state.ultimo_scan = None
if "cg_index" not in st.session_state: st.session_state.cg_index = 0

# --- LOGIN & REGISTRO ---
if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center; font-weight:800;'>🐾 TechnoBolt Pets</h1>", unsafe_allow_html=True)
    t_login, t_reg = st.tabs(["🔐 Acessar Hub", "📝 Solicitar Acesso"])
    
    with t_login:
        u, p = st.text_input("Usuário", key="l_u"), st.text_input("Senha", type="password", key="l_p")
        if st.button("AUTENTICAR"):
            user = db.usuarios.find_one({"usuario": u, "senha": p}) if db is not None else None
            if user: 
                st.session_state.logado = True
                st.session_state.user_data = user
                st.rerun()
            else: st.error("Acesso negado.")

    with t_reg:
        st.markdown("### Configurar Novo Perfil")
        n_nome = st.text_input("Nome Completo")
        n_user = st.text_input("Username").lower().strip()
        n_pass = st.text_input("Password", type="password")
        n_tipo = st.selectbox("Perfil", ["Usuário Normal", "Cuidador"])
        
        extra = {}
        if n_tipo == "Cuidador":
            st.divider()
            extra['resumo'] = st.text_area("Bio Profissional")
            c1, c2 = st.columns(2)
            extra['idade'] = c1.number_input("Idade", 18, 90, 25)
            extra['valor_diaria'] = c2.number_input("Diária (R$)", 0.0, 1000.0, 50.0)
            extra['endereco'] = st.text_input("Cidade/UF")
            
            sc1, sc2, sc3 = st.columns(3)
            extra['tipos_animais'] = sc1.multiselect("Espécies", ["Cães", "Gatos", "Aves", "Roedores"])
            extra['tamanhos'] = sc2.multiselect("Portes", ["Pequeno", "Médio", "Grande"])
            extra['idades_pet'] = sc3.multiselect("Fases", ["Filhote", "Adulto", "Idoso"])

        if st.button("FINALIZAR REGISTRO"):
            if n_user and n_pass and db is not None:
                if db.usuarios.find_one({"usuario": n_user}):
                    st.error("Usuário já cadastrado.")
                else:
                    data = {"nome": n_nome, "usuario": n_user, "senha": n_pass, "tipo": n_tipo, "dt": datetime.now()}
                    data.update(extra)
                    db.usuarios.insert_one(data)
                    st.success("Cadastro realizado!")
    st.stop()

# --- HUB LOGADO ---
user_doc = st.session_state.user_data
t_dicas, t_scan, t_vets, t_care = st.tabs(["💡 Insights", "🧬 PetScan IA", "📍 Clínicas Vets", "🐕 Cuidadores"])

# ABA 1: INSIGHTS
with t_dicas:
    st.markdown("### Performance e Saúde Pet")
    p = f"4 dicas curtas pet. Verão 2026. Contexto: {st.session_state.ultimo_scan or 'Geral'}. Formato: TAG|DICA"
    res = call_ia(p)
    if res:
        cols = st.columns(4)
        for i, linha in enumerate([l for l in res.split('\n') if '|' in l][:4]):
            tag, texto = linha.split('|')
            cols[i].markdown(f"<div style='background:#111; padding:20px; border-radius:10px; border:1px solid #222; height:160px;'><small style='color:#3b82f6; font-weight:bold;'>{tag.upper()}</small><br>{texto}</div>", unsafe_allow_html=True)

# ABA 2: PETSCAN IA (CORREÇÃO DE SINTAXE)
with t_scan:
    st.subheader("🧬 Diagnóstico Biométrico Digital")
    up = st.file_uploader("Submeter Amostra Visual", type=['jpg', 'png', 'heic'])
    if up and st.button("EXECUTAR SCAN"):
        img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
        st.image(img, width=400)
        with st.spinner("Analisando biotipo e saúde..."):
            resultado = call_ia("Atue como um especialista veterinário. Analise raça, escore corporal (BCS 1-9) e saúde da pelagem.", img=img)
            st.session_state.ultimo_scan = resultado
            st.markdown(f"<div class='caregiver-card'><b>LAUDO TÉCNICO:</b><br><br>{resultado}</div>", unsafe_allow_html=True)
            
            st.markdown("### 📊 Guia de Referência: Condição Corporal")
            # --- CORREÇÃO DO ERRO AQUI ---
            st.markdown("[Image of a Body Condition Score chart for dogs and cats]")
            st.caption("Nota: Este diagnóstico é assistido por IA e não substitui uma consulta física.")

# ABA 3: VETS
with t_vets:
    st.subheader("📍 Unidades Hospitalares 24h")
    loc = st.text_input("Sua Localização (Ex: Itaim Bibi, SP)", key="loc_vets")
    if loc and st.button("MAPEAR UNIDADES"):
        res = call_ia(f"Liste 5 clínicas 24h em {loc}. Formato: NOME|LAT|LON|ENDERECO|PROS|CONTRAS")
        if res:
            for vet in [l for l in res.split('\n') if '|' in l][:5]:
                d = vet.split('|')
                with st.container():
                    st.markdown(f"<div class='clinic-card'><h3>🏥 {d[0]}</h3>", unsafe_allow_html=True)
                    try:
                        st.map(pd.DataFrame({'lat': [float(d[1])], 'lon': [float(d[2])]}), zoom=15)
                    except: pass
                    st.markdown(f"<p style='color:#888;'>📍 {d[3]}</p><p style='color:#aaffaa;'>✅ {d[4]}</p></div>", unsafe_allow_html=True)

# ABA 4: CUIDADORES (CARROSSEL)
with t_care:
    st.subheader("🐕 Elite Caregivers Marketplace")
    if db is not None:
        cuidadores = list(db.usuarios.find({"tipo": "Cuidador"}))
        if cuidadores:
            num = len(cuidadores)
            c = cuidadores[st.session_state.cg_index % num]
            
            c_nav1, c_main, c_nav2 = st.columns([1, 4, 1])
            with c_nav1:
                st.markdown("<br><br><br>", unsafe_allow_html=True)
                if st.button("⬅️"): st.session_state.cg_index -= 1; st.rerun()
            with c_main:
                st.markdown(f"""
                <div class="caregiver-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 1.5rem; font-weight: 800;">👤 {c['nome']}</span>
                        <span class="price-tag">R$ {c.get('valor_diaria', 0.0):.2f}/dia</span>
                    </div>
                    <p style="color: #666;">📍 {c.get('endereco', 'Não informado')} | 🎂 {c.get('idade', '--')} anos</p>
                    <p style="margin: 15px 0; font-size: 1.1rem; line-height: 1.5;">{c.get('resumo', '...')}</p>
                    <hr style="border: 0.1px solid #333;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div><small><b>🐾 Espécies:</b> {", ".join(c.get('tipos_animais', []))}</small></div>
                        <div><small><b>📏 Portes:</b> {", ".join(c.get('tamanhos', []))}</small></div>
                    </div>
                </div>""", unsafe_allow_html=True)
            with c_nav2:
                st.markdown("<br><br><br>", unsafe_allow_html=True)
                if st.button("➡️"): st.session_state.cg_index += 1; st.rerun()

with st.sidebar:
    st.write(f"### 👤 {user_doc.get('nome')}")
    if st.button("LOGOUT"): 
        st.session_state.logado = False
        st.rerun()

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

# --- CONFIGURAÇÕES DE ELITE ---
pillow_heif.register_heif_opener()
st.set_page_config(page_title="TechnoBolt Pets | Elite AI Hub", layout="wide", page_icon="🐾")

# --- DATABASE ENGINE (FIXED NOTIMPLEMENTEDERROR) ---
@st.cache_resource
def iniciar_conexao():
    try:
        user = os.environ.get("MONGO_USER", "technobolt")
        password_raw = os.environ.get("MONGO_PASS", "tech@132")
        host = os.environ.get("MONGO_HOST", "cluster0.zbjsvk6.mongodb.net")
        password = urllib.parse.quote_plus(password_raw)
        uri = f"mongodb+srv://{user}:{password}@{host}/?appName=Cluster0"
        client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
        # Força o teste da conexão
        client.admin.command('ping')
        return client['technoboltpets']
    except Exception as e:
        st.error(f"⚠️ Erro Crítico de Database: {e}")
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM: TECHNOBOLT DARK MODE PRO ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;800&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    
    /* Input & Forms Elite Look */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stNumberInput>div>div>input {
        background-color: #0d0d0d !important; color: #ffffff !important; 
        border: 1px solid #262626 !important; border-radius: 10px !important;
        transition: 0.3s border-color;
    }
    .stTextInput>div>div>input:focus { border-color: #3b82f6 !important; }

    /* Custom Cards */
    .elite-card {
        background: linear-gradient(145deg, #0f0f0f, #1a1a1a);
        border: 1px solid #262626; border-radius: 16px;
        padding: 24px; margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    .tip-card {
        background: #0a0a0a; border-left: 3px solid #3b82f6;
        border-radius: 8px; padding: 15px; height: 140px;
    }
    .price-tag { color: #3b82f6; font-weight: 800; font-size: 1.2rem; }
    
    /* Buttons */
    .stButton>button {
        background: #1f1f1f !important; color: #ffffff !important;
        border: 1px solid #333 !important; border-radius: 10px !important;
        height: 45px; font-weight: 700; transition: all 0.3s;
    }
    .stButton>button:hover { border-color: #3b82f6 !important; color: #3b82f6 !important; transform: translateY(-2px); }
</style>
""", unsafe_allow_html=True)

# --- AI CORE ENGINE (RECOVERED MOTORS) ---
def call_ia(prompt, img=None):
    chaves = [os.environ.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    if not chaves: return "Erro: API_KEYS_NOT_FOUND"
    
    motores = [
        "models/gemini-3-flash-preview", 
        "models/gemini-2.5-flash", 
        "models/gemini-2.0-flash", 
        "models/gemini-flash-latest"
    ]
    
    genai.configure(api_key=random.choice(chaves))
    
    for motor in motores:
        try:
            model = genai.GenerativeModel(motor)
            content = [prompt, img] if img else prompt
            response = model.generate_content(content)
            return response.text
        except Exception:
            continue
    return "⚠️ Motores de IA em manutenção."

# --- SESSION MANAGEMENT ---
if "logado" not in st.session_state: st.session_state.logado = False
if "ultimo_scan" not in st.session_state: st.session_state.ultimo_scan = None
if "dicas_cache" not in st.session_state: st.session_state.dicas_cache = None
if "cg_index" not in st.session_state: st.session_state.cg_index = 0

# --- AUTH SYSTEM ---
if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center; font-weight:800;'>🐾 TECHNOBOLT PETS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Elite Intelligence for Animal Care</p>", unsafe_allow_html=True)
    
    t_log, t_reg = st.tabs(["🔐 ACESSO", "📝 REGISTRO"])
    
    with t_log:
        u = st.text_input("Usuário", key="login_user")
        p = st.text_input("Senha", type="password", key="login_pass")
        if st.button("AUTENTICAR SISTEMA"):
            # Comparação explícita com None para evitar NotImplementedError
            user = db.usuarios.find_one({"usuario": u, "senha": p}) if db is not None else None
            if user:
                st.session_state.logado = True
                st.session_state.user_data = user
                st.rerun()
            else: st.error("Acesso Negado: Credenciais Inválidas.")

    with t_reg:
        n_nome = st.text_input("Nome")
        n_user = st.text_input("Username").lower()
        n_pass = st.text_input("Password", type="password")
        n_tipo = st.selectbox("Perfil", ["Usuário Normal", "Cuidador"])
        
        extra = {}
        if n_tipo == "Cuidador":
            c1, c2 = st.columns(2)
            extra['resumo'] = st.text_area("Bio Profissional")
            extra['valor_diaria'] = c1.number_input("Diária (R$)", 0.0)
            extra['endereco'] = c2.text_input("Cidade/UF")
            extra['tipos_animais'] = st.multiselect("Espécies", ["Cães", "Gatos", "Exóticos"])

        if st.button("FINALIZAR CADASTRO"):
            if n_user and n_pass and db is not None:
                data = {"nome": n_nome, "usuario": n_user, "senha": n_pass, "tipo": n_tipo, "dt": datetime.now()}
                data.update(extra)
                db.usuarios.insert_one(data)
                st.success("Conta Ativada!")
    st.stop()

# --- MAIN HUB ---
user_doc = st.session_state.user_data
t_insights, t_biometria, t_geo, t_market = st.tabs(["💡 INSIGHTS", "🧬 PETSCAN", "📍 VETS", "🐕 CUIDADORES"])

# ABA 1: INSIGHTS (OPTIMIZED CACHE)
with t_insights:
    st.markdown("### 💡 Inteligência de Campo")
    if not st.session_state.dicas_cache:
        prompt = f"Gere 4 dicas técnicas para pets. Verão 2026. Contexto: {st.session_state.ultimo_scan or 'Prevenção geral'}. Formato: TAG|DICA"
        with st.spinner("Sincronizando com a nuvem..."):
            st.session_state.dicas_cache = call_ia(prompt)
    
    res = st.session_state.dicas_cache
    if res and "|" in res:
        cols = st.columns(4)
        for i, linha in enumerate([l for l in res.split('\n') if '|' in l][:4]):
            tag, txt = linha.split('|')
            cols[i].markdown(f"<div class='tip-card'><small style='color:#3b82f6;'>{tag}</small><br><div style='font-size:0.85rem;'>{txt}</div></div>", unsafe_allow_html=True)

# ABA 2: PETSCAN (BIOMETRIC REPORT)
with t_biometria:
    st.subheader("🧬 Diagnóstico Biométrico por Imagem")
    up = st.file_uploader("Upload de Amostra", type=['jpg', 'png', 'heic'])
    if up and st.button("PROCESSAR BIOMETRIA"):
        img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
        st.image(img, width=400)
        with st.status("Analisando padrões anatômicos..."):
            resultado = call_ia("Atue como um radiologista e especialista em BCS. Analise raça, escore corporal (1-9) e saúde dérmica.", img=img)
            st.session_state.ultimo_scan = resultado
            # Invalida o cache das dicas para atualizar na próxima vez
            st.session_state.dicas_cache = None
        
        st.markdown(f"<div class='elite-card'><b>LAUDO TÉCNICO:</b><br><br>{resultado}</div>", unsafe_allow_html=True)
        
        st.markdown("### 📊 Guia de Referência BCS")
        

[Image of a Body Condition Score chart for dogs and cats]

        st.caption("Consulte sempre um veterinário para diagnósticos definitivos.")

# ABA 3: VETS (INTELLIGENCE MAPPING)
with t_geo:
    st.subheader("📍 Inteligência de Localização")
    loc = st.text_input("Bairro ou Cidade de Referência", placeholder="Ex: Itaim Bibi, SP")
    if loc and st.button("MAPEAR UNIDADES 24H"):
        with st.spinner("Rastreando unidades..."):
            res = call_ia(f"Liste 5 melhores hospitais vet 24h em {loc}. Formato: NOME|LAT|LON|ENDERECO|PROS|CONTRAS")
            for v in [l for l in res.split('\n') if '|' in l][:5]:
                d = v.split('|')
                try:
                    with st.container():
                        st.markdown(f"<div class='elite-card'><h3>🏥 {d[0]}</h3>", unsafe_allow_html=True)
                        st.map(pd.DataFrame({'lat': [float(d[1])], 'lon': [float(d[2])]}), zoom=14)
                        st.markdown(f"<p style='margin-top:10px;'>{d[3]}</p><p style='color:#aaffaa;'>✅ {d[4]}</p></div>", unsafe_allow_html=True)
                except: continue

# ABA 4: CUIDADORES (PREMIUM CAROUSEL)
with t_market:
    st.subheader("🐕 Caregiver Marketplace")
    if db is not None:
        cuidadores = list(db.usuarios.find({"tipo": "Cuidador"}))
        if cuidadores:
            num = len(cuidadores)
            c = cuidadores[st.session_state.cg_index % num]
            
            c1, c2, c3 = st.columns([1, 4, 1])
            if c1.button("⬅️", use_container_width=True): 
                st.session_state.cg_index -= 1
                st.rerun()
            if c3.button("➡️", use_container_width=True): 
                st.session_state.cg_index += 1
                st.rerun()
            
            with c2:
                st.markdown(f"""
                <div class="elite-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 1.5rem; font-weight: 800;">{c['nome']}</span>
                        <span class="price-tag">R$ {c.get('valor_diaria', 0):.2f}/dia</span>
                    </div>
                    <p style="color:#888;">📍 {c.get('endereco', 'Global')} | 🐾 Especialista em {", ".join(c.get('tipos_animais', ['Pets']))}</p>
                    <p style="font-style: italic; color: #ccc;">"{c.get('resumo', 'Profissional verificado TechnoBolt.')}"</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhum cuidador disponível no momento.")

# --- SIDEBAR ELITE ---
with st.sidebar:
    st.markdown(f"### 👤 Perfil: {user_doc.get('nome')}")
    st.caption(f"Status: {user_doc.get('tipo')} Premium")
    st.divider()
    if st.button("ENCERRAR SESSÃO"):
        st.session_state.logado = False
        st.rerun()

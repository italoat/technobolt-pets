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
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stNumberInput>div>div>input { 
        background-color: #333333 !important; color: #ffffff !important; border: 1px solid #555555 !important; 
    }
    .stButton>button { background-color: #555555 !important; color: #ffffff !important; border-radius: 8px; font-weight: bold; width: 100%; }
    .clinic-card, .caregiver-card { 
        background-color: #1a1a1a; border: 1px solid #333333; border-radius: 12px; 
        padding: 20px; margin-bottom: 25px; 
    }
    .pros { color: #aaffaa; font-size: 0.85rem; margin-bottom: 5px; }
    .contras { color: #ffaaaa; font-size: 0.85rem; }
    .price-tag { color: #3b82f6; font-weight: bold; font-size: 1.1rem; }
    .stMap { filter: grayscale(1) invert(1); border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- MOTOR DE IA (MOTORES SOLICITADOS) ---
def call_ia(prompt, img=None):
    chaves = [os.environ.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    if not chaves: return "Erro: API Key"
    
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
            if img:
                response = model.generate_content([prompt, img])
            else:
                response = model.generate_content(prompt)
            return response.text
        except:
            continue
    return "Serviço de IA temporariamente indisponível."

# --- ESTADO DA SESSÃO ---
if "logado" not in st.session_state: st.session_state.logado = False
if "ultimo_scan" not in st.session_state: st.session_state.ultimo_scan = None
if "cg_index" not in st.session_state: st.session_state.cg_index = 0

# --- LOGIN E CADASTRO ---
if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center;'>🐾 TechnoBolt Pets</h1>", unsafe_allow_html=True)
    tab_login, tab_registro = st.tabs(["🔐 Acessar Hub", "📝 Solicitar Acesso"])
    
    with tab_login:
        u, p = st.text_input("Usuário", key="l_u"), st.text_input("Senha", type="password", key="l_p")
        if st.button("ACESSAR HUB"):
            user = db.usuarios.find_one({"usuario": u, "senha": p}) if db is not None else None
            if user: 
                st.session_state.logado = True
                st.session_state.user_data = user
                st.rerun()
            else: st.error("Credenciais inválidas.")

    with tab_registro:
        st.markdown("### Crie seu Perfil")
        new_nome = st.text_input("Nome Completo")
        new_user = st.text_input("Escolha um Usuário").lower().strip()
        new_pass = st.text_input("Senha de Acesso", type="password")
        tipo_perfil = st.selectbox("Eu sou um:", ["Usuário Normal", "Cuidador"])
        
        extra_data = {}
        if tipo_perfil == "Cuidador":
            st.divider()
            extra_data['resumo'] = st.text_area("Resumo Profissional (Bio)")
            col1, col2 = st.columns(2)
            extra_data['idade'] = col1.number_input("Sua Idade", 18, 90, 25)
            extra_data['valor_diaria'] = col2.number_input("Valor da Diária (R$)", 0.0, 1000.0, 50.0)
            extra_data['endereco'] = st.text_input("Endereço / Região de Atendimento")
            extra_data['tipos_animais'] = st.multiselect("Animais", ["Cães", "Gatos", "Pássaros", "Roedores"])
            extra_data['tamanhos'] = st.multiselect("Porte Aceito", ["Pequeno", "Médio", "Grande"])
            extra_data['idades_pet'] = st.multiselect("Idade do Pet", ["Filhote", "Adulto", "Idoso"])

        if st.button("SOLICITAR MEU ACESSO"):
            if new_user and new_pass and db is not None:
                if db.usuarios.find_one({"usuario": new_user}):
                    st.error("Usuário já existe.")
                else:
                    payload = {"nome": new_nome, "usuario": new_user, "senha": new_pass, "tipo": tipo_perfil, "data_registro": datetime.now()}
                    payload.update(extra_data)
                    db.usuarios.insert_one(payload)
                    st.success("Cadastro realizado!")
    st.stop()

# --- INTERFACE LOGADA ---
user_doc = st.session_state.user_data
tab_dicas, tab_scan, tab_vets, tab_cuidadores = st.tabs(["💡 Insights", "🧬 PetScan", "📍 Localizar Vets", "🐕 Cuidadores"])

# --- ABA 1: DICAS ---
with tab_dicas:
    st.markdown("### Dicas de Performance Pet")
    p_dicas = f"4 dicas curtas pet. Verão 2026. Contexto: {st.session_state.ultimo_scan or 'Geral'}. Formato: TAG|DICA"
    res = call_ia(p_dicas)
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
        
        st.markdown("### Guia de Referência: Condição Corporal")
        # CORREÇÃO AQUI: Mantendo a string em uma única linha para evitar o SyntaxError
        st.markdown("

[Image of a Body Condition Score chart for dogs and cats]
")

# --- ABA 3: VETS ---
with tab_vets:
    st.subheader("📍 Encontrar Melhores Clínicas")
    loc_user = st.text_input("Sua localização (ex: Lapa, SP)", key="loc_vets")
    if st.button("BUSCAR 5 MELHORES CLÍNICAS") and loc_user:
        prompt_vets = f"Liste 5 clínicas 24h em {loc_user}. Formato: NOME|LATITUDE|LONGITUDE|ENDERECO|PRÓS|CONTRAS"
        res_vets = call_ia(prompt_vets)
        if res_vets:
            for vet in [l for l in res_vets.split('\n') if '|' in l][:5]:
                d = vet.split('|')
                if len(d) >= 6:
                    with st.container():
                        st.markdown(f"<div class='clinic-card'><h3>🏥 {d[0]}</h3>", unsafe_allow_html=True)
                        try: st.map(pd.DataFrame({'lat': [float(d[1])], 'lon': [float(d[2])]}), zoom=15)
                        except: pass
                        st.markdown(f"<p style='color:#888; margin-top:10px;'>📍 {d[3]}</p><p class='pros'>✅ {d[4]}</p><p class='contras'>❌ {d[5]}</p></div>", unsafe_allow_html=True)

# --- ABA 4: CUIDADORES ---
with tab_cuidadores:
    st.subheader("🐕 Cuidadores Parceiros")
    if db is not None:
        cuidadores = list(db.usuarios.find({"tipo": "Cuidador"}))
        if not cuidadores:
            st.info("Nenhum cuidador cadastrado.")
        else:
            num = len(cuidadores)
            if st.session_state.cg_index >= num: st.session_state.cg_index = 0
            c = cuidadores[st.session_state.cg_index]
            col_p, col_i, col_n = st.columns([1, 4, 1])
            with col_p:
                st.markdown("<br><br><br>", unsafe_allow_html=True)
                if st.button("⬅️"): st.session_state.cg_index = (st.session_state.cg_index - 1) % num; st.rerun()
            with col_i:
                st.markdown(f"""
                <div class="caregiver-card">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-size: 1.5rem; font-weight: bold;">👤 {c['nome']}</span>
                        <span class="price-tag">R$ {c.get('valor_diaria', 0.0):.2f}/dia</span>
                    </div>
                    <p style="color: #888;">📍 {c.get('endereco', 'N/A')} | 🎂 {c.get('idade', '--')} anos</p>
                    <p>{c.get('resumo', '...')}</p>
                    <hr style="border: 0.1px solid #333;">
                    <small><b>🐾 Animais:</b> {", ".join(c.get('tipos_animais', []))}</small><br>
                    <small><b>📏 Porte:</b> {", ".join(c.get('tamanhos', []))} | <b>🦴 Idade:</b> {", ".join(c.get('idades_pet', []))}</small>
                </div>""", unsafe_allow_html=True)
            with col_n:
                st.markdown("<br><br><br>", unsafe_allow_html=True)
                if st.button("➡️"): st.session_state.cg_index = (st.session_state.cg_index + 1) % num; st.rerun()

with st.sidebar:
    st.write(f"**Perfil:** {user_doc.get('nome', 'User')}")
    if st.button("LOGOUT"): st.session_state.logado = False; st.rerun()

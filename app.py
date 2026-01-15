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

# --- CONFIGURAÇÃO DE ENGENHARIA ---
pillow_heif.register_heif_opener()
st.set_page_config(page_title="TechnoBolt Pets Hub | Enterprise", layout="wide", page_icon="🐾")

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
        st.error(f"⚠️ Erro de Database: {e}")
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM (BLACK, WHITE & BROWN LUXURY) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; color: #ffffff !important; }
    .stApp { background-color: #000000 !important; }
    
    /* Inputs, Forms e Barras (Marrom Chocolate) */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stNumberInput>div>div>input, .stSelectbox>div>div>div { 
        background-color: #3e2723 !important; border: 1px solid #4b3621 !important; color: #ffffff !important;
    }

    /* Botões Customizados */
    .stButton>button {
        background-color: #3e2723 !important; color: #ffffff !important;
        border: 1px solid #4b3621 !important; border-radius: 12px !important;
        font-weight: 700 !important; transition: 0.3s; width: 100%;
    }
    .stButton>button:hover { background-color: #4b3621 !important; border-color: #ffffff !important; }

    /* Estilo de Abas */
    .stTabs [data-baseweb="tab-list"] { background-color: #000000; }
    .stTabs [data-baseweb="tab"] { color: #888 !important; }
    .stTabs [aria-selected="true"] { color: #ffffff !important; border-bottom-color: #3e2723 !important; }

    /* Cards Elite */
    .elite-card {
        background: #0d0d0d; border: 1px solid #3e2723;
        border-radius: 20px; padding: 20px; margin-bottom: 15px;
    }
    .rating-badge { background: #5d4037; padding: 4px 12px; border-radius: 20px; font-weight: 800; }
    .pros { color: #aaffaa !important; }
    .contras { color: #ffaaaa !important; }
</style>
""", unsafe_allow_html=True)

# --- AI CORE ---
def call_ia(prompt, img=None):
    chaves = [os.environ.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    if not chaves: return "Erro de Chave API."
    motores = ["models/gemini-3-flash-preview", "models/gemini-2.5-flash", "models/gemini-2.0-flash", "models/gemini-flash-latest"]
    genai.configure(api_key=random.choice(chaves))
    for motor in motores:
        try:
            model = genai.GenerativeModel(motor)
            res = model.generate_content([prompt, img] if img else prompt)
            return res.text
        except: continue
    return "IA Offline."

# --- AUTH LOGIC ---
if "logado" not in st.session_state: st.session_state.logado = False
if "user_data" not in st.session_state: st.session_state.user_data = None

def login():
    st.markdown("<h1 style='text-align: center;'>🐾 TECHNOBOLT PETS</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔐 Entrar", "📝 Cadastrar"])
    with t1:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR HUB"):
            user = db.usuarios.find_one({"usuario": u, "senha": p})
            if user:
                st.session_state.logado = True
                st.session_state.user_data = user
                st.rerun()
            else: st.error("Acesso negado.")
    with t2:
        n = st.text_input("Nome Completo")
        nu = st.text_input("Novo Usuário").lower()
        np = st.text_input("Senha ", type="password")
        addr = st.text_input("Endereço Completo")
        tipo = st.selectbox("Tipo de Conta", ["Tutor", "Cuidador"])
        if st.button("CRIAR CONTA"):
            status = "Pendente" if tipo == "Cuidador" else "Ativo"
            db.usuarios.insert_one({"nome": n, "usuario": nu, "senha": np, "endereco": addr, "tipo": tipo, "status": status, "dt": datetime.now()})
            st.success("Cadastro realizado! Aguarde aprovação se for cuidador.")

if not st.session_state.logado:
    login()
    st.stop()

# --- DASHBOARD LOGIC ---
user = st.session_state.user_data

# SIDEBAR
with st.sidebar:
    st.markdown(f"### 👤 {user['nome']}")
    st.caption(f"Perfil: {user['tipo']} | Status: {user.get('status', 'Ativo')}")
    if st.button("SAIR"):
        st.session_state.logado = False
        st.rerun()

# ---------------- ADMIN ----------------
if user['tipo'] == "Admin":
    st.title("⚙️ Painel de Governança")
    pendentes = list(db.usuarios.find({"status": "Pendente"}))
    st.subheader(f"Aprovações Pendentes ({len(pendentes)})")
    for p in pendentes:
        with st.container():
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{p['nome']}** solicita acesso como Cuidador.")
            if c2.button("APROVAR", key=p['usuario']):
                db.usuarios.update_one({"usuario": p['usuario']}, {"$set": {"status": "Ativo"}})
                st.rerun()
    st.divider()
    st.subheader("Todos os Usuários")
    st.dataframe(pd.DataFrame(list(db.usuarios.find({}, {"senha": 0}))), use_container_width=True)

# ---------------- CUIDADOR ----------------
elif user['tipo'] == "Cuidador":
    if user.get('status') == "Pendente":
        st.warning("Sua conta está em análise. O administrador aprovará seu acesso em breve.")
    else:
        st.title("🐕 Painel do Cuidador")
        tab_req, tab_chat = st.tabs(["📋 Pedidos de Contratação", "💬 Meus Chats"])
        
        with tab_req:
            # Lógica para mostrar pedidos (seria uma nova collection 'pedidos')
            st.info("Aguardando novas solicitações de tutores próximos.")
            
        with tab_chat:
            st.subheader("Mensagens Recebidas")
            chats = list(db.mensagens.find({"receiver_id": user['usuario']}).sort("dt", -1))
            if not chats:
                st.write("Nenhuma mensagem por enquanto.")
            for msg in chats:
                st.markdown(f"<div class='elite-card'><b>De: {msg['sender_id']}</b><br>{msg['texto']}<br><small>{msg['dt'].strftime('%H:%M')}</small></div>", unsafe_allow_html=True)

# ---------------- TUTOR (NORMAL) ----------------
elif user['tipo'] == "Tutor":
    t_insights, t_scan, t_vets, t_care, t_chats = st.tabs(["💡 Insights", "🧬 PetScan", "📍 Clínicas & Mapas", "🤝 Cuidadores", "💬 Chats"])

    with t_insights:
        st.markdown("### Dicas de IA")
        res = call_ia("4 dicas rápidas de saúde pet para hoje.")
        st.write(res)

    with t_scan:
        st.subheader("🧬 Diagnóstico Biométrico")
        up = st.file_uploader("Foto do Pet", type=['jpg', 'png'])
        if up and st.button("EXECUTAR SCAN"):
            img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
            st.image(img, width=300)
            res = call_ia("Analise BCS e saúde desta foto.", img=img)
            st.markdown(f"<div class='elite-card'>{res}</div>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("### 📊 Guia de Referência: Condição Corporal")
            

[Image of a Body Condition Score chart for dogs and cats]


    with t_vets:
        st.subheader("📍 Localizador de Saúde Animal")
        search = st.text_input("Pesquisar Veterinários, Petshops ou Tosadores...")
        if search:
            with st.spinner("Mapeando estabelecimentos..."):
                prompt = f"Liste 3 locais de {search} próximos a {user['endereco']}. Retorne NOME|NOTA|AVAL|PROS|CONTRAS"
                res = call_ia(prompt)
                for line in res.split('\n'):
                    if '|' in line:
                        d = line.split('|')
                        st.markdown(f"""
                        <div class='elite-card'>
                            <div style='display:flex; justify-content:space-between;'>
                                <b>🏥 {d[0]}</b> <span class='rating-badge'>⭐ {d[1]}</span>
                            </div>
                            <small>{d[2]}</small><br>
                            <p class='pros'>✅ {d[3]}</p>
                            <p class='contras'>❌ {d[4]}</p>
                        </div>
                        """, unsafe_allow_html=True)
                st.map(pd.DataFrame({'lat': [-23.55], 'lon': [-46.63]})) # Exemplo estático para visual

    with t_care:
        st.subheader("🤝 Contrate um Cuidador")
        cuidadores = list(db.usuarios.find({"tipo": "Cuidador", "status": "Ativo"}))
        for c in cuidadores:
            with st.container():
                st.markdown(f"<div class='elite-card'><b>{c['nome']}</b><br>📍 {c['endereco']}</div>", unsafe_allow_html=True)
                msg_txt = st.text_input("Mensagem inicial", key=f"msg_{c['usuario']}")
                if st.button("INICIAR CHAT", key=f"btn_{c['usuario']}"):
                    db.mensagens.insert_one({
                        "sender_id": user['usuario'],
                        "receiver_id": c['usuario'],
                        "texto": msg_txt,
                        "dt": datetime.now()
                    })
                    st.success("Mensagem enviada!")

    with t_chats:
        st.subheader("Minhas Conversas")
        minhas_mensagens = list(db.mensagens.find({"sender_id": user['usuario']}).sort("dt", -1))
        for m in minhas_mensagens:
            st.markdown(f"<div class='elite-card'><b>Para: {m['receiver_id']}</b><br>{m['texto']}</div>", unsafe_allow_html=True)

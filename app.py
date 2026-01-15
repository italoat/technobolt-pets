import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps
import io
import pandas as pd
import urllib.parse
from datetime import datetime
from pymongo import MongoClient
import pillow_heif
import random

# --- CONFIGURAÇÃO DE ENGENHARIA SÊNIOR ---
pillow_heif.register_heif_opener()
st.set_page_config(
    page_title="TechnoBolt Pets Hub | Enterprise Edition", 
    layout="wide", 
    page_icon="🐾",
    initial_sidebar_state="expanded"
)

# --- DATABASE ENGINE (SECRETS) ---
@st.cache_resource
def iniciar_conexao():
    try:
        user = st.secrets["MONGO_USER"]
        pass_raw = st.secrets["MONGO_PASS"]
        host = st.secrets["MONGO_HOST"]
        password = urllib.parse.quote_plus(pass_raw)
        uri = f"mongodb+srv://{user}:{password}@{host}/?appName=Cluster0"
        client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
        return client['technoboltpets']
    except Exception as e:
        st.error(f"⚠️ Erro de Database: {e}")
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM (CORREÇÃO DE SIDEBAR E TABS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    
    /* Global e Sidebar */
    [data-testid="stSidebar"], .stApp, [data-testid="stSidebarContent"] { 
        background-color: #000000 !important; 
        color: #ffffff !important; 
    }
    
    * { font-family: 'Plus Jakarta Sans', sans-serif; color: #ffffff !important; }

    /* Estilização das Abas Superiores (Visibilidade Máxima) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #000000;
        border-bottom: 1px solid #3e2723;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #121212;
        border-radius: 8px 8px 0 0;
        color: #888888 !important;
        border: 1px solid #1a1a1a;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3e2723 !important;
        color: #ffffff !important;
        border: 1px solid #3e2723 !important;
    }

    /* Forms, Inputs e Barras (Marrom Chocolate) */
    input, textarea, [data-baseweb="select"] > div { 
        background-color: #3e2723 !important; 
        border: 1px solid #4b3621 !important; 
        color: #ffffff !important;
    }
    
    /* Botões Customizados */
    .stButton>button {
        background-color: #3e2723 !important;
        color: #ffffff !important;
        border: 1px solid #4b3621 !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        width: 100%;
    }
    .stButton>button:hover { background-color: #4b3621 !important; border-color: #ffffff !important; }

    /* Cards Elite */
    .elite-card {
        background: #0d0d0d; border: 1px solid #3e2723;
        border-radius: 20px; padding: 20px; margin-bottom: 15px;
    }
    
    /* Correção de labels brancos na sidebar branca */
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# --- AI CORE ENGINE ---
def call_ia(prompt, img=None):
    chaves = [st.secrets.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    if not chaves: return "Erro: Chaves de API não configuradas."
    motores = ["models/gemini-2.0-flash", "models/gemini-3-flash-preview", "models/gemini-flash-latest"]
    genai.configure(api_key=random.choice(chaves))
    for motor in motores:
        try:
            model = genai.GenerativeModel(motor)
            res = model.generate_content([prompt, img] if img else prompt)
            return res.text
        except: continue
    return "Serviço de IA Offline."

# --- AUTH & SESSION ---
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
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
    with t2:
        n = st.text_input("Nome Completo")
        nu = st.text_input("User").lower()
        np = st.text_input("Pass", type="password")
        addr = st.text_input("Endereço Completo")
        tipo = st.selectbox("Tipo", ["Tutor", "Cuidador"])
        if st.button("CRIAR CONTA"):
            status = "Pendente" if tipo == "Cuidador" else "Ativo"
            db.usuarios.insert_one({"nome": n, "usuario": nu, "senha": np, "endereco": addr, "tipo": tipo, "status": status, "dt": datetime.now()})
            st.success("Cadastrado! Cuidadores aguardam aprovação admin.")
    st.stop()

# --- INTERFACE PRINCIPAL ---
user = st.session_state.user_data

with st.sidebar:
    st.markdown(f"### 👤 {user['nome']}")
    st.caption(f"Perfil: {user['tipo']}")
    st.divider()
    
    if user['tipo'] == "Tutor":
        st.subheader("🐾 Meus Pets")
        pets = list(db.pets.find({"owner_id": user['usuario']}))
        if pets:
            sel_pet_name = st.selectbox("Selecionar Pet", [p['nome'] for p in pets])
            cur_pet = next(p for p in pets if p['nome'] == sel_pet_name)
        else:
            st.info("Nenhum pet registrado.")
            cur_pet = None
            
        with st.expander("➕ Novo Pet"):
            p_n = st.text_input("Nome")
            p_e = st.selectbox("Espécie", ["Cachorro", "Gato", "Ave", "Réptil", "Roedor", "Outro"])
            if st.button("Salvar Pet"):
                db.pets.insert_one({"owner_id": user['usuario'], "nome": p_n, "especie": p_e, "dt": datetime.now()})
                st.rerun()
    
    st.divider()
    if st.button("SAIR"):
        st.session_state.logado = False
        st.rerun()

# ---------------- ADMIN ----------------
if user['tipo'] == "Admin":
    st.title("⚙️ Painel de Governança")
    pendentes = list(db.usuarios.find({"status": "Pendente", "tipo": "Cuidador"}))
    if pendentes:
        st.subheader(f"Aprovações de Cuidadores ({len(pendentes)})")
        for p in pendentes:
            with st.container():
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{p['nome']}** | {p['endereco']}")
                if c2.button("APROVAR", key=p['usuario']):
                    db.usuarios.update_one({"usuario": p['usuario']}, {"$set": {"status": "Ativo"}})
                    st.rerun()
    st.divider()
    st.subheader("Base Geral")
    st.dataframe(pd.DataFrame(list(db.usuarios.find({}, {"senha": 0}))), use_container_width=True)

# ---------------- CUIDADOR ----------------
elif user['tipo'] == "Cuidador":
    if user.get('status') == "Pendente":
        st.warning("Aguardando aprovação do administrador.")
    else:
        st.title("🐕 Painel do Cuidador")
        mensagens = list(db.mensagens.find({"receiver_id": user['usuario']}).sort("dt", -1))
        st.subheader("Pedidos de Contratação")
        for m in mensagens:
            st.markdown(f"<div class='elite-card'><b>De: {m['sender_id']}</b><br>Endereço: {m.get('sender_addr', 'N/A')}<p>{m['texto']}</p></div>", unsafe_allow_html=True)

# ---------------- TUTOR ----------------
elif user['tipo'] == "Tutor":
    t_scan, t_vets, t_care, t_chats = st.tabs(["🧬 PetScan IA", "📍 Clínicas & Mapas", "🤝 Cuidadores", "💬 Chats"])

    with t_scan:
        st.subheader("🧬 Diagnóstico Biométrico Avançado")
        if not cur_pet:
            st.warning("Cadastre um pet na barra lateral.")
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                modo = st.radio("Tipo de Scan", ["Escore Corporal (BCS)", "Saúde Digestiva (Fezes)"])
                up = st.file_uploader("Enviar Foto", type=['jpg', 'png', 'heic'])
            with col_b:
                sintomas = st.text_area("Observações/Sintomas (Opcional)")
            
            if up and st.button("ANALISAR AGORA"):
                img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
                st.image(img, width=400)
                prompt = f"""Atue como um veterinário experiente. Analise este {cur_pet['especie']} ({cur_pet['nome']}).
                Modo: {modo}. Sintomas relatados: {sintomas}. Dê um laudo técnico completo e alertas."""
                res = call_ia(prompt, img=img)
                st.markdown(f"<div class='elite-card'>{res}</div>", unsafe_allow_html=True)
                
                if "BCS" in modo:
                    st.divider()
                    st.markdown("### 📊 Guia de Referência: Condição Corporal")
                    st.markdown("

[Image of a Body Condition Score chart for dogs and cats]
")

                if "Fezes" in modo:
                    st.divider()
                    st.markdown("### 📊 Guia de Referência: Escala de Bristol para Pets")
                    st.markdown("")

    with t_vets:
        st.subheader("📍 Localizador de Elite")
        search = st.text_input("Pesquisar Veterinários, Petshops ou Tosadores...")
        if search:
            prompt = f"Liste 3 locais de {search} próximos a {user['endereco']}. Retorne NOME|NOTA|AVAL|PROS|CONTRAS"
            res = call_ia(prompt)
            st.write(res)
            st.map(pd.DataFrame({'lat': [-23.55], 'lon': [-46.63]})) # Simulação

    with t_care:
        st.subheader("🤝 Cuidadores Disponíveis")
        cuidadores = list(db.usuarios.find({"tipo": "Cuidador", "status": "Ativo"}))
        for c in cuidadores:
            with st.container():
                st.markdown(f"<div class='elite-card'><b>{c['nome']}</b> (📍 {c['endereco']})</div>", unsafe_allow_html=True)
                m_txt = st.text_input("Mensagem", key=f"m_{c['usuario']}")
                if st.button("ENVIAR PEDIDO", key=f"b_{c['usuario']}"):
                    db.mensagens.insert_one({"sender_id": user['usuario'], "sender_addr": user['endereco'], "receiver_id": c['usuario'], "texto": m_txt, "dt": datetime.now()})
                    st.success("Enviado!")

    with t_chats:
        st.subheader("Histórico de Mensagens")
        msgs = list(db.mensagens.find({"sender_id": user['usuario']}).sort("dt", -1))
        for m in msgs:
            st.markdown(f"<div class='elite-card'><b>Para: {m['receiver_id']}</b><p>{m['texto']}</p></div>", unsafe_allow_html=True)

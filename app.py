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

# --- ENGENHARIA DE INICIALIZAÇÃO ---
pillow_heif.register_heif_opener()
st.set_page_config(
    page_title="TechnoBolt Pets Hub | Enterprise", 
    layout="wide", 
    page_icon="🐾",
    initial_sidebar_state="expanded"
)

# --- DATABASE ENGINE (SECRETS CLOUD) ---
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
        st.error(f"⚠️ Erro de Database: Verifique os Secrets. {e}")
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM: OBSIDIAN & DEEP COCOA (RESILIENTE) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    
    /* Global & Sidebar */
    [data-testid="stSidebar"], .stApp, [data-testid="stSidebarContent"], [data-testid="stHeader"] { 
        background-color: #000000 !important; 
        color: #ffffff !important; 
    }
    
    * { font-family: 'Plus Jakarta Sans', sans-serif; color: #ffffff !important; }

    /* Abas Superiores (Garantindo Visibilidade) */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #000000 !important;
        border-bottom: 2px solid #3e2723 !important;
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #0a0a0a !important;
        color: #888888 !important;
        font-weight: 600 !important;
        border: 1px solid #1a1a1a !important;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3e2723 !important;
        color: #ffffff !important;
        border: 1px solid #3e2723 !important;
    }

    /* Forms, Inputs e Selects */
    input, textarea, [data-baseweb="select"] > div { 
        background-color: #3e2723 !important; 
        border: 1px solid #4b3621 !important; 
        color: #ffffff !important;
    }
    
    /* Botões Marrom Chocolate */
    .stButton>button {
        background-color: #3e2723 !important;
        color: #ffffff !important;
        border: 1px solid #4b3621 !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        transition: 0.3s ease;
    }
    .stButton>button:hover { background-color: #4b3621 !important; border-color: #ffffff !important; }

    /* Cards Elite */
    .elite-card {
        background: #0d0d0d; border: 1px solid #3e2723;
        border-radius: 20px; padding: 20px; margin-bottom: 15px;
    }
    
    /* Ajuste para Sidebar labels */
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# --- AI CORE ENGINE (MULTIMOTORES) ---
def call_ia(prompt, img=None):
    chaves = [st.secrets.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    if not chaves: return "Erro: Chaves de API ausentes nos Secrets."
    
    motores = ["models/gemini-2.0-flash", "models/gemini-3-flash-preview", "models/gemini-flash-latest"]
    genai.configure(api_key=random.choice(chaves))
    
    for motor in motores:
        try:
            model = genai.GenerativeModel(motor)
            res = model.generate_content([prompt, img] if img else prompt)
            return res.text
        except: continue
    return "IA Offline no momento."

# --- SISTEMA DE SESSÃO ---
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center;'>🐾 TECHNOBOLT PETS</h1>", unsafe_allow_html=True)
    t_in, t_reg = st.tabs(["🔐 Acesso", "📝 Registro"])
    with t_in:
        u, p = st.text_input("Usuário"), st.text_input("Senha", type="password")
        if st.button("ACESSAR HUB"):
            user = db.usuarios.find_one({"usuario": u, "senha": p})
            if user:
                st.session_state.logado, st.session_state.user_data = True, user
                st.rerun()
    with t_reg:
        n, nu, np = st.text_input("Nome"), st.text_input("User").lower(), st.text_input("Pass", type="password")
        addr = st.text_input("Endereço Completo")
        tipo = st.selectbox("Perfil", ["Tutor", "Cuidador"])
        if st.button("REGISTRAR"):
            status = "Pendente" if tipo == "Cuidador" else "Ativo"
            db.usuarios.insert_one({"nome": n, "usuario": nu, "senha": np, "endereco": addr, "tipo": tipo, "status": status, "dt": datetime.now()})
            st.success("Conta criada! Cuidadores aguardam Admin.")
    st.stop()

# --- INTERFACE PRINCIPAL ---
user_data = st.session_state.user_data

with st.sidebar:
    st.markdown(f"### 👤 {user_data['nome']}")
    st.caption(f"Acesso: {user_data['tipo']}")
    st.divider()
    
    cur_pet = None
    if user_data['tipo'] == "Tutor":
        st.subheader("🐾 Gerenciar Pets")
        pets = list(db.pets.find({"owner_id": user_data['usuario']}))
        if pets:
            sel_pet = st.selectbox("Perfil do Pet", [p['nome'] for p in pets])
            cur_pet = next(p for p in pets if p['nome'] == sel_pet)
        else:
            st.info("Nenhum pet registrado.")
            
        with st.expander("➕ Novo Pet"):
            p_n = st.text_input("Nome do Animal")
            p_e = st.selectbox("Espécie", ["Cachorro", "Gato", "Ave", "Réptil", "Roedor", "Exótico"])
            if st.button("Salvar Pet"):
                db.pets.insert_one({"owner_id": user_data['usuario'], "nome": p_n, "especie": p_e, "dt": datetime.now()})
                st.rerun()
    
    st.divider()
    if st.button("SAIR"):
        st.session_state.logado = False
        st.rerun()

# ---------------- WORKFLOWS POR PERFIL ----------------

if user_data['tipo'] == "Admin":
    st.title("⚙️ Governança de Acesso")
    pendentes = list(db.usuarios.find({"status": "Pendente", "tipo": "Cuidador"}))
    for p in pendentes:
        with st.container():
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{p['nome']}** solicita acesso como Cuidador.")
            if c2.button("APROVAR", key=p['usuario']):
                db.usuarios.update_one({"usuario": p['usuario']}, {"$set": {"status": "Ativo"}})
                st.rerun()
    st.divider()
    st.subheader("Base Geral")
    st.dataframe(pd.DataFrame(list(db.usuarios.find({}, {"senha": 0}))), use_container_width=True)

elif user_data['tipo'] == "Cuidador":
    if user_data.get('status') == "Pendente":
        st.warning("Aguardando aprovação do administrador.")
    else:
        st.title("🐕 Painel do Cuidador")
        mensagens = list(db.mensagens.find({"receiver_id": user_data['usuario']}).sort("dt", -1))
        st.subheader("Mensagens e Pedidos")
        for m in mensagens:
            st.markdown(f"<div class='elite-card'><b>De: {m['sender_id']}</b><br>Tutor em: {m.get('sender_addr', 'N/A')}<p>{m['texto']}</p></div>", unsafe_allow_html=True)

elif user_data['tipo'] == "Tutor":
    t_scan, t_vets, t_care, t_chats = st.tabs(["🧬 PetScan IA", "📍 Clínicas & Mapas", "🤝 Cuidadores", "💬 Chats"])

    with t_scan:
        st.subheader("🧬 Diagnóstico Biométrico Avançado")
        if not cur_pet:
            st.warning("Cadastre um pet no menu lateral para iniciar o scan.")
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                modo = st.radio("Foco da Análise", ["Escore Corporal (BCS)", "Saúde Digestiva (Fezes)"])
                up = st.file_uploader("Submeter Amostra Visual", type=['jpg', 'png', 'heic'])
            with col_b:
                sintomas = st.text_area("Relato de Sintomas (Opcional)")
            
            if up and st.button("EXECUTAR ANÁLISE PhD"):
                img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
                st.image(img, width=400)
                prompt = f"""Atue como Veterinário PhD. Analise este {cur_pet['especie']} ({cur_pet['nome']}).
                Modo: {modo}. Sintomas: {sintomas}. Dê laudo técnico e alertas de saúde."""
                res = call_ia(prompt, img=img)
                st.markdown(f"<div class='elite-card'>{res}</div>", unsafe_allow_html=True)
                
                if "BCS" in modo:
                    st.divider()
                    st.markdown("### 📊 Guia de Referência: Condição Corporal")
                    

[Image of a Body Condition Score chart for dogs and cats]

                    st.markdown("""[Analise a silhueta do seu pet com base nos padrões acima]""")

                if "Fezes" in modo:
                    st.divider()
                    st.markdown("### 📊 Guia de Referência: Saúde Digestiva")
                    

    with t_vets:
        st.subheader("📍 Localizador de Saúde")
        search = st.text_input("Pesquisar Veterinários, Petshops ou Tosadores...")
        if search:
            prompt = f"Liste 3 locais de {search} próximos a {user_data['endereco']}. NOME|NOTA|AVAL|PROS|CONTRAS"
            res = call_ia(prompt)
            st.write(res)
            st.map(pd.DataFrame({'lat': [-23.55], 'lon': [-46.63]})) # Simulação visual

    with t_care:
        st.subheader("🤝 Contratar Cuidadores")
        cuidadores = list(db.usuarios.find({"tipo": "Cuidador", "status": "Ativo"}))
        for c in cuidadores:
            st.markdown(f"<div class='elite-card'>👤 <b>{c['nome']}</b><br>📍 {c['endereco']}</div>", unsafe_allow_html=True)
            m_txt = st.text_input("Mensagem para o Cuidador", key=f"chat_{c['usuario']}")
            if st.button("INICIAR CHAT", key=f"btn_{c['usuario']}"):
                db.mensagens.insert_one({"sender_id": user_data['usuario'], "sender_addr": user_data['endereco'], "receiver_id": c['usuario'], "texto": m_txt, "dt": datetime.now()})
                st.success("Mensagem enviada!")

    with t_chats:
        st.subheader("Histórico de Conversas")
        msgs = list(db.mensagens.find({"sender_id": user_data['usuario']}).sort("dt", -1))
        for m in msgs:
            st.markdown(f"<div class='elite-card'><b>Para: {m['receiver_id']}</b><p>{m['texto']}</p></div>", unsafe_allow_html=True)

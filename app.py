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

# --- INICIALIZAÇÃO DE SISTEMA ---
pillow_heif.register_heif_opener()
st.set_page_config(page_title="TechnoBolt Pets Hub | Enterprise", layout="wide", page_icon="🐾")

# --- DATABASE ENGINE (INTEGRAÇÃO COM SECRETS.TOML) ---
@st.cache_resource
def iniciar_conexao():
    try:
        # Recuperação via Secrets do Streamlit
        user = st.secrets["MONGO_USER"]
        pass_raw = st.secrets["MONGO_PASS"]
        host = st.secrets["MONGO_HOST"]
        
        password = urllib.parse.quote_plus(pass_raw)
        uri = f"mongodb+srv://{user}:{password}@{host}/?appName=Cluster0"
        client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
        return client['technoboltpets']
    except Exception as e:
        st.error(f"⚠️ Erro de Infraestrutura: Verifique o secrets.toml. {e}")
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM: OBSIDIAN & DEEP COCOA ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; color: #ffffff !important; }
    .stApp { background-color: #000000 !important; }
    
    /* Inputs, Forms e Barras (Marrom Chocolate) */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stNumberInput>div>div>input, .stSelectbox>div>div>div { 
        background-color: #3e2723 !important; border: 1px solid #4b3621 !important; color: #ffffff !important;
    }

    /* Botões Customizados (Marrom Escuro) */
    .stButton>button {
        background-color: #3e2723 !important; color: #ffffff !important;
        border: 1px solid #4b3621 !important; border-radius: 12px !important;
        font-weight: 700 !important; transition: 0.3s; width: 100%;
    }
    .stButton>button:hover { background-color: #4b3621 !important; border-color: #ffffff !important; }

    /* Cards Elite */
    .elite-card {
        background: #0d0d0d; border: 1px solid #3e2723;
        border-radius: 20px; padding: 20px; margin-bottom: 15px;
    }
    .rating-badge { background: #5d4037; padding: 4px 12px; border-radius: 20px; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# --- AI CORE ENGINE ---
def call_ia(prompt, img=None):
    # Rotação de chaves via Secrets
    chaves = [st.secrets.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    if not chaves: return "Erro: API_KEYS_NOT_FOUND"
    
    motores = ["models/gemini-3-flash-preview", "models/gemini-2.5-flash", "models/gemini-2.0-flash", "models/gemini-flash-latest"]
    genai.configure(api_key=random.choice(chaves))
    
    for motor in motores:
        try:
            model = genai.GenerativeModel(motor)
            res = model.generate_content([prompt, img] if img else prompt)
            return res.text
        except: continue
    return "Serviço de IA temporariamente indisponível."

# --- AUTH & SESSION ---
if "logado" not in st.session_state: st.session_state.logado = False
if "user_data" not in st.session_state: st.session_state.user_data = None

if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center;'>🐾 TECHNOBOLT PETS</h1>", unsafe_allow_html=True)
    tab_in, tab_reg = st.tabs(["🔐 Acesso", "📝 Registro"])
    with tab_in:
        u, p = st.text_input("Usuário"), st.text_input("Senha", type="password")
        if st.button("ACESSAR HUB"):
            user = db.usuarios.find_one({"usuario": u, "senha": p})
            if user:
                st.session_state.logado = True
                st.session_state.user_data = user
                st.rerun()
    with tab_reg:
        n, nu, np = st.text_input("Nome"), st.text_input("User").lower(), st.text_input("Pass", type="password")
        addr = st.text_input("Endereço Completo (Obrigatório para Logística)")
        tipo = st.selectbox("Perfil", ["Tutor", "Cuidador"])
        if st.button("SOLICITAR CADASTRO"):
            status = "Pendente" if tipo == "Cuidador" else "Ativo"
            db.usuarios.insert_one({"nome": n, "usuario": nu, "senha": np, "endereco": addr, "tipo": tipo, "status": status, "dt": datetime.now()})
            st.success("Cadastro realizado! Cuidadores aguardam aprovação admin.")
    st.stop()

# --- INTERFACE PRINCIPAL ---
user = st.session_state.user_data

with st.sidebar:
    st.markdown(f"### 👤 {user['nome']}")
    st.caption(f"Acesso: {user['tipo']}")
    st.divider()
    
    if user['tipo'] == "Tutor":
        st.subheader("🐾 Meus Animais")
        pets = list(db.pets.find({"owner_id": user['usuario']}))
        if pets:
            sel_pet = st.selectbox("Selecionar Perfil", [p['nome'] for p in pets])
            cur_pet = next(p for p in pets if p['nome'] == sel_pet)
        else:
            st.info("Nenhum pet registrado.")
            cur_pet = None
            
        with st.expander("➕ Novo Registro"):
            p_n = st.text_input("Nome do Animal")
            p_e = st.selectbox("Espécie", ["Cachorro", "Gato", "Ave", "Réptil", "Roedor", "Outro"])
            if st.button("Salvar Registro"):
                db.pets.insert_one({"owner_id": user['usuario'], "nome": p_n, "especie": p_e, "dt": datetime.now()})
                st.rerun()
    
    st.divider()
    if st.button("LOGOUT"):
        st.session_state.logado = False
        st.rerun()

# ---------------- LÓGICA DE ABAS POR PERFIL ----------------

if user['tipo'] == "Admin":
    st.title("⚙️ Governança Administrativa")
    pendentes = list(db.usuarios.find({"status": "Pendente"}))
    if pendentes:
        st.subheader(f"Aprovações Pendentes ({len(pendentes)})")
        for p in pendentes:
            with st.container():
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{p['nome']}** | {p['endereco']}")
                if c2.button("APROVAR", key=p['usuario']):
                    db.usuarios.update_one({"usuario": p['usuario']}, {"$set": {"status": "Ativo"}})
                    st.rerun()
    st.divider()
    st.subheader("Base de Usuários")
    st.dataframe(pd.DataFrame(list(db.usuarios.find({}, {"senha": 0}))), use_container_width=True)

elif user['tipo'] == "Cuidador":
    if user.get('status') == "Pendente":
        st.warning("Sua conta está em análise. O acesso será liberado após auditoria.")
    else:
        st.title("🐕 Central do Cuidador")
        mensagens = list(db.mensagens.find({"receiver_id": user['usuario']}).sort("dt", -1))
        st.subheader("Solicitações de Contratação")
        if not mensagens: st.info("Nenhuma solicitação no momento.")
        for m in mensagens:
            st.markdown(f"""
            <div class='elite-card'>
                <b>Interessado: {m['sender_id']}</b><br>
                <small>Endereço: {m.get('sender_addr', 'N/A')}</small><p>{m['texto']}</p>
            </div>""", unsafe_allow_html=True)

elif user['tipo'] == "Tutor":
    t_scan, t_vets, t_care, t_hist = st.tabs(["🧬 PetScan IA", "📍 Vets & Mapas", "🤝 Cuidadores", "💬 Chats Efetuados"])

    with t_scan:
        st.subheader("🧬 Diagnóstico Biométrico Contextual")
        if not cur_pet:
            st.warning("Cadastre um pet no menu lateral para iniciar.")
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                tipo_scan = st.radio("Objetivo do Scan", ["Condição Corporal (BCS)", "Análise de Fezes (Digestivo)"])
                up = st.file_uploader("Capturar Imagem", type=['jpg', 'png', 'heic'])
            with col_b:
                sintomas = st.text_area("Descreva sintomas ou comportamento (opcional)")
            
            if up and st.button("PROCESSAR ANÁLISE"):
                img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
                st.image(img, width=400)
                prompt = f"""
                Atue como um especialista veterinário. 
                Animal: {cur_pet['especie']} ({cur_pet['nome']}).
                Análise solicitada: {tipo_scan}.
                Sintomas relatados: {sintomas if sintomas else 'Nenhum'}.
                Dê um laudo técnico, escore e recomendações de elite.
                """
                resultado = call_ia(prompt, img=img)
                st.markdown(f"<div class='elite-card'>{resultado}</div>", unsafe_allow_html=True)
                
                if tipo_scan == "Condição Corporal (BCS)":
                    st.divider()
                    st.markdown("### 📊 Guia de Referência: Condição Corporal")
                    # CORREÇÃO DEFINITIVA DO SYNTAX ERROR:
                    st.markdown("""

[Image of a Body Condition Score chart for dogs and cats]
""")

    with t_vets:
        st.subheader("📍 Localizador de Saúde Animal")
        search = st.text_input("Buscar Clínicas, Petshops ou Tosadores...")
        if search:
            prompt = f"Liste 3 locais de {search} próximos a {user['endereco']}. Retorne NOME|NOTA|AVAL|PROS|CONTRAS"
            res = call_ia(prompt)
            st.write(res)
            st.map(pd.DataFrame({'lat': [-23.55], 'lon': [-46.63]})) # Exemplo de renderização

    with t_care:
        st.subheader("🤝 Cuidadores Parceiros")
        cuidadores = list(db.usuarios.find({"tipo": "Cuidador", "status": "Ativo"}))
        for c in cuidadores:
            with st.container():
                st.markdown(f"<div class='elite-card'><b>{c['nome']}</b><br>📍 {c['endereco']}</div>", unsafe_allow_html=True)
                m_txt = st.text_input("Mensagem para o cuidador", key=f"m_{c['usuario']}")
                if st.button("INICIAR CONTRATAÇÃO", key=f"b_{c['usuario']}"):
                    db.mensagens.insert_one({
                        "sender_id": user['usuario'], "sender_addr": user['endereco'],
                        "receiver_id": c['usuario'], "texto": m_txt, "dt": datetime.now()
                    })
                    st.success("Solicitação enviada!")

    with t_hist:
        st.subheader("Histórico de Conversas")
        msgs = list(db.mensagens.find({"sender_id": user['usuario']}).sort("dt", -1))
        for m in msgs:
            st.markdown(f"<div class='elite-card'><b>Para: {m['receiver_id']}</b><p>{m['texto']}</p></div>", unsafe_allow_html=True)

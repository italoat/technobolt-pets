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

# --- CONFIGURAÇÃO DE ENGENHARIA DE ELITE ---
pillow_heif.register_heif_opener()
st.set_page_config(
    page_title="TechnoBolt Pets Hub | Enterprise Edition", 
    layout="wide", 
    page_icon="🐾",
    initial_sidebar_state="expanded"
)

# --- DATABASE ENGINE (INTEGRAÇÃO COM STREAMLIT SECRETS) ---
@st.cache_resource
def iniciar_conexao():
    try:
        # Recuperação segura via secrets.toml do Streamlit
        user = st.secrets["MONGO_USER"]
        pass_raw = st.secrets["MONGO_PASS"]
        host = st.secrets["MONGO_HOST"]
        password = urllib.parse.quote_plus(pass_raw)
        uri = f"mongodb+srv://{user}:{password}@{host}/?appName=Cluster0"
        client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
        return client['technoboltpets']
    except Exception as e:
        st.error(f"⚠️ Erro de Infraestrutura: Verifique os Secrets. {e}")
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM: OBSIDIAN & DEEP COCOA ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    
    /* Global & Sidebar Dark Mode */
    [data-testid="stSidebar"], .stApp, [data-testid="stSidebarContent"] { 
        background-color: #000000 !important; 
        color: #ffffff !important; 
    }
    
    * { font-family: 'Plus Jakarta Sans', sans-serif; color: #ffffff !important; }

    /* Estilização das Abas Superiores */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #000000;
        border-bottom: 1px solid #3e2723;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #121212;
        color: #888888 !important;
        border: 1px solid #1a1a1a;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3e2723 !important;
        color: #ffffff !important;
    }

    /* Forms, Inputs e Barras de Pesquisa (Marrom Chocolate) */
    input, textarea, [data-baseweb="select"] > div { 
        background-color: #3e2723 !important; 
        border: 1px solid #4b3621 !important; 
        color: #ffffff !important;
    }
    
    /* Botões Customizados (Marrom Chocolate) */
    .stButton>button {
        background-color: #3e2723 !important;
        color: #ffffff !important;
        border: 1px solid #4b3621 !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        transition: 0.3s ease;
    }
    .stButton>button:hover { 
        background-color: #4b3621 !important; 
        border-color: #ffffff !important; 
    }

    /* Cards Elite */
    .elite-card {
        background: #0d0d0d; border: 1px solid #3e2723;
        border-radius: 20px; padding: 20px; margin-bottom: 15px;
    }
    
    /* Correção de labels brancos na sidebar */
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# --- ENGINE DE IA (ROTATIVO) ---
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
    return "⚠️ IA Offline. Tente novamente."

# --- SISTEMA DE SESSÃO E AUTH ---
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center;'>🐾 TECHNOBOLT PETS</h1>", unsafe_allow_html=True)
    t_in, t_reg = st.tabs(["🔐 Entrar", "📝 Registrar"])
    
    with t_in:
        u, p = st.text_input("Usuário"), st.text_input("Senha", type="password")
        if st.button("ACESSAR SISTEMA"):
            user = db.usuarios.find_one({"usuario": u, "senha": p})
            if user:
                st.session_state.logado, st.session_state.user_data = True, user
                st.rerun()
            else: st.error("Acesso Negado.")
            
    with t_reg:
        n, nu, np = st.text_input("Nome Completo"), st.text_input("Username").lower(), st.text_input("Password", type="password")
        addr = st.text_input("Endereço (Obrigatório para Logística)")
        tipo = st.selectbox("Tipo de Perfil", ["Tutor", "Cuidador"])
        if st.button("FINALIZAR REGISTRO"):
            status = "Pendente" if tipo == "Cuidador" else "Ativo"
            db.usuarios.insert_one({"nome": n, "usuario": nu, "senha": np, "endereco": addr, "tipo": tipo, "status": status, "dt": datetime.now()})
            st.success("Conta criada! Cuidadores aguardam aprovação do Admin.")
    st.stop()

# --- INTERFACE PRINCIPAL ---
user = st.session_state.user_data

# MENU LATERAL: GESTÃO MULTI-PET
with st.sidebar:
    st.markdown(f"### 👤 {user['nome']}")
    st.caption(f"Perfil: {user['tipo']}")
    st.divider()
    
    cur_pet = None
    if user['tipo'] == "Tutor":
        st.subheader("🐾 Meus Pets")
        pets = list(db.pets.find({"owner_id": user['usuario']}))
        if pets:
            sel_name = st.selectbox("Pet em Foco", [p['nome'] for p in pets])
            cur_pet = next(p for p in pets if p['nome'] == sel_name)
        else:
            st.info("Nenhum pet registrado.")
            
        with st.expander("➕ Novo Animal"):
            p_nome = st.text_input("Nome do Pet")
            p_esp = st.selectbox("Espécie", ["Cachorro", "Gato", "Ave", "Roedor", "Réptil", "Outro"])
            if st.button("Salvar Perfil"):
                db.pets.insert_one({"owner_id": user['usuario'], "nome": p_nome, "especie": p_esp, "dt": datetime.now()})
                st.rerun()
    
    st.divider()
    if st.button("ENCERRAR SESSÃO"):
        st.session_state.logado = False
        st.rerun()

# --- WORKFLOWS POR PERFIL ---

# 1. ADMIN: GOVERNANÇA E APROVAÇÃO
if user['tipo'] == "Admin":
    st.title("⚙️ Painel de Governança")
    pendentes = list(db.usuarios.find({"status": "Pendente", "tipo": "Cuidador"}))
    if pendentes:
        st.subheader(f"Solicitações de Cuidadores ({len(pendentes)})")
        for p in pendentes:
            with st.container():
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{p['nome']}** | Endereço: {p['endereco']}")
                if c2.button("APROVAR", key=p['usuario']):
                    db.usuarios.update_one({"usuario": p['usuario']}, {"$set": {"status": "Ativo"}})
                    st.rerun()
    st.divider()
    st.subheader("Base Geral de Usuários")
    st.dataframe(pd.DataFrame(list(db.usuarios.find({}, {"senha": 0}))), use_container_width=True)

# 2. CUIDADOR: PEDIDOS E CONTRATAÇÕES
elif user['tipo'] == "Cuidador":
    if user.get('status') == "Pendente":
        st.warning("Sua conta está em análise. O acesso será liberado após auditoria.")
    else:
        st.title("🐕 Central do Cuidador")
        chats = list(db.mensagens.find({"receiver_id": user['usuario']}).sort("dt", -1))
        st.subheader("Mensagens e Pedidos Recebidos")
        if not chats: st.info("Nenhuma proposta no momento.")
        for msg in chats:
            st.markdown(f"""
            <div class='elite-card'>
                <b>De: {msg['sender_id']}</b><br>
                Endereço do Tutor: {msg.get('sender_addr', 'Consultar')}<br>
                <p style='margin-top:10px;'>{msg['texto']}</p>
            </div>""", unsafe_allow_html=True)

# 3. TUTOR: ECOSSISTEMA COMPLETO
elif user['tipo'] == "Tutor":
    t_scan, t_mapa, t_hire, t_msg = st.tabs(["🧬 PetScan IA", "📍 Clínicas & Busca", "🤝 Cuidadores", "💬 Meus Chats"])

    with t_scan:
        st.subheader("🧬 Diagnóstico Biométrico Avançado")
        if not cur_pet:
            st.warning("Cadastre um pet no menu lateral para iniciar.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                modo = st.radio("Tipo de Diagnóstico", ["Escore Corporal (BCS)", "Saúde Digestiva (Fezes)"])
                up = st.file_uploader("Submeter Amostra", type=['jpg', 'png', 'heic'])
            with c2:
                sintomas = st.text_area("Descreva sintomas ou comportamentos estranhos (opcional)")
            
            if up and st.button("EXECUTAR ANÁLISE IA"):
                img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
                st.image(img, width=400)
                prompt = f"""Atue como um veterinário PhD. Analise este {cur_pet['especie']} ({cur_pet['nome']}).
                Modo de Análise: {modo}. Sintomas relatados: {sintomas if sintomas else 'Nenhum'}.
                Dê um laudo técnico, escore e recomendações de elite."""
                res = call_ia(prompt, img=img)
                st.markdown(f"<div class='elite-card'>{res}</div>", unsafe_allow_html=True)
                
                if "BCS" in modo:
                    st.divider()
                    st.markdown("### 📊 Guia de Referência: Condição Corporal")
                    # CORREÇÃO DEFINITIVA DO SYNTAX ERROR:
                    st.markdown("""""")

                if "Fezes" in modo:
                    st.divider()
                    st.markdown("### 📊 Guia de Referência: Saúde Digestiva")
                    st.markdown("""""")

    with t_mapa:
        st.subheader("📍 Busca Inteligente de Estabelecimentos")
        search = st.text_input("O que você procura? (Veterinário, Petshop, Tosa...)")
        if search:
            with st.spinner("Mapeando rede..."):
                p_map = f"Liste 3 locais de {search} próximos a {user['endereco']}. Retorne NOME|NOTA|AVALIAÇÃO|PRÓS|CONTRAS"
                res = call_ia(p_map)
                for line in res.split('\n'):
                    if '|' in line:
                        d = line.split('|')
                        st.markdown(f"""
                        <div class='elite-card'>
                            <div style='display:flex; justify-content:space-between;'>
                                <b>🏥 {d[0]}</b> <span class='rating-badge'>⭐ {d[1]}</span>
                            </div>
                            <small>{d[2]}</small><br>
                            <p style='color:#aaffaa;'>✅ {d[3]}</p>
                            <p style='color:#ffaaaa;'>❌ {d[4]}</p>
                        </div>""", unsafe_allow_html=True)
                st.map(pd.DataFrame({'lat': [-23.55], 'lon': [-46.63]})) # Exemplo Visual

    with t_hire:
        st.subheader("🤝 Cuidadores Disponíveis")
        cuidadores = list(db.usuarios.find({"tipo": "Cuidador", "status": "Ativo"}))
        for c in cuidadores:
            with st.container():
                st.markdown(f"<div class='elite-card'>👤 <b>{c['nome']}</b><br>📍 {c['endereco']}</div>", unsafe_allow_html=True)
                txt = st.text_input("Mensagem de proposta", key=f"chat_{c['usuario']}")
                if st.button("INICIAR CHAT", key=f"btn_{c['usuario']}"):
                    db.mensagens.insert_one({
                        "sender_id": user['usuario'], "sender_addr": user['endereco'],
                        "receiver_id": c['usuario'], "texto": txt, "dt": datetime.now()
                    })
                    st.success("Mensagem enviada com sucesso!")

    with t_msg:
        st.subheader("Histórico de Mensagens Enviadas")
        msgs = list(db.mensagens.find({"sender_id": user['usuario']}).sort("dt", -1))
        for m in msgs:
            st.markdown(f"<div class='elite-card'><b>Para: {m['receiver_id']}</b><p>{m['texto']}</p></div>", unsafe_allow_html=True)

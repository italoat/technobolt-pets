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
from fpdf import FPDF

# --- SETUP DE ENGENHARIA ---
pillow_heif.register_heif_opener()
st.set_page_config(
    page_title="TechnoBolt Pets Hub | Enterprise", 
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

# --- DESIGN SYSTEM: OBSIDIAN & DEEP COCOA (VISIBILIDADE TOTAL) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    
    /* Global & Sidebar Visibilidade */
    [data-testid="stSidebar"], .stApp, [data-testid="stHeader"], [data-testid="stSidebarContent"] { 
        background-color: #000000 !important; 
        color: #ffffff !important; 
    }
    
    * { font-family: 'Plus Jakarta Sans', sans-serif; color: #ffffff !important; }

    /* MENU SUPERIOR (TABS) - FORÇANDO VISIBILIDADE */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #000000 !important;
        border-bottom: 2px solid #3e2723 !important;
        gap: 15px !important;
        padding-top: 10px !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px !important;
        background-color: #0d0d0d !important;
        border-radius: 12px 12px 0 0 !important;
        color: #bbbbbb !important;
        border: 1px solid #1a1a1a !important;
        padding: 0 30px !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3e2723 !important;
        color: #ffffff !important;
        border-color: #3e2723 !important;
    }

    /* Forms e Inputs Marrom Chocolate */
    input, textarea, [data-baseweb="select"] > div { 
        background-color: #3e2723 !important; border: 1px solid #4b3621 !important; color: #ffffff !important;
    }

    /* Botões Elite */
    .stButton>button {
        background-color: #3e2723 !important; color: #ffffff !important;
        border: 1px solid #4b3621 !important; border-radius: 14px !important;
        font-weight: 700 !important; transition: 0.3s ease;
    }
    .stButton>button:hover { background-color: #4b3621 !important; border-color: #ffffff !important; }

    /* Cards e Mensagens */
    .elite-card { background: #0d0d0d; border: 1px solid #3e2723; border-radius: 20px; padding: 25px; margin-bottom: 15px; }
    .instruction-box { background: linear-gradient(145deg, #1a0f0d, #000000); border-left: 5px solid #3e2723; padding: 20px; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- GERADOR DE RELATÓRIO PDF (ESTÉTICA TECHNOBOLT) ---
class TechnoboltPDF(FPDF):
    def header(self):
        self.set_fill_color(62, 39, 35) # Marrom Technobolt (#3e2723)
        self.rect(0, 0, 210, 45, 'F')
        self.set_y(15)
        self.set_font('Helvetica', 'B', 28)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'TECHNOBOLT', ln=True, align='C')
        self.set_font('Helvetica', 'I', 11)
        self.cell(0, 10, 'Health Analytics & Veterinary AI Report', ln=True, align='C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'TechnoBolt Pets Hub - Pagina {self.page_no()}', align='C')

def create_pdf_report(pet_name, especie, modo, sintomas, laudo):
    pdf = TechnoboltPDF()
    pdf.add_page()
    pdf.set_text_color(62, 39, 35)
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, f"PACIENTE: {pet_name.upper()} ({especie.upper()})", ln=True)
    pdf.ln(5)
    
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Modulo: {modo}", ln=True)
    pdf.multi_cell(0, 8, f"Sintomas: {sintomas if sintomas else 'Nenhum sintoma descrito'}")
    pdf.ln(5)
    
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 12, "PARECER TECNICO IA", ln=True, fill=True, align='C')
    pdf.ln(5)
    
    pdf.set_font('Helvetica', '', 11)
    clean_text = laudo.replace('**', '').replace('###', '').replace('*', '-')
    pdf.multi_cell(0, 8, clean_text)
    return pdf.output()

# --- AI CORE ENGINE ---
def call_ia(prompt, img=None):
    chaves = [st.secrets.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    if not chaves: return "Erro: Chaves de API ausentes."
    motores = ["models/gemini-2.0-flash", "models/gemini-3-flash-preview", "models/gemini-flash-latest"]
    genai.configure(api_key=random.choice(chaves))
    for motor in motores:
        try:
            model = genai.GenerativeModel(motor)
            res = model.generate_content([prompt, img] if img else prompt)
            return res.text
        except: continue
    return "IA Offline."

# --- AUTH SYSTEM ---
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center; font-weight:800;'>🐾 TECHNOBOLT PETS</h1>", unsafe_allow_html=True)
    t_in, t_reg = st.tabs(["🔐 Entrar", "📝 Registrar"])
    with t_in:
        u, p = st.text_input("Usuário"), st.text_input("Senha", type="password")
        if st.button("ACESSAR HUB"):
            user = db.usuarios.find_one({"usuario": u, "senha": p})
            if user:
                st.session_state.logado, st.session_state.user_data = True, user
                st.rerun()
    with t_reg:
        n, nu, np = st.text_input("Nome"), st.text_input("User ID").lower(), st.text_input("Pass", type="password")
        addr = st.text_input("Endereço Completo")
        tipo = st.selectbox("Perfil", ["Tutor", "Cuidador"])
        if st.button("SOLICITAR ACESSO"):
            status = "Pendente" if tipo == "Cuidador" else "Ativo"
            db.usuarios.insert_one({"nome": n, "usuario": nu, "senha": np, "endereco": addr, "tipo": tipo, "status": status, "dt": datetime.now()})
            st.success("Conta criada! Cuidadores aguardam aprovação do Admin.")
    st.stop()

# --- MAIN HUB ---
user = st.session_state.user_data

with st.sidebar:
    st.markdown(f"### 👤 {user['nome']}")
    st.caption(f"Perfil: {user['tipo']}")
    st.divider()
    
    cur_pet = None
    if user['tipo'] == "Tutor":
        st.subheader("🐾 Meus Pets")
        pets = list(db.pets.find({"owner_id": user['usuario']}))
        if pets:
            sel_name = st.selectbox("Pet Ativo", [p['nome'] for p in pets])
            cur_pet = next(p for p in pets if p['nome'] == sel_name)
        
        with st.expander("➕ Adicionar Qualquer Animal"):
            p_n = st.text_input("Nome")
            p_e = st.text_input("Espécie (Cão, Gato, Réptil, Ave...)")
            if st.button("Salvar Pet"):
                db.pets.insert_one({"owner_id": user['usuario'], "nome": p_n, "especie": p_e, "dt": datetime.now()})
                st.rerun()
    st.divider()
    if st.button("SAIR"):
        st.session_state.logado = False
        st.rerun()

# ---------------- WORKFLOWS ----------------

# 1. ADMIN
if user['tipo'] == "Admin":
    t_home, t_gov = st.tabs(["🏠 Instruções", "⚙️ Governança"])
    with t_home:
        st.subheader("Bem-vindo ao Painel de Controle Technobolt")
        st.markdown("""
        <div class='instruction-box'>
            <b>Guia do Administrador:</b><br>
            1. <b>Aprovação:</b> Na aba de Governança, você visualiza Cuidadores pendentes.<br>
            2. <b>Ativação:</b> Clique em 'Aprovar' para liberar o acesso total ao sistema para novos parceiros.<br>
            3. <b>Monitoramento:</b> Você tem acesso à base de dados para auditoria de segurança.
        </div>
        """, unsafe_allow_html=True)

    with t_gov:
        pendentes = list(db.usuarios.find({"status": "Pendente"}))
        for p in pendentes:
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{p['nome']}** | {p['tipo']} | {p['endereco']}")
            if c2.button("APROVAR", key=p['usuario']):
                db.usuarios.update_one({"usuario": p['usuario']}, {"$set": {"status": "Ativo"}})
                st.rerun()

# 2. CUIDADOR
elif user['tipo'] == "Cuidador":
    if user.get('status') == "Pendente":
        st.warning("Sua conta está em análise administrativa.")
    else:
        t_home, t_msgs = st.tabs(["🏠 Instruções", "💬 Pedidos"])
        with t_home:
            st.subheader(f"Olá, {user['nome']}! Aqui estão suas diretrizes:")
            st.markdown("""
            <div class='elite-card'>
                <b>Como Funciona o Hub para Cuidadores:</b><br>
                - <b>Visibilidade:</b> Tutores próximos encontrarão seu perfil e endereço.<br>
                - <b>Chat:</b> As solicitações aparecerão na aba 'Pedidos'.<br>
                - <b>Logística:</b> Ao receber uma mensagem, o endereço do tutor será compartilhado com você para facilitar o atendimento.
            </div>
            """, unsafe_allow_html=True)

        with t_msgs:
            msgs = list(db.mensagens.find({"receiver_id": user['usuario']}).sort("dt", -1))
            for m in msgs:
                st.markdown(f"<div class='elite-card'><b>De: {m['sender_id']}</b><br>📍 Tutor em: {m.get('sender_addr', 'N/A')}<p>{m['texto']}</p></div>", unsafe_allow_html=True)

# 3. TUTOR
elif user['tipo'] == "Tutor":
    t_home, t_scan, t_map, t_care, t_chats = st.tabs(["🏠 Instruções", "🧬 PetScan IA", "📍 Clínicas", "🤝 Cuidadores", "💬 Chats"])
    
    with t_home:
        st.subheader(f"Bem-vindo, {user['nome']}! Explore o Hub:")
        st.markdown("""
        <div class='instruction-box'>
            <b>Passo a Passo Technobolt:</b><br>
            1. <b>Cadastre seus Pets:</b> Use o menu lateral para registrar qualquer espécie (aves, répteis, mamíferos).<br>
            2. <b>PetScan IA:</b> Faça upload de fotos para análise corporal ou digestiva contextualizada pela IA PhD.<br>
            3. <b>Contratação:</b> Encontre cuidadores aprovados e envie mensagens. Seu endereço será enviado para facilitar o cálculo de frete/visita.
        </div>
        """, unsafe_allow_html=True)

    with t_scan:
        st.subheader("🧬 Diagnóstico Biométrico Especializado")
        if not cur_pet: st.warning("Adicione um pet na barra lateral.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                modo = st.radio("Foco", ["Condição Corporal (BCS)", "Saúde Digestiva (Fezes)"])
                up = st.file_uploader("Submeter Amostra", type=['jpg', 'png', 'heic'])
            with c2:
                sintomas = st.text_area("Descreva alterações (Opcional)")
            
            if up and st.button("EXECUTAR ANÁLISE PhD"):
                img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
                st.image(img, width=400)
                prompt = f"Veterinário Especialista: Analise este {cur_pet['especie']} ({cur_pet['nome']}). Modo: {modo}. Sintomas: {sintomas if sintomas else 'Nenhum'}. Dê laudo estruturado."
                res = call_ia(prompt, img=img)
                st.markdown(f"<div class='elite-card'><h3>📝 Parecer IA</h3>{res}</div>", unsafe_allow_html=True)
                
                # Botão de Relatório PDF Customizado
                pdf_data = create_pdf_report(cur_pet['nome'], cur_pet['especie'], modo, sintomas, res)
                st.download_button(label="📥 BAIXAR RELATÓRIO PDF (TECHNOBOLT)", data=pdf_data, file_name=f"Laudo_{cur_pet['nome']}.pdf", mime="application/pdf")

                if "BCS" in modo:
                    st.divider()
                    st.markdown("""### 📊 Guia de Referência: Condição Corporal""")
                    st.markdown("""

[Image of a Body Condition Score chart for dogs and cats]
""")
                
                if "Fezes" in modo:
                    st.divider()
                    st.markdown("""### 📊 Guia de Referência: Saúde Digestiva""")
                    st.markdown("""""")

    with t_map:
        st.subheader("📍 Localizador Geográfico")
        search = st.text_input("Buscar estabelecimentos...")
        if search:
            res = call_ia(f"3 locais de {search} próximos a {user['endereco']}. NOME|NOTA|AVAL|PROS|CONTRAS")
            st.write(res)
            st.map(pd.DataFrame({'lat': [-23.55], 'lon': [-46.63]}))

    with t_care:
        st.subheader("🤝 Cuidadores Aprovados")
        cuidadores = list(db.usuarios.find({"tipo": "Cuidador", "status": "Ativo"}))
        for c in cuidadores:
            st.markdown(f"<div class='elite-card'>👤 <b>{c['nome']}</b> (📍 {c['endereco']})</div>", unsafe_allow_html=True)
            txt = st.text_input("Mensagem", key=f"chat_{c['usuario']}")
            if st.button("ENVIAR", key=f"btn_{c['usuario']}"):
                db.mensagens.insert_one({"sender_id": user['usuario'], "sender_addr": user['endereco'], "receiver_id": c['usuario'], "texto": txt, "dt": datetime.now()})
                st.success("Mensagem enviada!")

    with t_chats:
        st.subheader("Histórico")
        msgs = list(db.mensagens.find({"sender_id": user['usuario']}).sort("dt", -1))
        for m in msgs:
            st.markdown(f"<div class='elite-card'><b>Para: {m['receiver_id']}</b><p>{m['texto']}</p></div>", unsafe_allow_html=True)

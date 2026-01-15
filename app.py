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

# --- DATABASE ENGINE (SISTEMA DE SEGREDOS) ---
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
        st.error(f"⚠️ Falha na Camada de Dados: Verifique os Secrets. {e}")
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM: OBSIDIAN, SNOW & DEEP COCOA ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    
    /* Reset Global e Sidebar */
    [data-testid="stSidebar"], .stApp, [data-testid="stHeader"], [data-testid="stSidebarContent"] { 
        background-color: #000000 !important; 
        color: #ffffff !important; 
    }
    
    * { font-family: 'Plus Jakarta Sans', sans-serif; color: #ffffff !important; }

    /* VISIBILIDADE DO MENU SUPERIOR (TABS) */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #000000 !important;
        border-bottom: 2px solid #3e2723 !important;
        gap: 12px !important;
        padding: 10px 0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px !important;
        background-color: #0d0d0d !important;
        border: 1px solid #1a1a1a !important;
        border-radius: 12px 12px 0 0 !important;
        color: #bbbbbb !important;
        padding: 0 30px !important;
        font-weight: 600 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3e2723 !important;
        color: #ffffff !important;
        border-color: #3e2723 !important;
    }

    /* Inputs e Forms Marrom Chocolate */
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
        border-radius: 14px !important;
        font-weight: 700 !important;
        transition: 0.3s ease;
        padding: 0.6rem 1rem;
    }
    .stButton>button:hover { background-color: #4b3621 !important; border-color: #ffffff !important; }

    /* Cards Elite */
    .elite-card {
        background: #0d0d0d;
        border: 1px solid #3e2723;
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# --- GERADOR DE RELATÓRIO PDF TECHNOBOLT ---
class TechnoboltPDF(FPDF):
    def header(self):
        self.set_fill_color(62, 39, 35) # Marrom Technobolt (#3e2723)
        self.rect(0, 0, 210, 45, 'F')
        self.set_y(15)
        self.set_font('Helvetica', 'B', 28)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'TECHNOBOLT', ln=True, align='C')
        self.set_font('Helvetica', 'I', 11)
        self.cell(0, 10, 'Relatório Avançado de Inteligência Veterinária', ln=True, align='C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'TechnoBolt Pets Hub - Página {self.page_no()}', align='C')

def create_report_pdf(pet_data, analysis_type, symptoms, ai_response):
    pdf = TechnoboltPDF()
    pdf.add_page()
    pdf.set_text_color(50, 50, 50)
    
    # Header do Pet
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, f"PET: {pet_data['nome'].upper()} | ESPÉCIE: {pet_data['especie'].upper()}", ln=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 10, f"Data da Análise: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.cell(0, 10, f"Módulo: {analysis_type}", ln=True)
    pdf.ln(5)

    # Conteúdo
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, " PARECER TÉCNICO IA", ln=True, fill=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.ln(3)
    
    if symptoms:
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 7, "Sintomas Relatados:", ln=True)
        pdf.set_font('Helvetica', '', 10)
        pdf.multi_cell(0, 7, symptoms)
        pdf.ln(3)

    pdf.set_font('Helvetica', '', 11)
    clean_text = ai_response.replace('**', '').replace('###', '').replace('*', '-')
    pdf.multi_cell(0, 8, clean_text)
    
    return pdf.output()

# --- AI CORE ENGINE ---
def call_ia(prompt, img=None):
    chaves = [st.secrets.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    if not chaves: return "Erro: API_KEYS ausentes."
    motores = ["models/gemini-2.0-flash", "models/gemini-3-flash-preview", "models/gemini-flash-latest"]
    genai.configure(api_key=random.choice(chaves))
    for motor in motores:
        try:
            model = genai.GenerativeModel(motor)
            res = model.generate_content([prompt, img] if img else prompt)
            return res.text
        except: continue
    return "Serviço de IA Offline."

# --- AUTH SYSTEM ---
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center; font-weight:800;'>🐾 TECHNOBOLT PETS</h1>", unsafe_allow_html=True)
    t_login, t_cad = st.tabs(["🔐 Acesso Hub", "📝 Novo Registro"])
    with t_login:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("AUTENTICAR"):
            user = db.usuarios.find_one({"usuario": u, "senha": p})
            if user:
                st.session_state.logado, st.session_state.user_data = True, user
                st.rerun()
    with t_cad:
        n, nu, np = st.text_input("Nome"), st.text_input("User ID").lower(), st.text_input("Pass Code", type="password")
        addr = st.text_input("Endereço Completo")
        tipo = st.selectbox("Perfil de Acesso", ["Tutor", "Cuidador"])
        if st.button("CRIAR CONTA"):
            status = "Pendente" if tipo == "Cuidador" else "Ativo"
            db.usuarios.insert_one({"nome": n, "usuario": nu, "senha": np, "endereco": addr, "tipo": tipo, "status": status, "dt": datetime.now()})
            st.success("Conta criada! Cuidadores aguardam liberação do Admin.")
    st.stop()

# --- MAIN HUB ---
user_data = st.session_state.user_data

with st.sidebar:
    st.markdown(f"### 👤 {user_data['nome']}")
    st.caption(f"Privilégio: {user_data['tipo']}")
    st.divider()
    
    cur_pet = None
    if user_data['tipo'] == "Tutor":
        st.subheader("🐾 Gestão de Pets")
        pets = list(db.pets.find({"owner_id": user_data['usuario']}))
        if pets:
            sel_pet = st.selectbox("Pet em Foco", [p['nome'] for p in pets])
            cur_pet = next(p for p in pets if p['nome'] == sel_pet)
        
        with st.expander("➕ Novo Animal"):
            p_n = st.text_input("Nome")
            p_e = st.text_input("Espécie (Ex: Cão, Gato, Ave, Iguana...)")
            if st.button("Salvar Perfil Pet"):
                db.pets.insert_one({"owner_id": user_data['usuario'], "nome": p_n, "especie": p_e, "dt": datetime.now()})
                st.rerun()
    st.divider()
    if st.button("LOGOUT"):
        st.session_state.logado = False
        st.rerun()

# ---------------- WORKFLOWS ----------------

if user_data['tipo'] == "Admin":
    st.title("⚙️ Governança Administrativa")
    pendentes = list(db.usuarios.find({"status": "Pendente", "tipo": "Cuidador"}))
    for p in pendentes:
        c1, c2 = st.columns([3, 1])
        c1.write(f"**{p['nome']}** solicita credencial de Cuidador.")
        if c2.button("AUTORIZAR", key=p['usuario']):
            db.usuarios.update_one({"usuario": p['usuario']}, {"$set": {"status": "Ativo"}})
            st.rerun()

elif user_data['tipo'] == "Cuidador":
    if user_data.get('status') == "Pendente":
        st.warning("Seu acesso está em fase de auditoria.")
    else:
        st.title("🐕 Dashboard do Cuidador")
        msgs = list(db.mensagens.find({"receiver_id": user_data['usuario']}).sort("dt", -1))
        for m in msgs:
            st.markdown(f"<div class='elite-card'><b>De: {m['sender_id']}</b><br>Endereço: {m.get('sender_addr', 'N/A')}<p>{m['texto']}</p></div>", unsafe_allow_html=True)

elif user_data['tipo'] == "Tutor":
    # ABAS COM VISIBILIDADE FORÇADA VIA CSS
    t_scan, t_map, t_care, t_chats = st.tabs(["🧬 PetScan IA", "📍 Clínicas & Mapas", "🤝 Cuidadores", "💬 Meus Chats"])

    with t_scan:
        st.subheader("🧬 Diagnóstico Biométrico Universal")
        if not cur_pet:
            st.info("Cadastre um pet no menu lateral para iniciar.")
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                modo = st.radio("Foco do Scan", ["Escore Corporal (BCS)", "Saúde Digestiva (Fezes)"])
                up = st.file_uploader("Submeter Foto", type=['jpg', 'png', 'heic'])
            with col_b:
                sintomas = st.text_area("Observações ou Sintomas (Opcional)")
            
            if up and st.button("INICIAR ANÁLISE PhD"):
                img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
                st.image(img, width=400)
                prompt = f"Veterinário PhD: Analise este {cur_pet['especie']} ({cur_pet['nome']}). Modo: {modo}. Sintomas: {sintomas if sintomas else 'Nenhum'}. Dê laudo estruturado."
                res = call_ia(prompt, img=img)
                
                st.markdown(f"<div class='elite-card'><h3>📝 Laudo de Especialista IA</h3>{res}</div>", unsafe_allow_html=True)
                
                # Relatório PDF Technobolt
                pdf_data = create_report_pdf(cur_pet, modo, sintomas, res)
                st.download_button(
                    label="📥 BAIXAR LAUDO PDF (TECHNOBOLT)",
                    data=pdf_data,
                    file_name=f"Laudo_{cur_pet['nome']}.pdf",
                    mime="application/pdf"
                )

                # CORREÇÃO DEFINITIVA DO SYNTAX ERROR (Strings multilinhas)
                if "BCS" in modo:
                    st.divider()
                    st.markdown("""### 📊 Guia de Referência: Condição Corporal""")
                    st.markdown("")

                if "Fezes" in modo:
                    st.divider()
                    st.markdown("""### 📊 Guia de Referência: Saúde Digestiva""")
                    st.markdown("")

    with t_map:
        st.subheader("📍 Localizador Geográfico")
        search = st.text_input("O que você busca? (Vet, Petshop, Tosa...)")
        if search:
            res = call_ia(f"3 locais de {search} próximos a {user_data['endereco']}. NOME|NOTA|AVAL|PROS|CONTRAS")
            st.write(res)
            st.map(pd.DataFrame({'lat': [-23.55], 'lon': [-46.63]}))

    with t_care:
        st.subheader("🤝 Cuidadores Disponíveis")
        cuidadores = list(db.usuarios.find({"tipo": "Cuidador", "status": "Ativo"}))
        for c in cuidadores:
            st.markdown(f"<div class='elite-card'>👤 <b>{c['nome']}</b> (📍 {c['endereco']})</div>", unsafe_allow_html=True)
            txt = st.text_input("Sua Mensagem", key=f"chat_{c['usuario']}")
            if st.button("ENVIAR PROPOSTA", key=f"btn_{c['usuario']}"):
                db.mensagens.insert_one({"sender_id": user_data['usuario'], "sender_addr": user_data['endereco'], "receiver_id": c['usuario'], "texto": txt, "dt": datetime.now()})
                st.success("Enviado com sucesso!")

    with t_chats:
        st.subheader("Histórico de Conversas")
        msgs = list(db.mensagens.find({"sender_id": user_data['usuario']}).sort("dt", -1))
        for m in msgs:
            st.markdown(f"<div class='elite-card'><b>Para: {m['receiver_id']}</b><p>{m['texto']}</p></div>", unsafe_allow_html=True)

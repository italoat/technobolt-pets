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
from fpdf import FPDF # Nova dependência para o PDF

# --- CONFIGURAÇÃO DE ENGENHARIA SÊNIOR ---
pillow_heif.register_heif_opener()
st.set_page_config(
    page_title="TechnoBolt Pets Hub | Enterprise Edition", 
    layout="wide", 
    page_icon="🐾",
    initial_sidebar_state="expanded"
)

# --- DATABASE ENGINE ---
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
        st.error(f"⚠️ Falha na Camada de Dados: {e}")
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM: OBSIDIAN & CHOCOLATE (CORREÇÃO DE VISIBILIDADE) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    
    /* Global & Sidebar Dark Mode */
    [data-testid="stSidebar"], .stApp, [data-testid="stSidebarContent"] { 
        background-color: #000000 !important; 
        color: #ffffff !important; 
    }
    
    * { font-family: 'Plus Jakarta Sans', sans-serif; color: #ffffff !important; }

    /* CORREÇÃO DO MENU SUPERIOR (TABS) */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #000000 !important;
        border-bottom: 2px solid #3e2723 !important;
        gap: 10px;
        padding: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #0d0d0d !important;
        border: 1px solid #1a1a1a !important;
        border-radius: 10px 10px 0 0;
        color: #888888 !important;
        padding: 10px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3e2723 !important;
        color: #ffffff !important;
        border-color: #3e2723 !important;
    }

    /* Forms e Inputs */
    input, textarea, [data-baseweb="select"] > div { 
        background-color: #3e2723 !important; border: 1px solid #4b3621 !important; color: #ffffff !important;
    }
    .stButton>button {
        background-color: #3e2723 !important; border: 1px solid #4b3621 !important;
        border-radius: 12px !important; font-weight: 700 !important;
        width: 100%;
    }
    .stButton>button:hover { background-color: #4b3621 !important; border-color: #ffffff !important; }

    /* Cards Elite */
    .elite-card { background: #0d0d0d; border: 1px solid #3e2723; border-radius: 20px; padding: 20px; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# --- GERADOR DE RELATÓRIO PDF (VISUAL INCRÍVEL) ---
class PetReport(FPDF):
    def header(self):
        self.set_fill_color(62, 39, 35) # Marrom Technobolt
        self.rect(0, 0, 210, 40, 'F')
        self.set_font('Helvetica', 'B', 24)
        self.set_text_color(255, 255, 255)
        self.cell(0, 20, 'TECHNOBOLT', ln=True, align='C')
        self.set_font('Helvetica', 'I', 12)
        self.cell(0, 10, 'Laudo de Inteligencia Veterinaria Digital', ln=True, align='C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Pagina {self.page_no()} | Gerado em {datetime.now().strftime("%d/%m/%Y")}', align='C')

def gerar_pdf(pet_nome, especie, modo, sintomas, laudo):
    pdf = PetReport()
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(62, 39, 35)
    pdf.cell(0, 10, f"Paciente: {pet_nome} ({especie})", ln=True)
    pdf.ln(5)
    
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Tipo de Analise: {modo}", ln=True)
    pdf.multi_cell(0, 10, f"Sintomas Observados: {sintomas if sintomas else 'Nenhum descrito'}")
    pdf.ln(5)
    
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 12, "RESULTADO DO SCAN IA", ln=True, fill=True, align='C')
    pdf.ln(5)
    pdf.set_font('Helvetica', '', 11)
    pdf.multi_cell(0, 8, laudo.replace('**', '').replace('#', '')) # Limpa markdown simples
    
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
    st.markdown("<h1 style='text-align: center;'>🐾 TECHNOBOLT PETS</h1>", unsafe_allow_html=True)
    t_in, t_reg = st.tabs(["🔐 Acesso", "📝 Registro"])
    with t_in:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
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
            st.success("Conta criada!")
    st.stop()

# --- INTERFACE PRINCIPAL ---
user_data = st.session_state.user_data

with st.sidebar:
    st.markdown(f"### 👤 {user_data['nome']}")
    st.divider()
    cur_pet = None
    if user_data['tipo'] == "Tutor":
        st.subheader("🐾 Meus Animais")
        pets = list(db.pets.find({"owner_id": user_data['usuario']}))
        if pets:
            sel_pet = st.selectbox("Pet em Análise", [p['nome'] for p in pets])
            cur_pet = next(p for p in pets if p['nome'] == sel_pet)
        
        with st.expander("➕ Adicionar Pet"):
            p_n = st.text_input("Nome do Animal")
            p_e = st.text_input("Espécie (Cão, Gato, Ave, etc)")
            if st.button("Salvar Perfil"):
                db.pets.insert_one({"owner_id": user_data['usuario'], "nome": p_n, "especie": p_e, "dt": datetime.now()})
                st.rerun()
    st.divider()
    if st.button("SAIR DO SISTEMA"):
        st.session_state.logado = False
        st.rerun()

# ---------------- WORKFLOWS ----------------

if user_data['tipo'] == "Admin":
    st.title("⚙️ Governança")
    pendentes = list(db.usuarios.find({"status": "Pendente", "tipo": "Cuidador"}))
    for p in pendentes:
        c1, c2 = st.columns([3, 1])
        c1.write(f"**{p['nome']}** solicita acesso.")
        if c2.button("APROVAR", key=p['usuario']):
            db.usuarios.update_one({"usuario": p['usuario']}, {"$set": {"status": "Ativo"}})
            st.rerun()

elif user_data['tipo'] == "Cuidador":
    if user_data.get('status') == "Pendente":
        st.warning("Aguardando aprovação.")
    else:
        st.title("🐕 Painel do Cuidador")
        msgs = list(db.mensagens.find({"receiver_id": user_data['usuario']}).sort("dt", -1))
        for m in msgs:
            st.markdown(f"<div class='elite-card'><b>De: {m['sender_id']}</b><br>Endereço: {m.get('sender_addr', 'N/A')}<p>{m['texto']}</p></div>", unsafe_allow_html=True)

elif user_data['tipo'] == "Tutor":
    t_scan, t_map, t_care, t_chats = st.tabs(["🧬 PetScan IA", "📍 Clínicas & Mapas", "🤝 Cuidadores", "💬 Chats"])

    with t_scan:
        st.subheader("🧬 Diagnóstico Biométrico Universal")
        if not cur_pet:
            st.warning("Registre um pet no menu lateral.")
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                modo = st.radio("Foco", ["Condição Corporal (BCS)", "Saúde Digestiva (Fezes)"])
                up = st.file_uploader("Submeter Foto", type=['jpg', 'png', 'heic'])
            with col_b:
                sintomas = st.text_area("Sintomas observados (Opcional)")
            
            if up and st.button("INICIAR ANÁLISE ESPECIALIZADA"):
                img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
                st.image(img, width=400)
                prompt = f"Veterinário PhD: Analise este {cur_pet['especie']} ({cur_pet['nome']}). Modo: {modo}. Sintomas: {sintomas if sintomas else 'Nenhum'}. Dê laudo estruturado."
                res = call_ia(prompt, img=img)
                st.session_state['ultimo_laudo'] = res
                st.markdown(f"<div class='elite-card'>{res}</div>", unsafe_allow_html=True)
                
                # Botão para Download do PDF
                pdf_bytes = gerar_pdf(cur_pet['nome'], cur_pet['especie'], modo, sintomas, res)
                st.download_button(
                    label="📥 BAIXAR RELATÓRIO PDF (TECHNOBOLT)",
                    data=pdf_bytes,
                    file_name=f"Laudo_{cur_pet['nome']}_{datetime.now().strftime('%d%m%Y')}.pdf",
                    mime="application/pdf"
                )

                if "BCS" in modo:
                    st.divider()
                    st.markdown("### 📊 Guia de Referência: Condição Corporal")
                    

[Image of a Body Condition Score chart for dogs and cats]


                if "Fezes" in modo:
                    st.divider()
                    st.markdown("### 📊 Guia de Referência: Saúde Digestiva")
                    

    with t_map:
        st.subheader("📍 Localizador")
        search = st.text_input("Buscar estabelecimentos...")
        if search:
            res = call_ia(f"3 locais de {search} em {user_data['endereco']}. NOME|NOTA|AVAL|PROS|CONTRAS")
            st.write(res)
            st.map(pd.DataFrame({'lat': [-23.55], 'lon': [-46.63]}))

    with t_care:
        st.subheader("🤝 Cuidadores")
        cuidadores = list(db.usuarios.find({"tipo": "Cuidador", "status": "Ativo"}))
        for c in cuidadores:
            st.markdown(f"<div class='elite-card'>👤 <b>{c['nome']}</b> (📍 {c['endereco']})</div>", unsafe_allow_html=True)
            txt = st.text_input("Mensagem", key=f"chat_{c['usuario']}")
            if st.button("ENVIAR", key=f"btn_{c['usuario']}"):
                db.mensagens.insert_one({"sender_id": user_data['usuario'], "sender_addr": user_data['endereco'], "receiver_id": c['usuario'], "texto": txt, "dt": datetime.now()})
                st.success("Enviado!")

    with t_chats:
        st.subheader("Histórico")
        msgs = list(db.mensagens.find({"sender_id": user_data['usuario']}).sort("dt", -1))
        for m in msgs:
            st.markdown(f"<div class='elite-card'><b>Para: {m['receiver_id']}</b><p>{m['texto']}</p></div>", unsafe_allow_html=True)

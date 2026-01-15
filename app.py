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

# --- SETUP DE ENGENHARIA SÊNIOR ---
try:
    pillow_heif.register_heif_opener()
except:
    pass

st.set_page_config(
    page_title="TechnoBolt Pets Hub | Master Enterprise", 
    layout="wide", 
    page_icon="🐾",
    initial_sidebar_state="expanded"
)

# --- DATABASE ENGINE ---
@st.cache_resource
def iniciar_conexao():
    try:
        if "MONGO_USER" not in st.secrets:
            st.error("⚠️ Secrets do MongoDB não configuradas no .streamlit/secrets.toml")
            return None
            
        user = st.secrets["MONGO_USER"]
        pass_raw = st.secrets["MONGO_PASS"]
        host = st.secrets["MONGO_HOST"]
        password = urllib.parse.quote_plus(pass_raw)
        
        uri = f"mongodb+srv://{user}:{password}@{host}/?appName=Cluster0"
        client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
        
        client.admin.command('ping')
        return client['technoboltpets']
    except Exception as e:
        st.error(f"⚠️ Erro de Database: {e}")
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM: OBSIDIAN & DEEP COCOA ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    
    [data-testid="stSidebar"], .stApp, [data-testid="stHeader"], [data-testid="stSidebarContent"], .main { 
        background-color: #000000 !important; color: #ffffff !important; 
    }
    * { font-family: 'Plus Jakarta Sans', sans-serif; color: #ffffff !important; }

    /* MENU SUPERIOR (TABS) */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #000000 !important;
        border-bottom: 2px solid #3e2723 !important;
        gap: 15px !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px !important; background-color: #0d0d0d !important;
        border-radius: 12px 12px 0 0 !important; color: #bbbbbb !important;
        border: 1px solid #1a1a1a !important; padding: 0 30px !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3e2723 !important; color: #ffffff !important; border-color: #3e2723 !important;
    }

    /* --- CORREÇÃO: LABELS E TEXTOS FLUTUANTES (TRANSPARENTES) --- */
    label, [data-testid="stLabel"], .stMarkdown p {
        background-color: transparent !important;
        color: #ffffff !important;
    }

    /* --- AJUSTE: FORMS E CONTAINERS --- */
    div[data-testid="stForm"], .stForm {
        background-color: #1e110f !important; /* Marrom escuro profundo */
        border: 1px solid #4e342e !important;
        padding: 20px !important;
        border-radius: 15px !important;
    }

    /* --- CORREÇÃO: EXPANDER (CONVERSA COM...) --- */
    [data-testid="stExpander"] {
        background-color: #1e110f !important;
        border: 1px solid #4e342e !important;
        border-radius: 15px !important;
        color: #ffffff !important;
    }
    [data-testid="stExpander"] summary {
        color: #ffffff !important;
        background-color: #1e110f !important; /* Remove fundo branco do header */
    }
    [data-testid="stExpander"] summary:hover {
        background-color: #3e2723 !important;
        color: #ffffff !important;
    }
    [data-testid="stExpander"] div[role="button"] p {
        color: #ffffff !important;
    }
    
    /* --- AJUSTE: INPUTS ESPECÍFICOS (Apenas a caixa digitável fica marrom) --- */
    input, textarea, .stNumberInput input { 
        background-color: #3e2723 !important; /* Marrom Cocoa */
        color: #ffffff !important;
        border-radius: 5px !important;
    }
    
    /* Borda dos inputs */
    div[data-baseweb="input"], div[data-baseweb="base-input"] {
        background-color: #3e2723 !important;
        border: 1px solid #5d4037 !important; 
        border-radius: 5px !important;
    }

    /* --- AJUSTE: DROPDOWN (SELECTBOX) --- */
    div[data-baseweb="select"] > div {
        background-color: #3e2723 !important;
        border: 1px solid #5d4037 !important;
        color: #ffffff !important;
    }
    
    /* Lista Suspensa (Popover e Virtual Dropdown) */
    div[data-baseweb="popover"], div[role="listbox"], ul[data-testid="stSelectboxVirtualDropdown"] {
        background-color: #2b1d16 !important; /* Marrom Coffee */
        color: #ffffff !important;
        border: 1px solid #4e342e !important;
    }
    div[role="option"], li[role="option"] { 
        color: #ffffff !important; 
        background-color: transparent !important; 
    }
    div[role="option"]:hover, li[role="option"]:hover { 
        background-color: #4e342e !important; 
    }

    /* --- CORREÇÃO FINAL: CALENDÁRIO (DATE INPUT) --- */
    /* Container principal do popover do calendário */
    div[data-baseweb="popover"] > div {
        background-color: #2b1d16 !important;
    }

    /* O Calendário em si */
    div[data-baseweb="calendar"] {
        background-color: #2b1d16 !important;
        color: #ffffff !important;
    }
    
    /* Cabeçalho do calendário (Mês/Ano e Setas) */
    div[data-baseweb="calendar"] div[role="button"],
    div[data-baseweb="calendar"] div[aria-label] {
        color: #ffffff !important;
    }
    
    /* Botões dos dias (Grade) - Remove fundo branco padrão */
    div[data-baseweb="calendar"] button {
        background-color: transparent !important;
        color: #ffffff !important;
    }
    
    /* Hover no dia */
    div[data-baseweb="calendar"] button:hover {
        background-color: #3e2723 !important;
    }
    
    /* Dia Selecionado */
    div[data-baseweb="calendar"] button[aria-selected="true"] {
        background-color: #4e342e !important;
        border: 1px solid #ffffff !important;
        color: #ffffff !important;
    }
    
    /* Ícones SVG (Setas esquerda/direita) */
    div[data-baseweb="calendar"] svg {
        fill: #ffffff !important;
        color: #ffffff !important;
    }

    /* --- CORREÇÃO: FILE UPLOADER --- */
    [data-testid="stFileUploader"] {
        padding: 10px;
    }
    [data-testid="stFileUploaderDropzone"] {
        background-color: #1e110f !important;
        border: 1px dashed #4e342e !important;
    }
    [data-testid="stFileUploaderDropzone"] div {
        color: #bbbbbb !important;
        background-color: transparent !important;
    }
    [data-testid="stFileUploaderDropzone"] small {
        color: #888888 !important;
    }
    
    /* BOTÃO "BROWSE FILES" */
    [data-testid="stFileUploader"] button {
        background-color: #3e2723 !important; 
        color: #ffffff !important;
        border: 1px solid #5d4037 !important;
    }
    [data-testid="stFileUploader"] button:hover {
        background-color: #4b3621 !important;
        border-color: #ffffff !important;
    }

    /* BOTÕES GERAIS E ESPECÍFICOS */
    .stButton > button, 
    .stDownloadButton > button,
    [data-testid="stFormSubmitButton"] > button,
    button[kind="primary"], 
    button[kind="secondary"] {
        background-color: #3e2723 !important; 
        color: #ffffff !important;
        border: 1px solid #4b3621 !important; 
        border-radius: 14px !important;
        font-weight: 700 !important; 
        transition: 0.3s ease;
        width: 100% !important;
    }
    
    .stButton > button:hover, 
    .stDownloadButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover { 
        background-color: #4b3621 !important; 
        border-color: #ffffff !important; 
        color: white !important; 
    }

    /* CARDS E CHAT */
    .elite-card { background: #0d0d0d; border: 1px solid #3e2723; border-radius: 20px; padding: 25px; margin-bottom: 15px; }
    .instruction-box { background: linear-gradient(145deg, #1a0f0d, #000000); border-left: 5px solid #3e2723; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
    .bubble { padding: 12px; border-radius: 15px; max-width: 80%; line-height: 1.4; margin-bottom: 5px; }
    .sent { background-color: #3e2723; align-self: flex-end; color: white; margin-left: auto; }
    .received { background-color: #1a1a1a; align-self: flex-start; color: #bbbbbb; margin-right: auto; }
</style>
""", unsafe_allow_html=True)

# --- PDF ENGINE ---
class TechnoboltPDF(FPDF):
    def header(self):
        self.set_fill_color(62, 39, 35) 
        self.rect(0, 0, 210, 45, 'F')
        self.set_y(15)
        self.set_font('Helvetica', 'B', 28)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'TECHNOBOLT', ln=True, align='C')
        self.set_font('Helvetica', 'I', 11)
        self.cell(0, 10, 'Health Analytics & Veterinary AI Report', ln=True, align='C')
        self.ln(20)

def sanitize_pdf_text(text):
    if not text: return ""
    return text.encode('latin-1', 'replace').decode('latin-1').replace('?', '')

def create_pdf_report(pet_name, especie, modo, sintomas, laudo):
    pdf = TechnoboltPDF()
    pdf.add_page()
    pdf.set_text_color(62, 39, 35)
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, sanitize_pdf_text(f"PACIENTE: {pet_name.upper()} ({especie.upper()})"), ln=True)
    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, sanitize_pdf_text(f"Modulo: {modo}"), ln=True)
    pdf.multi_cell(0, 8, sanitize_pdf_text(f"Sintomas: {sintomas if sintomas else 'Nenhum descrito'}"))
    pdf.ln(5)
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 12, "PARECER TECNICO IA", ln=True, fill=True, align='C')
    pdf.ln(5)
    pdf.set_font('Helvetica', '', 11)
    clean_text = laudo.replace('**', '').replace('###', '').replace('*', '-')
    pdf.multi_cell(0, 8, sanitize_pdf_text(clean_text))
    return bytes(pdf.output(dest='S'))

# --- AI CORE ENGINE (CORRIGIDO) ---
def call_ia(prompt, img=None):
    chaves = [st.secrets.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8) if st.secrets.get(f"GEMINI_CHAVE_{i}")]
    if not chaves: 
        return "Erro: Chaves de API (GEMINI_CHAVE_X) não encontradas no secrets."
    
    genai.configure(api_key=random.choice(chaves))
    motores = [
        "models/gemini-3-flash-preview", 
        "models/gemini-2.5-flash", 
        "models/gemini-2.0-flash", 
        "models/gemini-flash-latest"
    ]
    
    # Configuração de segurança para permitir análise veterinária
    safe_config = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
    ]
    
    last_error = None

    for motor in motores:
        try:
            model = genai.GenerativeModel(motor)
            res = model.generate_content([prompt, img] if img else prompt, safety_settings=safe_config)
            return res.text
        except Exception as e: 
            last_error = e
            continue
    
    return f"IA Offline ou sobrecarregada. Detalhe do erro: {last_error}"

# --- AUTH SYSTEM ---
if "logado" not in st.session_state: st.session_state.logado = False
if "user_data" not in st.session_state: st.session_state.user_data = None

if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center; font-weight:800;'>🐾 TECHNOBOLT PETS</h1>", unsafe_allow_html=True)
    t_in, t_reg = st.tabs(["🔐 Entrar", "📝 Registrar"])
    
    with t_in:
        u, p = st.text_input("Usuário"), st.text_input("Senha", type="password")
        if st.button("ACESSAR HUB"):
            if db is not None:
                user = db.usuarios.find_one({"usuario": u, "senha": p})
                if user:
                    st.session_state.logado = True
                    st.session_state.user_data = user
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
            else:
                st.error("Sem conexão com o banco de dados.")

    with t_reg:
        n, nu, np = st.text_input("Nome Completo"), st.text_input("User ID").lower(), st.text_input("Password", type="password")
        tipo = st.selectbox("Perfil", ["Tutor", "Cuidador", "Admin"])
        if st.button("SOLICITAR ACESSO"):
            if db is not None:
                if db.usuarios.find_one({"usuario": nu}):
                    st.warning("Usuário já existe.")
                else:
                    db.usuarios.insert_one({
                        "nome": n, "usuario": nu, "senha": np, "tipo": tipo, 
                        "status": "Ativo", "rating": 5.0, "rating_count": 0, "valores": 0
                    })
                    st.success("Conta criada! Faça login.")
            else:
                st.error("Erro de conexão DB.")
    st.stop()

user_data = st.session_state.user_data

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"### 👤 {user_data['nome']}")
    st.caption(f"Perfil: {user_data['tipo']}")
    
    if st.button("ENCERRAR SESSÃO"):
        st.session_state.logado = False
        st.session_state.user_data = None
        st.rerun()
        
    st.divider()
    cur_pet = None
    if user_data['tipo'] == "Tutor" and db is not None:
        pets = list(db.pets.find({"owner_id": user_data['usuario']}))
        if pets:
            sel_name = st.selectbox("Pet em Foco", [p['nome'] for p in pets])
            cur_pet = next((p for p in pets if p['nome'] == sel_name), None)
        
        with st.expander("➕ Adicionar Pet"):
            p_n, p_e = st.text_input("Nome"), st.text_input("Espécie")
            if st.button("Salvar Pet"):
                db.pets.insert_one({"owner_id": user_data['usuario'], "nome": p_n, "especie": p_e})
                st.rerun()

# ---------------- WORKFLOWS ----------------

# 1. ADMIN MASTER
if user_data['tipo'] == "Admin":
    t_inst, t_audit, t_control = st.tabs(["🏠 Instruções", "💬 Auditoria de Chats", "⚙️ Controles Master"])
    
    with t_inst:
        st.markdown("""<div class='instruction-box'><b>Governança Admin Technobolt:</b><br>
        1. <b>Instruções:</b> Guia de uso.<br>
        2. <b>Auditoria:</b> Logs de todas as mensagens trocadas.<br>
        3. <b>Controles:</b> Edição direta da base de usuários.</div>""", unsafe_allow_html=True)

    with t_audit:
        st.subheader("Auditoria de Mensagens")
        logs = list(db.mensagens.find().sort("dt", -1)) if db is not None else []
        if logs: st.dataframe(pd.DataFrame(logs).astype(str), use_container_width=True)
        else: st.info("Sem logs disponíveis.")

    with t_control:
        usuarios = list(db.usuarios.find()) if db is not None else []
        if usuarios:
            df_users = pd.DataFrame(usuarios)
            df_users['_id'] = df_users['_id'].astype(str)
            new_df = st.data_editor(df_users, use_container_width=True)

# 2. CUIDADOR MASTER
elif user_data['tipo'] == "Cuidador":
    t_home, t_edit, t_agend, t_chat = st.tabs(["🏠 Instruções", "👤 Perfil", "📅 Agendamentos", "💬 Mensagens"])
    
    with t_home:
        st.info("Bem-vindo ao painel do Cuidador. Gerencie sua agenda e perfil aqui.")

    with t_edit:
        with st.form("perfil_form"):
            n_n = st.text_input("Nome", value=user_data['nome'])
            n_a = st.text_input("Endereço", value=user_data.get('endereco', ''))
            n_v = st.number_input("Valor Diária", value=float(user_data.get('valores', 0)))
            if st.form_submit_button("ATUALIZAR"):
                db.usuarios.update_one({"usuario": user_data['usuario']}, {"$set": {"nome": n_n, "endereco": n_a, "valores": n_v}})
                st.session_state.user_data['nome'] = n_n
                st.session_state.user_data['endereco'] = n_a
                st.session_state.user_data['valores'] = n_v
                st.rerun()

    with t_agend:
        pedidos = list(db.agendamentos.find({"cuidador_id": user_data['usuario'], "status": "Pendente"})) if db is not None else []
        if not pedidos: st.write("Nenhum pedido pendente.")
        for p in pedidos:
            st.write(f"📅 Pedido de {p['tutor_id']} para {p['data']}")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ APROVAR", key=f"ap_{p['_id']}"):
                    db.agendamentos.update_one({"_id": p['_id']}, {"$set": {"status": "Aprovado"}})
                    st.rerun()
            with c2:
                if st.button("❌ REPROVAR", key=f"rep_{p['_id']}"):
                    db.agendamentos.update_one({"_id": p['_id']}, {"$set": {"status": "Reprovado"}})
                    st.rerun()

    with t_chat:
        chats = db.mensagens.distinct("sender_id", {"receiver_id": user_data['usuario']}) if db is not None else []
        for tid in chats:
            with st.expander(f"Conversa com {tid}"):
                msgs = list(db.mensagens.find({"$or": [{"sender_id": user_data['usuario'], "receiver_id": tid}, {"sender_id": tid, "receiver_id": user_data['usuario']}]}).sort("dt", 1))
                for m in msgs:
                    cl = "sent" if m['sender_id'] == user_data['usuario'] else "received"
                    st.markdown(f"<div class='bubble {cl}'>{m['texto']}</div>", unsafe_allow_html=True)
                
                resp = st.text_input("Responder", key=f"res_{tid}")
                if st.button("Enviar", key=f"btn_{tid}"):
                    db.mensagens.insert_one({"sender_id": user_data['usuario'], "receiver_id": tid, "texto": resp, "dt": datetime.now()})
                    st.rerun()

# 3. TUTOR MASTER
elif user_data['tipo'] == "Tutor":
    t_home, t_scan, t_cuid, t_chat = st.tabs(["🏠 Instruções", "🧬 PetScan IA", "🤝 Cuidadores", "💬 Chats"])
    
    with t_home:
        st.markdown("""
        ### Bem-vindo ao TechnoBolt Pets
        - **PetScan IA:** Envie uma foto do seu pet para análise clínica preliminar.
        - **Cuidadores:** Encontre profissionais e agende visitas.
        """)

    with t_scan:
        st.subheader("🧬 Diagnóstico Biométrico Universal")
        up = st.file_uploader("Amostra (Foto do Pet)", type=['jpg', 'png', 'heic'])
        
        if up and st.button("EXECUTAR SCAN"):
            try:
                img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
                st.image(img, width=400)
                
                with st.spinner("IA processando biometria..."):
                    res = call_ia("Analise este animal: Escore corporal visual e sinais visíveis de saúde.", img=img)
                
                st.markdown(f"<div class='elite-card'>{res}</div>", unsafe_allow_html=True)
                
                pdf_bytes = create_pdf_report(
                    cur_pet['nome'] if cur_pet else "Pet", 
                    cur_pet['especie'] if cur_pet else "Geral", 
                    "Scan IA", 
                    "Análise Visual", 
                    res
                )
                st.download_button("📥 BAIXAR PDF TECHNOBOLT", data=pdf_bytes, file_name="laudo_technobolt.pdf", mime="application/pdf")
                
            except Exception as e:
                st.error(f"Erro ao processar imagem: {e}")

        st.divider()
        st.markdown("### 📊 Guia de Referência Clínica")
        
        st.markdown("""
        > **Nota:** O Escore de Condição Corporal (ECC) varia de 1 a 9.
        > - **1-3:** Abaixo do peso
        > - **4-5:** Ideal
        > - **6-9:** Acima do peso
        
        *[Referência Visual: Consulte seu veterinário para exames presenciais]*
        """)
        # Diagrama para contexto clínico
        st.markdown("""
        

[Image of body condition score chart for dogs and cats]

        """)

    with t_cuid:
        cuidadores = list(db.usuarios.find({"tipo": "Cuidador"})) if db is not None else []
        for c in cuidadores:
            with st.container():
                st.markdown(f"<div class='elite-card'><h3>{c['nome']}</h3><p>📍 {c.get('endereco', 'Não informado')} | R$ {c.get('valores', 0)}/dia</p></div>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    with st.expander("💬 Chat"):
                        txt = st.text_area("Mensagem", key=f"t_{c['usuario']}")
                        if st.button("Enviar", key=f"s_{c['usuario']}"):
                            db.mensagens.insert_one({"sender_id": user_data['usuario'], "receiver_id": c['usuario'], "texto": txt, "dt": datetime.now()})
                            st.success("Enviado!")
                with c2:
                    with st.expander("📅 Agendar"):
                        da = st.date_input("Data", key=f"d_{c['usuario']}")
                        if st.button("Solicitar", key=f"r_{c['usuario']}"):
                            db.agendamentos.insert_one({"tutor_id": user_data['usuario'], "cuidador_id": c['usuario'], "data": str(da), "status": "Pendente"})
                            st.success("Solicitado!")

    with t_chat:
        chats = db.mensagens.distinct("receiver_id", {"sender_id": user_data['usuario']}) if db is not None else []
        for cid in chats:
            with st.expander(f"Conversa com {cid}"):
                msgs = list(db.mensagens.find({"$or": [{"sender_id": user_data['usuario'], "receiver_id": cid}, {"sender_id": cid, "receiver_id": user_data['usuario']}]}).sort("dt", 1))
                for m in msgs:
                    cl = "sent" if m['sender_id'] == user_data['usuario'] else "received"
                    st.markdown(f"<div class='bubble {cl}'>{m['texto']}</div>", unsafe_allow_html=True)
                
                r_t = st.text_input("Mensagem", key=f"t_res_{cid}")
                if st.button("Enviar", key=f"t_btn_{cid}"):
                    db.mensagens.insert_one({"sender_id": user_data['usuario'], "receiver_id": cid, "texto": r_t, "dt": datetime.now()})
                    st.rerun()

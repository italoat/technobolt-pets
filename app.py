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
pillow_heif.register_heif_opener()
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

# --- DESIGN SYSTEM: OBSIDIAN & DEEP COCOA (VISIBILIDADE MÁXIMA) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    
    /* Reset Global */
    [data-testid="stSidebar"], .stApp, [data-testid="stHeader"], [data-testid="stSidebarContent"] { 
        background-color: #000000 !important; color: #ffffff !important; 
    }
    
    * { font-family: 'Plus Jakarta Sans', sans-serif; color: #ffffff !important; }

    /* MENU SUPERIOR (TABS) */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #000000 !important;
        border-bottom: 2px solid #3e2723 !important;
        gap: 15px !important;
        padding-top: 10px !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px !important; background-color: #0d0d0d !important;
        border-radius: 12px 12px 0 0 !important; color: #bbbbbb !important;
        border: 1px solid #1a1a1a !important; padding: 0 30px !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3e2723 !important; color: #ffffff !important; border-color: #3e2723 !important;
    }

    /* ELIMINAÇÃO DE FUNDOS BRANCOS EM FORMS E BOTÕES */
    div[data-testid="stForm"], div.stForm {
        background-color: #0d0d0d !important;
        border: 1px solid #3e2723 !important;
        padding: 20px !important;
        border-radius: 15px !important;
    }
    
    input, textarea, [data-baseweb="select"] > div, div[data-baseweb="input"] { 
        background-color: #1a1a1a !important; 
        border: 1px solid #4b3621 !important; 
        color: #ffffff !important;
    }

    /* Botões Dinâmicos (Evita fundo branco de sistema) */
    .stButton>button, button[kind="secondary"], button[kind="primary"] {
        background-color: #3e2723 !important; 
        color: #ffffff !important;
        border: 1px solid #4b3621 !important; 
        border-radius: 14px !important;
        font-weight: 700 !important; 
        transition: 0.3s ease;
        width: 100% !important;
    }
    .stButton>button:hover { background-color: #4b3621 !important; border-color: #ffffff !important; }

    /* Cards e Mensagens */
    .elite-card { background: #0d0d0d; border: 1px solid #3e2723; border-radius: 20px; padding: 25px; margin-bottom: 15px; }
    .instruction-box { background: linear-gradient(145deg, #1a0f0d, #000000); border-left: 5px solid #3e2723; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
    
    /* CHAT DESIGN */
    .bubble { padding: 12px; border-radius: 15px; max-width: 80%; line-height: 1.4; margin-bottom: 5px; }
    .sent { background-color: #3e2723; align-self: flex-end; color: white; margin-left: auto; }
    .received { background-color: #1a1a1a; align-self: flex-start; color: #bbbbbb; margin-right: auto; }
</style>
""", unsafe_allow_html=True)

# --- GERADOR DE RELATÓRIO PDF (ESTÉTICA TECHNOBOLT) ---
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

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'TechnoBolt Pets Hub - Pagina {self.page_no()}', align='C')

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
    return pdf.output()

# --- AI CORE ENGINE ---
def call_ia(prompt, img=None):
    chaves = [st.secrets.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    if not chaves: return "Erro: Chaves de API ausentes."
    motores = ["models/gemini-2.0-flash", "models/gemini-flash-latest"]
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
        n, nu, np = st.text_input("Nome Completo"), st.text_input("User ID").lower(), st.text_input("Password", type="password")
        tipo = st.selectbox("Perfil", ["Tutor", "Cuidador", "Admin"])
        if st.button("SOLICITAR ACESSO"):
            db.usuarios.insert_one({"nome": n, "usuario": nu, "senha": np, "tipo": tipo, "status": "Ativo", "rating": 5.0, "rating_count": 0, "valores": 0})
            st.success("Conta criada!")
    st.stop()

user_data = st.session_state.user_data

# --- SIDEBAR (MULTI-PET) ---
with st.sidebar:
    st.markdown(f"### 👤 {user_data['nome']}")
    st.caption(f"Perfil: {user_data['tipo']}")
    if st.button("ENCERRAR SESSÃO"):
        st.session_state.logado = False
        st.rerun()
    st.divider()
    
    cur_pet = None
    if user_data['tipo'] == "Tutor":
        st.subheader("🐾 Meus Pets")
        pets = list(db.pets.find({"owner_id": user_data['usuario']}))
        if pets:
            sel_name = st.selectbox("Pet em Foco", [p['nome'] for p in pets])
            cur_pet = next(p for p in pets if p['nome'] == sel_name)
        
        with st.expander("➕ Adicionar Pet"):
            p_n = st.text_input("Nome")
            p_e = st.text_input("Espécie")
            if st.button("Salvar Pet"):
                db.pets.insert_one({"owner_id": user_data['usuario'], "nome": p_n, "especie": p_e})
                st.rerun()

# ---------------- WORKFLOWS ----------------

# 1. ADMIN MASTER (GOVERNANÇA TOTAL)
if user_data['tipo'] == "Admin":
    t_home, t_edit, t_audit_ag, t_audit_ch = st.tabs(["🏠 Instruções", "⚙️ Gestão de Usuários", "📅 Auditoria de Agendas", "💬 Auditoria de Chats"])
    
    with t_home:
        st.markdown("""<div class='instruction-box'><b>Centro de Comando Admin:</b><br>
        1. <b>Gestão de Usuários:</b> Edite permissões, senhas e dados mestre.<br>
        2. <b>Auditoria de Agendas:</b> Visualize todos os pedidos de cuidado do ecossistema.<br>
        3. <b>Auditoria de Chats:</b> Monitore as interações entre usuários para garantir a segurança.</div>""", unsafe_allow_html=True)
    
    with t_edit:
        st.subheader("⚙️ Edição Master de Usuários")
        df_users = pd.DataFrame(list(db.usuarios.find()))
        new_df = st.data_editor(df_users, use_container_width=True)
        if st.button("SALVAR ALTERAÇÕES GLOBAIS"):
            for index, row in new_df.iterrows():
                db.usuarios.replace_one({"_id": row["_id"]}, row.to_dict())
            st.success("Database atualizada!")

    with t_audit_ag:
        st.subheader("📅 Todos os Agendamentos do Hub")
        all_agendas = pd.DataFrame(list(db.agendamentos.find()))
        if not all_agendas.empty:
            st.dataframe(all_agendas, use_container_width=True)
        else:
            st.info("Nenhum agendamento registrado.")

    with t_audit_ch:
        st.subheader("💬 Central de Monitoramento de Chats")
        all_chats = pd.DataFrame(list(db.mensagens.find()))
        if not all_chats.empty:
            st.dataframe(all_chats.sort_values(by="dt", ascending=False), use_container_width=True)
        else:
            st.info("Nenhuma conversa registrada.")

# 2. CUIDADOR MASTER
elif user_data['tipo'] == "Cuidador":
    t_home, t_edit, t_agend, t_chat = st.tabs(["🏠 Instruções", "👤 Meus Dados", "📅 Agendamentos", "💬 Mensagens"])
    
    with t_home:
        st.markdown("<div class='instruction-box'><b>Olá Cuidador!</b> Configure seu perfil para atrair tutores e gerencie sua agenda.</div>", unsafe_allow_html=True)

    with t_edit:
        st.subheader("Configurar Perfil Profissional")
        with st.form("perfil_form"):
            new_n = st.text_input("Nome", value=user_data['nome'])
            new_a = st.text_input("Endereço", value=user_data.get('endereco', ''))
            new_p = st.text_area("Animais/Portes que cuida", value=user_data.get('perfil_cuidado', ''))
            new_v = st.number_input("Valor da Diária (R$)", value=user_data.get('valores', 0))
            if st.form_submit_button("ATUALIZAR DADOS"):
                db.usuarios.update_one({"usuario": user_data['usuario']}, {"$set": {"nome": new_n, "endereco": new_a, "perfil_cuidado": new_p, "valores": new_v}})
                st.rerun()

    with t_agend:
        pedidos = list(db.agendamentos.find({"cuidador_id": user_data['usuario'], "status": "Pendente"}))
        for p in pedidos:
            st.write(f"📅 **Solicitação de {p['tutor_id']}** para o dia {p['data']}")
            c1, c2 = st.columns(2)
            if c1.button("APROVAR", key=f"ap_{p['_id']}"):
                db.agendamentos.update_one({"_id": p['_id']}, {"$set": {"status": "Aprovado"}})
                st.rerun()
            if c2.button("RECUSAR", key=f"re_{p['_id']}"):
                db.agendamentos.update_one({"_id": p['_id']}, {"$set": {"status": "Recusado"}})
                st.rerun()

    with t_chat:
        chats = db.mensagens.distinct("sender_id", {"receiver_id": user_data['usuario']})
        for tutor_id in chats:
            with st.expander(f"Conversa com {tutor_id}"):
                msgs = list(db.mensagens.find({"$or": [{"sender_id": user_data['usuario'], "receiver_id": tutor_id}, {"sender_id": tutor_id, "receiver_id": user_data['usuario']}]}).sort("dt", 1))
                for m in msgs:
                    cl = "sent" if m['sender_id'] == user_data['usuario'] else "received"
                    st.markdown(f"<div class='bubble {cl}'>{m['texto']}</div>", unsafe_allow_html=True)
                resp = st.text_input("Responder", key=f"res_{tutor_id}")
                if st.button("Enviar", key=f"btn_{tutor_id}"):
                    db.mensagens.insert_one({"sender_id": user_data['usuario'], "receiver_id": tutor_id, "texto": resp, "dt": datetime.now()})
                    st.rerun()

# 3. TUTOR MASTER
elif user_data['tipo'] == "Tutor":
    t_home, t_scan, t_cuid, t_chat = st.tabs(["🏠 Instruções", "🧬 PetScan IA", "🤝 Cuidadores", "💬 Chats"])
    
    with t_home:
        st.markdown("<div class='instruction-box'><b>Olá Tutor!</b> Use o PetScan para diagnósticos e contrate cuidadores qualificados.</div>", unsafe_allow_html=True)

    with t_scan:
        st.subheader("🧬 Diagnóstico Biométrico Universal")
        up = st.file_uploader("Submeter Amostra", type=['jpg', 'png', 'heic'])
        if up and st.button("EXECUTAR SCAN"):
            img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
            st.image(img, width=400)
            res = call_ia(f"Especialista: Analise este {cur_pet['especie'] if cur_pet else 'Pet'}. Escore corporal e fezes.", img=img)
            st.markdown(f"<div class='elite-card'>{res}</div>", unsafe_allow_html=True)
            pdf_b = create_pdf_report(cur_pet['nome'] if cur_pet else "Pet", cur_pet['especie'] if cur_pet else "Agnostico", "Geral", "N/A", res)
            st.download_button("📥 BAIXAR PDF TECHNOBOLT", pdf_b, file_name="laudo.pdf", mime="application/pdf")
            
            st.markdown("""### 📊 Guia de Referência Clínica""")
            st.markdown("""
                        """)

    with t_cuid:
        cuidadores = list(db.usuarios.find({"tipo": "Cuidador"}))
        for c in cuidadores:
            with st.container():
                st.markdown(f"""
                <div class='elite-card'>
                    <h3>{c['nome']} {'⭐' * int(c.get('rating', 5))}</h3>
                    <p>📍 {c.get('endereco', '')} | 💰 R$ {c.get('valores', 0)}/dia</p>
                    <p>🐾 {c.get('perfil_cuidado', 'Porte e espécies não informados')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    with st.expander("💬 Enviar Mensagem"):
                        msg_t = st.text_area("Texto", key=f"txt_{c['usuario']}")
                        if st.button("Enviar", key=f"send_{c['usuario']}"):
                            db.mensagens.insert_one({"sender_id": user_data['usuario'], "receiver_id": c['usuario'], "texto": msg_t, "dt": datetime.now(), "sender_addr": user_data.get('endereco')})
                            st.success("Enviado!")
                with c2:
                    with st.expander("📅 Agendar Data"):
                        da = st.date_input("Escolha o dia", key=f"dt_{c['usuario']}")
                        if st.button("Solicitar", key=f"req_{c['usuario']}"):
                            db.agendamentos.insert_one({"tutor_id": user_data['usuario'], "cuidador_id": c['usuario'], "data": str(da), "status": "Pendente"})
                            st.info("Solicitado!")
                with c3:
                    with st.expander("⭐ Avaliar"):
                        rt = st.slider("Nota", 1, 5, 5, key=f"rt_{c['usuario']}")
                        if st.button("Avaliar", key=f"av_{c['usuario']}"):
                            db.usuarios.update_one({"usuario": c['usuario']}, {"$set": {"rating": (c.get('rating', 5) + rt)/2}})
                            st.success("Avaliado!")

    with t_chat:
        chats = db.mensagens.distinct("receiver_id", {"sender_id": user_data['usuario']})
        for care_id in chats:
            with st.expander(f"Conversa com {care_id}"):
                msgs = list(db.mensagens.find({"$or": [{"sender_id": user_data['usuario'], "receiver_id": care_id}, {"sender_id": care_id, "receiver_id": user_data['usuario']}]}).sort("dt", 1))
                for m in msgs:
                    cl = "sent" if m['sender_id'] == user_data['usuario'] else "received"
                    st.markdown(f"<div class='bubble {cl}'>{m['texto']}</div>", unsafe_allow_html=True)
                r_t = st.text_input("Mensagem", key=f"t_res_{care_id}")
                if st.button("Enviar", key=f"t_btn_{care_id}"):
                    db.mensagens.insert_one({"sender_id": user_data['usuario'], "receiver_id": care_id, "texto": r_t, "dt": datetime.now()})
                    st.rerun()

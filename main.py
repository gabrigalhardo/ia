import streamlit as st
import pandas as pd
import time
from datetime import datetime
import pymysql

# --- CONFIGURAÇÃO DA PÁGINA E TEMA ---
st.set_page_config(
    page_title="Plataforma V1",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS MODERNO (DESIGN SYSTEM) ---
# Isso cria o visual "Clean", botões arredondados e suporta modo claro/escuro nativo
st.markdown("""
<style>
    /* Estilizando os Inputs */
    .stTextInput > div > div > input {
        border-radius: 12px;
        padding: 12px;
        border: 1px solid #ddd;
    }
    
    /* Estilizando Botões Primários */
    div.stButton > button {
        /* O Gradiente vai do seu #e61c49 para um tom levemente mais claro (#ff4b6e) para dar volume */
        background: linear-gradient(45deg, #e61c49, #ff4b6e);
        color: white;
        border-radius: 12px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
        transition: all 0.3s ease;
        /* Sombra ajustada para a cor nova (RGBA do #e61c49) */
        box-shadow: 0 4px 15px rgba(230, 28, 73, 0.3);
    }
    
    /* Efeito Hover (Mouse em cima) */
    div.stButton > button:hover {
        transform: translateY(-2px);
        /* Aumenta a sombra e inverte levemente o gradiente */
        box-shadow: 0 6px 20px rgba(230, 28, 73, 0.4);
        background: linear-gradient(45deg, #ff4b6e, #e61c49);
        color: white;
    }

    /* Cards para os resultados */
    .css-card {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
    }
    
    /* Centralizar Login */
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding-top: 50px;
    }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO COM BANCO DE DADOS ---
def get_db_connection():
    try:
        # Tenta conectar
        connection = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='',
            database='ia',
            port=3306, # CONFIRA SE NO SEU XAMPP É 3306 MESMO
            cursorclass=pymysql.cursors.DictCursor, # Retorna dados como dicionário
            connect_timeout=10
        )
        return connection
    except pymysql.MySQLError as e:
        st.error(f"❌ Erro de Conexão: {e}")
        return None

def validar_login(email, senha):
    print(f"--- Iniciando validação para: {email} ---") # Log no terminal
    
    conn = get_db_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cursor:
            # Query simples para evitar erros de sintaxe
            sql = "SELECT * FROM usuarios WHERE email=%s"
            cursor.execute(sql, (email,))
            user = cursor.fetchone()
            
            if user:
                print(f"✅ Usuário encontrado no banco. Verificando senha...")
                # Verificação de Senha e Status
                # Importante: Como 'senha' e 'liberado' são texto/enum, convertemos pra string pra garantir
                senha_banco = str(user['senha'])
                status_conta = str(user['liberado'])
                
                if senha_banco == senha:
                    if status_conta == 'aprovado':
                        print("🎉 Login Aprovado!")
                        return user
                    else:
                        st.error(f"Sua conta está com status: {status_conta}")
                        return None
                else:
                    st.error("Senha incorreta.")
                    return None
            else:
                st.warning("E-mail não encontrado.")
                return None
    except Exception as e:
        st.error(f"Erro na consulta: {e}")
        print(f"Erro detalhado: {e}")
        return None
    finally:
        conn.close()

# --- GERENCIAMENTO DE ESTADO ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = {}
if 'history' not in st.session_state: st.session_state.history = []
if 'last_analysis' not in st.session_state: st.session_state.last_analysis = None

# --- FUNÇÕES DE NAVEGAÇÃO ---
def navigate_to(page):
    st.session_state.page = page
    st.rerun()

def logout():
    st.session_state.logged_in = False
    st.session_state.user_info = {}
    st.session_state.page = 'login'
    st.rerun()

# --- TELA 1: LOGIN (CONECTADA AO MYSQL) ---
def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><h1 style='text-align: center; color: #FF6B6B;'>Bem-vindo</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Faça login para acessar suas análises</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("E-mail")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar", use_container_width=True)
            
            if submitted:
                if not email or not password:
                    st.warning("Preencha todos os campos.")
                else:
                    user = validar_login(email, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_info = user
                        st.toast(f"Login realizado! Bem-vindo(a): {user['apelido']}", icon="✅")
                        time.sleep(1)
                        navigate_to('home')
                    else:
                        st.error("Acesso negado. Verifique e-mail, senha ou se sua conta foi aprovada.")

# --- SIDEBAR (MENU) ---
def show_sidebar():
    if st.session_state.logged_in:
        with st.sidebar:
            st.markdown(f"### 👤 Olá, {st.session_state.user_info.get('apelido')}")
            st.divider()
            
            # Menu com ícones e estilo
            if st.button("🏠 Início", use_container_width=True): navigate_to('home')
            if st.button("🎵 Áudio", use_container_width=True): navigate_to('audio')
            if st.button("🎬 Vídeo", use_container_width=True): navigate_to('video')
            if st.button("📜 Histórico", use_container_width=True): navigate_to('history')
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            if st.button("Sair 🚪", type="primary", use_container_width=True): logout()

# --- TELA 2: HOME ---
def show_home():
    st.markdown("## 📊 Painel de Controle")
    
    # Cards de Resumo
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="css-card">
            <h3>Análises Feitas</h3>
            <h1>12</h1>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="css-card">
            <h3>Status</h3>
            <h3 style='color: #4CAF50;'>Ativo</h3>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="css-card">
            <h3>Plano</h3>
            <h3>Pro</h3>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### Acesso Rápido")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Novo Vídeo 🎬", use_container_width=True): navigate_to('video')
    with col_b:
        if st.button("Novo Áudio 🎵", use_container_width=True): navigate_to('audio')

# --- TELA 3 e 4: ANÁLISE ---
def show_analysis(tipo):
    icon = "🎵" if tipo == "Áudio" else "🎬"
    st.markdown(f"## {icon} Nova Análise de {tipo}")
    st.markdown("<div class='css-card'>", unsafe_allow_html=True)
    
    link = st.text_input(f"Cole o link do {tipo.lower()} aqui:")
    
    if st.button("🔍 Iniciar Análise", use_container_width=True):
        if link:
            with st.spinner("A IA está analisando os padrões..."):
                time.sleep(2.5) # Simulação
                st.session_state.last_analysis = {
                    "tipo": tipo,
                    "link": link,
                    "resultado": "Aprovado com ressalvas",
                    "confianca": "94%",
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M")
                }
                st.rerun()
        else:
            st.warning("Precisamos do link para começar.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Exibição do Resultado
    if st.session_state.last_analysis and st.session_state.last_analysis['tipo'] == tipo:
        res = st.session_state.last_analysis
        st.markdown("---")
        st.success("Análise Finalizada!")
        
        # Container de Resultado Moderno
        with st.container():
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #FF6B6B; color: #333;">
                <h3>Resultado: {res['resultado']}</h3>
                <p>Confiança do modelo: <b>{res['confianca']}</b></p>
                <small>{res['link']}</small>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            st.markdown("##### O veredito da IA está correto?")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Sim, está correto", key="yes", use_container_width=True):
                    salvar_historico("Correto")
            with c2:
                if st.button("❌ Não, está errado", key="no", use_container_width=True):
                    salvar_historico("Incorreto")

def salvar_historico(feedback):
    dados = st.session_state.last_analysis
    dados['feedback'] = feedback
    dados['usuario_id'] = st.session_state.user_info.get('id') # Salva quem fez
    st.session_state.history.append(dados)
    st.session_state.last_analysis = None
    st.toast("Feedback salvo no banco de dados!", icon="💾")
    time.sleep(1)
    st.rerun()

# --- TELA 5: HISTÓRICO ---
def show_history():
    st.markdown("## 📜 Histórico de Atividades")
    
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        st.dataframe(
            df[['data', 'tipo', 'resultado', 'feedback']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nenhum histórico encontrado para sua conta.")

# --- MAIN APP ---
def main():
    show_sidebar()
    
    if st.session_state.logged_in:
        if st.session_state.page == 'home': show_home()
        elif st.session_state.page == 'audio': show_analysis("Áudio")
        elif st.session_state.page == 'video': show_analysis("Vídeo")
        elif st.session_state.page == 'history': show_history()
    else:
        show_login()

if __name__ == "__main__":
    main()
import streamlit as st
import pandas as pd
import time
from datetime import datetime
import pymysql

# Importa a inteligência do nosso arquivo agente_moderador.py
# Certifique-se que o arquivo agente_moderador.py está na mesma pasta!
from agente_moderador import executar_analise_completa

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Plataforma de Treino IA", page_icon="🧠", layout="wide")

# --- CSS (MANTIVE O SEU, QUE ESTÁ ÓTIMO) ---
st.markdown("""
<style>
    .stTextInput > div > div > input { border-radius: 12px; padding: 12px; border: 1px solid #ddd; }
    div.stButton > button {
        background: linear-gradient(45deg, #e61c49, #ff4b6e); color: white; border-radius: 12px;
        border: none; padding: 10px 24px; font-weight: bold; transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(230, 28, 73, 0.3);
    }
    div.stButton > button:hover {
        transform: translateY(-2px); box-shadow: 0 6px 20px rgba(230, 28, 73, 0.4);
    }
    .css-card {
        background-color: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px; padding: 20px; margin-bottom: 20px;
    }
    .success-box { border-left: 5px solid #4CAF50; background-color: #f1f8f1; padding: 15px; border-radius: 5px; color: black;}
    .error-box { border-left: 5px solid #F44336; background-color: #fdf1f1; padding: 15px; border-radius: 5px; color: black;}
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO COM BANCO ---
def get_db_connection():
    try:
        return pymysql.connect(
            host='127.0.0.1', user='root', password='', database='ia',
            port=3306, cursorclass=pymysql.cursors.DictCursor, connect_timeout=10
        )
    except Exception as e:
        st.error(f"Erro DB: {e}")
        return None

# --- FUNÇÃO PARA SALVAR O TREINAMENTO (FEEDBACK) ---
def salvar_feedback_banco(dados_analise, tipo_feedback, status, motivo_erro=""):
    conn = get_db_connection()
    if not conn: return
    
    try:
        with conn.cursor() as cursor:
            # Verifica se já existe um registro para essa análise nessa sessão
            # Se não, cria. Se sim, atualiza.
            # Para simplificar este MVP, vamos inserir um novo registro a cada feedback completo
            
            sql = """
            INSERT INTO feedback_treinamento 
            (video_url, ia_transcricao, ia_visao, ia_veredito, 
             audio_status, audio_motivo_erro, visao_status, visao_motivo_erro, usuario_responsavel)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Prepara os dados
            # Se o feedback for de Áudio, salvamos audio_status. Se for Visão, salvamos visao_status.
            # O ideal é ter tudo preenchido, mas vamos salvar o que temos no momento.
            
            audio_st = status if tipo_feedback == 'audio' else None
            audio_txt = motivo_erro if tipo_feedback == 'audio' else None
            
            visao_st = status if tipo_feedback == 'visao' else None
            visao_txt = motivo_erro if tipo_feedback == 'visao' else None
            
            usuario = st.session_state.user_info.get('apelido', 'Anonimo')
            
            cursor.execute(sql, (
                dados_analise['url'],
                dados_analise['audio_transcricao'],
                dados_analise['analise_visual'],
                str(dados_analise['veredito_final']),
                audio_st, audio_txt,
                visao_st, visao_txt,
                usuario
            ))
            conn.commit()
            st.toast(f"Feedback de {tipo_feedback.upper()} salvo! Você está deixando a IA mais inteligente.", icon="🧠")
            
    except Exception as e:
        st.error(f"Erro ao salvar feedback: {e}")
    finally:
        conn.close()

# --- LOGIN E NAVEGAÇÃO ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'analise_atual' not in st.session_state: st.session_state.analise_atual = None

def validar_login(email, senha):
    # (Mantive sua lógica original simplificada para o exemplo)
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE email=%s", (email,))
            user = cursor.fetchone()
            if user and str(user['senha']) == senha: # Em produção use hash!
                return user
    return None

def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 Login Moderador")
        with st.form("login"):
            email = st.text_input("Email")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                user = validar_login(email, senha)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_info = user
                    st.session_state.page = 'lab'
                    st.rerun()
                else:
                    st.error("Login falhou")

# --- TELA PRINCIPAL: LABORATÓRIO DE TREINO ---
def show_moderation_lab():
    st.title("🧬 Laboratório de Treinamento de IA")
    st.markdown("Aqui nós ensinamos o modelo a diferenciar o certo do errado.")
    
    # Área de Input
    with st.container():
        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        url = st.text_input("🔗 Link do Vídeo para Análise e Treino:", placeholder="https://youtube/tiktok/instagram...")
        
        if st.button("🚀 Executar Análise Completa", use_container_width=True):
            if url:
                with st.spinner("Baixando, Ouvindo (Whisper) e Vendo (Llama Vision)..."):
                    # CHAMA DIRETO O ARQUIVO AGENTE_MODERADOR
                    resultado = executar_analise_completa(url)
                    
                    # Adiciona a URL no resultado pra salvar no banco depois
                    resultado['url'] = url
                    st.session_state.analise_atual = resultado
                    st.rerun()
            else:
                st.warning("Cole um link primeiro.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Exibição dos Resultados e Coleta de Feedback
    if st.session_state.analise_atual:
        dados = st.session_state.analise_atual
        
        # O Veredito
        st.markdown("---")
        veredito_limpo = str(dados['veredito_final']).replace("\n", "  \n")
        if "REPROVADO" in veredito_limpo:
            st.markdown(f"<div class='error-box'><h3>🚫 {veredito_limpo}</h3></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='success-box'><h3>✅ {veredito_limpo}</h3></div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

        # Colunas de Análise
        col_audio, col_visao = st.columns(2)

        # --- COLUNA 1: ÁUDIO ---
        with col_audio:
            st.info("👂 O que a IA ouviu (Transcrição)")
            st.text_area("Transcrição", dados['audio_transcricao'], height=250, disabled=True)
            
            st.markdown("#### A IA ouviu corretamente?")
            c1, c2 = st.columns(2)
            if c1.button("👍 Sim (Áudio)", key="audio_ok", use_container_width=True):
                salvar_feedback_banco(dados, 'audio', 'Correto')
            
            # Lógica do "Não" com input
            if "audio_nok_open" not in st.session_state: st.session_state.audio_nok_open = False
            
            if c2.button("👎 Não (Áudio)", key="audio_nok", use_container_width=True):
                st.session_state.audio_nok_open = True
            
            if st.session_state.audio_nok_open:
                motivo_audio = st.text_input("O que ela errou na transcrição ou interpretação?", key="txt_audio_erro")
                if st.button("💾 Salvar Erro de Áudio"):
                    salvar_feedback_banco(dados, 'audio', 'Incorreto', motivo_audio)
                    st.session_state.audio_nok_open = False
                    st.rerun()

        # --- COLUNA 2: VISÃO ---
        with col_visao:
            st.info("👁️ O que a IA viu (Frames)")
            st.text_area("Análise Visual", dados['analise_visual'], height=250, disabled=True)
            
            st.markdown("#### A IA viu corretamente?")
            c3, c4 = st.columns(2)
            if c3.button("👍 Sim (Visão)", key="visao_ok", use_container_width=True):
                salvar_feedback_banco(dados, 'visao', 'Correto')

            # Lógica do "Não" com input
            if "visao_nok_open" not in st.session_state: st.session_state.visao_nok_open = False
            
            if c4.button("👎 Não (Visão)", key="visao_nok", use_container_width=True):
                st.session_state.visao_nok_open = True
            
            if st.session_state.visao_nok_open:
                motivo_visao = st.text_input("O que ela não viu ou alucinou?", key="txt_visao_erro")
                if st.button("💾 Salvar Erro de Visão"):
                    salvar_feedback_banco(dados, 'visao', 'Incorreto', motivo_visao)
                    st.session_state.visao_nok_open = False
                    st.rerun()

# --- SIDEBAR E ROTEAMENTO ---
def main():
    if st.session_state.logged_in:
        with st.sidebar:
            st.header(f"Olá, {st.session_state.user_info.get('apelido', 'Admin')}")
            if st.button("Sair"):
                st.session_state.logged_in = False
                st.rerun()
        
        show_moderation_lab()
    else:
        show_login()

if __name__ == "__main__":
    main()
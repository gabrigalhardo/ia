import yt_dlp
import whisper
import ollama
import cv2
import os
import shutil
import time

# --- CONFIGURAÇÕES DO SISTEMA ---
PASTA_TEMP = "temp_moderacao_unificada"
MODELO_AUDIO = "medium"           # Whisper (Ouvido)
MODELO_VISAO = "llama3.2-vision"  # Llama Vision (Olhos)
MODELO_JUIZ = "llama3.1"          # Llama (Cérebro)

# --- REGRAS DO CLIENTE (SEU DASHBOARD) ---
REGRAS_COMPETICAO = """
1. PROIBIDO: Conteúdo sobre "ficar rico fácil", "ganância", "urubu do pix" ou promessas financeiras.
2. PROIBIDO: Linguagem desrespeitosa/ofensiva sobre família ou filhos (ex: "bucha").
3. PROIBIDO: Nudez, violência explícita ou armas.
4. PERMITIDO: Conteúdo motivacional, esportes, academia e humor saudável.
"""

def limpar_ambiente():
    """Remove a pasta temporária para começar limpo."""
    if os.path.exists(PASTA_TEMP):
        shutil.rmtree(PASTA_TEMP)
    os.makedirs(PASTA_TEMP)

def baixar_midia_unica(url):
    """
    Baixa o arquivo MP4 uma única vez. 
    Serve tanto para o áudio quanto para o vídeo.
    """
    print(f"📥 Baixando mídia completa (Áudio + Vídeo)...")
    caminho_saida = os.path.join(PASTA_TEMP, "midia_analise")
    
    # Detecção automática de Cookies
    cookies = None
    if "tiktok.com" in url: cookies = "cookies_tiktok.txt"
    elif "instagram.com" in url: cookies = "cookies_instagram.txt"
    
    if cookies and not os.path.exists(cookies): 
        print(f"⚠️  Aviso: Arquivo de cookies '{cookies}' não encontrado.")
        cookies = None

    # Configuração para baixar MP4 de qualidade média (bom para OCR, leve para baixar)
    opcoes = {
        'format': 'best[ext=mp4]', 
        'outtmpl': f"{caminho_saida}.%(ext)s",
        'quiet': True, 'no_warnings': True, 'nocheckcertificate': True,
        'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'},
        'cookiefile': cookies,
    }

    try:
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            ydl.download([url])
        
        arquivo_final = f"{caminho_saida}.mp4"
        if os.path.exists(arquivo_final):
            return arquivo_final
    except Exception as e:
        print(f"❌ Erro download: {e}")
    
    return None

def processar_audio(caminho_mp4):
    """Usa o Whisper para transcrever o áudio do MP4."""
    print("👂 [1/3] Whisper ouvindo o arquivo...")
    try:
        model = whisper.load_model(MODELO_AUDIO)
        # O Whisper aceita MP4 direto e extrai o áudio internamente
        result = model.transcribe(caminho_mp4, language="pt", fp16=False)
        return result["text"].strip()
    except Exception as e:
        return f"Erro na transcrição: {e}"

def processar_frames(caminho_mp4):
    """Usa o Llama 3.2 Vision para descrever 3 momentos do vídeo."""
    print("👀 [2/3] Llama 3.2 Vision analisando frames...")
    
    cap = cv2.VideoCapture(caminho_mp4)
    if not cap.isOpened(): return "Erro ao abrir vídeo."

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    pontos = [0.15, 0.50, 0.85] # Início, Meio, Fim
    relatorio_visual = []

    for i, p in enumerate(pontos):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(total_frames * p))
        ret, frame = cap.read()
        if not ret: continue

        # --- OTIMIZAÇÃO (Resize 960px) ---
        altura, largura = frame.shape[:2]
        nova_largura = 960
        fator = nova_largura / largura
        nova_altura = int(altura * fator)
        frame_redimensionado = cv2.resize(frame, (nova_largura, nova_altura))

        # Salva temporariamente
        img_path = os.path.join(PASTA_TEMP, f"frame_{i}.jpg")
        cv2.imwrite(img_path, frame_redimensionado)
        
        # --- PROMPT OTIMIZADO (PT-BR) ---
        prompt = """
        Atue como um especialista em Moderação de Conteúdo Brasileiro.
        
        1. CENA: Descreva quem está na imagem e o que fazem.
        2. TEXTO: Transcreva TODO texto visível na tela (Título e Legendas). Se não houver, diga "Sem texto".
        3. ALERTA: Cite se há nudez, violência ou armas.
        
        Responda APENAS em Português do Brasil.
        """
        
        try:
            resp = ollama.chat(
                model=MODELO_VISAO, 
                messages=[{'role': 'user', 'content': prompt, 'images': [img_path]}],
                options={'temperature': 0.1, 'num_predict': 400}
            )
            relatorio_visual.append(f"--- MOMENTO {int(p*100)}% ---\n{resp['message']['content']}")
        except:
            pass
    
    cap.release()
    return "\n".join(relatorio_visual)

def juiz_final(texto_audio, relatorio_visual):
    """O Llama 3.1 cruza os dados e dá o veredito."""
    print("⚖️  [3/3] O Juiz (Llama 3.1) está batendo o martelo...")
    
    prompt_sistema = f"""
    Você é o Auditor Chefe de uma competição de vídeos.
    Sua decisão é final. Analise as evidências abaixo e aplique as regras rigorosamente.

    AS REGRAS:
    {REGRAS_COMPETICAO}

    EVIDÊNCIAS COLETADAS:
    ---------------------
    1. TRANSCRIÇÃO (O que foi falado):
    "{texto_audio}"
    
    2. ANÁLISE VISUAL (O que foi visto):
    {relatorio_visual}
    ---------------------

    VEREDITO:
    Baseado nas regras, o vídeo foi APROVADO ou REPROVADO?
    Responda no seguinte formato:
    
    STATUS: [APROVADO / REPROVADO]
    MOTIVO: [Explicação curta citando a regra violada e a evidência encontrada]
    """

    res = ollama.chat(model=MODELO_JUIZ, messages=[{'role': 'user', 'content': prompt_sistema}])
    return res['message']['content']

def executar_analise_completa(url_video):
    limpar_ambiente()
    print(f"🚀 Iniciando análise via API: {url_video}")
    
    arquivo_video = baixar_midia_unica(url_video)
    
    if arquivo_video:
        texto_audio = processar_audio(arquivo_video)
        analise_visual = processar_frames(arquivo_video)
        decisao = juiz_final(texto_audio, analise_visual)
        
        # Retorna um Dicionário (JSON) limpo
        return {
            "status": "sucesso",
            "audio_transcricao": texto_audio,
            "analise_visual": analise_visual,
            "veredito_final": decisao
        }
    else:
        return {"status": "erro", "mensagem": "Falha no download"}

# Deixamos isso aqui pro caso de você ainda querer testar via terminal
if __name__ == "__main__":
    link = input("👉 Link do vídeo: ")
    print(executar_analise_completa(link))
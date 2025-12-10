import yt_dlp
import cv2
import ollama
import os
import time

# --- MUDANÇA: USANDO O NOVO MODELO DA META ---
PASTA_VISAO = "temp_visual"
MODELO_VISAO = "llama3.2-vision" 

def limpar_pasta():
    if not os.path.exists(PASTA_VISAO):
        os.makedirs(PASTA_VISAO)
    for f in os.listdir(PASTA_VISAO):
        try: os.remove(os.path.join(PASTA_VISAO, f))
        except: pass

def baixar_video_visual(url):
    print(f"1. 📥 Baixando vídeo com {MODELO_VISAO}...")
    caminho_saida = os.path.join(PASTA_VISAO, "video_teste.mp4")
    
    arquivo_cookies = None
    if "tiktok.com" in url: arquivo_cookies = "cookies_tiktok.txt"
    elif "instagram.com" in url: arquivo_cookies = "cookies_instagram.txt"
    if arquivo_cookies and not os.path.exists(arquivo_cookies): arquivo_cookies = None

    opcoes = {
        'format': 'best[ext=mp4]',
        'outtmpl': os.path.join(PASTA_VISAO, 'video_teste.%(ext)s'),
        'quiet': True, 'no_warnings': True, 'nocheckcertificate': True,
        'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'},
        'cookiefile': arquivo_cookies,
    }

    try:
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            ydl.download([url])
        if os.path.exists(caminho_saida):
            return caminho_saida
    except Exception:
        return None
    return None

def analisar_frames(caminho_video):
    print("2. 📸 Extraindo frames...")
    
    cap = cv2.VideoCapture(caminho_video)
    if not cap.isOpened(): return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    pontos = [0.15, 0.50, 0.85]
    
    for i, p in enumerate(pontos):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(total_frames * p))
        ret, frame = cap.read()
        if not ret: continue

        # --- AJUSTE 1: Aumentar para 960px (Melhor OCR) ---
        altura, largura = frame.shape[:2]
        nova_largura = 960 # Aumentei de 640 para 960 para ler legendas pequenas
        fator = nova_largura / largura
        nova_altura = int(altura * fator)
        frame_redimensionado = cv2.resize(frame, (nova_largura, nova_altura))

        nome_foto = os.path.join(PASTA_VISAO, f"frame_{i}.jpg")
        cv2.imwrite(nome_foto, frame_redimensionado)
        
        print(f"   ✅ Frame {i+1} capturado (960px). Analisando...")

        # --- AJUSTE 2: Prompt Específico para Legendas ---
        prompt = """
        Atue como um especialista em Moderação de Conteúdo Brasileiro.
        
        Sua missão é extrair TODO o contexto visual e textual.
        
        1. CENA: Descreva quem está na imagem e o que fazem. Ignore botões do app.
        2. TEXTO COMPLETO: Transcreva TUDO o que está escrito.
           - Leia o Título Superior.
           - Leia as Legendas Inferiores ou Rodapé.
           - Leia comentários visíveis na tela.
           - Se não houver texto, diga "Sem texto".
        3. ALERTA: Cite se há nudez, violência ou armas.
        
        Responda APENAS em Português. Mantenha o formato:
        CENA: ...
        TEXTO: ...
        ALERTA: ...
        """

        try:
            inicio_ia = time.time()
            resposta = ollama.chat(
                model=MODELO_VISAO, 
                messages=[{'role': 'user', 'content': prompt, 'images': [nome_foto]}],
                options={
                    'temperature': 0.1,  # Um pouquinho de criatividade ajuda a ler textos difíceis
                    'num_predict': 400,  # Aumentei o limite para caber o texto longo
                }
            )
            tempo = time.time() - inicio_ia
            conteudo = resposta['message']['content'].strip()
        except Exception as e:
            conteudo = f"Erro na IA: {e}"
            tempo = 0

        print(f"\n   👁️  ANÁLISE DO FRAME {i+1} ({tempo:.1f}s):")
        print("   " + "-"*40)
        print(f"   {conteudo}")
        print("   " + "-"*40 + "\n")

    cap.release()

def main():
    limpar_pasta()
    print("=== TESTE DE VISÃO (Llama 3.2 Vision) ===")
    url = input("👉 Link do vídeo: ")
    video = baixar_video_visual(url)
    if video: analisar_frames(video)

if __name__ == "__main__":
    main()
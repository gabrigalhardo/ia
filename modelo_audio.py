import yt_dlp
import whisper
import os
import sys

# --- CONFIGURAÇÕES ---
# Modelos disponíveis: tiny, base, small, medium, large
# 'medium' requer cerca de 5GB de VRAM/RAM e é muito preciso.
MODELO_ESCOLHIDO = "medium" 
PASTA_TEMP = "temp_download"

def baixar_apenas_audio(url_video):
    """
    Baixa o vídeo da URL, extrai o áudio em MP3 e deleta o vídeo.
    Retorna o caminho do arquivo MP3.
    """
    if not os.path.exists(PASTA_TEMP):
        os.makedirs(PASTA_TEMP)
    
    print(f"\n📥 [1/3] Baixando áudio de: {url_video}...")
    
    caminho_base = os.path.join(PASTA_TEMP, "audio_analise")
    
    # --- MUDANÇA AQUI: Camuflagem Anti-Bot ---
    opcoes_download = {
        'format': 'bestaudio/best',
        'outtmpl': caminho_base,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        
        # 1. Fingir ser um navegador Desktop moderno
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
        },
        
        # 2. Truque Mestre: Tentar usar clientes que não pedem login agressivo
        # Isso força o yt-dlp a tentar emular um Android ou TV se a Web falhar
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'web']
            }
        },
        
        # 3. Ignorar verificação de certificado SSL (ajuda em algumas redes)
        'nocheckcertificate': True,
    }

    try:
        with yt_dlp.YoutubeDL(opcoes_download) as ydl:
            ydl.download([url_video])
        
        return f"{caminho_base}.mp3"
    except Exception as e:
        print(f"❌ Erro no download: {e}")
        return None

def transcrever_audio(caminho_arquivo):
    """
    Carrega o modelo Whisper e transcreve o arquivo de áudio.
    """
    if not caminho_arquivo or not os.path.exists(caminho_arquivo):
        return "Erro: Arquivo de áudio não encontrado."

    print(f"\n🧠 [2/3] Carregando modelo '{MODELO_ESCOLHIDO}'... (Aguarde)")
    
    # Aqui ele baixa o modelo na primeira vez (aprox 1.5GB)
    # Device="cuda" usa sua placa de vídeo (se tiver NVIDIA). Se der erro, mude para "cpu".
    try:
        modelo = whisper.load_model(MODELO_ESCOLHIDO) # O sistema escolhe CPU ou GPU auto
    except Exception as e:
        print(f"Erro ao carregar modelo: {e}")
        return None

    print("🎧 [3/3] A IA está ouvindo e transcrevendo...")
    
    # language='pt' força o português para evitar que ele ache que é inglês
    resultado = modelo.transcribe(caminho_arquivo, language="pt")
    
    return resultado["text"]

def main():
    print("=== AGENTE DE ESCUTA (WHISPER) ===")
    url = input("👉 Cole o link do vídeo (YouTube, Instagram, TikTok): ")
    
    if not url:
        print("Nenhum link fornecido.")
        return

    # 1. Baixar
    arquivo_audio = baixar_apenas_audio(url)
    
    if arquivo_audio:
        # 2. Transcrever
        texto = transcrever_audio(arquivo_audio)
        
        if texto:
            print("\n" + "="*50)
            print("📝 RESULTADO DA TRANSCRIÇÃO:")
            print("="*50)
            print(texto.strip())
            print("="*50 + "\n")
        
        # 3. Limpeza (Deletar o arquivo temporário para não encher seu HD)
        try:
            os.remove(arquivo_audio)
            print("🧹 Arquivo temporário limpo com sucesso.")
        except:
            pass
    
    else:
        print("Falha ao processar o vídeo.")

if __name__ == "__main__":
    main()
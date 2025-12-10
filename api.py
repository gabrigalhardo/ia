from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from agente_moderador import executar_analise_completa

# Cria a aplicação
app = FastAPI(title="API Moderador Supremo")

# Define o formato do pedido (o que o site tem que mandar)
class PedidoAnalise(BaseModel):
    url: str

@app.get("/")
def home():
    return {"mensagem": "O Agente Moderador está online! 🤖"}

@app.post("/analisar")
def endpoint_analisar(pedido: PedidoAnalise):
    """
    Recebe um JSON: {"url": "https://..."}
    Retorna o veredito da IA.
    """
    print(f"📨 Recebido pedido para: {pedido.url}")
    
    try:
        # Chama a inteligência que criamos no outro arquivo
        resultado = executar_analise_completa(pedido.url)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Para rodar o servidor
if __name__ == "__main__":
    # Roda na porta 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
import httpx

# Mantenha o endpoint oficial em HTTP ou HTTPS
DOG_API_LIVE_LINK = "http://dog-api.kinduff.com/api/facts"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Definimos um User-Agent comum para evitar bloqueios do servidor externo
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    app.state.client = httpx.AsyncClient(headers=headers, follow_redirects=True)
    yield
    await app.state.client.aclose()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {
        "message": "API funcionando! Acesse /dogfact para obter curiosidades sobre cachorros."
    }

@app.get("/dogfact")
async def dogfact(
    number: int = Query(default=1, ge=1, le=10, description="Número de curiosidades retornadas")
):
    client: httpx.AsyncClient = app.state.client
    
    try:
        response = await client.get(DOG_API_LIVE_LINK, params={"number": number})
        response.raise_for_status()
        
        data = response.json()
        
        # Validação extra caso a API externa ainda retorne success = False
        if not data.get("success", False):
            raise HTTPException(
                status_code=502,
                detail="A Dog API externa respondeu, mas não conseguiu gerar os fatos."
            )
            
        return data

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code, 
            detail=f"Erro na requisição externa: {e.response.status_code}"
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="API externa indisponível. Tente novamente mais tarde."
        )
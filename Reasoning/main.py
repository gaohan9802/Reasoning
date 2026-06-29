from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
import httpx

app = FastAPI()

TARGET = "https://api.pioneer.ai"

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(request: Request, path: str):
    body = None
    if request.method == "POST":
        try:
            body = await request.json()
        except:
            pass

    if body and "chat/completions" in path:
        body["reasoning"] = {"effort": "high"}
        body["store"] = False

    headers = {}
    if "authorization" in request.headers:
        headers["authorization"] = request.headers["authorization"]
    headers["content-type"] = "application/json"

    async with httpx.AsyncClient(timeout=300) as client:
        if body and body.get("stream"):
            req = client.build_request(
                request.method,
                f"{TARGET}/{path}",
                json=body,
                headers=headers,
            )
            resp = await client.send(req, stream=True)
            return StreamingResponse(
                resp.aiter_bytes(),
                status_code=resp.status_code,
                headers={"content-type": "text/event-stream"},
            )
        elif body:
            resp = await client.request(
                request.method,
                f"{TARGET}/{path}",
                json=body,
                headers=headers,
            )
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
        else:
            resp = await client.request(
                request.method,
                f"{TARGET}/{path}",
                headers=headers,
            )
            try:
                return JSONResponse(content=resp.json(), status_code=resp.status_code)
            except:
                return JSONResponse(content={"error": "upstream error"}, status_code=502)

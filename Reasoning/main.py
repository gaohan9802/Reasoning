from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import httpx

app = FastAPI()

TARGET = "https://api.pioneer.ai"

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(request: Request, path: str):
    body = await request.json() if request.method == "POST" else None

    if body and path == "chat/completions":
        body["reasoning"] = {"effort": "high"}
        body["store"] = False

    headers = dict(request.headers)
    headers.pop("host", None)

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
                resp.aiter_raw(),
                status_code=resp.status_code,
                headers=dict(resp.headers),
            )
        else:
            resp = await client.request(
                request.method,
                f"{TARGET}/{path}",
                json=body,
                headers=headers,
            )
            return resp.json()

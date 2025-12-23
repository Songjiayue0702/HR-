"""
API Gateway / Reverse Proxy for Cloudflare Workers
- Handles CORS preflight
- Proxies /api/* requests to the backend (Railway Flask)
"""

from urllib.parse import urlparse
from js import Request, Response, fetch  # Cloudflare Workers globals

# 后端基地址（Railway）
BACKEND_BASE_URL = "https://web-production-5db0.up.railway.app"

# CORS 配置
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept",
    "Access-Control-Max-Age": "86400",
}


def with_cors(resp: Response) -> Response:
    """附加 CORS 头"""
    for k, v in CORS_HEADERS.items():
        resp.headers[k] = v
    return resp


async def handle_options(_: Request) -> Response:
    """处理预检请求"""
    return Response(None, status=204, headers=CORS_HEADERS)


async def forward(request: Request) -> Response:
    """将 /api/* 请求转发到后端"""
    parsed = urlparse(request.url)
    if not parsed.path.startswith("/api/"):
        return with_cors(Response("Not Found", status=404))

    # 构造目标 URL，保留查询参数
    target = f"{BACKEND_BASE_URL}{parsed.path}"
    if parsed.query:
        target += f"?{parsed.query}"

    # 复制请求头，去掉 host
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}

    # 读取请求体（GET/HEAD 不需要 body）
    body = None
    if request.method not in ("GET", "HEAD"):
        body = await request.arrayBuffer()

    # 发起转发
    upstream = await fetch(
        target,
        {
            "method": request.method,
            "headers": headers,
            "body": body,
        },
    )

    # 回传上游响应（状态码、头、体）
    resp_body = await upstream.arrayBuffer()
    resp = Response(resp_body, status=upstream.status, headers=upstream.headers)
    return with_cors(resp)


async def on_fetch(request: Request, env) -> Response:
    """Worker 入口"""
    try:
        if request.method == "OPTIONS":
            return await handle_options(request)
        return await forward(request)
    except Exception as e:
        print(f"Proxy error: {e}")
        return with_cors(Response("Internal Server Error", status=500))


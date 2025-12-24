"""
API Gateway / Reverse Proxy for Cloudflare Workers
- Handles CORS preflight
- Proxies /api/* requests to the backend (Railway Flask)
"""

from urllib.parse import urlparse

# 后端基地址（Railway）
BACKEND_BASE_URL = "https://web-production-5db0.up.railway.app"

# CORS 配置
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept",
    "Access-Control-Max-Age": "86400",
}


def with_cors(resp):
    """附加 CORS 头"""
    for k, v in CORS_HEADERS.items():
        resp.headers.set(k, v)
    return resp


async def handle_options():
    """处理预检请求"""
    from js import Response
    return Response.new(None, {"status": 204, "headers": CORS_HEADERS})


async def forward(request):
    """将 /api/* 请求转发到后端"""
    from js import Response, fetch
    
    parsed = urlparse(request.url)
    if not parsed.path.startswith("/api/"):
        from js import Response
        return with_cors(Response.new("Not Found", {"status": 404}))

    # 构造目标 URL，保留查询参数
    target = f"{BACKEND_BASE_URL}{parsed.path}"
    if parsed.query:
        target += f"?{parsed.query}"

    # 复制请求头，去掉 host
    headers = {}
    for k, v in request.headers.items():
        if k.lower() != "host":
            headers[k] = v

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
    resp = Response.new(resp_body, {
        "status": upstream.status,
        "headers": upstream.headers,
    })
    return with_cors(resp)


async def fetch(request, env):
    """Worker 入口 - Python Workers 必须使用这个函数名 (Python Workers)"""
    try:
        if request.method == "OPTIONS":
            return await handle_options()
        return await forward(request)
    except Exception as e:
        print(f"Proxy error: {e}")
        import traceback
        traceback.print_exc()
        from js import Response
        return with_cors(Response.new("Internal Server Error", {"status": 500}))


# Cloudflare Workers Python 事件处理器注册
# 使用 export 字典注册 fetch 处理器
export = {"fetch": fetch}

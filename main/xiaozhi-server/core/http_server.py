import asyncio
import os
import aiohttp
from aiohttp import web, WSMsgType
from config.logger import setup_logging
from core.api.ota_handler import OTAHandler
from core.api.vision_handler import VisionHandler

TAG = __name__
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


class SimpleHttpServer:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logging()
        self.ota_handler = OTAHandler(config)
        self.vision_handler = VisionHandler(config)

    def _get_websocket_url(self, local_ip: str, port: int) -> str:
        """获取websocket地址"""
        server_config = self.config["server"]
        websocket_config = server_config.get("websocket")
        if websocket_config and "你" not in websocket_config:
            return websocket_config
        else:
            return f"ws://{local_ip}:{port}/xiaozhi/v1/"

    async def _handle_websocket_proxy(self, request):
        """Proxy WebSocket connections to the internal websockets server."""
        ws_response = web.WebSocketResponse()
        await ws_response.prepare(request)

        ws_internal_port = int(self.config["server"].get("ws_internal_port", 8001))
        # Forward query string if present
        qs = request.query_string
        internal_url = f"ws://localhost:{ws_internal_port}{request.path}"
        if qs:
            internal_url += f"?{qs}"

        self.logger.bind(tag=TAG).info(f"WS proxy: {request.path} -> {internal_url}")

        try:
            session = aiohttp.ClientSession()
            # Forward headers from original request
            headers = {}
            for h in ["device-id", "client-id", "authorization", "protocol-version",
                       "user-agent", "accept-language", "x-real-ip", "x-forwarded-for"]:
                if h in request.headers:
                    headers[h] = request.headers[h]

            async with session.ws_connect(internal_url, headers=headers) as ws_internal:
                # Bidirectional pipe
                async def client_to_internal():
                    async for msg in ws_response:
                        if msg.type == WSMsgType.TEXT:
                            await ws_internal.send_str(msg.data)
                        elif msg.type == WSMsgType.BINARY:
                            await ws_internal.send_bytes(msg.data)
                        elif msg.type in (WSMsgType.CLOSE, WSMsgType.ERROR):
                            break

                async def internal_to_client():
                    async for msg in ws_internal:
                        if msg.type == WSMsgType.TEXT:
                            await ws_response.send_str(msg.data)
                        elif msg.type == WSMsgType.BINARY:
                            await ws_response.send_bytes(msg.data)
                        elif msg.type in (WSMsgType.CLOSE, WSMsgType.ERROR):
                            break

                await asyncio.gather(
                    client_to_internal(),
                    internal_to_client(),
                    return_exceptions=True
                )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"WS proxy error: {e}")
        finally:
            await session.close()
            if not ws_response.closed:
                await ws_response.close()

        return ws_response

    async def start(self):
        try:
            server_config = self.config["server"]
            read_config_from_api = self.config.get("read_config_from_api", False)
            host = server_config.get("ip", "0.0.0.0")
            # Listen on the main public port (Railway exposes this)
            port = int(server_config.get("port", 8000))

            app = web.Application()

            if not read_config_from_api:
                app.add_routes(
                    [
                        web.get("/xiaozhi/ota/", self.ota_handler.handle_get),
                        web.post("/xiaozhi/ota/", self.ota_handler.handle_post),
                        web.options("/xiaozhi/ota/", self.ota_handler.handle_options),
                        web.get(
                            "/xiaozhi/ota/download/{filename}",
                            self.ota_handler.handle_download,
                        ),
                        web.options(
                            "/xiaozhi/ota/download/{filename}",
                            self.ota_handler.handle_options,
                        ),
                    ]
                )

            # Vision API
            app.add_routes(
                [
                    web.get("/mcp/vision/explain", self.vision_handler.handle_get),
                    web.post("/mcp/vision/explain", self.vision_handler.handle_post),
                    web.options("/mcp/vision/explain", self.vision_handler.handle_options),
                ]
            )

            # WebSocket proxy to internal websockets server
            app.router.add_get("/xiaozhi/v1/", self._handle_websocket_proxy)
            app.router.add_get("/xiaozhi/v1", self._handle_websocket_proxy)

            # Flash tool page
            async def handle_flash_page(request):
                flash_file = os.path.join(DATA_DIR, "flash.html")
                if os.path.isfile(flash_file):
                    return web.FileResponse(flash_file)
                return web.Response(text="Flash page not found", status=404)

            # Dashboard page
            async def handle_dashboard(request):
                dash_file = os.path.join(DATA_DIR, "dashboard.html")
                if os.path.isfile(dash_file):
                    return web.FileResponse(dash_file)
                return web.Response(text="Dashboard not found", status=404)

            # Root redirect to dashboard
            async def handle_root(request):
                raise web.HTTPFound('/dashboard')

            app.router.add_get("/", handle_root)
            app.router.add_get("/flash", handle_flash_page)
            app.router.add_get("/dashboard", handle_dashboard)

            # Run on the public port
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, host, port)
            await site.start()
            self.logger.bind(tag=TAG).info(
                f"HTTP+WS proxy server listening on {host}:{port}"
            )

            # Keep running
            while True:
                await asyncio.sleep(3600)
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"HTTP服务器启动失败: {e}")
            import traceback
            self.logger.bind(tag=TAG).error(f"错误堆栈: {traceback.format_exc()}")
            raise

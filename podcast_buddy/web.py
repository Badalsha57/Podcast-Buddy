from __future__ import annotations

import argparse
import json
import mimetypes
import os
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse, parse_qs

from .config import DEFAULT_SUMMARY_MODEL, Settings, load_dotenv
from .episode import create_episode
from .summarizer import SummarizationError

STATIC_DIR = Path(__file__).with_name("static")
# Model ka path aur unique naam
CUSTOM_MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../models/custom_summarizer"))
UNIQUE_MODEL_NAME = "Podcast-Buddy-Brain-v1"

class PodcastBuddyWebHandler(BaseHTTPRequestHandler):
    settings: Settings

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        # --- STATUS ROUTE: Yahan fix kiya hai ---
        if parsed.path == "/api/status":
            display_model = self.settings.summary_model
            # Agar path custom model ka hai, toh unique naam bhejo
            if display_model and os.path.normpath(display_model) == os.path.normpath(CUSTOM_MODEL_PATH):
                display_model = UNIQUE_MODEL_NAME

            self._send_json(
                {
                    "serpapiKeyConfigured": bool(self.settings.serpapi_key),
                    "outputDir": str(self.settings.output_dir),
                    "defaultModel": display_model,
                }
            )
            return

        if parsed.path == "/api/episodes/stream":
            self._handle_stream(parsed.query)
            return

        path = "/index.html" if parsed.path == "/" else parsed.path
        self._serve_static(path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/ask":
            try:
                payload = self._read_json()
                question = str(payload.get("question", "")).strip()

                if not question:
                    self._send_json({"error": "Question is required"}, status=HTTPStatus.BAD_REQUEST)
                    return

                from .ai_chat import ask_local_ai
                answer = ask_local_ai(question)
                self._send_json({"question": question, "answer": answer, "success": True})
                return
            except Exception as exc:
                self._send_json({"error": str(exc), "success": False}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
                return

        if parsed.path == "/api/episodes":
            try:
                payload = self._read_json()
                episode_data = self._execute_episode_generation(payload)
                self._send_json(episode_data)
            except (ValueError, SummarizationError) as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def _handle_stream(self, query_string: str) -> None:
        query_params = parse_qs(query_string)
        payload = {
            "topic": query_params.get("topic", [""])[0],
            "limit": query_params.get("limit", [50])[0],
            "gl": query_params.get("gl", [None])[0],
            "hl": query_params.get("hl", [None])[0],
            "summarizer": query_params.get("summarizer", ["auto"])[0],
            "summaryModel": query_params.get("summaryModel", [""])[0],
            "maxSummaryWords": query_params.get("maxSummaryWords", [160])[0],
            "hostAName": query_params.get("hostAName", ["Aarav"])[0],
            "hostBName": query_params.get("hostBName", ["Meera"])[0],
        }

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        try:
            episode_data = self._execute_episode_generation(payload)
            final_response = {"status": "completed", "payload": episode_data}
            self.wfile.write(f"data: {json.dumps(final_response)}\n\n".encode("utf-8"))
            self.wfile.flush()
        except Exception as e:
            err_msg = {"status": "progress", "message": f"Error: {str(e)}", "percentage": 0}
            self.wfile.write(f"data: {json.dumps(err_msg)}\n\n".encode("utf-8"))
            self.wfile.flush()

    def _execute_episode_generation(self, data_source: dict[str, Any]) -> dict[str, Any]:
        """Wrapper execution unit evaluating standard file saving parameters."""
        model_input = str(data_source.get("summaryModel") or self.settings.summary_model)

        episode = create_episode(
            topic=str(data_source.get("topic", "")).strip(),
            limit=_as_int(data_source.get("limit"), default=50, minimum=1, maximum=1000),
            gl=str(data_source.get("gl") or self.settings.serpapi_gl),
            hl=str(data_source.get("hl") or self.settings.serpapi_hl),
            serpapi_key=self.settings.serpapi_key,
            summarizer=str(data_source.get("summarizer") or "auto"),
            summary_model=model_input,
            max_summary_words=_as_int(data_source.get("maxSummaryWords"), default=160, minimum=40, maximum=260),
            host_a_name=str(data_source.get("hostAName") or "Aarav"),
            host_b_name=str(data_source.get("hostBName") or "Meera"),
            output_dir=self.settings.output_dir,
        )

        final_model_name = episode.summary_result.model
        if final_model_name and os.path.normpath(final_model_name) == os.path.normpath(CUSTOM_MODEL_PATH):
            final_model_name = UNIQUE_MODEL_NAME

        return {
            "topic": episode.topic,
            "conversation": episode.conversation_markdown,
            "summary": episode.summary_markdown,
            "sources": [asdict(item) for item in episode.news_items],
            "files": {
                "conversation": str(episode.paths["conversation"]),
                "summary": str(episode.paths["summary"]),
                "metadata": str(episode.paths["metadata"]),
            },
            "summarizer": episode.summary_result.engine,
            "model": final_model_name,
            "fallbackUsed": episode.summary_result.fallback_used,
            "paidModelsUsed": False,
        }

    def _send_sse_event(self, status: str, message: str, percentage: int) -> None:
        packet = {"status": status, "message": message, "percentage": percentage}
        self.wfile.write(f"data: {json.dumps(packet)}\n\n".encode("utf-8"))
        self.wfile.flush()

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0: return {}
        raw = self.rfile.read(length).decode("utf-8")
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}

    def _serve_static(self, request_path: str) -> None:
        relative = unquote(request_path).lstrip("/")
        target = (STATIC_DIR / relative).resolve()
        static_root = STATIC_DIR.resolve()
        if static_root not in target.parents and target != static_root:
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return
        if not target.exists() or not target.is_file():
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        body = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Podcast Buddy local web UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser

def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    settings = Settings.from_env()
    args = build_parser().parse_args(argv)
    handler = PodcastBuddyWebHandler
    handler.settings = settings
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Podcast Buddy running at http://{args.host}:{args.port}")
    try: server.serve_forever()
    except KeyboardInterrupt: print("\nStopping.")
    finally: server.server_close()
    return 0

def _as_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
    try: parsed = int(value)
    except (TypeError, ValueError): parsed = default
    return min(max(parsed, minimum), maximum)

if __name__ == "__main__":
    raise SystemExit(main())
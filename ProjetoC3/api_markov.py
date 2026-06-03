from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


HOST = "127.0.0.1"
PORT = 8787
ROOT = Path(__file__).resolve().parent
HTML_FILE = ROOT / "roleta-markov.html"


class MarkovApiHandler(BaseHTTPRequestHandler):
    server_version = "MarkovRouletteAPI/1.0"

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:
        if self.path in {"/", "/index.html", "/roleta-markov.html"}:
            self._send_file(HTML_FILE, "text/html; charset=utf-8")
            return

        if self.path == "/api/health":
            self._send_json({"ok": True, "service": "Markov Roulette API"})
            return

        self.send_error(404, "Not found")

    def do_POST(self) -> None:
        if self.path != "/api/explain":
            self.send_error(404, "Not found")
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            self._send_json({"html": build_explanation(payload)})
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=400)

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self.send_error(404, "File not found")
            return

        body = path.read_bytes()
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[api] {self.address_string()} - {format % args}")


def build_explanation(payload: dict[str, Any]) -> str:
    current = payload.get("currentState", "estado atual")
    selected = payload.get("selectedBet", "cor selecionada")
    best = payload.get("bestBet", "melhor cor")
    probability = float(payload.get("selectedProbability", 0.0))
    odd = float(payload.get("selectedOdd", 0.0))
    ev = float(payload.get("selectedEv", 0.0))
    best_ev = float(payload.get("bestEv", 0.0))
    spins = int(payload.get("spinCount", 0))
    stake = float(payload.get("stake", 0.0))

    sign = "+" if ev >= 0 else "-"
    best_sign = "+" if best_ev >= 0 else "-"
    convergence = (
        "a amostra ainda é pequena, então a diferença entre frequência empírica e π é parte natural do ruído Monte Carlo"
        if spins < 50
        else "a simulação já começa a revelar a convergência das frequências para a distribuição estacionária π"
    )

    return f"""
      <p><strong>Resposta da API Python:</strong> no estado {current}, a próxima roleta é sorteada usando somente a linha correspondente de P. Isso materializa a propriedade P(X<sub>n+1</sub>|X<sub>n</sub>, histórico) = P(X<sub>n+1</sub>|X<sub>n</sub>).</p>
      <p>A aposta em {selected} tem probabilidade condicional de {probability * 100:.1f}% e odd {odd:.2f}x. Com aposta de R$ {stake:.2f}, o valor esperado é <strong>{sign}R$ {abs(ev):.2f}</strong>.</p>
      <p>A melhor decisão local é {best}, com EV de <strong>{best_sign}R$ {abs(best_ev):.2f}</strong>. O ponto matemático é que a decisão usa a distribuição condicional da próxima etapa, não uma média ingênua.</p>
      <p>Após {spins} rodadas, {convergence}.</p>
    """


def main() -> None:
    print(f"Roleta de Markov rodando em http://{HOST}:{PORT}")
    print("Pressione Ctrl+C para encerrar.")
    ThreadingHTTPServer((HOST, PORT), MarkovApiHandler).serve_forever()


if __name__ == "__main__":
    main()

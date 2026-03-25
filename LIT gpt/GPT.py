import sys
import os
import json
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from unittest.mock import MagicMock

# Заменяем Pythonista-модули
sys.modules['ui'] = MagicMock()
sys.modules['console'] = MagicMock()
sys.modules['dialogs'] = MagicMock()
sys.modules['scene'] = MagicMock()

os.chdir(os.path.dirname(os.path.abspath(__file__)))

import INIT

# ============================================================
# HTML-интерфейс
# ============================================================

HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LIT GPT</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #1a1a1a;
    color: #fff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    padding: 24px;
  }
  h1 { font-size: 2rem; margin-bottom: 32px; letter-spacing: 2px; }
  .card {
    background: #2a2a2a;
    border-radius: 16px;
    padding: 28px;
    width: 100%;
    max-width: 520px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  textarea {
    background: #1a1a1a;
    color: #fff;
    border: none;
    border-radius: 10px;
    padding: 14px;
    font-size: 1rem;
    resize: none;
    outline: none;
    font-family: inherit;
    height: 90px;
  }
  button {
    background: #4a4a4a;
    color: #fff;
    border: none;
    border-radius: 10px;
    padding: 12px;
    font-size: 1rem;
    cursor: pointer;
    transition: background 0.15s;
  }
  button:hover { background: #606060; }
  .answer {
    background: #1a1a1a;
    border-radius: 10px;
    padding: 14px;
    font-size: 1.1rem;
    color: #90e090;
    min-height: 52px;
    word-break: break-word;
  }
  .label { font-size: 0.8rem; color: #888; }
</style>
</head>
<body>
<h1>LIT GPT</h1>
<div class="card">
  <div class="label">Введи сообщение</div>
  <textarea id="input" placeholder="Напиши что-нибудь..." autofocus></textarea>
  <button onclick="send()">Отправить</button>
  <div class="label">Ответ</div>
  <div class="answer" id="output">—</div>
</div>
<script>
  document.getElementById('input').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  });
  function send() {
    const text = document.getElementById('input').value.trim();
    if (!text) return;
    fetch('/ask', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text})
    })
    .then(r => r.json())
    .then(data => {
      document.getElementById('output').textContent = data.answer || '—';
    });
  }
</script>
</body>
</html>"""

# ============================================================
# Сервер
# ============================================================

class Handler(BaseHTTPRequestHandler):
	def log_message(self, *_args):
		pass  # тихий режим

	def do_GET(self):
		self.send_response(200)
		self.send_header('Content-Type', 'text/html; charset=utf-8')
		self.end_headers()
		self.wfile.write(HTML.encode('utf-8'))

	def do_POST(self):
		if self.path == '/ask':
			length = int(self.headers.get('Content-Length', 0))
			body = json.loads(self.rfile.read(length))
			text = body.get('text', '').strip()
			if text:
				INIT.learn(text)
				answer = INIT.answer(text)
			else:
				answer = ''
			response = json.dumps({'answer': answer}).encode('utf-8')
			self.send_response(200)
			self.send_header('Content-Type', 'application/json')
			self.end_headers()
			self.wfile.write(response)

PORT = 5050
server = HTTPServer(('localhost', PORT), Handler)

print(f"LIT GPT запущен → http://localhost:{PORT}")
print("Для остановки: Ctrl+C")

threading.Timer(0.3, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()
server.serve_forever()

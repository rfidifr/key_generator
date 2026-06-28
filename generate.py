"""
keygen_server.py — Single-file arcade license key generator.
Uses only Python standard library (no FastAPI, no third-party deps).

Run:  python keygen_server.py
Then open:  http://127.0.0.1:8500
"""

import hashlib
import http.server
import json
import urllib.parse
from http import HTTPStatus

# ─── Cryptographic core (identical logic to the original) ────────────────────

def calculate_license_hash(mobo: str, bios: str, mac: str) -> str:
    raw = f"ARCADE_CORE_v1||{mobo.strip()}||{bios.strip()}||{mac.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ─── HTML frontend ───────────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Arcade Keygen</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@400;500;600&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:        #0b0c10;
    --surface:   #13151c;
    --border:    #1f2330;
    --accent:    #00e5ff;
    --accent-dim:#007a8a;
    --success:   #39ff82;
    --error:     #ff4d6d;
    --text:      #c8cdd8;
    --text-dim:  #5a6175;
    --mono:      'Share Tech Mono', monospace;
    --sans:      'Inter', system-ui, sans-serif;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 48px 16px 64px;
  }

  /* ── Header ── */
  header {
    text-align: center;
    margin-bottom: 48px;
  }
  .badge {
    display: inline-block;
    font-family: var(--mono);
    font-size: 11px;
    letter-spacing: .15em;
    text-transform: uppercase;
    color: var(--accent);
    border: 1px solid var(--accent-dim);
    border-radius: 2px;
    padding: 3px 10px;
    margin-bottom: 18px;
  }
  h1 {
    font-size: clamp(24px, 5vw, 38px);
    font-weight: 600;
    letter-spacing: -.02em;
    color: #e8ecf4;
    line-height: 1.15;
  }
  h1 span { color: var(--accent); }
  header p {
    margin-top: 10px;
    font-size: 14px;
    color: var(--text-dim);
    max-width: 420px;
    line-height: 1.6;
  }

  /* ── Card ── */
  .card {
    width: 100%;
    max-width: 520px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
  }
  .card-header {
    padding: 18px 24px;
    border-bottom: 1px solid var(--border);
    font-family: var(--mono);
    font-size: 12px;
    letter-spacing: .1em;
    color: var(--text-dim);
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--border); }
  .dot.r { background: #ff5f57; }
  .dot.y { background: #febc2e; }
  .dot.g { background: #28c840; }
  .card-body { padding: 28px 24px; }

  /* ── Form ── */
  .field { margin-bottom: 20px; }
  label {
    display: block;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-bottom: 7px;
  }
  input {
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--text);
    font-family: var(--mono);
    font-size: 13px;
    padding: 10px 13px;
    outline: none;
    transition: border-color .15s;
  }
  input::placeholder { color: var(--text-dim); }
  input:focus { border-color: var(--accent-dim); }
  input.err { border-color: var(--error); }

  button {
    width: 100%;
    padding: 12px;
    background: var(--accent);
    color: #000;
    border: none;
    border-radius: 4px;
    font-family: var(--mono);
    font-size: 13px;
    font-weight: 700;
    letter-spacing: .08em;
    cursor: pointer;
    transition: opacity .15s, transform .1s;
    margin-top: 4px;
  }
  button:hover  { opacity: .88; }
  button:active { transform: scale(.98); }
  button:disabled { opacity: .4; cursor: not-allowed; }

  /* ── Result ── */
  #result { margin-top: 24px; }

  .result-box {
    border-radius: 4px;
    padding: 16px;
    font-size: 13px;
    line-height: 1.5;
  }
  .result-box.success {
    background: #071a10;
    border: 1px solid #1a4d2a;
  }
  .result-box.error {
    background: #1a070a;
    border: 1px solid #4d1a22;
    color: var(--error);
  }

  .result-label {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: var(--success);
    margin-bottom: 10px;
  }
  .key-display {
    font-family: var(--mono);
    font-size: 12.5px;
    word-break: break-all;
    color: #e8ecf4;
    background: #040d08;
    border: 1px solid #1a4d2a;
    border-radius: 3px;
    padding: 10px 12px;
    cursor: pointer;
    position: relative;
    transition: border-color .15s;
  }
  .key-display:hover { border-color: var(--success); }
  .copy-hint {
    font-size: 10px;
    color: var(--text-dim);
    margin-top: 8px;
    font-family: var(--mono);
  }
  .copy-hint.copied { color: var(--success); }

  .instruction {
    margin-top: 14px;
    font-size: 12px;
    color: var(--text-dim);
    line-height: 1.6;
    font-family: var(--mono);
  }
  .instruction code {
    color: var(--accent);
    background: rgba(0,229,255,.07);
    padding: 1px 5px;
    border-radius: 2px;
  }

  /* ── Footer ── */
  footer {
    margin-top: 40px;
    font-size: 11px;
    font-family: var(--mono);
    color: var(--text-dim);
    letter-spacing: .05em;
  }
</style>
</head>
<body>

<header>
  <div class="badge">Internal Tool · v1</div>
  <h1>Arcade <span>Keygen</span></h1>
  <p>Enter hardware identifiers to generate a hardware-locked <code>license.key</code> for offline deployments.</p>
</header>

<div class="card">
  <div class="card-header">
    <div class="dot r"></div><div class="dot y"></div><div class="dot g"></div>
    ARCADE_CORE_v1 · SHA-256 · HWID
  </div>
  <div class="card-body">

    <div class="field">
      <label for="mobo">Motherboard UUID</label>
      <input id="mobo" type="text" placeholder="e.g. A1B2C3D4-E5F6-7890-ABCD-EF1234567890" autocomplete="off" spellcheck="false">
    </div>

    <div class="field">
      <label for="bios">BIOS Serial</label>
      <input id="bios" type="text" placeholder="e.g. BIOS-SN-00421X" autocomplete="off" spellcheck="false">
    </div>

    <div class="field">
      <label for="mac">MAC Address</label>
      <input id="mac" type="text" placeholder="e.g. AA:BB:CC:DD:EE:FF" autocomplete="off" spellcheck="false">
    </div>

    <button id="genBtn" onclick="generate()">Generate License Key</button>

    <div id="result"></div>
  </div>
</div>

<footer>POST /api/generate-license · 127.0.0.1:8500</footer>

<script>
async function generate() {
  const mobo = document.getElementById('mobo').value.trim();
  const bios = document.getElementById('bios').value.trim();
  const mac  = document.getElementById('mac').value.trim();

  // Clear previous state
  ['mobo','bios','mac'].forEach(id => document.getElementById(id).classList.remove('err'));
  document.getElementById('result').innerHTML = '';

  let valid = true;
  if (!mobo) { document.getElementById('mobo').classList.add('err'); valid = false; }
  if (!bios) { document.getElementById('bios').classList.add('err'); valid = false; }
  if (!mac)  { document.getElementById('mac').classList.add('err');  valid = false; }
  if (!valid) return;

  const btn = document.getElementById('genBtn');
  btn.disabled = true;
  btn.textContent = 'Generating…';

  try {
    const res = await fetch('/api/generate-license', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ motherboard_uuid: mobo, bios_serial: bios, mac_address: mac })
    });
    const data = await res.json();

    if (!res.ok) {
      showError(data.detail || 'Unknown error.');
      return;
    }

    showKey(data.license_key_content);
  } catch (e) {
    showError('Could not reach the server. Is it running?');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate License Key';
  }
}

function showKey(key) {
  document.getElementById('result').innerHTML = `
    <div class="result-box success">
      <div class="result-label">✓ License Key Generated</div>
      <div class="key-display" id="keyBox" title="Click to copy" onclick="copyKey()">${key}</div>
      <div class="copy-hint" id="copyHint">Click key to copy</div>
      <div class="instruction">
        Paste into a plain text file named <code>license.key</code>
        and deploy it alongside the client executable.
      </div>
    </div>`;
}

function showError(msg) {
  document.getElementById('result').innerHTML =
    `<div class="result-box error">✗ ${msg}</div>`;
}

async function copyKey() {
  const key = document.getElementById('keyBox').textContent;
  try {
    await navigator.clipboard.writeText(key);
    const hint = document.getElementById('copyHint');
    hint.textContent = '✓ Copied to clipboard';
    hint.classList.add('copied');
    setTimeout(() => { hint.textContent = 'Click key to copy'; hint.classList.remove('copied'); }, 2000);
  } catch { /* silently fail on non-secure contexts */ }
}

// Allow Enter key to submit
document.addEventListener('keydown', e => { if (e.key === 'Enter') generate(); });
</script>
</body>
</html>"""


# ─── HTTP handler ─────────────────────────────────────────────────────────────

class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # Custom concise logging
        print(f"  [{self.command}] {self.path} → {args[1] if len(args) > 1 else ''}")

    # ── GET / → serve the HTML frontend ──
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = HTML.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self._send_json({"detail": "Not found."}, HTTPStatus.NOT_FOUND)

    # ── POST /api/generate-license ──
    def do_POST(self):
        if self.path != "/api/generate-license":
            self._send_json({"detail": "Not found."}, HTTPStatus.NOT_FOUND)
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            self._send_json({"detail": "Invalid JSON body."}, HTTPStatus.BAD_REQUEST)
            return

        mobo = str(payload.get("motherboard_uuid", "")).strip()
        bios = str(payload.get("bios_serial", "")).strip()
        mac  = str(payload.get("mac_address", "")).strip()

        if not mobo or not bios or not mac:
            self._send_json(
                {"detail": "All hardware identifiers (Motherboard, BIOS, and MAC) must be provided."},
                HTTPStatus.BAD_REQUEST,
            )
            return

        token = calculate_license_hash(mobo, bios, mac)
        self._send_json({
            "status": "success",
            "hardware_received": {"mobo": mobo, "bios": bios, "mac": mac},
            "license_key_content": token,
            "instructions": (
                "Copy the 'license_key_content' value, paste it into a plain text file "
                "named 'license.key', and deploy it next to the client executable."
            ),
        }, HTTPStatus.OK)

    # ── helper ──
    def _send_json(self, data: dict, status: HTTPStatus = HTTPStatus.OK):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    HOST, PORT = "127.0.0.1", 8500
    server = http.server.HTTPServer((HOST, PORT), Handler)
    print(f"""
  ╔══════════════════════════════════════════╗
  ║       Arcade Keygen  ·  stdlib only      ║
  ╠══════════════════════════════════════════╣
  ║  Frontend  →  http://{HOST}:{PORT}      ║
  ║  API       →  POST /api/generate-license ║
  ║  Stop      →  Ctrl-C                     ║
  ╚══════════════════════════════════════════╝
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
from flask import Flask, render_template, request, jsonify, Response
import threading
import time
import random
import os
import traceback

app = Flask(__name__)
LOG_FILE = "/tmp/bot_log.txt"
bot_running = False

def log(msg):
    print(msg, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")
        f.flush()

def clear_log():
    with open(LOG_FILE, "w") as f:
        f.write("")

def run_bot(username, password):
    global bot_running
    bot_running = True
    try:
        from curl_cffi import requests as cf_requests
        from bs4 import BeautifulSoup

        URL = "https://sma.uniguajira.edu.co/smaudg/"

        log("🚀 Iniciando sesión con impersonación de Chrome...")

        # curl_cffi impersona el TLS fingerprint exacto de Chrome
        session = cf_requests.Session(impersonate="chrome124")

        log("🌐 Abriendo sitio...")
        resp = session.get(URL, timeout=30)
        log(f"📄 Status: {resp.status_code}")

        if resp.status_code == 403 or "sorry, you have been blocked" in resp.text.lower():
            log("🚫 Bloqueado. Reintentando con Chrome120...")
            session = cf_requests.Session(impersonate="chrome120")
            resp = session.get(URL, timeout=30)
            log(f"📄 Status reintento: {resp.status_code}")

        if "sorry, you have been blocked" in resp.text.lower():
            log("❌ Cloudflare bloqueó la IP de Railway permanentemente.")
            log("💡 Necesitas proxy residencial para continuar.")
            return

        log("✅ Sitio accedido correctamente")

        # Parsear el HTML para encontrar el formulario
        soup = BeautifulSoup(resp.text, "html.parser")
        form = soup.find("form")

        if not form:
            log("❌ No se encontró formulario en la página.")
            log(f"HTML: {resp.text[:300]}")
            return

        # Obtener action del form
        action = form.get("action", "")
        if not action.startswith("http"):
            from urllib.parse import urljoin
            action = urljoin(URL, action)
        log(f"📋 Form action: {action}")

        # Recopilar todos los campos hidden
        payload = {}
        for inp in form.find_all("input"):
            name  = inp.get("name", "")
            value = inp.get("value", "")
            itype = inp.get("type", "text").lower()
            if name and itype == "hidden":
                payload[name] = value
                log(f"   hidden: {name}={value}")
            elif name and itype not in ["submit","button","checkbox","radio"]:
                log(f"   campo: name='{name}' type='{itype}'")

        # Detectar campos de usuario y contraseña
        codigo_name = None
        pass_name = None
        for inp in form.find_all("input"):
            name  = inp.get("name", "")
            itype = inp.get("type", "text").lower()
            iid   = inp.get("id", "")
            if not codigo_name and any(x in name.lower() or x in iid.lower()
               for x in ["codigo","user","login","cod","cedula","txt"]):
                codigo_name = name
            if not pass_name and (itype == "password" or any(x in name.lower() or x in iid.lower()
               for x in ["pass","contrasena","clave","pwd"])):
                pass_name = name

        # Fallback por posición
        if not codigo_name or not pass_name:
            visible = [i for i in form.find_all("input")
                       if i.get("type","text").lower() not in ["hidden","submit","button","checkbox","radio"]]
            if len(visible) >= 2:
                codigo_name = visible[0].get("name","")
                pass_name   = visible[1].get("name","")
                log(f"⚠️ Fallback: codigo='{codigo_name}' pass='{pass_name}'")

        if not codigo_name or not pass_name:
            log("❌ No se encontraron los campos del formulario.")
            return

        log(f"✅ Campos: codigo='{codigo_name}' pass='{pass_name}'")

        payload[codigo_name] = username
        payload[pass_name]   = password

        # Headers realistas
        headers = {
            "Referer": URL,
            "Origin": "https://sma.uniguajira.edu.co",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        log("🖱️ Enviando formulario de login...")
        time.sleep(random.uniform(1, 2))

        resp2 = session.post(action, data=payload, headers=headers, timeout=30)
        log(f"📄 Status post: {resp2.status_code}")

        src = resp2.text.lower()
        if "logout" in src or "cerrar" in src or "bienvenido" in src or "salir" in src:
            log("🎉 ¡LOGIN EXITOSO!")
        elif "incorrecto" in src or "invalido" in src or "error" in src:
            log("❌ Credenciales incorrectas.")
        else:
            log(f"⚠️ Respuesta desconocida. Primeros 200 chars:")
            log(resp2.text[:200])

    except Exception as e:
        log(f"💥 Error: {str(e)}")
        log(traceback.format_exc())
    finally:
        bot_running = False
        log("__END__")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run", methods=["POST"])
def run():
    global bot_running
    if bot_running:
        return jsonify({"error": "El bot ya está corriendo"}), 400
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    if not username or not password:
        return jsonify({"error": "Ingresa código y contraseña"}), 400
    clear_log()
    thread = threading.Thread(target=run_bot, args=(username, password), daemon=True)
    thread.start()
    return jsonify({"ok": True})

@app.route("/logs")
def logs():
    def generate():
        sent = 0
        deadline = time.time() + 120
        while time.time() < deadline:
            try:
                with open(LOG_FILE, "r") as f:
                    lines = f.readlines()
                new_lines = lines[sent:]
                for line in new_lines:
                    line = line.strip()
                    if line:
                        yield f"data: {line}\n\n"
                        sent += 1
                        if line == "__END__":
                            return
            except:
                pass
            time.sleep(0.5)
    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

if __name__ == "__main__":
    clear_log()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)

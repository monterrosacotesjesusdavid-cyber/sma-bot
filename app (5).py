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
    driver = None
    try:
        from seleniumbase import Driver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        URL = "https://sma.uniguajira.edu.co/smaudg/"

        log("🚀 Iniciando Chrome modo UC...")
        driver = Driver(
            browser="chrome",
            uc=True,
            headless=True,
            no_sandbox=True,
            disable_gpu=True,
        )
        log("✅ Chrome iniciado")

        log("🌐 Abriendo sitio...")
        driver.uc_open_with_reconnect(URL, reconnect_time=6)
        log(f"📄 Título: {driver.title}")

        # Manejar Cloudflare automáticamente
        src = driver.page_source.lower()
        title = driver.title.lower()

        if "sorry, you have been blocked" in src or "you are unable to access" in src:
            log("🚫 IP bloqueada por Cloudflare permanentemente.")
            return

        if "just a moment" in title or "verificaci" in title or "turnstile" in src:
            log("⏳ Cloudflare challenge detectado, resolviendo...")
            try:
                driver.uc_gui_click_captcha()
                time.sleep(4)
                log("✅ Captcha clickeado")
            except Exception as ce:
                log(f"⚠️ No se pudo clickear captcha: {ce}")
            time.sleep(3)

        src = driver.page_source.lower()
        if "sorry, you have been blocked" in src:
            log("🚫 Bloqueado tras intento de captcha.")
            return

        log("✅ Cloudflare superado")
        time.sleep(2)

        # Detectar inputs
        log("🔍 Detectando campos...")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for i, inp in enumerate(inputs):
            log(f"   input[{i}] name='{inp.get_attribute('name')}' type='{inp.get_attribute('type')}' id='{inp.get_attribute('id')}'")

        codigo_field = None
        password_field = None

        for inp in inputs:
            name  = (inp.get_attribute("name") or "").lower()
            iid   = (inp.get_attribute("id") or "").lower()
            itype = (inp.get_attribute("type") or "text").lower()
            if not codigo_field and any(x in name or x in iid for x in ["codigo","user","login","cod","cedula","txt"]):
                codigo_field = inp
            if not password_field and (itype == "password" or any(x in name or x in iid for x in ["pass","contrasena","clave","pwd"])):
                password_field = inp

        if not codigo_field or not password_field:
            visible = [i for i in inputs if (i.get_attribute("type") or "text") not in ["hidden","submit","button","checkbox","radio"]]
            if len(visible) >= 2:
                codigo_field  = visible[0]
                password_field = visible[1]
                log("⚠️ Usando posición: primer y segundo campo visible")

        if not codigo_field or not password_field:
            log("❌ No se encontraron los campos. HTML:")
            log(driver.find_element(By.TAG_NAME, "body").text[:400])
            return

        codigo_field.click()
        codigo_field.clear()
        for char in username:
            codigo_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        log("✍️ Código ingresado")

        time.sleep(random.uniform(0.5, 1.0))

        password_field.click()
        password_field.clear()
        for char in password:
            password_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        log("✍️ Contraseña ingresada")

        time.sleep(random.uniform(0.5, 1.5))

        btn = None
        for b in driver.find_elements(By.TAG_NAME, "input"):
            btype = (b.get_attribute("type") or "").lower()
            bval  = (b.get_attribute("value") or "").lower()
            bname = (b.get_attribute("name") or "").lower()
            if btype in ["submit","button"] or "login" in bval or "ingresar" in bval or "login" in bname:
                btn = b
                break
        if not btn:
            for b in driver.find_elements(By.TAG_NAME, "button"):
                btn = b
                break

        log("🖱️ Haciendo click en Login...")
        if btn:
            btn.click()
        else:
            password_field.send_keys("\n")

        time.sleep(random.uniform(3, 5))

        src = driver.page_source.lower()
        if "logout" in src or "cerrar sesion" in src or "bienvenido" in src or "salir" in src:
            log("🎉 ¡LOGIN EXITOSO!")
        elif "incorrecto" in src or "invalido" in src:
            log("❌ Credenciales incorrectas.")
        else:
            log(f"⚠️ Estado desconocido. URL: {driver.current_url}")

    except Exception as e:
        log(f"💥 Error: {str(e)}")
        log(traceback.format_exc())
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
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

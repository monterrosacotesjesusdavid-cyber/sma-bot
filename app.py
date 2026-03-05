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
        import undetected_chromedriver as uc
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        URL = "https://sma.uniguajira.edu.co/smaudg/"

        log("🚀 Iniciando Chrome...")
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--single-process")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--lang=es-CO,es;q=0.9")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
        options.binary_location = "/usr/bin/google-chrome-stable"
        driver = uc.Chrome(options=options, use_subprocess=True,
                           driver_executable_path="/usr/local/bin/chromedriver")
        log("✅ Chrome iniciado correctamente")

        log("🌐 Abriendo sitio...")
        driver.get(URL)
        time.sleep(random.uniform(3, 5))

        log("⏳ Verificando Cloudflare...")
        start = time.time()
        passed = False
        while time.time() - start < 30:
            title = driver.title.lower()
            if "just a moment" not in title and "verificaci" not in title:
                log("✅ Cloudflare superado")
                passed = True
                break
            try:
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    try:
                        driver.switch_to.frame(iframe)
                        checkbox = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                        if checkbox:
                            checkbox[0].click()
                            log("🖱️ Click en checkbox Cloudflare")
                            time.sleep(random.uniform(2, 4))
                        driver.switch_to.default_content()
                    except:
                        driver.switch_to.default_content()
            except:
                pass
            time.sleep(2)

        if not passed:
            log("❌ No se pudo pasar Cloudflare.")
            return

        time.sleep(2)

        # Detectar todos los inputs disponibles
        log("🔍 Detectando inputs en la página...")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for i, inp in enumerate(inputs):
            name = inp.get_attribute("name") or "sin-nombre"
            itype = inp.get_attribute("type") or "text"
            iid = inp.get_attribute("id") or "sin-id"
            log(f"   input[{i}] name='{name}' type='{itype}' id='{iid}'")

        if not inputs:
            log("⚠️ No se encontraron inputs. HTML del body:")
            body = driver.find_element(By.TAG_NAME, "body").text[:500]
            log(body)
            return

        # Intentar con name, id, o por índice
        codigo_field = None
        password_field = None

        for inp in inputs:
            name = (inp.get_attribute("name") or "").lower()
            iid = (inp.get_attribute("id") or "").lower()
            itype = (inp.get_attribute("type") or "text").lower()

            if any(x in name or x in iid for x in ["codigo", "user", "login", "cod", "cedula", "documento"]):
                codigo_field = inp
                log(f"✅ Campo código encontrado: name='{inp.get_attribute('name')}'")
            elif itype == "password" or any(x in name or x in iid for x in ["pass", "contrasena", "clave", "pwd"]):
                password_field = inp
                log(f"✅ Campo contraseña encontrado: name='{inp.get_attribute('name')}'")

        # Fallback: primer text, primer password
        if not codigo_field or not password_field:
            text_inputs = [i for i in inputs if (i.get_attribute("type") or "text") not in ["hidden", "submit", "button", "checkbox"]]
            if len(text_inputs) >= 2:
                codigo_field = text_inputs[0]
                password_field = text_inputs[1]
                log(f"⚠️ Usando fallback: input[0] y input[1]")
            elif len(text_inputs) == 1:
                log("❌ Solo se encontró 1 input visible. No se puede continuar.")
                return

        # Llenar código
        codigo_field.click()
        codigo_field.clear()
        for char in username:
            codigo_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        log("✍️ Código ingresado")
        time.sleep(random.uniform(0.5, 1.0))

        # Llenar contraseña
        password_field.click()
        password_field.clear()
        for char in password:
            password_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        log("✍️ Contraseña ingresada")
        time.sleep(random.uniform(0.5, 1.5))

        # Buscar botón login
        log("🖱️ Buscando botón Login...")
        btn = None
        for b in driver.find_elements(By.TAG_NAME, "input"):
            btype = (b.get_attribute("type") or "").lower()
            bname = (b.get_attribute("name") or "").lower()
            bval  = (b.get_attribute("value") or "").lower()
            if btype in ["submit", "button"] or "login" in bname or "login" in bval or "ingresar" in bval:
                btn = b
                log(f"✅ Botón encontrado: name='{b.get_attribute('name')}' value='{b.get_attribute('value')}'")
                break

        if not btn:
            # Buscar en <button>
            for b in driver.find_elements(By.TAG_NAME, "button"):
                btn = b
                log(f"✅ Botón <button> encontrado: '{b.text}'")
                break

        if btn:
            btn.click()
        else:
            log("⚠️ No se encontró botón, enviando ENTER")
            password_field.send_keys("\n")

        time.sleep(random.uniform(3, 5))

        page_source = driver.page_source.lower()
        if "logout" in page_source or "cerrar" in page_source or "bienvenido" in page_source or "salir" in page_source:
            log("🎉 ¡LOGIN EXITOSO!")
        elif "incorrecto" in page_source or "contraseña incorrecta" in page_source:
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

from flask import Flask, render_template, request, jsonify, Response
import threading
import queue
import time
import random
import os

app = Flask(__name__)

# Cola para logs en tiempo real
log_queue = queue.Queue()
bot_running = False

def log(msg):
    print(msg)
    log_queue.put(msg)

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
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--lang=es-CO,es;q=0.9")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--single-process")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--ignore-certificate-errors")
        options.binary_location = "/usr/bin/google-chrome-stable"
        driver = uc.Chrome(options=options, use_subprocess=True)

        log(f"🌐 Abriendo {URL}")
        driver.get(URL)
        time.sleep(random.uniform(3, 5))

        # Esperar Cloudflare
        log("⏳ Esperando verificación de Cloudflare...")
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
            log("❌ No se pudo pasar Cloudflare. Intenta de nuevo.")
            return

        time.sleep(random.uniform(1, 2))

        log("🔍 Buscando campos de login...")
        wait = WebDriverWait(driver, 20)
        codigo_field = wait.until(EC.presence_of_element_located((By.NAME, "txtCodigo")))
        time.sleep(random.uniform(0.5, 1.5))
        codigo_field.click()
        codigo_field.clear()
        for char in username:
            codigo_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))

        log("✍️ Código ingresado")
        time.sleep(random.uniform(0.5, 1.0))

        password_field = driver.find_element(By.NAME, "txtContrasena")
        password_field.click()
        password_field.clear()
        for char in password:
            password_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))

        log("✍️ Contraseña ingresada")
        time.sleep(random.uniform(0.5, 1.5))

        log("🖱️ Haciendo click en Login...")
        login_btn = driver.find_element(By.NAME, "btnLogin")
        login_btn.click()
        time.sleep(random.uniform(3, 5))

        page_source = driver.page_source.lower()
        if "logout" in page_source or "cerrar" in page_source or "bienvenido" in page_source:
            log("🎉 ¡LOGIN EXITOSO!")
        elif "incorrecto" in page_source or "error" in page_source:
            log("❌ Credenciales incorrectas. Verifica tu código y contraseña.")
        else:
            log(f"⚠️ Estado desconocido. URL: {driver.current_url}")

    except Exception as e:
        log(f"💥 Error: {str(e)}")
    finally:
        if driver:
            driver.quit()
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
    # Limpiar cola
    while not log_queue.empty():
        log_queue.get()
    thread = threading.Thread(target=run_bot, args=(username, password), daemon=True)
    thread.start()
    return jsonify({"ok": True})

@app.route("/logs")
def logs():
    def generate():
        while True:
            try:
                msg = log_queue.get(timeout=30)
                yield f"data: {msg}\n\n"
                if msg == "__END__":
                    break
            except queue.Empty:
                yield f"data: ⌛ Esperando...\n\n"
    return Response(generate(), mimetype="text/event-stream")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

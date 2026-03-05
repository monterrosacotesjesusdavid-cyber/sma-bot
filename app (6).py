from flask import Flask, render_template, request, jsonify, Response
import threading
import time
import random
import os
import traceback

app = Flask(__name__)
LOG_FILE = "/tmp/bot_log.txt"
bot_running = False

# Proxies de WebShare — formato ip:port:user:pass
PROXIES = [
    "31.59.20.176:6754:pvwatrle:d5aea66wl86v",
    "23.95.150.145:6114:pvwatrle:d5aea66wl86v",
    "198.23.239.134:6540:pvwatrle:d5aea66wl86v",
    "45.38.107.97:6014:pvwatrle:d5aea66wl86v",
    "107.172.163.27:6543:pvwatrle:d5aea66wl86v",
    "198.105.121.200:6462:pvwatrle:d5aea66wl86v",
    "64.137.96.74:6641:pvwatrle:d5aea66wl86v",
    "216.10.27.159:6837:pvwatrle:d5aea66wl86v",
    "142.111.67.146:5611:pvwatrle:d5aea66wl86v",
    "194.39.32.164:6461:pvwatrle:d5aea66wl86v",
]

def log(msg):
    print(msg, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")
        f.flush()

def clear_log():
    with open(LOG_FILE, "w") as f:
        f.write("")

def try_login(username, password, proxy_str):
    """Intenta login con un proxy específico. Retorna True si tuvo éxito."""
    ip, port, user, pwd = proxy_str.split(":")
    proxy_url = f"http://{user}:{pwd}@{ip}:{port}"

    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    URL = "https://sma.uniguajira.edu.co/smaudg/"
    driver = None
    try:
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--single-process")
        options.add_argument("--disable-extensions")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--lang=es-CO,es;q=0.9")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
        options.add_argument(f"--proxy-server={proxy_url}")
        options.binary_location = "/usr/bin/google-chrome-stable"

        driver = uc.Chrome(
            options=options,
            use_subprocess=True,
            driver_executable_path="/usr/local/bin/chromedriver"
        )

        driver.get(URL)
        time.sleep(random.uniform(4, 6))

        # Verificar bloqueo o cloudflare
        src   = driver.page_source.lower()
        title = driver.title.lower()

        if "sorry, you have been blocked" in src or "you are unable to access" in src:
            log(f"   🚫 {ip} — bloqueado por Cloudflare")
            return False, driver

        if "just a moment" in title or "verificaci" in title:
            log(f"   ⏳ {ip} — resolviendo challenge...")
            start = time.time()
            while time.time() - start < 25:
                try:
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    for iframe in iframes:
                        try:
                            driver.switch_to.frame(iframe)
                            cb = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                            if cb:
                                cb[0].click()
                                time.sleep(3)
                            driver.switch_to.default_content()
                        except:
                            driver.switch_to.default_content()
                except:
                    pass
                time.sleep(2)
                title = driver.title.lower()
                src   = driver.page_source.lower()
                if "just a moment" not in title and "verificaci" not in title:
                    break

        src = driver.page_source.lower()
        if "sorry, you have been blocked" in src:
            log(f"   🚫 {ip} — bloqueado tras challenge")
            return False, driver

        log(f"   ✅ {ip} — Cloudflare superado!")

        # Detectar campos
        time.sleep(2)
        inputs = driver.find_elements(By.TAG_NAME, "input")
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

        if not codigo_field or not password_field:
            log(f"   ❌ {ip} — campos no encontrados")
            return False, driver

        # Llenar formulario
        codigo_field.click()
        codigo_field.clear()
        for char in username:
            codigo_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.12))

        time.sleep(0.5)
        password_field.click()
        password_field.clear()
        for char in password:
            password_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.12))

        time.sleep(0.8)

        # Click login
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

        if btn:
            btn.click()
        else:
            password_field.send_keys("\n")

        time.sleep(4)

        src = driver.page_source.lower()
        if "logout" in src or "cerrar" in src or "bienvenido" in src or "salir" in src:
            return True, driver
        elif "incorrecto" in src or "invalido" in src:
            log("   ❌ Credenciales incorrectas")
            return "bad_creds", driver
        else:
            log(f"   ⚠️ Respuesta desconocida en {driver.current_url}")
            return False, driver

    except Exception as e:
        log(f"   💥 Error con {ip}: {str(e).splitlines()[0]}")
        return False, driver
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def run_bot(username, password):
    global bot_running
    bot_running = True
    try:
        proxies = PROXIES.copy()
        random.shuffle(proxies)

        for i, proxy in enumerate(proxies):
            ip = proxy.split(":")[0]
            log(f"🔀 Intentando proxy {i+1}/{len(proxies)}: {ip}...")
            result, _ = try_login(username, password, proxy)

            if result is True:
                log("🎉 ¡LOGIN EXITOSO!")
                return
            elif result == "bad_creds":
                log("❌ Credenciales incorrectas — verifica tu código y contraseña.")
                return
            # Si False, prueba el siguiente proxy

        log("😔 Todos los proxies fueron bloqueados. Intenta más tarde.")

    except Exception as e:
        log(f"💥 Error general: {str(e)}")
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
        deadline = time.time() + 300
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

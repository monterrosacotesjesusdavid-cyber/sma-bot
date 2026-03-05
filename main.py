import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import os

USERNAME = os.environ.get("SMA_USERNAME", "TU_CODIGO")
PASSWORD = os.environ.get("SMA_PASSWORD", "TU_CONTRASENA")
URL = "https://sma.uniguajira.edu.co/smaudg/"

def human_delay(a=1.0, b=3.0):
    time.sleep(random.uniform(a, b))

def get_driver():
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
    driver = uc.Chrome(options=options)
    return driver

def wait_for_cloudflare(driver, timeout=30):
    """Espera a que Cloudflare pase el challenge automáticamente."""
    print("⏳ Esperando Cloudflare...")
    start = time.time()
    while time.time() - start < timeout:
        title = driver.title.lower()
        url = driver.current_url
        # Si ya no estamos en el challenge, avanzamos
        if "just a moment" not in title and "verificaci" not in title:
            print("✅ Cloudflare superado")
            return True
        # Intentar click en el checkbox de Turnstile si aparece
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                try:
                    driver.switch_to.frame(iframe)
                    checkbox = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                    if checkbox:
                        checkbox[0].click()
                        print("🖱️ Click en checkbox Cloudflare")
                        human_delay(2, 4)
                    driver.switch_to.default_content()
                except:
                    driver.switch_to.default_content()
        except:
            pass
        time.sleep(2)
    print("❌ Timeout esperando Cloudflare")
    return False

def do_login(driver):
    print(f"🌐 Abriendo {URL}")
    driver.get(URL)
    human_delay(3, 5)

    # Esperar que pase Cloudflare
    if not wait_for_cloudflare(driver):
        raise Exception("No se pudo pasar Cloudflare")

    human_delay(1, 2)

    # Esperar campos de login
    wait = WebDriverWait(driver, 20)

    print("🔍 Buscando campo Código...")
    codigo_field = wait.until(
        EC.presence_of_element_located((By.NAME, "txtCodigo"))
    )
    human_delay(0.5, 1.5)
    codigo_field.click()
    codigo_field.clear()
    for char in USERNAME:
        codigo_field.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))

    human_delay(0.5, 1.0)

    print("🔍 Buscando campo Contraseña...")
    password_field = driver.find_element(By.NAME, "txtContrasena")
    password_field.click()
    password_field.clear()
    for char in PASSWORD:
        password_field.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))

    human_delay(0.5, 1.5)

    print("🖱️ Haciendo click en Login...")
    login_btn = driver.find_element(By.NAME, "btnLogin")
    login_btn.click()

    human_delay(3, 5)

    # Verificar login exitoso
    current_url = driver.current_url
    page_source = driver.page_source.lower()

    if "logout" in page_source or "cerrar" in page_source or "bienvenido" in page_source:
        print("✅ Login exitoso!")
        return True
    elif "incorrecto" in page_source or "error" in page_source:
        print("❌ Credenciales incorrectas")
        return False
    else:
        print(f"⚠️ Estado desconocido. URL actual: {current_url}")
        return False

def main():
    driver = None
    try:
        driver = get_driver()
        success = do_login(driver)
        if success:
            print("🎉 Bot ejecutado correctamente")
            # Aquí puedes agregar más acciones después del login
            # Ej: navegar a otra página, extraer datos, etc.
        else:
            print("💥 Fallo en el login")
    except Exception as e:
        print(f"💥 Error: {e}")
        raise
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()

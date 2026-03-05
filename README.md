# SMA Uniguajira Bot 🤖

Bot de login automático para `sma.uniguajira.edu.co` usando `undetected-chromedriver` para evadir Cloudflare.

## 🚀 Deploy en Railway

### 1. Sube el proyecto a GitHub
```bash
git init
git add .
git commit -m "first commit"
git remote add origin https://github.com/TU_USUARIO/sma-bot.git
git push -u origin main
```

### 2. Crea proyecto en Railway
- Ve a [railway.app](https://railway.app)
- New Project → Deploy from GitHub repo
- Selecciona este repositorio

### 3. Agrega las variables de entorno en Railway
En tu proyecto → Variables → Add:

| Variable | Valor |
|----------|-------|
| `SMA_USERNAME` | Tu código estudiantil |
| `SMA_PASSWORD` | Tu contraseña |

### 4. Deploy
Railway detecta el `Dockerfile` automáticamente y hace el build.

## 📁 Estructura
```
sma-bot/
├── main.py          # Script principal
├── requirements.txt # Dependencias Python
├── Dockerfile       # Config de contenedor con Chrome
├── railway.toml     # Config de Railway
└── README.md
```

## ⚙️ Cómo funciona
1. Abre Chrome en modo headless (invisible)
2. Navega al sitio
3. Espera/evade el challenge de Cloudflare
4. Llena los campos y hace login
5. Verifica que el login fue exitoso

## 🔧 Agregar acciones post-login
En `main.py`, después de `do_login(driver)`, puedes agregar lo que necesites:
```python
# Navegar a otra página
driver.get("https://sma.uniguajira.edu.co/smaudg/notas")

# Extraer datos
datos = driver.find_element(By.ID, "tabla-notas").text
print(datos)
```

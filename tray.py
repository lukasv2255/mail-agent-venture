import pystray
from PIL import Image, ImageDraw
import threading
import subprocess
import sys
import os

def create_icon():
    img = Image.new("RGB", (64, 64), color=(30, 100, 200))
    draw = ImageDraw.Draw(img)
    # Obálka — jednoduchá ikona emailu
    draw.rectangle((10, 20, 54, 44), outline=(255, 255, 255), width=3)
    draw.line((10, 20, 32, 35), fill=(255, 255, 255), width=2)
    draw.line((54, 20, 32, 35), fill=(255, 255, 255), width=2)
    return img

def run_bot():
    global bot_process
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, "logs", "agent.log")
    os.makedirs(os.path.join(script_dir, "logs"), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as log:
        bot_process = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=script_dir,
            stdout=log,
            stderr=log
        )
        bot_process.wait()

def stop(icon, item):
    if bot_process:
        bot_process.terminate()
    icon.stop()

bot_process = None
threading.Thread(target=run_bot, daemon=True).start()

icon = pystray.Icon(
    "mail_agent",
    create_icon(),
    "Mail Agent běží",
    menu=pystray.Menu(
        pystray.MenuItem("Mail Agent běží ✅", None, enabled=False),
        pystray.MenuItem("Ukončit", stop)
    )
)

icon.run()

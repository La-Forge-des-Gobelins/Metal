import random
from neopixel import NeoPixel
from machine import Pin
import utime
from WebSocketClient import WebSocketClient
from WSclient import WSclient
import uasyncio as asyncio
import math

NUM_LEDS = 41
NEOPIXEL_PIN = Pin(13)
led_strip = NeoPixel(NEOPIXEL_PIN, NUM_LEDS)

# Variables pour le contrôle du fade
fade_running = False
FADE_DURATION = 30  # 40 secondes
current_duration = FADE_DURATION
start_time = 0

WebSocket_URL = "ws://192.168.2.241:8080/metal"
# WebSocket_URL = "ws://192.168.10.250:8080/metal"

RECONNECT_DELAY = 5  # Délai de 5 secondes entre les tentatives de reconnexion
WIFI_RETRY_DELAY = 10  # Délai plus long pour les retentatives WiFi

async def connect_wifi():
    """Fonction dédiée à la connexion WiFi avec retentatives"""
    while True:
        try:
            print("Tentative de connexion WiFi...")
            # ws_client = WSclient("Cudy-EFFC", "33954721", WebSocket_URL)
            ws_client = WSclient("Potatoes 2.4Ghz", "Hakunamatata7342!", WebSocket_URL)
            if ws_client.connect_wifi():
                print("WiFi connecté avec succès")
                return ws_client
            print(f"Échec de connexion WiFi, nouvelle tentative dans {WIFI_RETRY_DELAY} secondes...")
        except Exception as e:
            print(f"Erreur WiFi: {e}")
            print(f"Nouvelle tentative dans {WIFI_RETRY_DELAY} secondes...")
        await asyncio.sleep(WIFI_RETRY_DELAY)

async def connect_websocket(ws_client):
    """Fonction dédiée à la connexion WebSocket"""
    try:
        ws = WebSocketClient(WebSocket_URL)
        if ws.connect():
            print("WebSocket connecté avec succès")
            ws.send("connect")
            # Test visuel de connexion
            for i in range(NUM_LEDS):
                led_strip[i] = (0, 255, 0)  # Vert pour indiquer succès
                led_strip.write()
                await asyncio.sleep_ms(50)
                led_strip[i] = (0, 0, 0)
                led_strip.write()
            return ws
    except Exception as e:
        print(f"Erreur WebSocket: {e}")
        return None

async def setup_connection():
    """Configuration de la connexion avec gestion séparée WiFi/WebSocket"""
    while True:
        try:
            # Étape 1 : Connexion WiFi
            ws_client = await connect_wifi()
            
            # Étape 2 : Connexion WebSocket
            print("Tentative de connexion WebSocket...")
            ws = await connect_websocket(ws_client)
            if ws:
                return ws
            
            print(f"Échec de connexion WebSocket, nouvelle tentative dans {RECONNECT_DELAY} secondes...")
            await asyncio.sleep(RECONNECT_DELAY)
            
        except Exception as e:
            print(f"Erreur de connexion: {e}")
            await asyncio.sleep(RECONNECT_DELAY)

def smooth_transition(x):
    """
    Fonction de lissage avec une courbe plus douce
    Utilise une courbe sinusoïdale modifiée pour une transition plus naturelle
    """
    # Utilisation d'une fonction de lissage cubique
    x = max(0, min(1, x))  # Assure que x est entre 0 et 1
    return x * x * (3 - 2 * x)

def set_color_transition(progress):
    """
    Fait la transition du rouge vif vers le blanc avec une diminution progressive 
    et naturelle de l'intensité
    """
    progress = max(0, min(1, progress))  # Assure que progress est entre 0 et 1
    
    # Calcul de l'intensité globale avec une courbe plus douce
    base_intensity = 1 - (smooth_transition(progress) * 0.7)  # Diminue jusqu'à 30% de l'intensité initiale
    
    # Phase 1 (0-40%): Rouge pur qui diminue en intensité
    # Phase 2 (40-100%): Transition progressive vers le blanc
    if progress < 0.4:
        # Intensité maximale au début, diminution progressive
        normalized_progress = progress / 0.4
        intensity = 1 - (normalized_progress * 0.3)  # Diminue jusqu'à 70% pendant cette phase
        red = int(255 * intensity)
        green = blue = 0
    else:
        # Transition vers le blanc
        normalized_progress = (progress - 0.4) / 0.6  # Normalise de 0 à 1 pour cette phase
        smooth_prog = smooth_transition(normalized_progress)
        
        # Le rouge reste dominant mais diminue progressivement
        red = int(255 * base_intensity)
        
        # Le vert et le bleu augmentent progressivement mais restent toujours légèrement 
        # inférieurs au rouge pour éviter le rose
        white_intensity = smooth_prog * base_intensity
        green = blue = int(red * white_intensity * 0.95)  # 95% du rouge pour garder une teinte chaude
    
    # Appliquer les couleurs à toutes les LEDs
    for i in range(NUM_LEDS):
        led_strip[i] = (red, green, blue)
    led_strip.write()

def reduce_duration():
    global current_duration, start_time
    elapsed_time = utime.time() - start_time
    remaining_time = max(0, current_duration - elapsed_time)
    
    new_remaining_time = max(0, remaining_time - 10)
    
    if remaining_time > 0:
        progress = elapsed_time / current_duration
        current_duration = new_remaining_time + elapsed_time
        start_time = utime.time() - (progress * current_duration)

async def run_main_loop():
    global fade_running, start_time, current_duration
    while True:
        if fade_running:
            elapsed_time = utime.time() - start_time
            if elapsed_time < current_duration:
                progress = elapsed_time / current_duration
                set_color_transition(progress)
            else:
                # Éteindre complètement les LEDs
                fade_running = False
                current_duration = FADE_DURATION
                for i in range(NUM_LEDS):
                    led_strip[i] = (0, 0, 0)
                led_strip.write()
        await asyncio.sleep_ms(10)

async def listen_websocket(ws):
    global fade_running, start_time, current_duration
    connection_alive = True
    while connection_alive:
        try:
            msg = ws.receive()
            if msg is None:
                print("Perte de connexion WebSocket détectée")
                connection_alive = False
                continue
            
            print("Message reçu :", msg)
            
            if msg == "Metal - Fire On":
                print("Starting color transition")
                fade_running = True
                current_duration = FADE_DURATION
                start_time = utime.time()
                set_color_transition(0)
            
            elif msg == "Impact":
                print("Impact")
                if fade_running:
                    reduce_duration()
                    print(f"Temps restant réduit de 10s. Nouveau temps : {current_duration}")
            
            elif msg == "ping":
                ws.send("Metal - pong")
                
            elif msg == "led_blink":
                for i in range(NUM_LEDS):
                    led_strip[i] = (255, 0, 0)
                    led_strip.write()
                    led_strip[i] = (0, 0, 0)
                    led_strip.write()
            
            elif msg == "Metal-Stop":
                fade_running = False
                current_duration = FADE_DURATION
                for i in range(NUM_LEDS):
                    led_strip[i] = (0, 0, 0)
                led_strip.write()
                
        except Exception as e:
            print(f"Erreur WebSocket: {e}")
            connection_alive = False
        await asyncio.sleep_ms(10)

async def main():
    while True:
        try:
            # Tenter d'établir la connexion
            ws = await setup_connection()
            
            # Exécuter les tâches principales une fois connecté
            await asyncio.gather(
                run_main_loop(),
                listen_websocket(ws)
            )
        except Exception as e:
            print(f"Erreur principale: {e}")
        finally:
            # Nettoyage en cas d'erreur
            for i in range(NUM_LEDS):
                led_strip[i] = (0, 0, 0)
            led_strip.write()
            if 'ws' in locals():
                ws.close()
        
        print(f"Perte de connexion, redémarrage dans {RECONNECT_DELAY} secondes...")
        await asyncio.sleep(RECONNECT_DELAY)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        for i in range(NUM_LEDS):
            led_strip[i] = (0, 0, 0)
        led_strip.write()
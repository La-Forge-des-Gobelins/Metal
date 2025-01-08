import random
from neopixel import NeoPixel
from machine import Pin
import utime
from WebSocketClient import WebSocketClient
from WSclient import WSclient
import uasyncio as asyncio

NUM_LEDS = 37
NEOPIXEL_PIN = Pin(13)
led_strip = NeoPixel(NEOPIXEL_PIN, NUM_LEDS)

# Variables pour le contrôle du fade
fade_running = False
current_intensity = 255
FADE_DURATION = 40  # 40 secondes
current_duration = FADE_DURATION  # Durée actuelle qui peut être modifiée
fade_step = 255 / FADE_DURATION
start_time = 0

WebSocket_URL = "ws://192.168.10.31:8080/metal"

def setup_connection():
    ws_client = WSclient("Cudy-EFFC", "33954721", WebSocket_URL)
    try:
        if ws_client.connect_wifi():
            ws = WebSocketClient(WebSocket_URL)
            if ws.connect():
                print("WebSocket connection established")
                ws.send("Métal connecté")
                # Code de test
                for i in range(NUM_LEDS):
                    led_strip[i] = (255, 0, 0)
                    led_strip.write()
                    led_strip[i] = (0, 0, 0)
                    led_strip.write()
                return ws
        return None
    except Exception as e:
        print(f"Connection error: {e}")
        return None

def set_red_intensity(intensity):
    intensity = int(max(0, min(255, intensity)))
    for i in range(NUM_LEDS):
        led_strip[i] = (intensity, 0, 0)
    led_strip.write()

def reduce_duration():
    global current_duration, start_time
    elapsed_time = utime.time() - start_time
    remaining_time = max(0, current_duration - elapsed_time)
    
    # Réduire le temps restant de 10 secondes, minimum 0
    new_remaining_time = max(0, remaining_time - 10)
    
    # Ajuster le temps de début pour maintenir la progression relative
    if remaining_time > 0:
        progress = elapsed_time / current_duration
        current_duration = new_remaining_time + elapsed_time
        # Ajuster le temps de début pour maintenir la même intensité relative
        start_time = utime.time() - (progress * current_duration)

async def run_main_loop():
    global fade_running, current_intensity, start_time, current_duration
    while True:
        if fade_running:
            elapsed_time = utime.time() - start_time
            if elapsed_time < current_duration:
                # Calculer l'intensité en fonction du temps écoulé
                current_intensity = 255 * (1 - elapsed_time / current_duration)
                set_red_intensity(current_intensity)
            else:
                # Arrêter le fade
                fade_running = False
                current_intensity = 0
                current_duration = FADE_DURATION  # Réinitialiser la durée
                set_red_intensity(0)
        await asyncio.sleep_ms(50)

async def listen_websocket(ws):
    global fade_running, current_intensity, start_time, current_duration
    while True:
        try:
            msg = ws.receive()
            print("Message reçu :", msg)
            
            if msg is None:
                continue
            
            if msg == "Metal - Fire On":
                print("red")
                fade_running = True
                current_intensity = 255
                current_duration = FADE_DURATION  # Réinitialiser la durée
                start_time = utime.time()
                set_red_intensity(current_intensity)
                print(f"Intensité actuelle : {current_intensity}")
            
            elif msg == "Impact":
                print("Impact")
                if fade_running:
                    reduce_duration()
                    print(f"Temps restant réduit de 10s. Nouveau temps : {current_duration}")
            
            elif msg == "ping":
                ws.send("Metal - pong")
            
            elif msg == "Metal-Stop":
                fade_running = False
                current_intensity = 0
                current_duration = FADE_DURATION  # Réinitialiser la durée
                set_red_intensity(0)
                
        except Exception as e:
            print(f"WebSocket error: {e}")
            break
        await asyncio.sleep_ms(200)

async def main():
    ws = setup_connection()
    if not ws:
        print("Failed to start - no connection")
        return
    
    try:
        await asyncio.gather(
            run_main_loop(),
            listen_websocket(ws)
        )
    except Exception as e:
        print(f"Error: {e}")
    finally:
        set_red_intensity(0)
        if ws:
            ws.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        set_red_intensity(0)
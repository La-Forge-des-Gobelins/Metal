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
fade_step = 255 / FADE_DURATION  # Diminution par seconde
start_time = 0

WebSocket_URL = "ws://192.168.10.31:8080/step1"

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

async def run_main_loop():
    global fade_running, current_intensity, start_time
    while True:
        if fade_running:
            elapsed_time = utime.time() - start_time
            if elapsed_time < FADE_DURATION:
                # Calculer l'intensité en fonction du temps écoulé
                current_intensity = 255 * (1 - elapsed_time / FADE_DURATION)
                set_red_intensity(current_intensity)
            else:
                # Arrêter le fade après 60 secondes
                fade_running = False
                current_intensity = 0
                set_red_intensity(0)
        await asyncio.sleep_ms(50)

async def listen_websocket(ws):
    global fade_running, current_intensity, start_time
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
                start_time = utime.time()  # Enregistrer le temps de début
                set_red_intensity(current_intensity)
                print(f"Intensité actuelle : {current_intensity}")
            
            
            elif msg == "ping":
                ws.send ("Metal - pong")
                
            
            elif msg == "Metal-Stop":
                fade_running = False
                current_intensity = 0
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
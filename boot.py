import random
from neopixel import NeoPixel
from machine import Pin
import utime
from WebSocketClient import WebSocketClient
from WSclient import WSclient
import uasyncio as asyncio

NUM_LEDS = 20
NEOPIXEL_PIN = Pin(13)
led_strip = NeoPixel(NEOPIXEL_PIN, NUM_LEDS)
fade_running = False
current_intensity = 255
fade_step = 255 / (60 * 20)  # 60 secondes * 20 steps/seconde

WebSocket_URL = "ws://192.168.10.31:8080/step3"

def setup_connection():
    ws_client = WSclient("Cudy-EFFC", "33954721", WebSocket_URL)
    try:
        if ws_client.connect_wifi():
            ws = WebSocketClient(WebSocket_URL)
            if ws.connect():
                print("WebSocket connection established")
                ws.send("Métal connecté")
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
    global fade_running, current_intensity
    while True:
        if fade_running and current_intensity > 0:
            current_intensity = max(0, current_intensity - fade_step)
            set_red_intensity(current_intensity)
            if current_intensity == 0:
                fade_running = False
        await asyncio.sleep_ms(50)

async def listen_websocket(ws):
    global fade_running, current_intensity
    while True:
        try:
            msg = ws.receive()
            if msg == "Metal-Start":
                fade_running = True
                current_intensity = 255
                set_red_intensity(current_intensity)
            elif msg == "Metal-Stop":
                fade_running = False
                current_intensity = 0
                set_red_intensity(0)
        except Exception as e:
            print(f"WebSocket error: {e}")
            break
        await asyncio.sleep_ms(100)

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
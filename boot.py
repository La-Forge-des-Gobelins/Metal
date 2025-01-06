from machine import Pin
import utime
from neopixel import NeoPixel
from WSclient import WSclient
from WebSocketClient import WebSocketClient

# Initialize WebSocket client
ws_client = WSclient("Cudy-EFFC", "33954721", "ws://192.168.10.31:8080/step3")
# ws_client = WSclient("Potatoes 2.4Ghz", "Hakunamatata7342!", "ws://192.168.2.241:8080/step3")

# Configuration du bandeau LED WS2812
LED_PIN = 13  # GPIO où est connecté le bandeau
NUM_LEDS = 30  # Nombre de LEDs dans le bandeau
led_strip = NeoPixel(Pin(LED_PIN), NUM_LEDS)

# Attempt to connect WiFi and WebSocket
def setup_connection():
    try:
        if ws_client.connect_wifi():
            ws = WebSocketClient(ws_client.WEBSOCKET_URL)
            if ws.connect():
                print("WebSocket connection established")
                ws.send("Métal connecté")
                return ws
        print("Failed to establish connection")
        return None
    except Exception as e:
        print(f"Connection error: {e}")
        return None

# Fonction pour allumer ou éteindre tout le bandeau
def set_strip_color(color):
    """
    Met tout le bandeau à une couleur donnée.
    :param color: Tuple RGB, par exemple (255, 0, 0) pour rouge.
    """
    for i in range(NUM_LEDS):
        led_strip[i] = color
    led_strip.write()  # Envoie les couleurs au bandeau
    
# Fonction pour gérer les commandes reçues
def control_led_strip(command):
    try:
        if command.startswith("COLOR:"):
            # Extraire la couleur au format RGB (ex: COLOR:255,0,0)
            _, rgb = command.split(":")
            r, g, b = map(int, rgb.split(","))
            set_strip_color((r, g, b))
            print(f"LED strip set to color: ({r}, {g}, {b})")
        elif command == "OFF":
            set_strip_color((0, 0, 0))  # Éteindre le bandeau
            print("LED strip turned OFF")
        else:
            print(f"Unknown command: {command}")
    except Exception as e:
        print(f"Error processing command: {e}")

# Establish WebSocket connection
ws = setup_connection()

control_led_strip("COLOR:255,0,0")

try:
    while True:
        if ws:
            try:
                # Check for messages from the WebSocket server
                message = ws.receive()
                if message == "Chaud":
                    print(f"Received message: {message}")
                    control_led_strip("ON")  # Control the LED strip based on the message
            except Exception as e:
                print(f"Receive error: {e}")
                ws = setup_connection()  # Attempt to reconnect if receiving fails

        utime.sleep(0.1)  # Short delay to avoid excessive polling

except KeyboardInterrupt:
    print("Exiting program")
finally:
    # Ensure WebSocket is closed and LED strip is off
    if ws:
        ws.close()
    led_strip.value(0)
    print("LED strip turned OFF, program terminated")


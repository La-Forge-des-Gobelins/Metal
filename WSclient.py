import network
import time
import gc
from machine import Pin
from WebSocketClient import WebSocketClient

class WSclient:
    def __init__(self, ssid, password, websocket_url):
        self.WIFI_SSID = ssid
        self.WIFI_PASSWORD = password
        self.WEBSOCKET_URL = websocket_url
        self.led = Pin(19, Pin.OUT)
        self.wlan = None
        self.ws = None

    def connect_wifi(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        print(f'Connecting to network {self.WIFI_SSID}...')

        if not self.wlan.isconnected():
            self.wlan.connect(self.WIFI_SSID, self.WIFI_PASSWORD)
            max_wait = 10
            while max_wait > 0:
                if self.wlan.isconnected():
                    break
                max_wait -= 1
                print('Waiting for connection...')
                time.sleep(1)

        if self.wlan.isconnected():
            print('WiFi connection successful!')
            print('IP Address:', self.wlan.ifconfig()[0])
            return True
        else:
            print('WiFi connection failed')
            return False

    def main(self):
        gc.collect()

        if not self.connect_wifi():
            print("Cannot continue without WiFi connection")
            return

        self.ws = WebSocketClient(self.WEBSOCKET_URL)
        last_message_time = time.time()
        last_check_time = time.time()

        try:
            if self.ws.connect():
                print("Connected to WebSocket server")
                self.ws.socket.setblocking(False)

                while True:
                    current_time = time.time()

                    # Check for messages every 100ms
                    if current_time - last_check_time >= 0.1:
                        try:
                            # Attempt to read socket
                            data = self.ws.socket.recv(1)
                            if data:
                                # Set socket to blocking mode to read full message
                                self.ws.socket.setblocking(True)
                                message = self.ws.receive(first_byte=data)
                                self.ws.socket.setblocking(False)

                                if message:
                                    print("Message received")
                                    if message.lower() == "allumer":
                                        print("================")
                                        print(f"Received message: {message}")
                                        print("================")
                                        self.led.value(1)
                                        time.sleep(5)
                                        self.led.value(0)

                        except OSError as e:
                            if e.args[0] != 11:  # If not EAGAIN
                                raise

                        last_check_time = current_time

                    # Send periodic message every 5 seconds
                    if current_time - last_message_time >= 5:
                        message = f"{current_time}"
                        if self.ws.send(message):
                            print(f"Message sent: {message}")
                            last_message_time = current_time
                        else:
                            print("Message sending error")
                            raise Exception("Sending error")

                    # Small delay to prevent CPU overload
                    time.sleep(0.001)

        except KeyboardInterrupt:
            print("User requested stop")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if self.ws:
                self.ws.close()
                print("WebSocket connection closed")

# Usage
if __name__ == "__main__":
    client = WSclient("Cudy-EFFC", "33954721", "ws://192.168.10.31:8080/step1")
    client.main()

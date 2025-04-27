import cv2
import requests
import pyttsx3
import time
from gpiozero import Button, Buzzer

# Flask Server Details (Laptop IP)
FLASK_SERVER_URL = "flask-server-in-server-device-port/process_image"

# DroidCam Settings (Replace with your DroidCam IP)
DROIDCAM_IP = "droid-cam-ip"
DROIDCAM_PORT = "droid-cam-port"
DROIDCAM_URL = f"http://{DROIDCAM_IP}:{DROIDCAM_PORT}/video"

# GPIO Pin Configurations
BUTTON_PIN = 8  # Button to trigger capture
BUZZER_PIN = 9  # Buzzer to beep

# Initialize GPIO components
button = Button(BUTTON_PIN)
buzzer = Buzzer(BUZZER_PIN)

# Initialize Text-to-Speech
engine = pyttsx3.init()
engine.setProperty('rate', 125)  # Slow down the speech rate
engine.setProperty('volume', 1.0)  # Max volume

def speak(text):
    """Convert text to speech with a delay for clarity."""
    print(f"Speaking: {text}")
    engine.say(text)
    engine.runAndWait()
    time.sleep(1)

def capture_image(cap):
    """Capture image from DroidCam and save it."""
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame.")
        return None
    
    image_path = "captured_image.jpg"
    cv2.imwrite(image_path, frame)
    print(f"Image saved: {image_path}")
    return image_path

def send_image_to_server(image_path):
    """Send the captured image to the Flask server and return the response."""
    try:
        with open(image_path, 'rb') as image_file:
            files = {'image': image_file}
            response = requests.post(FLASK_SERVER_URL, files=files)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("message", "Unknown response from server")
            elif response.status_code == 400:
                return "Error: Server did not receive an image properly"
            elif response.status_code == 500:
                return "Error: Internal server error during analysis"
            else:
                return f"Error: Server returned status code {response.status_code}"
    except Exception as e:
        return f"Error sending image: {str(e)}"

def main():
    cap = cv2.VideoCapture(DROIDCAM_URL)
    if not cap.isOpened():
        print("Error: Could not connect to DroidCam.")
        return
    
    print("Camera started. Press the button to capture an image...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break
        
        cv2.imshow("Live Camera Feed", frame)
        
        if button.is_pressed:
            print("Button pressed! Capturing image...")
            buzzer.on()
            time.sleep(0.3)  # Beep for 300ms
            buzzer.off()
            
            img_path = capture_image(cap)
            if img_path:
                print("Sending image to server for recognition...")
                result_text = send_image_to_server(img_path)
                print(f"Server Response: {result_text}")
                speak(result_text)
            else:
                print("Image capture failed. Try again.")
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("Exiting system.")
    speak("Exiting the system. Goodbye!")

if __name__ == "__main__":
    main()

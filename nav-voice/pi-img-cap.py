import cv2  
import urllib.request  
import numpy as np  
import requests  
import os  
import time  
import RPi.GPIO as GPIO  

# GPIO Pin Configuration
BUTTON_PIN = 8  # Button to capture image
BUZZER_PIN = 9  # Buzzer to beep

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# ? Step 1: Configure Camera Stream & API
URL = "droid-cam-port-and-ip/mjpegfeed"  # Update with your DroidCam IP
IMAGE_PATH = "captured_image.jpg"

API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"
HEADERS = {"Authorization": "Bearer huggingface-auth-token"}  # Replace with your API key

# ? Step 2: Function to Get Caption from Hugging Face API
def get_caption(image_path):
    try:
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
            response = requests.post(API_URL, headers=HEADERS, data=image_bytes)

        response_json = response.json()
        print("? API Response:", response_json)  # Debugging output

        if "error" in response_json:
            print("? API Error:", response_json["error"])
            if "loading" in response_json["error"]:
                print("? Model is still loading. Retrying in 10 seconds...")
                time.sleep(10)
                return get_caption(image_path)  # Retry
            return None

        if isinstance(response_json, list) and "generated_text" in response_json[0]:
            return response_json[0]["generated_text"]
        
        return response_json.get("generated_text", "No caption generated")
    except Exception as e:
        print(f"? Error while processing image: {str(e)}")
        return None

# ? Step 3: Faster TTS using `flite`
def speak_text(text):
    os.system(f'flite -t "{text}"')

# ? Step 4: Capture Video Stream with Lower Resolution
def main():
    stream = urllib.request.urlopen(URL)
    bytes_data = bytes()
    frame_count = 0  # Frame counter

    print("? Press the button to capture an image and caption it. Press 'q' to quit.")

    while True:
        bytes_data += stream.read(1024)
        a = bytes_data.find(b'\xff\xd8')
        b = bytes_data.find(b'\xff\xd9')

        if a != -1 and b != -1:
            jpg = bytes_data[a:b+2]
            bytes_data = bytes_data[b+2:]
            
            # ? Convert frame to OpenCV format
            img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            
            # ? Reduce resolution for better performance
            img = cv2.resize(img, (320, 240))  

            cv2.imshow('DroidCam Feed (Press "q" to Exit)', img)

            frame_count += 1  # Increment frame counter

            # ? Check for button press
            if GPIO.input(BUTTON_PIN) == GPIO.LOW:
                print("? Button pressed! Capturing image...")
                GPIO.output(BUZZER_PIN, GPIO.HIGH)
                time.sleep(0.3)  # Beep for 300ms
                GPIO.output(BUZZER_PIN, GPIO.LOW)
                
                cv2.imwrite(IMAGE_PATH, img)
                print(f"? Image saved as '{IMAGE_PATH}'")
                
                caption = get_caption(IMAGE_PATH)
                if caption:
                    print(f"? Caption: {caption}")
                    speak_text(caption)
                else:
                    print("? Could not generate a caption. Please check the API response.")
                
                time.sleep(1)  # Small delay to prevent multiple captures

            # ? Check for quit command
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("? Exiting...")
                break

    GPIO.cleanup()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

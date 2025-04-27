import cv2
import pytesseract
from gtts import gTTS
import os
import time
from gpiozero import Button, Buzzer

# Configure Tesseract OCR path
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# DroidCam IP and video feed
DROIDCAM_IP = "10.162.166.66"
VIDEO_URL = f"http://{DROIDCAM_IP}:4747/video"

# GPIO Pin Configurations
BUTTON_PIN = 8  # Button to trigger capture
BUZZER_PIN = 9  # Buzzer to beep

# Initialize GPIO components
button = Button(BUTTON_PIN)
buzzer = Buzzer(BUZZER_PIN)

def capture_image(cap):
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame. Check DroidCam connection.")
        return None
    
    img_path = "captured_image.jpg"
    cv2.imwrite(img_path, frame)
    return img_path

def extract_text(img_path):
    img = cv2.imread(img_path)
    text = pytesseract.image_to_string(img)
    return text.strip()

def text_to_speech(text):
    if text:
        tts = gTTS(text=text, lang='en')
        audio_path = "output_audio.mp3"
        tts.save(audio_path)
        
        # Use mpg321 to play the audio on Raspberry Pi
        os.system(f"mpg321 {audio_path}")
        
    else:
        print("No text found in the image.")

def main():
    cap = cv2.VideoCapture(VIDEO_URL)
    if not cap.isOpened():
        print("Failed to open camera stream.")
        return
    
    print("Camera started. Press the button to capture an image...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame.")
            break
        
        cv2.imshow("Live Camera Feed", frame)
        
        if button.is_pressed:
            print("Button pressed! Capturing image...")
            buzzer.on()  # Turn on buzzer
            time.sleep(0.3)  # Beep for 300ms
            buzzer.off()  # Turn off buzzer
            
            img_path = capture_image(cap)
            if img_path:
                extracted_text = extract_text(img_path)
                print("Extracted Text:\n", extracted_text)
                text_to_speech(extracted_text)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

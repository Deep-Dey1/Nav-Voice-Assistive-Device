import RPi.GPIO as GPIO
import time
import subprocess
import os
import signal

def speak(message):
    """Use flite TTS to output a voice message."""
    os.system(f'flite -t "{message}"')

# GPIO Pins for Buttons and LEDs
SCRIPTS = {
    2: ("/home/deep/deep-iot-design-project/image-voice/script.py", 3, 
        "Capture the image of the text to generate the voice result", 
        "Exiting text-to-voice script"),
    
    4: ("/home/deep/deep-iot-design-project/face-recognition/main.py", 5, 
        "Capture the image to identify the persons in front of you", 
        "Exiting the face recognition script"),
    
    6: ("/home/deep/deep-iot-design-project/image-captioning/script-3.py", 7, 
        "Capture the image of the environment to know about it", 
        "Exiting the image captioning script goodbye")
}

# GPIO Setup
GPIO.setmode(GPIO.BCM)
for button, (script, led, _, _) in SCRIPTS.items():
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Button as input with pull-up
    GPIO.setup(led, GPIO.OUT)  # LED as output
    GPIO.output(led, GPIO.LOW)  # Turn off LEDs initially

current_process = None  # Track running process
current_exit_message = None  # Track exit message for current script

def stop_current_process():
    """Stop the currently running script and announce its exit message."""
    global current_process, current_exit_message
    if current_process:
        os.killpg(os.getpgid(current_process.pid), signal.SIGTERM)  # Kill process group
        current_process = None
        if current_exit_message:
            speak(current_exit_message)  # Speak exit message before stopping
            current_exit_message = None
        print("Stopped running script.")

def run_script(script_path, led_pin, start_message, exit_message):
    """Run the given script and turn on the LED with a voice announcement."""
    global current_process, current_exit_message
    
    # Stop any running script before starting a new one
    stop_current_process()
    
    # Turn off all LEDs
    for _, led, _, _ in SCRIPTS.values():
        GPIO.output(led, GPIO.LOW)
    
    # Announce the start message
    speak(start_message)
    
    # Turn on selected LED
    GPIO.output(led_pin, GPIO.HIGH)
    
    print(f"Starting script: {script_path}")
    
    # Store the exit message
    current_exit_message = exit_message
    
    # Run the script in a new process group
    current_process = subprocess.Popen(["python3", script_path], preexec_fn=os.setpgrp)

try:
    while True:
        for button, (script, led, start_msg, exit_msg) in SCRIPTS.items():
            if GPIO.input(button) == GPIO.LOW:  # Button pressed
                run_script(script, led, start_msg, exit_msg)
                time.sleep(0.3)  # Debounce delay

except KeyboardInterrupt:
    stop_current_process()  # Stop any running script
    GPIO.cleanup()  # Cleanup GPIO on exit

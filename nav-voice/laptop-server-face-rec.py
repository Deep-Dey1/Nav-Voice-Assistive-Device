from flask import Flask, request, jsonify
import cv2
import os
from deepface import DeepFace
import numpy as np

app = Flask(__name__)

# Load registered user data
user_data = {}
for file in os.listdir("user_data"):
    if file.endswith(".jpg"):
        user_name = file.split(".")[0]
        user_data[user_name] = f"user_data/{file}"

@app.route('/process_image', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return jsonify({"error": "No file received"}), 400
    
    file = request.files['image']
    image_path = "received_image.jpg"
    file.save(image_path)

    try:
        face_objs = DeepFace.extract_faces(img_path=image_path, detector_backend="mtcnn")
        result_text = "Unknown User"

        for idx, face_obj in enumerate(face_objs):
            face_image = face_obj["face"]
            face_image_path = f"face_{idx + 1}.jpg"
            cv2.imwrite(face_image_path, np.array(face_image * 255, dtype=np.uint8))

            match_found = False
            for user_name, registered_image_path in user_data.items():
                try:
                    result = DeepFace.verify(img1_path=face_image_path, img2_path=registered_image_path, model_name="Facenet", distance_metric="cosine", threshold=0.4)
                    if result["verified"]:
                        result_text = f"Recognized User: {user_name}"
                        match_found = True
                        break
                except Exception as e:
                    print(f"DeepFace error: {str(e)}")

            os.remove(face_image_path)

        os.remove(image_path)
        return jsonify({"message": result_text})

    except Exception as e:
        return jsonify({"error": f"Error during analysis: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

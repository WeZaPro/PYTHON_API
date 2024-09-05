from flask import Flask, request, jsonify, render_template
# from inference_sdk import InferenceHTTPClient
import requests
from PIL import Image
from io import BytesIO
import torch
import easyocr
from fuzzywuzzy import process  # นำเข้า fuzzywuzzy
# from pathlib import Path

app = Flask(__name__)

get_model_id= "lpr-p9o6t/1"
get_api_key="0FXo3Oxzy9kwEkpI1j0u"

# Initialize the client with API details
# CLIENT = InferenceHTTPClient(
#     api_url="https://detect.roboflow.com",
#     api_key=get_api_key
# )

model = torch.hub.load('ultralytics/yolov5', 'custom', path='./custom_model/best.pt')  # Update with your model path


@app.route('/process-image', methods=['POST'])
def process_image():
    data = request.json
    image_url = data.get('image_url')

    # Download the image
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))

    img_rgb = img.convert("RGB")
    img_rgb.save('./temp_image.jpg')

    print("response image",response)

    



    results = model('./temp_image.jpg')

    license_plate_boxes = []
    for box in results.xyxy[0]:  # Assuming you have only one image in the batch

        if box[5] == 0:  # Assuming class 0 is the license plate class
            license_plate_boxes.append(box[:4].tolist())

    if not license_plate_boxes:
        return jsonify({
            'license_plate': 'ไม่พบป้ายทะเบียน',
            'country': 'ไม่พบ'
        })
    
    box = license_plate_boxes[0]
    xmin, ymin, xmax, ymax = map(int, box)
    cropped_img = img_rgb.crop((xmin, ymin, xmax, ymax))
    cropped_img.save('./cropped_plate.jpg')

    # result = CLIENT.infer(cropped_img, model_id=get_model_id)

    # sorted_predictions = sorted(result['predictions'], key=lambda p: p['x'])
  
    # confidence_threshold = 0.5
    # sorted_classes_by_x = [
    #     prediction['class'] for prediction in sorted_predictions 
    #     if prediction['confidence'] > confidence_threshold
    # ]

    return jsonify({
            'license_plate': 'พบป้ายทะเบียน',
            'country': 'พบ'
    })

    # mapped_characters = [class_to_char_mapping[cls] for cls in sorted_classes_by_x]
    # plate_number = ''.join(mapped_characters)
 
    # reader = easyocr.Reader(['th'])
    # ocr_result = reader.readtext('cropped_plate.jpg')
    # ocr_texts = [item[1] for item in ocr_result]
    # filtered_texts = [text for text in ocr_texts if text not in word_list]
    # filtered_texts_not_wordlist = [text for text in ocr_texts if text in word_list]
    # check_country_filter = find_closest_word(ocr_texts, word_list)
    # country = find_closest_word(filtered_texts, word_list)  

    # get_gg_data =""  

    # if get_gg_data:
    #     return jsonify({
    #     'license_plate':plate_number ,
    #     'country':check_country_filter[0],
    #     'status': True
    #     })
    # else:
    #     return jsonify({
    #     'license_plate':plate_number ,
    #     'country':check_country_filter[0],
    #     'status': False
    #     })

    

@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == '__main__':
  app.run(port=5000)

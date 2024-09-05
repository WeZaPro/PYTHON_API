from flask import Flask, request, jsonify, render_template
from inference_sdk import InferenceHTTPClient
import requests
from PIL import Image
from io import BytesIO
import torch
import easyocr
import difflib
from fuzzywuzzy import process  # นำเข้า fuzzywuzzy


app = Flask(__name__)

#ของคนอื่น
# get_model_id="license-plate-ahihihi/1"
# get_api_key="H5p54bphqFH0yJ7VQZgY"
#ขอเรา 
get_model_id= "lpr-p9o6t/1"
get_api_key="0FXo3Oxzy9kwEkpI1j0u"

# Initialize the client with API details
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key=get_api_key
)


# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'custom', path='./custom_model/best.pt')  # Update with your model path

# JSON data containing class-to-character mapping
class_to_char_mapping = {
    "0": "0", "1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", "8": "8", "9": "9",
    "A00": "ก", "A01": "ข", "A02": "ฃ", "A03": "ค", "A04": "ฅ", "A05": "ฆ", "A06": "ง", "A07": "จ",
    "A08": "ฉ", "A09": "ช", "A11": "ฌ", "A12": "ญ", "A13": "ฎ", "A14": "ฏ", "A15": "ฐ", "A17": "ฒ",
    "A18": "ณ", "A19": "ด", "A20": "ต", "A21": "ถ", "A22": "ท", "A23": "ธ", "A24": "น", "A25": "บ",
    "A26": "ป", "A27": "ผ", "A28": "ฝ", "A29": "พ", "A30": "ฟ", "A31": "ภ", "A32": "ม", "A33": "ย",
    "A34": "ร", "A35": "ล", "A36": "ว", "A37": "ศ", "A38": "ษ", "A39": "ส", "A40": "ห", "A41": "ฬ",
    "A42": "อ", "A43": "ฮ"
}

# Predefined list of words to check against
word_list = [
    "กระบี่", "กรุงเทพมหานคร", "กาญจนบุรี", "กาฬสินธุ์", "กำแพงเพชร", "ขอนแก่น", "จันทบุรี", "ฉะเชิงเทรา",
    "ชลบุรี", "ชัยนาท", "ชัยภูมิ", "ชุมพร", "เชียงราย", "เชียงใหม่", "ตรัง", "ตราด", "ตาก", "นครนายก",
    "นครปฐม", "นครพนม", "นครราชสีมา", "นครศรีธรรมราช", "นครสวรรค์", "นนทบุรี", "นราธิวาส", "น่าน",
    "บึงกาฬ", "บุรีรัมย์", "ปทุมธานี", "ประจวบคีรีขันธ์", "ปราจีนบุรี", "ปัตตานี", "พระนครศรีอยุธยา",
    "พะเยา", "พังงา", "พัทลุง", "พิจิตร", "พิษณุโลก", "เพชรบุรี", "เพชรบูรณ์", "แพร่", "ภูเก็ต",
    "มหาสารคาม", "มุกดาหาร", "แม่ฮ่องสอน", "ยโสธร", "ยะลา", "ร้อยเอ็ด", "ระนอง", "ระยอง", "ราชบุรี",
    "ลพบุรี", "ลำปาง", "ลำพูน", "เลย", "ศรีสะเกษ", "สกลนคร", "สงขลา", "สตูล", "สมุทรปราการ",
    "สมุทรสงคราม", "สมุทรสาคร", "สระแก้ว", "สระบุรี", "สิงห์บุรี", "สุโขทัย", "สุพรรณบุรี",
    "สุราษฎร์ธานี", "สุรินทร์", "หนองคาย", "หนองบัวลำภู", "อ่างทอง", "อำนาจเจริญ", "อุดรธานี",
    "อุตรดิตถ์", "อุทัยธานี", "อุบลราชธานี", "เบตง"
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process-image', methods=['POST'])
def process_image():
    data = request.json
    image_url = data.get('image_url')

    

    print("data ",data)
    print("image_url ",image_url)

    # Download the image
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))

    # Convert image to RGB format for YOLOv5
    img_rgb = img.convert("RGB")
    img_rgb.save('temp_image.jpg')

    # Perform object detection using YOLOv5
    results = model('temp_image.jpg')

    # Extract bounding boxes for license plates
    license_plate_boxes = []
    for box in results.xyxy[0]:  # Assuming you have only one image in the batch
        # Format: xmin, ymin, xmax, ymax, confidence, class
        if box[5] == 0:  # Assuming class 0 is the license plate class
            license_plate_boxes.append(box[:4].tolist())

    if not license_plate_boxes:
        return jsonify({
            'formatted_output': 'ไม่พบป้ายทะเบียน',
            'corrected_word': 'ไม่พบ'
        })

    # Process the first detected license plate (if multiple detections, you might want to handle them)
    box = license_plate_boxes[0]
    xmin, ymin, xmax, ymax = map(int, box)
    cropped_img = img_rgb.crop((xmin, ymin, xmax, ymax))
    cropped_img.save('cropped_plate.jpg')

 
    # Roboflow &&&&&&&&&&&
    # Perform inference using your model
    result = CLIENT.infer(cropped_img, model_id=get_model_id)
    print("result >>>>>>> ",result)
    # Sort predictions based on the 'x' coordinate
    sorted_predictions = sorted(result['predictions'], key=lambda p: p['x'])
    print("sorted_predictions >>>>>>> ",sorted_predictions)
    # Extract 'class' values sorted by 'x'

    # sorted_classes_by_x = [prediction['class'] for prediction in sorted_predictions]
    # สมมติว่าคุณต้องการให้ confidence มากกว่า 0.5
    confidence_threshold = 0.5
    sorted_classes_by_x = [
        prediction['class'] for prediction in sorted_predictions 
        if prediction['confidence'] > confidence_threshold
    ]
    # print("sorted_classes_by_x >>>>>>> ",sorted_classes_by_x)
    # Map the sorted classes to their corresponding characters
    mapped_characters = [class_to_char_mapping[cls] for cls in sorted_classes_by_x]
    print("mapped_characters >>>>>>> ",mapped_characters)
    # Concatenate array elements into a single string
    plate_number = ''.join(mapped_characters)
    print("plate_number >>>>>>> ",plate_number)
    # Format the output
    formatted_output = f"เลขทะเบียน : {plate_number}"
    # print("formatted_output >>>>>>> ",formatted_output)
    # Roboflow &&&&&&&&&&&


    # Perform OCR using EasyOCR
    reader = easyocr.Reader(['th'])
    ocr_result = reader.readtext('cropped_plate.jpg')

    # Extract text from OCR results
    ocr_texts = [item[1] for item in ocr_result]
    print("ocr_texts >>>>> ",ocr_texts)

    # Filter out words in ocr_texts that are in word_list
    filtered_texts = [text for text in ocr_texts if text not in word_list]
    print("filtered_texts >>>>> ",filtered_texts)

    filtered_texts_not_wordlist = [text for text in ocr_texts if text in word_list]
    print("filtered_texts_not_wordlist >>>>> ",filtered_texts_not_wordlist)

    check_country_filter = find_closest_word(ocr_texts, word_list)
    print("check_country_filter >>>>> ",check_country_filter[0])
    # print("filtered_texts ",filtered_texts)
    # print("country_texts ",country_texts)

    # corrected_word = find_closest_word(ocr_texts, word_list)
    corrected_word = find_closest_word(filtered_texts, word_list)
    print("corrected_word ",corrected_word)

    # Format the output
    formatted_output = f"เลขทะเบียน : {''.join(filtered_texts)}"

    
    return jsonify({
        # 'formatted_output': ocr_texts,
        # 'formatted_output': formatted_output,
        'formatted_output': f"เลขทะเบียน : {plate_number}" ,
        # 'corrected_word': corrected_word[0] if corrected_word else 'ไม่พบ'
        'corrected_word':  f"จังหวัด : {check_country_filter[0]}"
    })

def find_closest_word(texts, word_list,threshold=40):
    closest_word = None
    closest_text = None
    highest_score = 0
    closest_index = None

    for i, text in enumerate(texts):
        # Find the closest match from word_list using fuzzywuzzy
        match, score = process.extractOne(text, word_list)
        if score >= threshold and score > highest_score:
            highest_score = score
            closest_word = match
            closest_text = text
            closest_index = i  # Update index of the closest match

    return [closest_word, closest_text, closest_index]

    # for i, text in enumerate(texts):
    #     # Find the closest match from word_list
    #     match = difflib.get_close_matches(text, word_list, n=1, cutoff=0.4)
    #     if match:
    #         score = difflib.SequenceMatcher(None, text, match[0]).ratio()
    #         if score > highest_score:
    #             highest_score = score
    #             closest_word = match[0]
    #             closest_text = text
    #             closest_index = i  # Update index of the closest match

    # return [closest_word, closest_text, closest_index]

if __name__ == '__main__':
    app.run(debug=True)

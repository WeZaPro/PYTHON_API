from flask import Flask, request, jsonify, render_template
from inference_sdk import InferenceHTTPClient
import requests
from PIL import Image
from io import BytesIO
import torch
import easyocr
import difflib
from fuzzywuzzy import process  # นำเข้า fuzzywuzzy
import os
# from fastapi import FastAPI

# สร้างแอป FastAPI
# app = FastAPI()
# app = FastAPI(
    
# )

# google sheet START +++++++++++++++++++++++++++++++++++++++++++
# import gspread
# from google.oauth2.service_account import Credentials

# ตั้งค่า Google Sheets API 
# SERVICE_ACCOUNT_FILE = './service_account.json'
# SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# สร้าง credentials ด้วย service account
# credentials = Credentials.from_service_account_file(
#     SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# เปิดใช้งาน Google Sheets API
# gc = gspread.authorize(credentials)
# เปิด Google Sheet ด้วย Spreadsheet ID
# spreadsheet_id = '1CbJ9mcf6U5cK4j6W0NIPmA3KUHrWbDT3yBmQKJmdjBc'  # ใส่ Spreadsheet ID ที่นี่
# spreadsheet = gc.open_by_key(spreadsheet_id)

# เลือก worksheet (sheet)
# worksheet = spreadsheet.sheet1


# ค่าที่ต้องการค้นหา
# search_lpn = ''
# search_country = ''

# # อ่านข้อมูลทั้งหมดจาก worksheet
# all_data = worksheet.get_all_records()
# # ค้นหาค่าที่ตรงตามเงื่อนไข
# found = False


# google sheet END +++++++++++++++++++++++++++++++++++++++++++



app = Flask(__name__)

users = [
    {'id': "Abc1234", 'name': 'ABC', 'token': 'a12345678'},
    {'id': "Abc5678", 'name': 'DEF', 'token': 'b12345678'}
]

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


@app.route('/read-lpr/<string:user_id>', methods=['POST'])
def find_item(user_id):
    # ค้นหาผู้ใช้ที่ตรงกับ user_id
    print("user_id ",user_id)
    try:
        for user in users:
            print("user ",user)
            if user['id'] == user_id:
                # return user
         
                data = request.json
                print("data ",data)

                # ดึงค่าของ plate_image
                plate_image_url = data.get('plate_image')


                token = data.get('token')
                print("token ",token)
 
                filtered_users = [user for user in users if user['id'] == user_id]
    
                # ดึงค่า name จากรายการ filtered_users
                _names = [user['name'] for user in filtered_users]
                # print("names ",_names[0])
                _id = [user['id'] for user in filtered_users]
                # print("names ",_id[0])
                _token = [user['token'] for user in filtered_users]
                print("_token ",_token[0])

                if token == _token[0]:
                    print('The value is token!')
                    # return jsonify(filtered_users)
                    return read_lpr(plate_image_url)
                else:
                    print('The value is not token.')
                    return jsonify({'error': 'token not found'}), 404 
                    # return jsonify({
                    #     'license_plate':"No data" ,
                    #     'country':"No data",
                    #     'status': False
                    # })   


                # if not filtered_users:
                #     return jsonify({'error': '_uid not found'}), 404
                # return jsonify(filtered_users)
                #TODO อ่านทะเบียน
                # return read_lpr(plate_image_url)
            
            return jsonify({'error': 'user not found'}), 404
        

    # except requests.exceptions.RequestException as e:
    #     return jsonify({'error': 'Failed to fetch image URL', 'details': str(e)}), 500
    # except Exception as e:
    #     # จัดการข้อผิดพลาดทั่วไปอื่น ๆ
    #     return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Failed to fetch image", "details": str(e)}), 500
        
  
        
@app.errorhandler(500)
def internal_server_error(e):
    # ส่ง JSON ตอบกลับสำหรับข้อผิดพลาด 500
    return jsonify({'error': 'Internal Server Error', 'message': 'Something went wrong on our end.'}), 500


def read_lpr(plate_image_url):
    
    try:
        # Download the image
        response = requests.get(plate_image_url)
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
                'license_plate': 'ไม่พบป้ายทะเบียน',
                'country': 'ไม่พบ'
            })

        # Process the first detected license plate (if multiple detections, you might want to handle them)
        box = license_plate_boxes[0]
        xmin, ymin, xmax, ymax = map(int, box)
        cropped_img = img_rgb.crop((xmin, ymin, xmax, ymax))
        cropped_img.save('cropped_plate.jpg')

        result = CLIENT.infer(cropped_img, model_id=get_model_id)

        sorted_predictions = sorted(result['predictions'], key=lambda p: p['x'])
        # print("sorted_predictions >>>>>>> ",sorted_predictions)

        confidence_threshold = 0.5
        sorted_classes_by_x = [
            prediction['class'] for prediction in sorted_predictions 
            if prediction['confidence'] > confidence_threshold
        ]

        mapped_characters = [class_to_char_mapping[cls] for cls in sorted_classes_by_x]
        plate_number = ''.join(mapped_characters)
        print("plate_number >>>>>>> ",plate_number)
 
        # Perform OCR using EasyOCR
        reader = easyocr.Reader(['th'])
        ocr_result = reader.readtext('cropped_plate.jpg')

        # Extract text from OCR results
        ocr_texts = [item[1] for item in ocr_result]
        # print("ocr_texts >>>>> ",ocr_texts)

        # Filter out words in ocr_texts that are in word_list
        filtered_texts = [text for text in ocr_texts if text not in word_list]
        # print("filtered_texts >>>>> ",filtered_texts)

        filtered_texts_not_wordlist = [text for text in ocr_texts if text in word_list]
        # print("filtered_texts_not_wordlist >>>>> ",filtered_texts_not_wordlist)

        check_country_filter = find_closest_word(ocr_texts, word_list)


        country = find_closest_word(filtered_texts, word_list)  
        # ไม่ต้องค้นหาข้อมูลใน google sheet
        get_gg_data =""  

        if get_gg_data:
            return jsonify({
            'license_plate':plate_number ,
            'country':check_country_filter[0],
            'status': True
            })
        else:
            return jsonify({
            'license_plate':plate_number ,
            'country':check_country_filter[0],
            'status': False
            })
    except ZeroDivisionError:
    # การจัดการข้อผิดพลาดที่เกิดจากการหารด้วยศูนย์
        return jsonify({'Error: Division by zero is not allowed.'}), 404
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    
    except Exception as e:
        # response = jsonify({"error": "Internal Server Error", "message": str(e)})
        # response.status_code = 500
        return jsonify({'error': "URL ERROR"}), 500



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
            'license_plate': 'ไม่พบป้ายทะเบียน',
            'country': 'ไม่พบ'
        })

    # Process the first detected license plate (if multiple detections, you might want to handle them)
    box = license_plate_boxes[0]
    xmin, ymin, xmax, ymax = map(int, box)
    cropped_img = img_rgb.crop((xmin, ymin, xmax, ymax))
    cropped_img.save('cropped_plate.jpg')

    result = CLIENT.infer(cropped_img, model_id=get_model_id)

    sorted_predictions = sorted(result['predictions'], key=lambda p: p['x'])
    # print("sorted_predictions >>>>>>> ",sorted_predictions)

    confidence_threshold = 0.5
    sorted_classes_by_x = [
        prediction['class'] for prediction in sorted_predictions 
        if prediction['confidence'] > confidence_threshold
    ]

    mapped_characters = [class_to_char_mapping[cls] for cls in sorted_classes_by_x]
    plate_number = ''.join(mapped_characters)
    print("plate_number >>>>>>> ",plate_number)
 
    # Perform OCR using EasyOCR
    reader = easyocr.Reader(['th'])
    ocr_result = reader.readtext('cropped_plate.jpg')

    # Extract text from OCR results
    ocr_texts = [item[1] for item in ocr_result]
    # print("ocr_texts >>>>> ",ocr_texts)

    # Filter out words in ocr_texts that are in word_list
    filtered_texts = [text for text in ocr_texts if text not in word_list]
    # print("filtered_texts >>>>> ",filtered_texts)

    filtered_texts_not_wordlist = [text for text in ocr_texts if text in word_list]
    # print("filtered_texts_not_wordlist >>>>> ",filtered_texts_not_wordlist)

    check_country_filter = find_closest_word(ocr_texts, word_list)


    country = find_closest_word(filtered_texts, word_list)  
    # ไม่ต้องค้นหาข้อมูลใน google sheet
    get_gg_data =""  

    if get_gg_data:
        return jsonify({
        'license_plate':plate_number ,
        'country':check_country_filter[0],
        'status': True
        })
    else:
        return jsonify({
        'license_plate':plate_number ,
        'country':check_country_filter[0],
        'status': False
        })
    



# def find_data_googlesheet(search_lpn,search_country):
#     global worksheet
#     # อ่านข้อมูลทั้งหมดจาก worksheet
#     all_data = worksheet.get_all_records()
#     # ค้นหาค่าที่ตรงตามเงื่อนไข
#     found = False
    
#     # print("search_lpn ",search_lpn)
#     # print("search_country ",search_country)
#     # find data from google sheet
#     for row in all_data:
#         if row['LPN'] == search_lpn and row['COUNTRY'] == search_country:
#             found = True

#             # ดึงค่าแต่ละตัวจากดิกชันนารี
#             id_value = row['ID']
#             lpn_value = row['LPN']
#             country_value = row['COUNTRY']

#             # print(f"id: {id_value}")
#             # print(f"LPN: {lpn_value}")
#             # print(f"COUNTRY: {country_value}")
            

#             if found:
#                 print(f"พบข้อมูล: {row}")
#                 return [id_value,lpn_value,country_value,True]
#             else:
                
#                 id_value = "NO"
#                 lpn_value = "NO"
#                 country_value = "NO"

#                 print("ไม่พบข้อมูลที่ตรงตามเงื่อนไข")
#                 return [id_value,lpn_value,country_value,False]
            
#     #         break
        

#     # if not found:
#     #     print("ไม่พบข้อมูลที่ตรงตามเงื่อนไข")
    

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


# if __name__ == '__main__':
#     app.run(debug=True)

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == '__main__':
    app.run()
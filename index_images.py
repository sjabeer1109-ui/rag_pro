import os 
import ollama 
import json 

def describe_image_for_indexing(image_path):
    """استخدام نموذج Llava لاستخراج محتوى الصورة بدقة."""
    try:
        res = ollama.chat(model='llava', messages=[{
            'role': 'user', 
            'content': 'Extract all text, names, and IDs accurately from this document image.', 
            'images': [image_path]
        }])
        return res['message']['content']
    except Exception as e:
        print(f"خطأ في معالجة الصورة {image_path}: {e}")
        return "غير قادر على معالجة هذه الصورة."

def index_images(image_folder="extracted_images", output_file="image_index.json"):
    """فهرسة الصور وحفظ الوصف في ملف JSON."""
    image_descriptions = {}
    
    if not os.path.exists(image_folder):
        print(f"المجلد {image_folder} غير موجود!")
        return {}

    for filename in os.listdir(image_folder):
        if filename.endswith(".png"):
            path = os.path.join(image_folder, filename)
            print(f"جاري معالجة: {filename}...")
            
            description = describe_image_for_indexing(path)
            image_descriptions[filename] = description
    
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(image_descriptions, f, ensure_ascii=False, indent=4)
        
    print(f"--- تم الفهرسة بنجاح وحفظ النتائج في {output_file} ---")
    return image_descriptions

if __name__ == "__main__":
    index_images()
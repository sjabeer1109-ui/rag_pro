from pdf2image import convert_from_path
import os
import shutil

def extract_images_from_pdf(directory_path, output_folder="extracted_images"):
    # 1. مسار Poppler (تأكد أنه صحيح على جهازك)
    poppler_path = r"C:\Users\sjabe\Desktop\Release-26.02.0-0\poppler-26.02.0\Library\bin"
    
    # 2. تنظيف المجلد عند كل عملية استخراج
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder)
    
    # 3. التحقق مما إذا كان المدخل ملفاً واحداً أو مجلداً
    pdf_files = []
    if os.path.isfile(directory_path) and directory_path.endswith('.pdf'):
        pdf_files.append(directory_path)
    elif os.path.isdir(directory_path):
        for file in os.listdir(directory_path):
            if file.endswith(".pdf"):
                pdf_files.append(os.path.join(directory_path, file))
    
    # 4. المعالجة لكل الملفات المكتشفة
    for pdf_path in pdf_files:
        try:
            print(f"--- جاري معالجة: {pdf_path} ---")
            images = convert_from_path(pdf_path, dpi=70, poppler_path=poppler_path)
            
            for i, image in enumerate(images):
                
                base_name = os.path.basename(pdf_path).replace('.pdf', '')
                image_path = os.path.join(output_folder, f"{base_name}_page_{i + 1}.png")
                image.save(image_path, "PNG")
                
        except Exception as e:
            print(f"خطأ أثناء استخراج الصور من {pdf_path}: {e}")
            
    return output_folder
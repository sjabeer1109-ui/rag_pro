import os
import ollama
import json
import smtplib
from email.message import EmailMessage
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_ollama import ChatOllama
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from image_processor import extract_images_from_pdf

class RAGSystem:
    def __init__(self, file_path):
        self.file_path = file_path
        self.db = None
        self.chain = None
        self.llm = None
        self.image_index = {}
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="question",
            output_key="answer"
        )

    # --- نظام إدارة المهام ---
    def send_task_reminder(self, employee_name, task_name, email):
        try:
            msg = EmailMessage()
            msg['Subject'] = f'تذكير بمهمة: {task_name}'
            msg['From'] = 'zaid.said1109@gmail.com'
            msg['To'] = email
            msg.set_content(f'مرحباً {employee_name}، نود تذكيرك بضرورة إكمال مهمة: {task_name}')

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login('zaid.said1109@gmail.com', 'lcwxidolcaomsfia')
                smtp.send_message(msg)
            return f"تم إرسال الإيميل إلى {employee_name} بنجاح!"
        except Exception as e:
            return f"حدث خطأ أثناء إرسال الإيميل: {e}"

    # --- معالجة الصور ---
    def process_pdf_to_images(self):
        try:
            self.image_folder = extract_images_from_pdf(self.file_path)
        except Exception as e:
            print(f"--- تحذير: فشل استخراج الصور من PDF: {e} ---")

    def index_all_images(self, image_folder="extracted_images"):
        if not os.path.exists(image_folder): return
        
        # 1. تحميل الفهرس الموجود مسبقاً 
        index_file = 'image_index.json'
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    self.image_index = json.load(f)
            except:
                self.image_index = {}
        else:
            self.image_index = {}

        
        images_in_folder = [f for f in os.listdir(image_folder) if f.endswith(".png")]
        
        # معالجة الصور التي ليست في الفهرس فقط
        for filename in images_in_folder:
            if filename in self.image_index:
                continue 
            
            path = os.path.join(image_folder, filename)
            print(f"--- جاري تحليل الصورة الجديدة: {filename} ---")
            try:
                res = ollama.chat(model='llava', messages=[{
                    'role': 'user',
                    'content': 'Extract text, names, and IDs.',
                    'images': [path]
                }])
                self.image_index[filename] = res['message']['content']
                
                # حفظ دوري للفهرس بعد كل صورة (للحماية من التعليق)
                with open(index_file, 'w', encoding='utf-8') as f:
                    json.dump(self.image_index, f, ensure_ascii=False, indent=4)
                    
            except Exception as e:
                print(f"خطأ في معالجة {filename}: {e}")

    # --- إعداد النظام ---
    def switch_model(self, model_name="llama3.1"):
        self.llm = ChatOllama(model=model_name, base_url="http://localhost:11434")
        template = """You are a helpful assistant. Answer in the same language as the question (Arabic or English).
        Context: {context}
        Chat History: {chat_history}
        Question: {question}
        Answer:"""
        QA_CHAIN_PROMPT = PromptTemplate.from_template(template)

        if self.db is not None:
            self.chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.db.as_retriever(),
                memory=self.memory,
                combine_docs_chain_kwargs={"prompt": QA_CHAIN_PROMPT},
                return_source_documents=True
            )

    def ingest_data(self, directory_path):
        if os.path.exists("./chroma_db"):
            import shutil
            try: shutil.rmtree("./chroma_db")
            except: print("--- ملاحظة: قاعدة البيانات قيد الاستخدام ---")

        loader = DirectoryLoader(directory_path, glob="./*.pdf", loader_cls=PyPDFLoader)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = text_splitter.split_documents(documents)

        self.db = Chroma.from_documents(
            chunks,
            HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"),
            persist_directory="./chroma_db"
        )
        self.process_pdf_to_images()
        self.index_all_images()
        self.switch_model("llama3.1")
        print("--- Data indexed successfully! ---")

    def ask(self, question):
        
        if self.chain:
            result = self.chain.invoke({"question": question})
            return f"{result['answer']}"
        return "النظام يحتاج ترتيب الملفات أولاً."
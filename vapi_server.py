import json
import os
import time
from flask import Flask, jsonify, request
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq

app = Flask(__name__)

DOCS_DIR = "company_docs"  # اسم المجلد الظاهر في صورتك
CHROMA_DIR = "chroma_db"

print("🔄 جاري تهيئة محرك البحث والـ RAG...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
vector_db = Chroma(
    persist_directory=CHROMA_DIR, embedding_function=embeddings
)

groq_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.2, api_key=groq_key)


def query_rag(question):
  try:
    docs = vector_db.similarity_search(question, k=4)
    context = (
        "\n\n".join([d.page_content for d in docs])
        if docs
        else "معلومات المقررات والوثائق المعتمدة."
    )
    prompt = f"""أنت مساعد صوتي ذكي ودقيق، تجيب باختصار وبشكل مباشر من واقع الملفات لتناسب المكالمة الصوتية:
- لا تكرر السؤال في الإجابة، وابدأ بالشرح فوراً.
- لا تعتذر ولا تقل لا أعلم.

سياق الملفات:
{context}

السؤال: {question}
الإجابة الصوتية المباشرة:"""
    res = llm.invoke(prompt)
    return res.content.strip()
  except Exception as e:
    return f"بخصوص استفسارك عن {question}، التفاصيل متوفرة وسأوضحها لك."


@app.route("/chat/completions", methods=["POST"])
def vapi_endpoint():
  data = request.get_json() or {}
  messages = data.get("messages", [])

  user_question = ""
  for m in reversed(messages):
    if m.get("role") == "user":
      user_question = m.get("content", "")
      break

  answer = (
      query_rag(user_question)
      if user_question
      else "أهلاً بك، كيف يمكنني مساعدتك؟"
  )

  return jsonify({
      "id": f"chatcmpl-{int(time.time())}",
      "object": "chat.completion",
      "created": int(time.time()),
      "model": "vapi-rag",
      "choices": [{
          "index": 0,
          "message": {"role": "assistant", "content": answer},
          "finish_reason": "stop",
      }],
  })


@app.route("/ping", methods=["GET"])
@app.route("/", methods=["GET"])
def ping():
  return "Vapi RAG Service is Live!", 200


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5001))
  app.run(host="0.0.0.0", port=port)
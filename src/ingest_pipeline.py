from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline, IngestionCache
from llama_index.core.node_parser import TokenTextSplitter
from llama_index.core.extractors import SummaryExtractor
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
import openai
import streamlit as st
import requests
import base64
import json
from src.global_settings import STORAGE_PATH, FILES_PATH, CACHE_FILE
from src.prompts import CUSTORM_SUMMARY_EXTRACT_TEMPLATE

openai.api_key = st.secrets.openai.OPENAI_API_KEY
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.2)

def update_github_file(file_path, content, message):
    token = st.secrets["github"]["Githup_API_KEY"]
    repo = "NguyenHuy190303/Mental-Care-AI"
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"

    # Lấy thông tin file hiện tại
    response = requests.get(url, headers={"Authorization": f"token {token}"})
    response_json = response.json()
    sha = response_json["sha"]

    # Mã hóa nội dung file mới
    encoded_content = base64.b64encode(content.encode()).decode()

    # Tạo payload để cập nhật file
    data = {
        "message": message,
        "content": encoded_content,
        "sha": sha
    }

    # Gửi yêu cầu cập nhật file
    response = requests.put(url, headers={"Authorization": f"token {token}"}, data=json.dumps(data))
    if response.status_code == 200:
        st.success("File updated successfully on GitHub!")
    else:
        st.error("Failed to update file on GitHub.")

def save_cache_to_github():
    file_path = CACHE_FILE
    with open(file_path, "r") as file:
        content = file.read()
    message = "Update cache file"
    update_github_file(file_path, content, message)

def ingest_documents():
    # Load documents, easy but we can't move data or share for another device.
    # Because document id is root file name when our input is a folder.
    # documents = SimpleDirectoryReader(
    #     STORAGE_PATH, 
    #     filename_as_id = True
    # ).load_data()

    documents = SimpleDirectoryReader(
        input_files=FILES_PATH, 
        filename_as_id = True
    ).load_data()
    for doc in documents:
        print(doc.id_)
    
    try: 
        cached_hashes = IngestionCache.from_persist_path(
            CACHE_FILE
            )
        print("Cache file found. Running using cache...")
    except:
        cached_hashes = ""
        print("No cache file found. Running without cache...")
    pipeline = IngestionPipeline(
        transformations=[
            TokenTextSplitter(
                chunk_size=512, 
                chunk_overlap=20
            ),
            SummaryExtractor(summaries=['self'], prompt_template=CUSTORM_SUMMARY_EXTRACT_TEMPLATE),
            OpenAIEmbedding()
        ],
        cache=cached_hashes
    )
   
    nodes = pipeline.run(documents=documents)
    pipeline.cache.persist(CACHE_FILE)
    
    # Gọi hàm save_cache_to_github() để cập nhật cache lên GitHub
    save_cache_to_github()
    
    return nodes
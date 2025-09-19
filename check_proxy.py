import os
import httpx
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
proxy = os.getenv("OPENAI_PROXY")

print("API key:", bool(api_key))
print("Proxy:", proxy)

# ⚠️ В httpx>=0.28 используется параметр proxy (единственное число)
client = OpenAI(
    api_key=api_key,
    http_client=httpx.Client(proxy=proxy, timeout=15.0)
)

try:
    models = client.models.list()
    print("✅ Успех, моделей получено:", len(models.data))
except Exception as e:
    print("❌ Ошибка:", e)

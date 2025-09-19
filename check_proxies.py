import os, time
import httpx
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
assert API_KEY, "Нет OPENAI_API_KEY в .env"

def test_proxy(proxy: str) -> tuple[bool, str]:
    try:
        client = OpenAI(
            api_key=API_KEY,
            http_client=httpx.Client(proxy=proxy, timeout=12.0)
        )
        t0 = time.time()
        _ = client.models.list()     # лёгкий запрос
        dt = time.time() - t0
        return True, f"OK ({dt:.2f}s)"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

with open("proxies.txt", "r", encoding="utf-8") as f:
    candidates = [line.strip() for line in f if line.strip() and not line.startswith("#")]

print(f"Протестируем {len(candidates)} прокси...")
best = None
for p in candidates:
    ok, msg = test_proxy(p)
    print(f"{p}  ->  {msg}")
    if ok and best is None:
        best = p

if best:
    print("\n✅ Нашли рабочий прокси!")
    print("Поставь в .env строку:\nOPENAI_PROXY=" + best)
else:
    print("\n❌ Ни один из прокси не прошёл. Возьми другой список или платный SOCKS5/HTTPS.")

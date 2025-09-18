from dotenv import load_dotenv
import os

load_dotenv()

print("BOT_TOKEN:", os.getenv("BOT_TOKEN"))
print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY")[:10], "...")  # только первые 10 символов

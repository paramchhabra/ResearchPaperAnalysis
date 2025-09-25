from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL="mongodb://localhost:27017/rp"
client = AsyncIOMotorClient(MONGO_URL)

db = client.paperanalysis
login_collection = db.logincreds
chat_collections = db.chats
vector_db_pdf = db.paper_id
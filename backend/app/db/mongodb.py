import logging
import motor.motor_asyncio

logger = logging.getLogger(__name__)

class Database:
    client: motor.motor_asyncio.AsyncIOMotorClient = None
    db = None

db = Database()

async def connect_to_mongo():
    logger.info("Đang kết nối tới MongoDB...")
    mongo_url = "mongodb://localhost:27017" # Dùng localhost cho môi trường phát triển cục bộ
    db.client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
    db.db = db.client.nales_it
    logger.info("Kết nối MongoDB thành công!")

async def close_mongo_connection():
    logger.info("Đóng kết nối MongoDB...")
    if db.client:
        db.client.close()
        logger.info("Đã đóng kết nối MongoDB.")

def get_database() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    return db.db

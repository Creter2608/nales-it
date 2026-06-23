import logging
import motor.motor_asyncio

logger = logging.getLogger(__name__)

class Database:
    client: motor.motor_asyncio.AsyncIOMotorClient = None
    db = None

db = Database()

async def connect_to_mongo():
    logger.info("Đang kết nối tới MongoDB...")
    from app.core.config import settings
    mongo_url = settings.MONGODB_URI
    try:
        db.client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=2000)
        await db.client.server_info() # Kiểm tra kết nối nhanh
        db.db = db.client[settings.DATABASE_NAME]
        logger.info("Kết nối MongoDB thành công!")
    except Exception as e:
        logger.warning("Không thể kết nối MongoDB. Hệ thống sẽ tự động chuyển sang chế độ Mock DB (Bộ nhớ tạm).")
        db.client = None
        db.db = None

async def close_mongo_connection():
    logger.info("Đóng kết nối MongoDB...")
    if db.client:
        db.client.close()
        logger.info("Đã đóng kết nối MongoDB.")

def get_database() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    return db.db

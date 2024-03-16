import logging  

from pyrogram import Client 

from telegram.ext import Application
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)

logging.getLogger("apscheduler").setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger("pyrate_limiter").setLevel(logging.ERROR)
LOGGER = logging.getLogger(__name__)

OWNER_ID = "5116239739"
sudo_users = ["5116239739", "6590287973"]
GROUP_ID = "-1002010986967"
TOKEN = "6770670571:AAFiM9-vMtWJMic2L4OUZEZs39l_hOvZO_o"
mongo_url = "mongodb+srv://tiwarireeta004:peqxLEd36RAg7ors@cluster0.furypd3.mongodb.net/?retryWrites=true&w=majority"
PHOTO_URL = ["https://telegra.ph/file/a17bbdf36197b0f0eb2c1.jpg", "https://telegra.ph/file/4754711cd88be32baf5b4.jpg", "https://telegra.ph/file/46b1151c6088fabc62250.jpg", "https://telegra.ph/file/4ed692d4e678216f87083.jpg"]
SUPPORT_CHAT = "welovewesimp"
UPDATE_CHAT = "Anime Girl trade and Gift"
BOT_USERNAME = "Seducer_charm_bot"
CHARA_CHANNEL_ID = "-1002010986967"
api_id = "20457610"
api_hash = "b7de0dfecd19375d3f84dbedaeb92537"

application = Application.builder().token(TOKEN).build()
Grabberu = Client("Grabber", api_id, api_hash, bot_token=TOKEN)
client = AsyncIOMotorClient(mongo_url)
db = client['Character_catcher']
collection = db['anime_characters']
user_totals_collection = db['user_totals']
user_collection = db["user_collection"]
group_user_totals_collection = db['group_user_total']
top_global_groups_collection = db['top_global_groups']

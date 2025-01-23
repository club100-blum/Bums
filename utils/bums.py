import asyncio
import random

from aiohttp import ClientSession
import aiohttp

from data import config
from utils.core import logger
from utils.telegram import AccountInterface
import urllib.parse
def gen_xapi(lid=None, mid=None, appid=None):
    return f"{lid}:{mid}:{appid}:{str(random.random())}"
headers = {
    "Host": "api.bums.bot",
    "Sec-Ch-Ua": '"Android WebView";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
    "Accept-Language": "en",
    "Sec-Ch-Ua-Mobile": "?1",
    "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.193 Mobile Safari/537.36 Telegram-Android/11.3.3 (Samsung SM-G977N; Android 7.1.2; SDK 25; LOW)",
    "Accept": "application/json, text/plain, */*",
    "Sec-Ch-Ua-Platform": '"Android"',
    "Origin": "https://app.bums.bot",
    "X-Requested-With": "org.telegram.messenger",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://app.bums.bot/",
    "Accept-Encoding": "gzip, deflate, br"
}
def convert_to_url_encoded(data: str) -> str:

    parts = data.split('&')
    parsed_data = {}

    for part in parts:
        key, value = part.split('=', 1)
        if key == "user":
            parsed_data[key] = urllib.parse.quote(value)
        else:
            parsed_data[key] = value

    encoded_data = "&".join([f"{key}={value}" for key, value in parsed_data.items()])
    return encoded_data

class RefCodeError(Exception):
    pass

class AccountUsedError(Exception):
    pass

class BumsBot:
    def __init__(
            self,
            account: AccountInterface,
            session: ClientSession
            ):
        self.account = account
        self.session = session

    async def logout(self):

        await self.session.close()


    async def login(self,invite_id):

        try:
            data=await self.account.get_tg_web_data()
            encoded_data = convert_to_url_encoded(data)

            data = {
                "invitationCode": f'{invite_id}',
                "initData": encoded_data
            }

            resp = await self.session.post("https://api.bums.bot/miniapps/api/user/telegram_auth",
                                           data=data,headers=headers,ssl=False)
            resp_json = await resp.json()
            auth_token=resp_json['data']['token']
            self.session.headers['Authorization'] = "Bearer " + auth_token
            return auth_token
        except Exception as err:
            logger.info(f"{err}")

            return False

    async def user_data(self):

        response = await self.session.get('https://api.bums.bot/miniapps/api/user_game_level/getGameInfo',headers=headers,ssl=False)
        rer=await response.json()
        return rer

    async def sign_in_data(self):
        response = await self.session.get( url="https://api.bums.bot/miniapps/api/sign/getSignLists",
                                           headers=headers,ssl=False)
        rer=await response.json()
        return rer

    async def sign_in(self):
        web_boundary = {
            "": "undefined"
        }
        response = await self.session.post( url="https://api.bums.bot/miniapps/miniapps/api/sign/sign",
                                           headers=headers,data=web_boundary,ssl=False)
        rer=await response.text()
        return rer

    async def box_info(self):

        response = await self.session.get( url="https://api.bums.bot/miniapps/api/prop_shop/Lists?showPages=spin&page=1&pageSize=10",
                                           headers=headers,ssl=False)
        rer=await response.json()
        return rer

    async def open_box(self):
        web_boundary = {
            "count": 1,
            "propId": 500010001
        }
        response = await self.session.post(
            url="https://api.bums.bot/miniapps/api/game_spin/Start",data=web_boundary,
            headers=headers, ssl=False)
        rer = await response.json()
        return rer
    async def get_tap_info(self,nickname):
        user_data = await self.user_data()

        if not user_data or user_data.get('code') != 0:
            logger.error(f"{nickname} | Unknown error while collecting User Data!")
            return None

        try:
            prop_info = user_data['data'].get('propInfo')
            auto_click = False
            if prop_info:
                auto_click = any(prop.get('source') == 'autoClick' for prop in prop_info)
            tap_data = {
                "balance": int(user_data['data']['gameInfo'].get('coin', 0)),
                "todayCoin": int(user_data['data']['gameInfo'].get('todayCollegeCoin', 0)),
                "todayCoinLimit": int(user_data['data']['gameInfo'].get('todayMaxCollegeCoin', 0)),
                "leftEnergy": int(user_data['data']['gameInfo'].get('energySurplus', 0)),
                "totalEnergy": int(user_data['data']['tapInfo']['energy'].get('value', 0)),
                "recovery": int(user_data['data']['tapInfo']['recovery'].get('value', 0)),
                "tap": int(user_data['data']['tapInfo']['tap'].get('value', 0)),
                "bonusChance": int(user_data['data']['tapInfo']['bonusChance'].get('value', 0)),
                "bonusRatio": int(user_data['data']['tapInfo']['bonusRatio'].get('value', 0)),
                "collectSeqNo": int(user_data['data']['tapInfo']['collectInfo'].get('collectSeqNo', 0)),
                "autoClick": auto_click
            }
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"{nickname} | Error parsing tap data: {e}")
            return None

        return tap_data
    async def submit_taps(self,collect_seq, taps_amount, hashCode):
        web_boundary = {
            "hashCode": hashCode,
            "collectSeqNo": collect_seq,
            "collectAmount": taps_amount
        }
        response = await self.session.post(
            url="https://api.bums.bot/miniapps/api/user_game/collectCoin",data=web_boundary,
            headers=headers, ssl=False)
        rer = await response.json()
        return rer
    async def get_tasklist(self):

        response = await self.session.get(
            url="https://api.bums.bot/miniapps/api/task/lists",
            headers=headers, ssl=False)
        rer = await response.json()
        return rer
    async def done_task(self,task_id,pwd=None):
        urlencoded_data = {
            "id": task_id
        }
        if pwd:
            urlencoded_data["pwd"] = pwd

        response = await self.session.post(
            url="https://api.bums.bot/miniapps/api/task/finish_task",data=urlencoded_data,
            headers=headers, ssl=False)
        rer = await response.json()
        return rer
    async def spin_info(self):
        response = await self.session.get(
            url="https://api.bums.bot/miniapps/api/game_slot/stamina",
            headers=headers, ssl=False)
        rer = await response.json()
        return rer

    async def upgrade_tap(self,card_type):
        web_boundary = {
            "type": card_type
        }
        response = await self.session.post(
            url="https://api.bums.bot/miniapps/api/user_game_level/upgradeLeve",
            headers=headers,data=web_boundary, ssl=False)
        rer = await response.json()
        return rer

    async def get_tap_cards(self):
        response = await self.session.post(
            url="https://api.bums.bot/miniapps/api/mine/getMineLists",
            headers=headers, ssl=False)
        rer = await response.json()
        return rer

    async def upgrade_mine(self,mineId):
        web_boundary = {
            "mineId": mineId
        }
        response = await self.session.post(
            url="https://api.bums.bot/miniapps/api/mine/getMineLists",data=web_boundary,
            headers=headers, ssl=False)
        rer = await response.json()
        return rer

    async def leave_gang(self):
        response = await self.session.get(
            url="https://api.bums.bot/miniapps/api/gang/gang_leave",
            headers=headers, ssl=False)
        rer = await response.json()
        return rer

    async def get_gang_list(self):
        web_boundary = {
            "boostNum": 100,
            "powerNum": 0
        }
        response = await self.session.post(
            url="https://api.bums.bot/miniapps/api/gang/gang_lists",data=web_boundary,
            headers=headers, ssl=False)
        rer = await response.json()
        return rer

    async def join_gang(self):
        web_boundary = {
            "name": config.GANG_USERNAME
        }
        response = await self.session.post(
            url="https://api.bums.bot/miniapps/api/gang/gang_join",data=web_boundary,
            headers=headers, ssl=False)
        rer = await response.json()
        return rer

    async def combo_details(self):

        response = await self.session.get(
            url="https://api.bums.bot/miniapps/api/mine_active/getMineAcctiveInfo",
            headers=headers, ssl=False)
        rer = await response.json()
        return rer

    async def submit_combo(self,one,two,three):
        web_boundary = {
            "cardIdStr": f"{one},{two},{three}"
        }

        response = await self.session.post(
            url="https://api.bums.bot/miniapps/api/mine_active/JoinMineAcctive",data=web_boundary,
            headers=headers, ssl=False)
        rer = await response.json()
        return rer

    async def start_spin(self,count):
        web_boundary = {
            "count": count
        }

        response = await self.session.post(
            url="https://api.bums.bot/miniapps/api/game_slot/start",data=web_boundary,
            headers=headers, ssl=False)
        rer = await response.json()
        return rer





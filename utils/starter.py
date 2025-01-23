import asyncio
from asyncio import sleep, Semaphore
from random import uniform
from typing import Union
import random
import aiohttp
from aiohttp_proxy import ProxyConnector
import re
from .agents import generate_random_user_agent
from data import config
from utils.bums import BumsBot
from utils.core import logger
from utils.helper import format_duration
from utils.telegram import AccountInterface
from utils.proxy import to_url
import hashlib
from pyrogram.errors import (
    Unauthorized, UserDeactivated, AuthKeyUnregistered, UserDeactivatedBan,
    AuthKeyDuplicated, SessionExpired, SessionRevoked, FloodWait, UserAlreadyParticipant
)
from pyrogram.raw import types
from pyrogram.raw import functions
import json

def combo_answer(method='get'):
    try:
        with open("./combo.json", "r", encoding='utf8') as file:
            data = json.load(file)

        if method == 'get':
            if 'combo' in data and len(data['combo']) == 3:
                return data['combo']
            return None

        elif method == 'wrong':
            data["combo"] = []

            with open("./combo.json", "w", encoding='utf8') as file:
                json.dump(data, file, indent=4)
            return None
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def count_spin(value):
    valid_values = [1, 2, 3, 5, 10, 50]
    return max([v for v in valid_values if v <= value], default=0)

async def get_profit_card(cards):

    for card in cards:
        card["nextLevelCost"] = int(card["nextLevelCost"])
        card["perHourReward"] = int(card["perHourReward"])
        card["nextPerHourReward"] = int(card["nextPerHourReward"])

    most_profitable_card = None
    highest_ratio = float('-inf')

    for card in cards:
        profit_increase = card["nextPerHourReward"] - card["perHourReward"]
        cost = card["nextLevelCost"]

        if cost > 0:
            ratio = profit_increase / cost

            if ratio > highest_ratio:
                highest_ratio = ratio
                most_profitable_card = card

    return most_profitable_card
def card_details(card_id):
    try:
        with open("./card-list.json", "r", encoding='utf8') as file:
            data = json.load(file)
            if str(card_id) in data:
                title = data[str(card_id)].get("title", "No title available")
                description = data[str(card_id)].get(
                    "desc", "No description available")
                return [title, description]
            else:
                return [card_id, "ID not found"]
    except FileNotFoundError:
        return [card_id, "File not found"]
    except json.JSONDecodeError:
        return [card_id, "Error reading JSON"]

try:
    from aiocfscrape import CloudflareScraper
    Session = CloudflareScraper
except:
    logger.info("Error when importing aiocfscrape.CloudflareScraper, using aiohttp.ClientSession instead")
    Session = aiohttp.ClientSession

def generate_taps(tap_value, left_energy, bonus_chance, bonus_multiplier):
    if tap_value < left_energy:
        gain = False
        if tap_value * bonus_multiplier / 100 <= left_energy:
            gain = random.randint(0, 100) <= bonus_chance / 100
            tap_value = tap_value * bonus_multiplier / 100 if gain else tap_value
            return int(tap_value)
        return 0

def tapHash(taps_amount, collect_seq):
    secretData = str(taps_amount) + str(collect_seq) + \
        "7be2a16a82054ee58398c5edb7ac4a5a"

    hashCode = hashlib.md5(secretData.encode('utf-8')).hexdigest()

    return hashCode


def fnum(number):
    try:
        number = float(number)
    except ValueError:
        return number

    return (
        f"{number / 1e9:.1f}B" if number >= 1e9 else
        f"{number / 1e6:.1f}M" if number >= 1e6 else
        f"{number / 1e3:.1f}K" if number >= 1e3 else
        str(number)
    )

sem = Semaphore(config.ACCOUNT_PER_ONCE)
async def start(account: AccountInterface):
    sleep_dur = 0
    while True:
        await sleep(sleep_dur)
        async with sem:
            proxy = account.get_proxy()
            if proxy is None:
                connector = None
            else:
                connector = ProxyConnector.from_url(to_url(proxy))
            async with Session(headers={'User-Agent': generate_random_user_agent(device_type='android',
                                                                                        browser_type='chrome')},
                                        timeout=aiohttp.ClientTimeout(total=60), connector=connector) as session:
                try:
                    bums = BumsBot(account=account, session=session)
                    await sleep(uniform(*config.DELAYS['ACCOUNT']))
                    a=await bums.login(config.REF_KEY)
                    user_data=await bums.user_data()
                    if not user_data:
                        logger.info(f"Reconnecting in {format_duration(config.ITERATION_DURATION)}...")
                        await asyncio.sleep(delay=config.ITERATION_DURATION)
                        break
                    nickname=user_data['data']['userInfo']['nickName']
                    logger.success(f"{nickname} | 📦 Login Successful")


                    coin = int(user_data['data']['gameInfo'].get('coin')) or 0

                    current_level = user_data['data']['gameInfo'].get('level') or 0
                    profit_hour = user_data['data']['mineInfo'].get('minePower') or 0

                    logger.info(
                        f" | Balance: {coin} | Level: {current_level} | Profit Per Hour: {profit_hour}")
                    signin_data=await bums.sign_in_data()
                    lists = signin_data['data']['lists']
                    sign_status = signin_data['data']['signStatus']
                    if not signin_data:
                        logger.error(f"{nickname} | Unknown error while collecting Check-In Data!")
                        logger.info(f"{nickname} | Sleep {round(config.ITERATION_DURATION / 60, 1)} min")
                        await asyncio.sleep(delay=config.ITERATION_DURATION)
                        break
                    if sign_status == 0:
                        for item in lists:
                            if item["status"] == 0:
                                day_reward = item["normal"]
                                current_day = item["daysDesc"]
                                make_signin = await bums.sign_in()
                                if make_signin:
                                    logger.success(
                                        f"{nickname} | Successful Sign-In {current_day}: {day_reward}")
                                continue


                    await asyncio.sleep(random.randint(1, 3))
                    box_info=await bums.box_info()

                    box_list = box_info.get("data", {})
                    for box in box_list:
                        if box.get("propId") == 500010001:
                            usage = box.get("toDayUse")
                            max_use = int(box.get("toDayMaxUseNum"))
                            today_use = int(box.get("toDayNowUseNum"))
                            if usage == False and today_use < max_use:
                                open_box = await bums.open_box()
                                if not open_box:
                                    logger.error(f"{nickname} | Unknown error while Opening Box!")
                                    logger.info(
                                        f"{nickname} | Sleep <y>{round(config.ITERATION_DURATION / 60, 1)}</y> min")
                                    await asyncio.sleep(delay=config.ITERATION_DURATION)
                                    continue
                                fb_name = open_box['rewardLists'][0].get('name')
                                logger.success(
                                    f"{nickname} | Free Box Opened: 500010001 | Prize: {fb_name}")
                    tapData=await bums.get_tap_info(nickname=nickname)
                    coin = tapData['balance']
                    tap_value = tapData['tap']
                    today_coin_limit = tapData['todayCoinLimit']
                    today_tap_done = tapData['todayCoin']
                    energy_left = tapData['leftEnergy']
                    total_energy = tapData['totalEnergy']
                    recovery = tapData['recovery']
                    bonus_chance = tapData['bonusChance']
                    bonus_multiplier = tapData['bonusRatio']
                    collect_seq = tapData['collectSeqNo']
                    auto_clicker = tapData['autoClick']

                    logger.info(f"{nickname} | Starting Auto-Taps...")
                    while energy_left > 1:
                        if auto_clicker:
                            logger.info(f"{nickname} | Auto-clicker detected. Skipping Auto-Taps...")
                            break

                        if today_tap_done > today_coin_limit:
                            logger.warning(f"{nickname} | Today Tap limit is over, Skipping.")
                            break

                        TAPS_PER_BATCH = [15, 30]

                        total_taps = random.randint(TAPS_PER_BATCH[0], TAPS_PER_BATCH[1])
                        taps_amount = 0
                        for _ in range(total_taps):
                            taps_amount += generate_taps(tap_value, energy_left, bonus_chance, bonus_multiplier)
                            if taps_amount > 0 and taps_amount <= energy_left:
                                hashCode = tapHash(taps_amount=taps_amount, collect_seq=collect_seq)
                                post_taps = await bums.submit_taps(collect_seq=collect_seq, taps_amount=taps_amount,hashCode=hashCode)
                                if post_taps:
                                    tapData = await bums.get_tap_info(nickname)
                                    energy_left = tapData['leftEnergy']
                                    today_tap_done = tapData['todayCoin']
                                    collect_seq = tapData['collectSeqNo']
                                    logger.success(
                                        f"{nickname} | Tapped x{total_taps}: +{fnum(taps_amount)} | Balance: {fnum(post_taps['data'].get('coin'))} | Energy: ({energy_left}/{total_energy})")
                                    await asyncio.sleep(
                                        random.randint(config.DELAY_BETWEEN_TAPS[0], config.DELAY_BETWEEN_TAPS[1]))
                                else:
                                    logger.error(f"{nickname} | Unknown error while tapping, Skipping taps!")
                                    break
                            else:
                                logger.warning(
                                    f"{nickname} | Insufficient energy for tap amount: <y>({energy_left}/{total_energy})</y>")
                                break

                            if energy_left <= 0:
                                logger.error(f"{nickname} | Left energy depleted, Skipping Auto-Taps!")
                                break

                        await asyncio.sleep(random.randint(1, 3))
                    task_list=await bums.get_tasklist()
                    if not task_list:
                        logger.error(f"{nickname} | Unknown error while collecting Task-List!")
                        logger.info(f"{nickname} | Sleep <y>{round(config.ITERATION_DURATION / 60, 1)}</y> min")
                        await asyncio.sleep(delay=config.ITERATION_DURATION)
                        return

                    tasks = task_list.get("data", {}).get("lists", [])
                    filtered_tasks = [
                        task for task in tasks
                        if task.get("limitInviteCount") == 0 and
                           task.get("InviteCount") == 0 and
                           task.get("isFinish") == 0 and
                           task.get("qualify") == 1 and
                           task.get("classifyName", "").lower() in ['youtube', 'partner task', 'welcome task',
                                                                    'in-game tasks'] and
                           task.get("taskType") in ['level', 'pwd', 'nickname_check', 'normal']
                    ]

                    if not filtered_tasks:
                        logger.info(f"{nickname} | No Task Found")

                    if filtered_tasks:
                        for task in filtered_tasks:
                            task_id = task.get("id")
                            task_name = task.get("name", "")
                            task_reward = task.get("rewardParty", "")
                            task_type = task.get("taskType")
                            task_classify = task.get("classifyName")
                            jump_url = task.get("jumpUrl", "")

                            if task.get("type") == "open_link" and task_type == "normal" and re.match(
                                    r"https?:\/\/(?:t\.me|telegram\.me|telegram\.dog)\/(?:[a-zA-Z0-9_]{4,32}|\+[a-zA-Z0-9_-]{08,18})",
                                    jump_url):
                                if any(keyword in task_name for keyword in ["Subscribe", "Join", "Follow"]):
                                    await asyncio.sleep(random.randint(5, 10))
                            data_done = await bums.done_task(task_id=task_id)
                            if data_done:
                                logger.success(
                                    f"{nickname} | Task: {task_name} | Reward: +{fnum(task_reward)}")
                            await asyncio.sleep(random.randint(3, 10))
                            # Update Tap-Cards
                            if config.AUTO_UPGRADE_TAP_CARDS:
                                logger.info(f"{nickname} | Updating Tap-Cards...")
                                upgrades = {
                                    "bonusChance": {"level": "jackpot_level", "max_level": config.JACKPOT_LEVEL},
                                    "bonusRatio": {"level": "crit_multiplier_level", "max_level": config.CRIT_LEVEL},
                                    "energy": {"level": "max_energy_level", "max_level": config.ENERGY_LEVEL},
                                    "tap": {"level": "tap_reward_level", "max_level": config.TAP_LEVEL},
                                    "recovery": {"level": "energy_regen_level",
                                                 "max_level": config.ENERGY_REGEN_LEVEL}
                                }

                                while True:
                                    user_data = await bums.user_data()
                                    if not user_data:
                                        logger.error(f"{nickname} | Unknown error while collecting User Data!")
                                        logger.info(
                                            f"{nickname} | Sleep {round(config.ITERATION_DURATION / 60, 1)} min")
                                        await asyncio.sleep(delay=config.ITERATION_DURATION)
                                        continue

                                    coin = int(user_data['data']['gameInfo'].get('coin') or 0)
                                    profit_hour = int(user_data['data']['mineInfo'].get('minePower') or 0)
                                    current_level = user_data['data']['gameInfo'].get('level') or 0
                                    tap_info = user_data['data']['tapInfo']

                                    upgrade_made = False
                                    for card_type, data in upgrades.items():
                                        level = int(tap_info[card_type].get('level'))
                                        price = int(tap_info[card_type].get('nextCostCoin'))
                                        max_level = data["max_level"]

                                        if level < max_level and coin >= price:
                                            upgrade_tap = await bums.upgrade_tap(
                                                                                 card_type=card_type)
                                            if upgrade_tap:
                                                card_name = card_details(card_type)
                                                logger.success(
                                                    f"{nickname} | '{card_name[0]}' upgraded: {level + 1}, -{fnum(price)}")
                                                upgrade_made = True
                                            break

                                        await asyncio.sleep(random.randint(3, 10))

                                    if not upgrade_made:
                                        all_upgraded = all(
                                            int(tap_info[card]["level"]) >= upgrades[card]["max_level"] for card in
                                            upgrades)
                                        if all_upgraded:
                                            logger.success(f"{nickname} | All Tap-Cards upgraded!")
                                            logger.info(
                                                f"{nickname} | Updated Balance: {fnum(coin)} | Updated Level: {current_level}")
                                        else:
                                            logger.info(
                                                f"{nickname} | Insufficient Balance to keep upgrading.")
                                            logger.info(
                                                f"{nickname} | Updated Balance: {fnum(coin)} | Updated Level: {current_level}")
                                        break

                                await asyncio.sleep(random.randint(1, 3))

                            # Update Mine-Cards
                            if config.AUTO_UPGRADE_MINE_CARDS:
                                logger.info(f"{nickname} | Updating Mine-Cards...")
                                while True:
                                    mine_data = await bums.get_tap_cards()
                                    if not mine_data:
                                        logger.error(f"{nickname} | Unknown error while collecting Mine List!")
                                        logger.info(
                                            f"{nickname} | Sleep {round(config.ITERATION_DURATION / 60, 1)} min")
                                        await asyncio.sleep(delay=config.ITERATION_DURATION)
                                        continue

                                    mine_list = mine_data['data']['lists']

                                    user_data = await bums.user_data()
                                    if not user_data:
                                        logger.error(f"{nickname} | Unknown error while collecting User Data!")
                                        logger.info(
                                            f"{nickname} | Sleep {round(config.ITERATION_DURATION / 60, 1)} min")
                                        await asyncio.sleep(delay=config.ITERATION_DURATION)
                                        continue

                                    coin = int(user_data['data']['gameInfo'].get('coin') or 0)
                                    current_level = user_data['data']['gameInfo'].get('level') or 0
                                    profit_hour = user_data['data']['mineInfo'].get('minePower') or 0

                                    upgrades_done = False

                                    if config.PROFIT_UPGRADE:
                                        allowed_cards = []
                                        for mine in mine_list:
                                            next_level_cost = int(mine['nextLevelCost'])
                                            status = int(mine['status'])
                                            mine_id = int(mine['mineId'])

                                            if next_level_cost <= coin and next_level_cost <= config.MAX_CARD_PRICE_PURCHASE and status == 1:
                                                allowed_cards.append(mine)
                                        if allowed_cards:
                                            profit_card = await get_profit_card(cards=allowed_cards)
                                            if profit_card:
                                                mine_id = profit_card["mineId"]
                                                next_level_cost = profit_card["nextLevelCost"]
                                                mine_level = int(profit_card['level'])

                                                mine_card = card_details(mine_id)

                                                upgrade_card = await bums.upgrade_mine(mineId=mine_id)

                                                if upgrade_card:
                                                    logger.success(
                                                        f"{nickname} | '{mine_card[0]}' upgraded: {mine_level + 1}, -{fnum(next_level_cost)}")
                                                    upgrades_done = True

                                    else:
                                        for mine in mine_list:
                                            next_level_cost = int(mine['nextLevelCost'])
                                            status = int(mine['status'])
                                            mine_id = int(mine['mineId'])
                                            mine_level = int(mine['level'])

                                            mine_card = card_details(mine_id)
                                            if next_level_cost <= coin and next_level_cost <= config.MAX_CARD_PRICE_PURCHASE and status == 1:
                                                upgrade_card = await bums.upgrade_mine(
                                                                                       mineId=mine_id)

                                                if upgrade_card:
                                                    logger.success(
                                                        f"{nickname} | '{mine_card[0]}' upgraded: {mine_level + 1}, -{fnum(next_level_cost)}")
                                                    upgrades_done = True

                                    if not upgrades_done:
                                        logger.info(
                                            f"{nickname} | No more upgrades possible. Stopping process.")
                                        logger.info(
                                            f"{nickname} | Updated Balance: {fnum(coin)} | Updated Level: {current_level} | Updated Profit/Hour: {fnum(profit_hour)}")
                                        break

                                    await asyncio.sleep(random.randint(3, 10))

                                await asyncio.sleep(random.randint(1, 3))

                            # Leave Gang
                            if config.LEAVE_GANG:
                                left_gang = await bums.leave_gang()
                                if left_gang and left_gang != "wait":
                                    logger.success(f"{nickname} | Successfully left Gang!")
                                elif left_gang == "wait":
                                    logger.warning(
                                        f"{nickname} | After user joins the gang he can not quit the gang for a week (168 hours)")
                                else:
                                    logger.error(f"{nickname} | Unknown error while Leaving Gang!")

                            # Join Gang
                            if config.JOIN_GANG:
                                gang_list = await bums.get_gang_list()
                                if not gang_list:
                                    logger.error(f"{nickname} | Unknown error while collecting Gang-List!")
                                    logger.info(f"{nickname} | Sleep {round(config.ITERATION_DURATION / 60, 1)} min")
                                    await asyncio.sleep(delay=config.ITERATION_DURATION)
                                    continue

                                my_gang = gang_list['data']['myGang'].get('gangId') or None
                                if my_gang is None:
                                    logger.info(f"{nickname} | Joining Gang...")

                                    join_gang = await bums.join_gang()
                                    if not join_gang:
                                        logger.error(f"{nickname} | Unknown error while Joining Gang!")
                                        logger.info(
                                            f"{nickname} | Sleep {round(config.ITERATION_DURATION / 60, 1)} min")
                                        await asyncio.sleep(delay=config.ITERATION_DURATION)
                                        continue
                                    logger.success(f"{nickname} | Gang joined successfully!")

                                await asyncio.sleep(random.randint(1, 3))

                            # Auto Solve Combos
                            if config.SOLVE_COMBO:
                                user_data = await bums.user_data()
                                if not user_data:
                                    logger.error(f"{nickname} | Unknown error while collecting User Data!")
                                    logger.info(f"{nickname} | Sleep {round(config.ITERATION_DURATION / 60, 1)} min")
                                    await asyncio.sleep(delay=config.ITERATION_DURATION)
                                    continue

                                if "Lottery" in user_data["data"]["gameInfo"]["collegeCanUse"]:
                                    combo_available = await bums.combo_details()
                                    if combo_available:
                                        reward = combo_available['data'].get('rewardNum')
                                        combo_data = combo_answer(method='get')
                                        if combo_data:
                                            await asyncio.sleep(random.randint(1, 3))
                                            logger.info(f"{nickname} | Checking Combo...")
                                            solve_combo = await bums.submit_combo(
                                                                                  one=combo_data[0], two=combo_data[1],
                                                                                  three=combo_data[2])
                                            if not solve_combo:
                                                logger.error(
                                                    f"{nickname} | Unknown error while solving Combo!")
                                                logger.info(
                                                    f"{nickname} | Sleep {round(config.ITERATION_DURATION / 60, 1)} min")
                                                await asyncio.sleep(delay=config.ITERATION_DURATION)
                                                continue
                                            answer_status = solve_combo['data'].get('status')
                                            if answer_status == 0:
                                                logger.success(f"{nickname} | Combo solved: +{reward}")
                                            else:
                                                attempt_left = solve_combo['data'].get('resultNum')
                                                combo_answer(method='wrong')
                                                logger.error(
                                                    f"{nickname} | Combo is wrong, Left Chance: {attempt_left}. Edit 'combo.json' with valid combo.")
                                        else:
                                            logger.error(
                                                f"{nickname} | Skipping Combo, Combo is empty or invalid. Edit 'combo.json' with correct answers!")
                                else:
                                    logger.error(
                                        f"{nickname} | Skipping Combo, Combo (Lottery) is currently locked!")

                                await asyncio.sleep(random.randint(1, 3))

                            # Auto Spins
                            if config.AUTO_SPINS:
                                spin_info = await bums.spin_info()
                                if not spin_info:
                                    logger.error(f"{nickname} | Unknown error while collecting Spin Info!")
                                    logger.info(f"{nickname} | Sleep {round(config.ITERATION_DURATION / 60, 1)} min")
                                    await asyncio.sleep(delay=config.ITERATION_DURATION)
                                    continue

                                spin_count = config.SPIN_COUNT
                                total_spins = int(spin_info.get('data', {}).get('staminaNow')) or 0
                                max_spins = spin_info.get('data', {}).get('staminaMax') or 'NaN'

                                if total_spins > 0:
                                    logger.info(
                                        f"{nickname} | Total Spins: ({total_spins}/{max_spins}), Spinning...")

                                while total_spins > 0:
                                    if spin_count > total_spins:
                                        spin_count = count_spin(total_spins)

                                    spin_data = await bums.start_spin(count=spin_count)
                                    if not spin_data:
                                        logger.error(f"{nickname} | Unknown error while collecting Spin Data!")
                                        logger.info(
                                            f"{nickname} | Sleep {round(config.ITERATION_DURATION / 60, 1)} min")
                                        await asyncio.sleep(delay=config.ITERATION_DURATION)
                                        continue

                                    spin_reward = (
                                            spin_data.get('data', {}).get('rewardLists', {}).get('rewardList', [{}])[
                                                0].get(
                                                'name') or 'None')

                                    logger.success(f"{nickname} | Spin Reward: {spin_reward}")

                                    spin_info = await bums.spin_info()
                                    if not spin_info:
                                        logger.error(f"{nickname} | Unknown error while collecting Spin Info!")
                                        logger.info(
                                            f"{nickname} | Sleep {round(config.ITERATION_DURATION / 60, 1)} min")
                                        await asyncio.sleep(delay=config.ITERATION_DURATION)
                                        continue

                                    total_spins = int(spin_info.get('data', {}).get('staminaNow')) or 0
                                    await asyncio.sleep(random.randint(2, 8))

                                await asyncio.sleep(random.randint(1, 3))

                            logger.info(f"{nickname} | Sleep {round(config.ITERATION_DURATION / 60, 1)} min")
                            await asyncio.sleep(delay=config.ITERATION_DURATION)





                except Exception as e:
                        logger.error(f"Error: {e}")
                except Exception as outer_e:
                    logger.error(f"Session error: {outer_e}")
        logger.info(f"Reconnecting in {format_duration(config.ITERATION_DURATION)}...")
        sleep_dur = config.ITERATION_DURATION


async def stats():
    logger.success("Analytics disabled")

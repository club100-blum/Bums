# Available modes:
# - "lazy"           (uses accounts from running telegram.exe proccess on your PC. No configuration needed)
# - "pyrogram"
# - "telethon"
# - "telethon+json"  (uses api_id, api_hash, sdk version, etc. from json file)

MODE = 'telethon'


# api id, hash
# You can get it here: https://my.telegram.org/
# Used only in "telethon", "pyrogram" modes
API_ID: int = 21876073
API_HASH: str = '2678a2132ee44d4bb41e0497e27ca20b'  
REF_KEY: str = 'ref_TNHiWxDO'  # KEY AFTER 'startapp=' from invite link

DELAYS = {
    'ACCOUNT':    [1, 2],       # delay between connections to accounts (the more accounts, the longer the delay)
    'PLAY':       [5, 15],      # delay between play in seconds
    'ERROR_PLAY': [60, 180],    # delay between errors in the game in seconds
}
AUTO_UPGRADE_TAP_CARDS: bool = True
JACKPOT_LEVEL: int = 9
CRIT_LEVEL: int = 8
ENERGY_LEVEL: int = 12
TAP_LEVEL: int = 12
ENERGY_REGEN_LEVEL: int = 10

AUTO_UPGRADE_MINE_CARDS: bool = True
MAX_CARD_PRICE_PURCHASE: int = 10000
PROFIT_UPGRADE: bool = True

AUTO_TAP: bool = True
TAPS_PER_BATCH: list[int] = [15, 30]
DELAY_BETWEEN_TAPS: list[int] = [10, 20]

AUTO_TASK: bool = True
AUTO_JOIN_CHANNELS: bool = True
AUTO_NAME_CHANGE: bool = True

COLLECT_REFER_BALANCE: bool = True

LEAVE_GANG: bool = False
JOIN_GANG: bool = True

SOLVE_COMBO: bool = True

AUTO_SIGN_IN: bool = True
AUTO_OPEN_FREE_BOX: bool = True

AUTO_SPINS: bool = True
SPIN_COUNT: int = 50

SLEEP_TIME: list[int] = [2700, 4200]
START_DELAY: list[int] = [5, 100]


# Use proxies or not
# Paste proxies to data/proxy.txt
PROXY = False

# dataimpulse.com proxies (cheap rotating proxies).
# Automatically gets proxy of phone's country
# Works only with mode telethon+json, where session files in format "<phone_number>.session"
DATAIMPULSE = False
DI_LOGIN =    ''
DI_PASSWORD = ''

# Session folder (do not change)
WORKDIR = "sessions/"

# Iteration duration in seconds, 1 hour = 60 * 60
ITERATION_DURATION = 60 * 60

# Threads/Workers count
ACCOUNT_PER_ONCE = 10

REFERRAL_COUNT = 5

# Dont change this, if you dont know what you are doing
DATABASE_URL = "sqlite+aiosqlite:///accounts.db"
APP_VERSION = '1.0.2'

from dotenv import load_dotenv

load_dotenv()

from typing import Any, List  # noqa
from deta import Deta  # noqa
import os  # noqa
import requests  # noqa

s = requests.Session()


deta = Deta()
dpsBase = deta.Base("DpsDB")
userBase = deta.Base("Users")
loginsBase = deta.Base("WebLogin")

TOKEN = os.getenv("TOKEN", "")
DISCORD_API = "https://discord.com/api/v10"
WHITELIST_API = os.getenv("WHITELIST_API", "")
WHITELIST_KEY = os.getenv("WHITELIST_KEY", "")
GUILD_ID = os.getenv("GUILD_ID", "")


def fetch_all_items():
    res = dpsBase.fetch(last="876888699827265566")
    all_items: List[Any] = res.items

    while res.last:
        res = dpsBase.fetch(last=res.last)
        all_items += res.items

    return all_items


# check if user exists in the discord server
def guild_member_exists(userid: str):
    r = s.get(
        f"{DISCORD_API}/guilds/{GUILD_ID}/members/{userid}",
        headers={"Authorization": f"Bot {TOKEN}"},
    )

    if r.status_code == 200:
        return True

    return False


# check if user's data exists in `Users` base
def user_data_exists(userid: str):
    user = userBase.get(userid)
    if user is None:
        return False

    return True


def get_login_data(wallet: str):
    return loginsBase.get(wallet)


# add wallet to whitelist
# call api
def add_whitelist(wallet: str):
    r = s.post(
        f"{WHITELIST_API}/whitelist",
        headers={
            "X-Space-App-Key": WHITELIST_KEY,
        },
        json={"wallet": wallet},
    )

    print(r)


def main():
    dps_items = fetch_all_items()
    for i in dps_items:
        userid = i["id"]
        wallet = i["wallet"]

        print("log", userid)

        # if user left // 404 error, we can't do anything
        if not guild_member_exists(userid):
            continue

        # if user's data exists, no need to process further
        if user_data_exists(userid):
            continue

        # get wallet's token
        login = get_login_data(wallet)
        if login is None:
            print(userid, wallet, "WEB Login data does not exist.")
            continue

        # recover user's data
        userData = {
            "key": userid,
            "id": userid,
            "is_stopped": False,
            "is_whitelisted": True,
            "not_whitelisted_reason": "",
            "token": login["token"],
            "wallet": wallet,
        }
        userBase.put(userData)

        # add wallet to whitelist
        add_whitelist(wallet)

        # update wallet to linked
        loginsBase.update({"linked": True}, wallet)


if __name__ == "__main__":
    main()

import asyncio
import requests
import re
import os
import pandas as pd
from playwright.async_api import async_playwright

# ------------------------------------
# Step 1: Login and grab cookies/token/player ID
# ------------------------------------
async def get_bga_cookies_token_and_player_id():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://boardgamearena.com")
        print("🔐 Please log in manually, then press ENTER here to continue.")
        input()

        cookies = await context.cookies()
        cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
        token = next((c["value"] for c in cookies if "TournoiEnLigneidt" in c["name"]), None)

        player_id = extract_player_id_from_html(cookie_header)
        await browser.close()
        return cookie_header, token, player_id

# ------------------------------------
# Step 2: Scrape player ID
# ------------------------------------
def extract_player_id_from_html(cookie_header):
    print("🌐 Getting /player page to extract player ID...")
    headers = {
        "accept": "text/html",
        "upgrade-insecure-requests": "1",
        "cookie": cookie_header,
        "referer": "https://boardgamearena.com/",
    }

    response = requests.get("https://boardgamearena.com/player", headers=headers)

    if not response.ok:
        print("❌ Failed to get /player page")
        return None

    match = re.search(r"https://en\.boardgamearena\.com/player\?id=(\d+)", response.text)
    return match.group(1) if match else None

# ------------------------------------
# Step 3: Fetch game metadata
# ------------------------------------
def fetch_game_data(cookie_header, token, player_id, page):
    url = "https://boardgamearena.com/gamestats/gamestats/getGames.html"
    params = {
        "player": str(player_id),
        "opponent_id": "0",
        "game_id": "1131",
        "finished": "0",
        "page": str(page),
        "updateStats": "0"
    }

    headers = {
        "accept": "*/*",
        "x-request-token": token,
        "x-requested-with": "XMLHttpRequest",
        "cookie": cookie_header,
        "referer": f"https://boardgamearena.com/gamestats?player={player_id}&game_id=1131"
    }

    response = requests.get(url, headers=headers, params=params)
    return response.json() if response.ok else None

# ------------------------------------
# Step 4: Fetch detailed game data for table
# ------------------------------------
def fetch_table_info(table_id, cookie_header, token):
    url = "https://boardgamearena.com/table/table/tableinfos.html"
    headers = {
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
        "x-request-token": token,
        "cookie": cookie_header,
        "referer": f"https://boardgamearena.com/table?table={table_id}",
    }
    data = {"id": str(table_id)}
    response = requests.post(url, headers=headers, data=data)
    return response.json() if response.ok else None

# ------------------------------------
# Step 5: Main scraping loop + DataFrame creation
# ------------------------------------
async def main():
    cookie_header, token, player_id = await get_bga_cookies_token_and_player_id()
    if not player_id:
        print("🚫 Could not determine player ID.")
        return


    page = 1

    while True:
        print(f"\n📄 Fetching game data (Page {page})...")
        data = fetch_game_data(cookie_header, token, player_id, page)
        if not data or not data["data"]["tables"]:
            break

        for game in data["data"]["tables"]:
            table_id = game["table_id"]
            if os.path.exists(f"data/{table_id}.csv"):
                print(f"Found data for table {table_id}")
                continue
            
            print(f"\n🔍 Fetching info for table {table_id}...")
            table_info = fetch_table_info(table_id, cookie_header, token)
            if not table_info or "data" not in table_info:
                continue

            game_data = table_info["data"]
            result = game_data.get("result", {})
            players = result.get("player", [])
            stats = result.get("stats", {}).get("player", {})

            # All these should be dicts of {player_id: value}
            wonder_ids = stats.get("wonder_id", {}).get("values", {})
            points_by_category = {
                "civilian": stats.get("points_civilian", {}).get("values", {}),
                "science": stats.get("points_science", {}).get("values", {}),
                "commerce": stats.get("points_commerce", {}).get("values", {}),
                "guild": stats.get("points_guild", {}).get("values", {}),
                "treasure": stats.get("points_treasure", {}).get("values", {}),
                "wonder": stats.get("points_wonder", {}).get("values", {}),
                "victory": stats.get("points_victory", {}).get("values", {}),
                "defeat": stats.get("points_defeat", {}).get("values", {}),
                "time": stats.get("reflexion_time", {}).get("values", {}),
            }
            all_rows = []
            if len(points_by_category["civilian"]) > 0:
                for player in players:
                    pid = str(player["player_id"])  # Make sure the ID is a string to match dict keys
                    row = {
                        "Table ID": table_id,
                        "Player Name": player.get("name"),
                        "Rank": player.get("gamerank"),
                        "Score": player.get("score"),
                        "Wonder ID": wonder_ids.get(pid),
                        "VP - Civilian": points_by_category["civilian"].get(pid),
                        "VP - Science": points_by_category["science"].get(pid),
                        "VP - Commerce": points_by_category["commerce"].get(pid),
                        "VP - Guild": points_by_category["guild"].get(pid),
                        "VP - Coins": points_by_category["treasure"].get(pid),
                        "VP - Wonder": points_by_category["wonder"].get(pid),
                        "VP - Military (Victory)": points_by_category["victory"].get(pid),
                        "VP - Military (Defeat)": points_by_category["defeat"].get(pid),
                        "ELO Won": player.get('point_win'),
                        "ELO After": player.get('rank_after_game'),
                        "Start": game['start'],
                        "End": game['end'],
                    }
                    all_rows.append(row)
                df = pd.DataFrame(all_rows)
                df.to_csv(f"data/{table_id}.csv", index=False)
            


        page += 1

    

# Run the script
asyncio.run(main())

import requests
import math

# ─────────────────────────────────────────────────────────────────────
# ░█▄█░█▀█░█▀▀░█░█░█░█░█▀█░▀█▀░█▀▀░█▀▄░█▀▀░█▀▀
# ░█░█░█▀█░█░█░█░█░█░█░█▀█░░█░░█▀▀░█▀▄░█▀▀░▀▀█
# ░▀░▀░▀░▀░▀▀▀░▀▀▀░▀▀▀░▀░▀░░▀░░▀▀▀░▀░▀░▀▀▀░▀▀▀
#
# NIKITA DONT BAN
# мне пожалуйста никита
# я все свои монеты потратил на тарков
# лучшее редактирование :(
# ─────────────────────────────────────────────────────────────────────

# konstante
TAX_TI = 0.03
TAX_TR = 0.03
TOP_RESULTS = 5


def calculate_fee(base_price, sell_price, quantity):
    vo = base_price * quantity
    vr = sell_price * quantity
    q = 1  # don't touch this. seriously.

    po = math.log10(vo / vr) if vr else 0
    if vr < vo:
        po = po ** 1.08  # because why use round numbers when you can do this shit

    pr = math.log10(vr / vo) if vo else 0
    if vr >= vo:
        pr = pr ** 1.08

    fee = (vo * TAX_TI * (4 ** po) * q) + (vr * TAX_TR * (4 ** pr) * q)
    return fee

def estimate_probability(buy_count, velocity_ratio):
    if buy_count == 0:
        return 0.0
    normalized_buy_count = min(buy_count / 200, 1.0)
    normalized_velocity = max(min(velocity_ratio, 2.0), 0.1)
    raw_probability = (normalized_velocity / (normalized_buy_count + 0.2))
    return round(max(min(raw_probability, 1.0), 0.0), 2)

def should_skip_item(name, tags, price):
    forbidden_keywords = [
        "barrel", "grip", "muzzle", "receiver", "handguard", "weapon",
        "stock", "slide", "rail", "mount", "gas tube", "charging handle",
        "buffer tube", "recoil pad", "flash hider", "compensator", "foregrip", "adapter"
    ]
    name_lower = name.lower()
    return any(word in name_lower for word in forbidden_keywords) and price <= 10000

def get_items(api_key):
    url = "https://api.tarkov-market.app/api/v1/items/all"
    headers = {"x-api-key": api_key}
    r = requests.get(url, headers=headers)
    r.raise_for_status() 
    return r.json()

def analyze_item(item, budget):
    base_price = item.get("basePrice")
    name = item.get("name")
    lowest_price = item.get("price")
    avg24h = item.get("avg24hPrice") or 0
    avg7d = item.get("avg7daysPrice") or 0
    tags = item.get("tags", [])
    slots = item.get("slots", 1)

    if base_price is None or lowest_price is None:
        return None
    if should_skip_item(name, tags, lowest_price):
        return None
    if avg24h == 0 or avg7d == 0 or abs(avg24h - avg7d) / avg7d < 0.05:
        return None

    velocity = round(lowest_price / avg24h, 2)
    if velocity < 0.9:
        return None

    # simulate real listings (Tarkov won't give them to us)
    listings = [lowest_price + (i * 500) for i in range(1, 101)]

    max_profit = 0
    best = None

    for n in range(1, len(listings)):
        cost = sum(listings[:n])
        if cost > budget:
            break 
        resale_price = listings[n]
        revenue = resale_price * n
        fees = calculate_fee(base_price, resale_price, n)
        profit = revenue - cost - fees

        if profit > max_profit:
            max_profit = profit
            best = {
                "name": name,
                "buy_count": n,
                "buy_cost": cost,
                "resell_price": resale_price,
                "profit": int(profit),
                "velocity_ratio": velocity,
                "probability": estimate_probability(n, velocity),
                "total_listings": len(listings)
            }

    return best

def main():
    print("main\\start")
    api_key = input("main\\start\\enter_api_key > ").strip()
    budget = int(input("main\\start\\enter_budget > "))
    gamba_input = input("main\\start\\enter_gambaindex > (enter the minimum % probability of the flip going through. default: 80) ").strip()
    min_confidence = 0.8
    if gamba_input:
        try:
            min_confidence = float(gamba_input) / 100
        except ValueError:
            print("main\\start\\invalid_input\\defaulting_to_80_percent")

    print("main\\fetching_data\\requesting_market_data")
    try:
        items = get_items(api_key)
    except Exception as e:
        print("main\\fetching_data\\error\\", e)
        return

    print("main\\analyze\\begin_flip_analysis")
    flips = []

    for item in items:
        if not item.get("price") or not item.get("basePrice"):
            continue
        result = analyze_item(item, budget)
        if result and result["profit"] > 0 and result["probability"] >= min_confidence:
            flips.append(result)

    if not flips:
        print("main\\results\\no_profitable_flips_found")
        print("// maybe go scav instead today.")
        return

    flips.sort(key=lambda x: x["profit"], reverse=True)

    print(f"\nmain\\results\\top_flips")
    print(f"main\\results\\total_flips: {len(flips)}\n")

    for i, item in enumerate(flips[:TOP_RESULTS], 1):
        print(f"main\\results\\{i}_item")
        print(f"  name: {item['name']}")
        print(f"  buy_count: {item['buy_count']}")
        print(f"  total_listings: {item['total_listings']}")
        print(f"  buy_cost: {item['buy_cost']} ₽")
        print(f"  resell_price: {item['resell_price']} ₽")
        print(f"  estimated_profit: {item['profit']} ₽")
        print(f"  velocity_ratio: {item['velocity_ratio']}  (1.0 = avg speed)")
        print(f"  probability: {item['probability']}  (1.0 = highest confidence)\n")

if __name__ == "__main__":
    main()

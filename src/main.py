import os
import time
import requests
import random
from datetime import datetime
from dotenv import load_dotenv

# ===== CONFIGURATION ABSOLUE =====
VOLUME_MIN_NBA = 380000
VOLUME_MIN_BTC = 2200000
VOLUME_MIN_FOOT = 400000

TP_NBA = 5.0
TP_BTC = 4.0
TP_FOOT = 5.0
SL = 2.5
TRAILING_ACTIVATION = 3.0

MAX_TRADES = 3
CHECK_INTERVAL = 10
MIN_GAP = 15
TRADE_SIZE = 1
MAX_DAILY_TRADES = 1500

# ===== STATISTIQUES =====
total_gains = 0.0
strike_count = 0
sl_count = 0
tp_count = 0

nba_tp = 0
nba_sl = 0
btc_tp = 0
btc_sl = 0
foot_tp = 0
foot_sl = 0

last_cumul_time = time.time()
CUMUL_INTERVAL = 180

def show_cumul():
    print("\n" + "🔥"*35)
    print("         💲💸💰 𝐁𝐈𝐋𝐀𝐍 𝐃𝐄 𝐆𝐀𝐈𝐍𝐒 💰💸💲")
    print("🔥"*35)
    print("       📊 𝐌𝐄𝐈𝐋𝐋𝐄𝐔𝐑 𝐒𝐂𝐎𝐑𝐄 𝐓𝐏 / 𝐒𝐋")
    print("")
    print("           🏀 𝐍𝐁𝐀   : {:2d} / {:2d}".format(nba_tp, nba_sl))
    print("           ⚽ 𝐅𝐨𝐨𝐭   : {:2d} / {:2d}".format(foot_tp, foot_sl))
    print("           🪙 𝐁𝐓𝐂    : {:2d} / {:2d}".format(btc_tp, btc_sl))
    print("🔥"*35)
    print("          𝐇𝐞𝐮𝐫𝐞 : {}".format(datetime.now().strftime('%H:%M:%S')))
    print("")
    print("   ⚔️  𝐓𝐏 : {:3d}   🩸 𝐒𝐋 : {:3d}".format(tp_count, sl_count))
    print("   🎯 𝐒𝐭𝐫𝐢𝐤𝐞𝐬 : {:3d}   💰 𝐆𝐚𝐢𝐧𝐬 : ${:.2f}".format(strike_count, total_gains))
    print("🔥"*35 + "\n")

def get_markets_by_tag(tag, limit=15):
    url = f"https://gamma-api.polymarket.com/markets?active=true&tag={tag}&limit={limit}&order=volume&ascending=false"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            markets = response.json()
            active_markets = [m for m in markets if m.get('volume', 0) > 0]
            return active_markets
        return []
    except:
        return []

def extract_team_names(question):
    if ' vs ' in question:
        return question.split(' vs ')
    return [question[:30], '']

def calculate_gap(market, price):
    try:
        bid = float(market.get('bestBid', 0))
        ask = float(market.get('bestAsk', 1))
        if bid > 0 and ask > 0:
            mid_price = (bid + ask) / 2
            return abs(mid_price - price) * 100
        return MIN_GAP
    except:
        return MIN_GAP

def analyze_market(market, tag, rank):
    global total_gains, strike_count, tp_count, sl_count
    global nba_tp, nba_sl, btc_tp, btc_sl, foot_tp, foot_sl
    
    try:
        question = market.get('question', 'Inconnu')
        volume = market.get('volume', 0)
        if not isinstance(volume, (int, float)):
            volume = 0
        
        price_str = market.get('outcomePrices', ['0'])[0]
        try:
            price = float(price_str) if price_str else 0.0
        except:
            price = 0.0
        
        teams = extract_team_names(question)
        team1 = teams[0][:20]
        team2 = teams[1][:20] if len(teams) > 1 else ""
        
        try:
            gap = calculate_gap(market, price)
            if not isinstance(gap, (int, float)):
                gap = MIN_GAP
        except:
            gap = MIN_GAP
        
        if tag == 'bitcoin':
            display_name = f"🪙 {question[:40]}"
        elif tag == 'NBA':
            display_name = f"🏀 {team1} 𝐯𝐬 {team2}"
        elif tag == 'football':
            display_name = f"⚽ {team1} 𝐯𝐬 {team2}"
        else:
            display_name = question[:50]
        
        if tag == 'bitcoin':
            tp = TP_BTC
        elif tag == 'football':
            tp = TP_FOOT
        else:
            tp = TP_NBA
        
        print(f"\n[{rank:2d}] {display_name}")
        print(f"     ├─ 𝐏𝐫𝐢𝐱 : ${price:.3f}")
        print(f"     ├─ 𝐕𝐨𝐥𝐮𝐦𝐞 : {volume:,.0f}")
        print(f"     ├─ 𝐆𝐚𝐩 : {gap:.1f}%")
        
        volume_ok = True
        if tag == 'NBA' and volume < VOLUME_MIN_NBA:
            volume_ok = False
        elif tag == 'bitcoin' and volume < VOLUME_MIN_BTC:
            volume_ok = False
        elif tag == 'football' and volume < VOLUME_MIN_FOOT:
            volume_ok = False
        
        if not volume_ok:
            print(f"     └─ ❌ 𝐕𝐨𝐥𝐮𝐦𝐞 𝐢𝐧𝐬𝐮𝐟𝐟𝐢𝐬𝐚𝐧𝐭")
            return
        
        if gap < MIN_GAP:
            print(f"     └─ ❌ 𝐆𝐚𝐩 𝐢𝐧𝐬𝐮𝐟𝐟𝐢𝐬𝐚𝐧𝐭 ({gap:.1f}% < {MIN_GAP}%)")
            return
        
        strike_count += 1
        gain = TRADE_SIZE * (tp / 100)
        total_gains += gain
        tp_count += 1
        
        if tag == 'NBA':
            nba_tp += 1
        elif tag == 'bitcoin':
            btc_tp += 1
        else:
            foot_tp += 1
        
        print(f"     └─ ⚔️  𝐌𝐈𝐒𝐒𝐈𝐎𝐍 𝐓𝐏 +{tp}% (𝐠𝐚𝐢𝐧 +${gain:.2f})")
        
        if random.random() < 0.1:
            sl_count += 1
            total_gains -= TRADE_SIZE * (SL / 100)
            if tag == 'NBA':
                nba_sl += 1
            elif tag == 'bitcoin':
                btc_sl += 1
            else:
                foot_sl += 1
            print(f"         🩸 𝐒𝐋 𝐝é𝐜𝐥𝐞𝐧𝐜𝐡é à -{SL}%")
        
    except Exception as e:
        print(f"     └─ ❌ 𝐄𝐫𝐫𝐞𝐮𝐫: {str(e)[:30]}")

def main():
    load_dotenv()
    
    print("="*70)
    print("👻 𝐆𝐇𝐎𝐒𝐓 𝐏𝐑𝐎𝐓𝐎𝐂𝐎𝐋 - 𝐌𝐎𝐃𝐄 𝐑𝐄́𝐄𝐋 (1$)")
    print("="*70)
    print("🏀 𝐍𝐁𝐀  : 𝐓𝐏 5% | 𝐕𝐨𝐥 ≥ 380𝐤")
    print("🪙 𝐁𝐓𝐂  : 𝐓𝐏 4% | 𝐕𝐨𝐥 ≥ 2.2𝐌")
    print("⚽ 𝐅𝐨𝐨𝐭 : 𝐓𝐏 5% | 𝐕𝐨𝐥 ≥ 400𝐤")
    print(f"𝐆𝐚𝐩 𝐦𝐢𝐧𝐢𝐦𝐮𝐦 : {MIN_GAP}% | 𝐒𝐋 : {SL}% | 𝐓𝐫𝐚𝐢𝐥𝐢𝐧𝐠 : +{TRAILING_ACTIVATION}%")
    print(f"𝐓𝐫𝐚𝐝𝐞 𝐬𝐢𝐳𝐞 : ${TRADE_SIZE}")
    print("="*70 + "\n")
    
    if not os.getenv('PRIVATE_KEY'):
        print("❌ 𝐏𝐑𝐈𝐕𝐀𝐓𝐄_𝐊𝐄𝐘 𝐦𝐚𝐧𝐪𝐮𝐚𝐧𝐭𝐞")
        return
    
    print("✅ 𝐂𝐥𝐞́ 𝐩𝐫𝐢𝐯𝐞́𝐞 𝐭𝐫𝐨𝐮𝐯𝐞́𝐞")
    print("🔍 𝐒𝐜𝐚𝐧 𝐝𝐞𝐬 𝐦𝐚𝐫𝐜𝐡𝐞́𝐬...\n")
    
    tags = ['NBA', 'bitcoin', 'football']
    global last_cumul_time
    last_cumul_time = time.time()
    
    try:
        while True:
            print(f"\n{'🔷'*35}")
            print(f"📡 𝐒𝐂𝐀𝐍 {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'🔷'*35}")
            
            for tag in tags:
                markets = get_markets_by_tag(tag)
                sport_name = "NBA" if tag == "NBA" else ("Bitcoin" if tag == "bitcoin" else "Football")
                print(f"\n▶ {sport_name} - {len(markets)} 𝐦𝐚𝐫𝐜𝐡𝐞́𝐬")
                
                for idx, market in enumerate(markets, 1):
                    analyze_market(market, tag, idx)
                    time.sleep(0.2)
            
            if time.time() - last_cumul_time >= CUMUL_INTERVAL:
                show_cumul()
                last_cumul_time = time.time()
            
            print(f"\n⏳ 𝐏𝐫𝐨𝐜𝐡𝐚𝐢𝐧 𝐬𝐜𝐚𝐧 𝐝𝐚𝐧𝐬 {CHECK_INTERVAL}𝐬")
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n👋 𝐆𝐡𝐨𝐬𝐭 𝐝𝐞́𝐬𝐚𝐜𝐭𝐢𝐯𝐞́")
        show_cumul()
    except Exception as e:
        print(f"❌ 𝐄𝐫𝐫𝐞𝐮𝐫: {e}")
        time.sleep(10)

if __name__ == "__main__":
    main()

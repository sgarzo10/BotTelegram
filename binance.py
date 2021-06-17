from utility import Config, make_request
from logging import info
from json import loads
from hmac import new
from hashlib import sha256
from tabulate import tabulate
from csv import writer


def generate_signature(query_string):
    return new(bytes(Config.settings['binance']['binance_info']['secret'], 'latin-1'), msg=bytes(query_string, 'latin-1'), digestmod=sha256).hexdigest().upper()


def get_server_time():
    return loads(make_request("https://api.binance.com/api/v3/time", api_binance=True)['response'])['serverTime']


def get_flexible_savings_balance(asset):
    query_string = "asset={}&timestamp={}".format(asset, str(get_server_time()))
    signature = generate_signature(query_string)
    return loads(make_request("https://api.binance.com/sapi/v1/lending/daily/token/position?{}&signature={}".format(query_string, signature), api_binance=True)['response'])


def get_locked_savings_balance(asset, project_id):
    query_string = "asset={}&projectId={}&status=HOLDING&timestamp={}".format(asset, project_id, str(get_server_time()))
    signature = generate_signature(query_string)
    return loads(make_request("https://api.binance.com/sapi/v1/lending/project/position/list?{}&signature={}".format(query_string, signature), api_binance=True)['response'])


def get_open_orders():
    f = open("binance/order-wallet.txt", "w")
    f.write("")
    f.close()
    query_string = "timestamp=" + str(get_server_time())
    resp = make_request("https://api.binance.com/api/v3/openOrders?" + query_string + "&signature=" + generate_signature(query_string), api_binance=True)
    orders = loads(resp['response'])
    order_list = []
    for order in orders:
        order_list.append([order['side'], order['symbol'], order['price'], order['origQty'], str(float(order['price']) * float(order['origQty']))])
    f = open("binance/order-wallet.txt", "a")
    f.write(tabulate(order_list, headers=['TYPE', 'ASSET', 'PRICE', 'QTY', 'TOTAL'], tablefmt='orgtbl', floatfmt=".8f") + "\n\n\n")
    f.close()


def get_order_history():
    order_list = []
    buy_sell_orders = {}
    for key in Config.settings['binance']['symbols'].keys():
        info(key)
        params = "timestamp=" + str(get_server_time()) + "&symbol=" + key
        resp = make_request("https://api.binance.com/api/v3/myTrades?" + params + "&signature=" + generate_signature(params), api_binance=True)
        orders = {}
        if resp['state'] is True:
            orders = loads(resp['response'])
        medium = 0
        qty_total = 0
        medium_sell = 0
        qty_total_sell = 0
        if key in Config.settings['binance']["orders"]:
            for order in Config.settings['binance']["orders"][key]:
                qty_total += order['amount']
                if "crypto" in order:
                    medium += order['amount'] * buy_sell_orders[order["crypto"] + "BUSD"]['buy']['medium']
                else:
                    medium += order['amount'] * order['value']
        for order in orders:
            type_order = "SELL"
            if order['isBuyer']:
                type_order = "BUY"
                medium += float(order['price']) * float(order['qty'])
                qty_total += float(order['qty'])
            else:
                medium_sell += float(order['price']) * float(order['qty'])
                qty_total_sell += float(order['qty'])
            order_list.append([type_order, order['symbol'], order['price'], order['qty'], order['commission'] + " " + order['commissionAsset'], order['quoteQty']])
        buy_sell_orders[key] = {}
        if qty_total > 0:
            buy_sell_orders[key]['buy'] = {
                'medium': medium / qty_total,
                'qty_total': qty_total
            }
        else:
            buy_sell_orders[key]['buy'] = {
                'medium': 0,
                'qty_total': 0
            }
        if qty_total_sell > 0:
            buy_sell_orders[key]['sell'] = {
                'medium': medium_sell / qty_total_sell,
                'qty_total': qty_total_sell
            }
        else:
            buy_sell_orders[key]['sell'] = {
                'medium': 0,
                'qty_total': 0
            }
    f = open("binance/order-wallet.txt", "a")
    f.write(tabulate(order_list, headers=['TYPE', 'ASSET', 'PRICE', 'QTY', 'FEE', 'TOTAL'], tablefmt='orgtbl', floatfmt=".8f") + "\n\n\n")
    f.close()
    return buy_sell_orders


def get_wallet(buy_sell_orders):
    assets_list = []
    total_total_margin = 0
    coin = 'USD'
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?CMC_PRO_API_KEY=e06c6aea-b4a6-422d-9f76-6ac205a5eae1&convert=" + coin + "&slug="
    for key in buy_sell_orders.keys():
        url += Config.settings['binance']["symbols"][key] + ","
    url = url[:-1]
    res_conv = list(loads(make_request(url)['response'])['data'].values())
    for key in buy_sell_orders.keys():
        cry = {}
        for cry in res_conv:
            if cry['slug'] == Config.settings['binance']["symbols"][key]:
                break
        info(key)
        res = str(make_request("https://coinmarketcap.com/currencies/" + cry['slug'])['response'])
        ath = res.split("<div>All Time High</div>")[1].split("<span>")[1].split("</span>")[0][1:]
        actual_value = cry['quote'][coin]['price']
        total_invest = buy_sell_orders[key]['buy']['qty_total'] * buy_sell_orders[key]['buy']['medium']
        total_return = buy_sell_orders[key]['sell']['qty_total'] * buy_sell_orders[key]['sell']['medium']
        mining_budget = 0
        total_margin = 0
        actual_margin = 0
        sell_mining = 0
        if key in Config.settings['binance']['mining']:
            mining_budget = Config.settings['binance']['mining'][key]
        if buy_sell_orders[key]['sell']['qty_total'] > 0:
            if buy_sell_orders[key]['sell']['qty_total'] > buy_sell_orders[key]['buy']['qty_total']:
                total_margin = total_return - total_invest
                sell_mining = buy_sell_orders[key]['sell']['qty_total'] - buy_sell_orders[key]['buy']['qty_total']
            else:
                total_margin = total_return - (buy_sell_orders[key]['sell']['qty_total'] * buy_sell_orders[key]['buy']['medium'])
        actual_budget = mining_budget + buy_sell_orders[key]['buy']['qty_total'] - buy_sell_orders[key]['sell']['qty_total']
        if key.find("ADA") == 0:
            actual_budget -= 30.5
        sell_now = actual_budget * actual_value
        if actual_budget > 0:
            if sell_mining > 0:
                actual_margin = sell_now
            else:
                actual_margin = (sell_now - (mining_budget * actual_value)) - ((actual_budget - mining_budget) * buy_sell_orders[key]['buy']['medium'])
        final_margin = actual_margin + total_margin + ((mining_budget - sell_mining) * actual_value)
        total_total_margin += final_margin
        assets_list.append([key.replace("BUSD", ""), mining_budget, buy_sell_orders[key]['buy']['qty_total'], buy_sell_orders[key]['buy']['medium'], actual_value, ath, total_invest, buy_sell_orders[key]['sell']['qty_total'], buy_sell_orders[key]['sell']['medium'], total_return, total_margin, actual_budget, sell_now, actual_margin, final_margin])
    f = open("binance/order-wallet.txt", "a")
    f.write(tabulate(assets_list, headers=['ASSET', 'MINED', 'TOT BUY', 'AVG BUY', 'ACTUAL', 'ATH', 'TOT INVEST', 'TOT SELL', 'AVG SELL', 'TOT RETURN', 'TOT MARGIN', 'BUDGET', 'SELL NOW', 'MARGIN', 'FINAL MARGIN'], tablefmt='orgtbl', floatfmt=".6f") + "\n\n\n" + "TOTAL MARGIN: " + str(total_total_margin))
    f.close()
    assets_list_tg = []
    for asset in assets_list:
        if asset[11] > 0 and asset[3] > 0:
            assets_list_tg.append([asset[0], asset[3], asset[4], asset[11], asset[13]])
    to_ret = tabulate(assets_list_tg, headers=['ASSET', 'AVG BUY', 'ACTUAL', 'BUDGET', 'MARGIN'], tablefmt='orgtbl', floatfmt=".6f")
    assets_list.insert(0, ["ASSET", "MINED", 'TOT BUY', 'AVG BUY', 'ACTUAL', 'ATH', 'TOT INVEST', 'TOT SELL', 'AVG SELL', 'TOT RETURN', 'TOT MARGIN', 'BUDGET', 'SELL NOW', 'MARGIN', 'FINAL MARGIN'])
    with open('binance/assets.csv', 'w', newline='') as file:
        writer(file).writerows(assets_list)
    return to_ret

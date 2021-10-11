from utility import Config, make_request
from json import loads
from hmac import new
from hashlib import sha256
from tabulate import tabulate
from csv import writer
from matplotlib.pyplot import pie, legend, suptitle, axis, figure, close, cla
from matplotlib.backends.backend_pdf import PdfPages
from numpy import array


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
                if order['type'] == 'BUY':
                    qty_total += order['amount']
                    medium += order['amount'] * order['value']
                else:
                    qty_total_sell += order['amount']
                    medium_sell += order['amount'] * order['value']
                order_list.append([order['type'], key, order['value'], order['amount'], "", order['amount'] * order['value']])
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


def calculate_budget_coin(buy_sell_orders, key):
    to_ret = {
        'mining': 0,
        'fee': 0
    }
    if key in Config.settings['binance']['mining']:
        to_ret['mining'] = Config.settings['binance']['mining'][key]
    if key in Config.settings['binance']['fee']:
        to_ret['fee'] = Config.settings['binance']['fee'][key]
    to_ret['budget'] = to_ret['mining'] + buy_sell_orders['buy']['qty_total'] - buy_sell_orders['sell']['qty_total'] - to_ret['fee']
    return to_ret


def prepare_url_coinmarketcap(buy_sell_orders, coin):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?CMC_PRO_API_KEY=e06c6aea-b4a6-422d-9f76-6ac205a5eae1&convert=" + coin + "&slug="
    for key in buy_sell_orders.keys():
        if Config.settings['binance']["symbols"][key][:2] != '0x':
            url += Config.settings['binance']["symbols"][key] + ","
    url += "celo-euro"
    return url


def get_ath_and_value(res_conv, key, coin):
    cry = {}
    to_ret = {}
    found = False
    for cry in res_conv:
        if cry['symbol'] == key.replace("BUSD", ""):
            found = True
            break
    if found:
        res = str(make_request("https://coinmarketcap.com/currencies/" + cry['slug'])['response'])
        to_ret['ath'] = res.split("<div>All Time High</div>")[1].split("<span>")[1].split("</span>")[0][1:]
        to_ret['actual_value'] = cry['quote'][coin]['price']
    else:
        addr = Config.settings['binance']["symbols"][key].split("-")[0]
        chain = Config.settings['binance']["symbols"][key].split("-")[1]
        to_ret['actual_value'] = round(loads(
            make_request(Config.settings["chain_defi"][chain]['url'] + addr + "/price?network=" + chain)['response'])[
                                 Config.settings["chain_defi"][chain]['key']], 5)
        to_ret['ath'] = 'N.D.'
    return to_ret


def prepare_output(output_data):
    gain = round(output_data['total_eur'] - output_data['total_deposit_eur'], 2)
    gain_perc = round(gain / output_data['total_deposit_eur'] * 100, 2)
    fig1 = figure(figsize=(7, 5))
    fig1.subplots_adjust(0.3, 0, 1, 0.9)
    patch, text = pie(array([p['perc'] for p in output_data['percs_wall_eur']]))
    legend(patch, [p['label'] for p in output_data['percs_wall_eur']], loc="upper left", prop={'size': 12}, bbox_to_anchor=(0.0, 0.65), bbox_transform=fig1.transFigure)
    axis('equal')
    suptitle(f"\nDEPOSIT: {round(output_data['total_deposit_eur'], 2)}€    NOW: {round(output_data['total_eur'], 2)}€    GAIN: {gain}€ ({gain_perc}%)")
    fig2 = figure(figsize=(7, 5))
    fig2.subplots_adjust(0.3, 0, 1, 0.9)
    patch, text = pie(array([p['perc'] for p in output_data['percs_wall']]))
    legend(patch, [p['label'] for p in output_data['percs_wall']], loc="upper left", prop={'size': 9}, bbox_to_anchor=(0.0, 0.8), bbox_transform=fig2.transFigure)
    axis('equal')
    suptitle("\nTOTAL CRYPTO: " + str(round(output_data['total_balance'], 2)) + "$ - " + str(round(output_data['total_balance_crypto_eur'], 2)) + "€")
    pdf = PdfPages("binance/wallet-allocation.pdf")
    for fig in range(1, figure().number):
        pdf.savefig(fig)
    pdf.close()
    fig1.clear()
    fig2.clear()
    cla()
    close("all")
    head = ['ASSET', 'MINED/FEE', 'TOT BUY', 'TOT SELL', 'AVG BUY', 'AVG SELL', 'ACTUAL', 'ATH', 'TOT INVEST', 'TOT RETURN', 'TOT MARGIN', 'BUDGET', 'SELL NOW', 'MARGIN', 'FINAL MARGIN']
    f = open("binance/order-wallet.txt", "a")
    f.write(tabulate(output_data['assets_list'], headers=head, tablefmt='orgtbl', floatfmt=".6f") + "\n\n\n" + "TOTAL INVEST: " +
            str(round(output_data['total_total_invest'], 2)) + "$  TOTAL MARGIN: " + str(round(output_data['total_total_margin'], 2)) +
            "$   TOTAL BALANCE: " + str(round(output_data['total_balance'], 2)) + "$ - " + str(round(output_data['total_balance_crypto_eur'], 2)) +
            "€\n\nTOTAL STABLECOIN: " + str(round(output_data['total_balance_stable'], 2)) + "$ - " + str(round(output_data['total_balance_stable_eur'], 2)) +
            "€\n\nTOTAL DEPOSIT: " + str(round(output_data['total_deposit_eur'], 2)) + "€   TOTAL BALANCE: " + str(round(output_data['total_balance_eur'], 2)) + "€   TOTAL: " + str(round(output_data['total_eur'], 2)) + "€")
    f.close()
    assets_list_tg = []
    for asset in output_data['assets_list']:
        if asset[11] > 0:
            assets_list_tg.append([asset[0], asset[4], asset[6], asset[11], asset[14]])
    output_data['assets_list'].insert(0, head)
    with open('binance/assets.csv', 'w', newline='') as file:
        writer(file).writerows(output_data['assets_list'])
    return tabulate(assets_list_tg, headers=['ASSET', 'AVG BUY', 'ACTUAL', 'BUDGET', 'FINAL MARGIN'], tablefmt='orgtbl', floatfmt=".4f")


def get_wallet(buy_sell_orders):
    output_data = {
        'assets_list': [],
        'percs_wall': [],
        'percs_wall_eur': [],
        'total_total_invest': 0,
        'total_total_margin': 0,
        'total_balance': 0
    }
    coin = 'USD'
    res_conv = list(loads(make_request(prepare_url_coinmarketcap(buy_sell_orders, coin))['response'])['data'].values())
    for key in buy_sell_orders.keys():
        value_and_ath = get_ath_and_value(res_conv, key, coin)
        total_invest = buy_sell_orders[key]['buy']['qty_total'] * buy_sell_orders[key]['buy']['medium']
        total_return = buy_sell_orders[key]['sell']['qty_total'] * buy_sell_orders[key]['sell']['medium']
        total_margin = 0
        actual_margin = 0
        sell_mining = 0
        actual_budget = calculate_budget_coin(buy_sell_orders[key], key)
        if buy_sell_orders[key]['sell']['qty_total'] > 0 or actual_budget['fee'] > 0:
            if buy_sell_orders[key]['sell']['qty_total'] > buy_sell_orders[key]['buy']['qty_total']:
                total_margin = total_return - total_invest - (actual_budget['fee'] * buy_sell_orders[key]['buy']['medium'])
                sell_mining = buy_sell_orders[key]['sell']['qty_total'] - buy_sell_orders[key]['buy']['qty_total']
            else:
                total_margin = total_return - ((buy_sell_orders[key]['sell']['qty_total'] + actual_budget['fee']) * buy_sell_orders[key]['buy']['medium'])
        sell_now = actual_budget['budget'] * value_and_ath['actual_value']
        output_data['total_balance'] += sell_now
        if actual_budget['budget'] > 0:
            output_data['percs_wall'].append({'perc': sell_now, 'label': key.replace("BUSD", "") + " - " + str(round(sell_now, 2)) + "$ "})
            if sell_mining > 0:
                actual_margin = sell_now
            else:
                actual_margin = (sell_now - (actual_budget['mining'] * value_and_ath['actual_value'])) - ((actual_budget['budget'] - actual_budget['mining']) * buy_sell_orders[key]['buy']['medium'])
        if sell_mining > 0:
            final_margin = actual_margin + total_margin
        else:
            final_margin = actual_margin + total_margin + ((actual_budget['mining'] - sell_mining) * value_and_ath['actual_value'])
        output_data['total_total_invest'] += total_invest - total_return
        output_data['total_total_margin'] += final_margin
        output_data['assets_list'].append([key.replace("BUSD", ""), actual_budget['mining'] - actual_budget['fee'], buy_sell_orders[key]['buy']['qty_total'], buy_sell_orders[key]['sell']['qty_total'], buy_sell_orders[key]['buy']['medium'], buy_sell_orders[key]['sell']['medium'], value_and_ath['actual_value'], value_and_ath['ath'], total_invest, total_return, total_margin, actual_budget['budget'], sell_now, actual_margin, final_margin])
    i = 0
    while i < len(output_data['percs_wall']):
        output_data['percs_wall'][i]['perc'] = (output_data['percs_wall'][i]['perc'] * 100) / output_data['total_balance']
        output_data['percs_wall'][i]['label'] += f"({round(output_data['percs_wall'][i]['perc'], 2)}%)"
        i += 1
    output_data['total_balance_stable'] = sum(Config.settings["binance"]["stablecoin"]["USD"])
    output_data['total_balance_crypto_eur'] = output_data['total_balance'] / get_ath_and_value(res_conv, 'CEUR', coin)['actual_value']
    output_data['total_balance_stable_eur'] = output_data['total_balance_stable'] / get_ath_and_value(res_conv, 'CEUR', coin)['actual_value']
    output_data['total_deposit_eur'] = sum(Config.settings["binance"]["deposits"]) - sum(Config.settings["binance"]["card"]["add"]) + Config.settings["binance"]["card"]["res"]
    output_data['total_balance_eur'] = sum(Config.settings["binance"]["stablecoin"]["EUR"]) + Config.settings["binance"]["card"]["res"]
    output_data['total_eur'] = output_data['total_balance_eur'] + output_data['total_balance_stable_eur'] + output_data['total_balance_crypto_eur']
    output_data['percs_wall_eur'].append({"perc": (output_data['total_balance_crypto_eur'] * 100) / output_data['total_eur'], "label": f"CRYPTO perc\n{round(output_data['total_balance_crypto_eur'], 2)}€"})
    output_data['percs_wall_eur'].append({"perc": (output_data['total_balance_stable_eur'] * 100) / output_data['total_eur'], "label": f"STABLE perc\n{round(output_data['total_balance_stable_eur'], 2)}€"})
    output_data['percs_wall_eur'].append({"perc": (output_data['total_balance_eur'] * 100) / output_data['total_eur'], "label": f"EUR perc\n{round(output_data['total_balance_eur'], 2)}€"})
    i = 0
    while i < len(output_data['percs_wall_eur']):
        output_data['percs_wall_eur'][i]['label'] = output_data['percs_wall_eur'][i]['label'].replace("perc", f"({round(output_data['percs_wall_eur'][i]['perc'], 2)}%)")
        i += 1
    output_data['assets_list'].sort(key=lambda x: x[12], reverse=True)
    output_data['percs_wall'].sort(key=lambda x: x['perc'], reverse=True)
    output_data['percs_wall_eur'].sort(key=lambda x: x['perc'], reverse=True)
    return prepare_output(output_data)

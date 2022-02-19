from utility import Config, make_request
from json import loads
from hmac import new
from hashlib import sha256
from tabulate import tabulate
from logic import be_get_token_defi_value
from matplotlib import use
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


def get_locked_savings_balance(asset):
    query_string = "asset={}&status=HOLDING&timestamp={}".format(asset, str(get_server_time()))
    signature = generate_signature(query_string)
    return loads(make_request("https://api.binance.com/sapi/v1/lending/project/position/list?{}&signature={}".format(query_string, signature), api_binance=True)['response'])


def get_intrest_history():
    query_string = "lendingType=CUSTOMIZED_FIXED&timestamp={}".format(str(get_server_time()))
    signature = generate_signature(query_string)
    return loads(make_request("https://api.binance.com/sapi/v1/lending/union/interestHistory?{}&signature={}".format(query_string, signature), api_binance=True)['response'])


def get_spot_balance():
    to_ret = {}
    params = "timestamp=" + str(get_server_time())
    resp = make_request("https://api.binance.com/api/v3/account?" + params + "&signature=" + generate_signature(params), api_binance=True)
    for coin in loads(resp['response'])["balances"]:
        if float(coin["free"]) + float(coin["locked"]) > 0:
            to_ret[coin["asset"]] = float(coin["free"]) + float(coin["locked"])
    return to_ret


def get_open_orders(filename):
    f = open(filename, "w")
    f.write("")
    f.close()
    query_string = "timestamp=" + str(get_server_time())
    resp = make_request("https://api.binance.com/api/v3/openOrders?" + query_string + "&signature=" + generate_signature(query_string), api_binance=True)
    orders = loads(resp['response'])
    order_list = []
    for order in orders:
        order_list.append([order['side'], order['symbol'], order['price'], order['origQty'], str(float(order['price']) * float(order['origQty']))])
    f = open(filename, "a")
    f.write(tabulate(order_list, headers=['TYPE', 'ASSET', 'PRICE', 'QTY', 'TOTAL'], tablefmt='orgtbl', floatfmt=".8f") + "\n\n\n")
    f.close()


def get_order_history(filename):
    order_list = []
    buy_sell_orders = {}
    for key in Config.settings['binance']['symbols'].keys():
        params = "timestamp=" + str(get_server_time()) + "&symbol=" + key
        resp = make_request("https://api.binance.com/api/v3/myTrades?" + params + "&signature=" + generate_signature(params), api_binance=True)
        orders = {}
        if resp['state'] is True:
            orders = loads(resp['response'])
        medium, qty_total, medium_sell, qty_total_sell = 0, 0, 0, 0
        if key in Config.orders:
            for order in Config.orders[key]:
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
        buy_sell_orders[key] = {
            'buy': {'medium': 0, 'qty_total': 0},
            'sell': {'medium': 0, 'qty_total': 0}
        }
        if qty_total > 0:
            buy_sell_orders[key]['buy'] = {'medium': medium / qty_total, 'qty_total': qty_total}
        if qty_total_sell > 0:
            buy_sell_orders[key]['sell'] = {'medium': medium_sell / qty_total_sell, 'qty_total': qty_total_sell}
    f = open(filename, "a")
    f.write(tabulate(order_list, headers=['TYPE', 'ASSET', 'PRICE', 'QTY', 'FEE', 'TOTAL'], tablefmt='orgtbl', floatfmt=".8f") + "\n\n\n")
    f.close()
    return buy_sell_orders


def calculate_budget_coin(buy_sell_orders, key):
    to_ret = {'mining': 0, 'fee': 0}
    if key in Config.settings['binance']['mining']:
        to_ret['mining'] = Config.settings['binance']['mining'][key]
    if key in Config.settings['binance']['fee']:
        to_ret['fee'] = Config.settings['binance']['fee'][key]
    to_ret['budget'] = to_ret['mining'] + buy_sell_orders['buy']['qty_total'] - buy_sell_orders['sell']['qty_total'] - to_ret['fee']
    return to_ret


def prepare_url_coinmarketcap(buy_sell_orders, coin):
    url = f'{Config.settings["coinmarketcap"]["price_url"]}{Config.settings["coinmarketcap"]["key"]}&convert={coin}&slug='
    for key in buy_sell_orders.keys():
        if Config.settings['binance']["symbols"][key][:2] != '0x':
            url += Config.settings['binance']["symbols"][key] + ","
    url += "celo-euro"
    return url


def get_ath_and_value(res_conv, key, coin, ath=False):
    cry = {}
    to_ret = {}
    name = key.replace("BUSD", "")
    if key not in Config.settings['binance']["symbols"].keys() or Config.settings['binance']["symbols"][key][:2] != '0x':
        for cry in res_conv:
            if cry['symbol'] == name:
                break
        if ath:
            res = str(make_request("https://coinmarketcap.com/currencies/" + cry['slug'])['response'])
            to_ret['ath'] = res.split("<div>All Time High</div>")[1].split("<span>")[1].split("</span>")[0][1:]
        to_ret['actual_value'] = cry['quote'][coin]['price']
    else:
        addr = Config.settings['binance']["symbols"][key].split("-")[0]
        chain = Config.settings['binance']["symbols"][key].split("-")[1]
        to_ret['actual_value'] = be_get_token_defi_value({chain: {addr: name}})[name]
        if ath:
            to_ret['ath'] = 'N.D.'
    return to_ret


def prepare_output(output_data, file_name_order, file_name_pdf):
    gain = round(output_data['total_eur'] - output_data['total_deposit_eur'], 2)
    gain_perc = round(gain / output_data['total_deposit_eur'] * 100, 2)
    fig1 = figure(figsize=(7, 5))
    fig1.subplots_adjust(0.3, 0, 1, 0.9)
    patch, text = pie(array([p['perc'] for p in output_data['percs_wall_eur']]))
    legend(patch, [p['label'] for p in output_data['percs_wall_eur']], loc="upper left", prop={'size': 12}, bbox_to_anchor=(0.0, 0.65), bbox_transform=fig1.transFigure)
    axis('equal')
    suptitle(f"\nDEPOSIT: {round(output_data['total_deposit_eur'], 2)}€    NOW: {round(output_data['total_eur'], 2)}€    GAIN: {gain}€ ({gain_perc}%)\n")
    fig2 = figure(figsize=(7, 5))
    fig2.subplots_adjust(0.3, 0, 1, 0.9)
    patch, text = pie(array([p['perc'] for p in output_data['percs_wall']]))
    legend(patch, [p['label'] for p in output_data['percs_wall']], loc="upper left", prop={'size': 9}, bbox_to_anchor=(0.0, 0.9), bbox_transform=fig2.transFigure)
    axis('equal')
    suptitle(f"\nTOTAL INVEST CRYPTO: {round(output_data['total_total_invest_eur'], 2)}€  - TOTAL CRYPTO: {str(round(output_data['total_balance_crypto_eur'], 2))}€")
    pdf = PdfPages(file_name_pdf)
    for fig in range(1, figure().number):
        pdf.savefig(fig)
    pdf.close()
    fig1.clear()
    fig2.clear()
    cla()
    close("all")
    head_asset_list = ['ASSET', 'MINED/FEE', 'TOT BUY', 'TOT SELL', 'AVG BUY', 'AVG SELL', 'TOT INVEST', 'TOT RETURN', 'TOT MARGIN', 'SELL NOW']
    head_actual_list = ['ASSET', 'ACT INVEST', 'REAL AVG BUY',  'ACT AVG BUY', 'ACT PRICE', 'BUDGET', 'SELL NOW', 'MARGIN', 'FINAL MARGIN']
    f = open(file_name_order, "a")
    f.write(tabulate(output_data['assets_list'], headers=head_asset_list, tablefmt='orgtbl', floatfmt=".6f") + "\n\n\n" +
            tabulate(output_data['actual_list'], headers=head_actual_list, tablefmt='orgtbl', floatfmt=".6f") + "\n\n\n" +
            "TOTAL CRYPTO INVEST: " + str(round(output_data['total_total_invest_eur'], 2)) + "€ - " + str(round(output_data['total_total_invest'], 2)) + "$\n\n" +
            "TOTAL CRYPTO MARGIN: " + str(round(output_data['total_total_margin_eur'], 2)) + "€ - " + str(round(output_data['total_total_margin'], 2)) + "$\n\n" +
            "TOTAL CRYPTO BALANCE: " + str(round(output_data['total_balance_crypto_eur'], 2)) + "€ - " + str(round(output_data['total_balance'], 2)) + "$\n\n" +
            "TOTAL STABLECOIN: " + str(round(output_data['total_balance_stable_eur'], 2)) + "€ - " + str(round(output_data['total_balance_stable'], 2)) + "$\n\n" +
            "TOTAL EUR DEPOSIT: " + str(round(output_data['total_deposit_eur'], 2)) + "€\n\n" +
            "TOTAL EUR BALANCE: " + str(round(output_data['total_balance_eur'], 2)) + "€\n\n" +
            "TOTAL EUR IF SELL AL NOW: " + str(round(output_data['total_eur'], 2)) + "€\n\n" +
            "TOTAL EUR MARGIN: " + str(gain) + "€\n")
    f.close()
    assets_list_tg = []
    for asset in output_data['actual_list']:
        if asset[5] > 0:
            assets_list_tg.append([asset[0], asset[3], asset[4], asset[5], asset[8]])
    return tabulate(assets_list_tg, headers=['ASSET', 'AVG BUY', 'ACTUAL', 'BUDGET', 'FINAL MARGIN'], tablefmt='orgtbl', floatfmt=".4f")


def get_wallet(buy_sell_orders, file_name_order, file_name_pdf):
    output_data = {
        'assets_list': [],
        'actual_list': [],
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
        total_margin, actual_margin, sell_mining = 0, 0, 0
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
        my_actual_mid_buy = 0
        real_actual_mid_buy = 0
        my_actual_invest = 0
        output_data['total_total_margin'] += final_margin
        if actual_budget['budget'] > 0:
            if total_invest - total_return > 0:
                my_actual_invest = total_invest - total_return
                my_actual_mid_buy = my_actual_invest / actual_budget['budget']
                real_actual_mid_buy = my_actual_invest / (actual_budget['budget'] - actual_budget['mining'])
                output_data['total_total_invest'] += my_actual_invest
            output_data['actual_list'].append([key.replace("BUSD", ""), my_actual_invest, real_actual_mid_buy, my_actual_mid_buy, value_and_ath['actual_value'], actual_budget['budget'], sell_now, actual_margin, final_margin])
        output_data['assets_list'].append([key.replace("BUSD", ""), actual_budget['mining'] - actual_budget['fee'], buy_sell_orders[key]['buy']['qty_total'], buy_sell_orders[key]['sell']['qty_total'], buy_sell_orders[key]['buy']['medium'], buy_sell_orders[key]['sell']['medium'], total_invest, total_return, total_margin, sell_now])
    i = 0
    while i < len(output_data['percs_wall']):
        output_data['percs_wall'][i]['perc'] = (output_data['percs_wall'][i]['perc'] * 100) / output_data['total_balance']
        output_data['percs_wall'][i]['label'] += f"({round(output_data['percs_wall'][i]['perc'], 2)}%)"
        i += 1
    eur_value = get_ath_and_value(res_conv, 'CEUR', coin)['actual_value']
    output_data['total_total_margin_eur'] = output_data['total_total_margin'] / eur_value
    output_data['total_total_invest_eur'] = output_data['total_total_invest'] / eur_value
    output_data['total_balance_stable'] = sum(Config.settings["binance"]["stablecoin"]["USD"])
    output_data['total_balance_crypto_eur'] = output_data['total_balance'] / eur_value
    output_data['total_balance_stable_eur'] = output_data['total_balance_stable'] / eur_value
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
    output_data['assets_list'].sort(key=lambda x: x[9], reverse=True)
    output_data['actual_list'].sort(key=lambda x: x[6], reverse=True)
    output_data['percs_wall'].sort(key=lambda x: x['perc'], reverse=True)
    output_data['percs_wall_eur'].sort(key=lambda x: x['perc'], reverse=True)
    use('Agg')
    return prepare_output(output_data, file_name_order, file_name_pdf)

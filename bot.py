from telegram.ext import Updater, Filters, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from logging import basicConfig, INFO, exception
from utility import make_cmd, markdown_text, Config, get_separator, initial_log
from logic import be_get_public_ip, be_get_file_ovpn, get_nvidia_info, be_stop_miner, be_stop_server_vpn, get_program_status, be_set_trex_profile, be_start_access_point, be_stop_access_point, be_get_access_point_status, be_set_gpu_speed_fan, be_shutdown_system, get_meross_info, get_trex_info, get_miner_info, get_balance_info, be_get_apy_defi, be_get_link
from binance import get_open_orders, get_order_history, get_wallet
from pyrogram import Client
from time import sleep


def get_public_ip(update, context):
    initial_log("get_public_ip", context.args)
    update.message.reply_text(be_get_public_ip())


def get_file_ovpn(update, context):
    initial_log("get_file_ovpn", context.args)
    response = be_get_file_ovpn()
    if response == "OK":
        update.message.reply_document(open('ovpn/client.ovpn', 'r'))
    else:
        update.message.reply_text(response)


def get_apy_defi(update, context):
    initial_log("get_apy_defi", context.args)
    update.message.reply_text(be_get_apy_defi())


def get_binance_status(update, context):
    initial_log("get_binance_status", context.args)
    get_open_orders()
    buy_sell_orders = get_order_history()
    update.message.reply_text(get_wallet(buy_sell_orders))
    update.message.reply_document(open('binance/order-wallet.txt', 'r'))


def get_balance_status(update, context):
    initial_log("get_balance_status", context.args)
    ret_str = ""
    total_euro = 0
    for key, value in Config.settings['cryptos'].items():
        balance_info = get_balance_info(key, value['wallets'])
        total_euro = total_euro + balance_info['tot_eur_value']
        ret_str = ret_str + get_separator(key.upper()) + "*VALUE:* " + balance_info['conv_eur'] + "   *WALLET NUMBER:* " + str(len(balance_info['walletts'].keys())) + "\n" + get_separator()
        for key_b, value_b in balance_info['walletts'].items():
            ret_str = ret_str + "*WALLET:* " + key_b.replace("_", " ").title() + "\n*ID*: " + value_b['id'] + "\n*CRYPTO:* " + value_b['crypto_value'] + " *FIAT:* " + value_b['eur_value'] + "\n" + get_separator()
        ret_str = ret_str + "*TOT CRYPTO:* " + balance_info['tot_crypto_value'] + " *FIAT:* " + str(balance_info['tot_eur_value']) + " €\n"
    ret_str = ret_str + get_separator("FINAL RECAP") + "*TOTAL EURO:* " + str(round(total_euro, 2)) + " €"
    update.message.reply_text(markdown_text(ret_str), parse_mode='MarkdownV2')


def get_mining_status(update, context):
    initial_log("get_mining_status", context.args)
    try:
        pow_str = ""
        if Config.settings['meross'] != {}:
            meross_info = get_meross_info()
            if meross_info['state'] is True:
                pow_str = "*TOTAL POWER CONSUME:* " + meross_info['power'] + "\n"
        trex_info = get_trex_info()
        uptime = "*UPTIME:* " + trex_info['uptime']
        pool_url = "*POOL:* " + trex_info['pool_url']
        wallet_id = "*WALLET:* " + trex_info['wallet_id']
        total_share = "*SHA TOT:* " + trex_info['total_share']
        share_min = "*MIN:* " + trex_info['share_min']
        share_min_avg = "*AVG:* " + trex_info['share_min_avg']
        general_str = get_separator("GENERAL") + uptime + "\n" + wallet_id + "\n" + pool_url + "\n" + total_share + " " + share_min + " " + share_min_avg + "\n"
        first = True
        gpu_str = ""
        gpu_list = []
        for t in trex_info['gpus']:
            for n in get_nvidia_info():
                if n['uuid'] == t['uuid']:
                    gpu_list.append(n | t)
        for gpu in gpu_list:
            if not first:
                gpu_str = gpu_str + get_separator()
            else:
                gpu_str = get_separator("GPU LIST")
                first = False
            gpu_name = "*GPU:* " + gpu['gpu_name']
            gpu_efficency = "*EFFICIENCY:* " + gpu['gpu_efficency']
            intensity = "*INTENSITY:* " + gpu['intensity']
            accepted_count = "*SHARE:* " + gpu['accepted_count']
            reported_hashrate = "*HASHRATE:* " + gpu['reported_hashrate']
            gpu_fan = "*FAN:* " + gpu['fan']
            gpu_temp = "*TEMP:* " + gpu['temp']
            gpu_pow = "*POW:* " + gpu['power']
            gpu_mem_used = "*RAM USE:* " + gpu['mem_used']
            gpu_mem_free = "*FREE:* " + gpu['mem_free']
            gpu_usage = "*LOAD:* " + gpu['load']
            gpu_str = gpu_str + gpu_name + " " + gpu_usage + "\n" + intensity + " " + gpu_efficency + "\n" + reported_hashrate + " " + accepted_count + "\n"
            gpu_str = gpu_str + gpu_fan + " " + gpu_pow + " " + gpu_temp + "\n" + gpu_mem_used + " " + gpu_mem_free + "\n"
        miner_info = get_miner_info(trex_info['cur_trex_profile'], trex_info['wallet_id'])
        balance_info = get_balance_info(Config.settings['trex']['profiles'][trex_info['cur_trex_profile']]['crypto'], {"trex": trex_info['wallet_id']})
        immature_balance = ""
        if 'immature_balance' in miner_info:
            immature_balance = "*IMMATURE:* " + miner_info['immature_balance'] + "\n"
        unpaid_balance = "*UNPAID:* " + miner_info['unpaid_balance']
        estimated_earning = "*EST:* " + miner_info['estimated_earning']
        total_earning = "*TOT CRYPTO*: " + balance_info['tot_crypto_value']
        total_earning_euro = "*FIAT*: " + str(balance_info['tot_eur_value']) + " €"
        pay_str = get_separator("PAYOUT") + immature_balance + unpaid_balance + " " + estimated_earning + "\n" + total_earning + " " + total_earning_euro + "\n"
        total_reported_hashrate = "*R:* " + trex_info['total_reported_hashrate']
        current_hashrate = "*C:* " + miner_info['current_hashrate']
        average_hashrate = "*A(6h):* " + miner_info['average_hashrate']
        active_worker = "*WORKERS:* " + miner_info['active_worker']
        valid_shares = ""
        stale_shares = ""
        invalid_shares = ""
        if 'valid_shares' in miner_info:
            valid_shares = "*SHARES:* " + miner_info['valid_shares'] + "*V*"
            stale_shares = miner_info['stale_shares'] + "*S*"
            invalid_shares = miner_info['invalid_shares'] + "*I*"
        work_str = get_separator("WORKER") + total_reported_hashrate + " " + current_hashrate + " " + average_hashrate + "\n"
        work_str = work_str + active_worker + " " + valid_shares + " " + stale_shares + " " + invalid_shares
        update.message.reply_text(markdown_text(pow_str + general_str + gpu_str + pay_str + work_str), parse_mode='MarkdownV2')
    except Exception as e:
        exception(e)
        update.message.reply_text("ERRORE: " + str(e))


def stop_miner(update, context):
    initial_log("stop_miner", context.args)
    update.message.reply_text(be_stop_miner())


def shutdown_system(update, context):
    initial_log("shutdown_system", context.args)
    vpn = get_program_status("openvpn-gui", "OPENVPN")
    if vpn.find("ACCESO") > -1:
        ret_str = be_stop_server_vpn() + "\n"
    else:
        ret_str = vpn + "\n"
    trex = get_program_status("t-rex", "T-REX")
    if trex.find("ACCESO") > -1:
        ret_str = ret_str + be_stop_miner() + "\n"
    else:
        ret_str = ret_str + trex + "\n"
    ap = be_get_access_point_status()
    if ap['status'] == 'Avviato':
        ret_str = ret_str + be_stop_access_point() + "\n"
    else:
        ret_str = ret_str + 'AP ' + ap['status'] + "\n"
    ret_str = ret_str + be_shutdown_system()
    update.message.reply_text(ret_str)


def start_server_vpn(update, context):
    initial_log("start_server_vpn", context.args)
    make_cmd("start openvpn-gui --connect server.ovpn", sys=True)
    update.message.reply_text("SERVER VPN ACCESO")


def stop_server_vpn(update, context):
    initial_log("stop_server_vpn", context.args)
    update.message.reply_text(be_stop_server_vpn())


def get_status_server_vpn(update, context):
    initial_log("get_status_server_vpn", context.args)
    update.message.reply_text(get_program_status("openvpn-gui", "OPENVPN"))


def get_trex_profiles(update, context):
    initial_log("get_trex_profile", context.args)
    ret_str = ""
    first = True
    for key, value in Config.settings['trex']['profiles'].items():
        if not first:
            ret_str += get_separator()
        else:
            first = False
        name = "*NAME:* " + key
        crypto = "*CRYPTO:* " + value['crypto']
        intensity = "*INTENSITY:* " + str(value['intensity'])[1:-1]
        pool_url = "*POOL URL:* " + value['pool_url']
        wallet_id = "*WALLET ID:* " + value['wallet']
        ret_str += name + " " + crypto + "\n" + intensity + "\n" + pool_url + "\n" + wallet_id + "\n"
    update.message.reply_text(markdown_text(ret_str), parse_mode='MarkdownV2')


def start_miner(update, context):
    initial_log("start_miner", context.args)
    make_cmd("start /d trex t-rex.exe -c config.json", sys=True)
    update.message.reply_text("MINER ATTIVATO")


def set_trex_profile(update, context):
    if context.args is not None:
        initial_log("set_trex_profile", context.args)
        trex_profile_list = list(Config.settings['trex']['profiles'].keys())
        button_list = []
        for i in range(0, len(trex_profile_list), 2):
            profiles = trex_profile_list[i:i + 2]
            row = []
            for profile in profiles:
                row.append(InlineKeyboardButton(profile, callback_data="set_trex_profile " + profile))
            button_list.append(row)
        update.message.reply_text("SCEGLI UN PROFILO", reply_markup=InlineKeyboardMarkup(button_list))
    else:
        callback_data = update.callback_query.data
        initial_log("set_trex_profile", callback_data.split(" ")[1:])
        ret_str = be_set_trex_profile(callback_data.replace("set_trex_profile ", ""))
        update.callback_query.answer()
        update.callback_query.message.edit_text(text=ret_str)


def start_access_point(update, context):
    initial_log("start_access_point", context.args)
    update.message.reply_text(be_start_access_point())


def stop_access_point(update, context):
    initial_log("stop_access_point", context.args)
    update.message.reply_text(be_stop_access_point())


def get_access_point_status(update, context):
    initial_log("get_access_point_status", context.args)
    try:
        response = be_get_access_point_status()
        if response['state'] is True:
            ret_str = '*SSID:* ' + response['name'] + "\n*PASSWORD:* " + response['password'] + "\n*STATO:* " + response['status']
            if 'client' in response:
                ret_str = ret_str + " *CLIENT: *" + response['client']
            if 'clients' in response:
                for key, value in response['clients'].items():
                    ret_str = ret_str + "\n*MAC:* " + key + " *IP:* " + value
        else:
            ret_str = response["status"]
        update.message.reply_text(markdown_text(ret_str), parse_mode='MarkdownV2')
    except Exception as e:
        exception(e)
        update.message.reply_text("ERRORE: " + str(e))


def set_gpu_speed_fan(update, context):
    initial_log("set_gpu_speed_fan", context.args)
    gpu_list = Config.settings['afterburner']['gpus'].keys()
    if len(context.args) == 2:
        if context.args[0] in gpu_list:
            try:
                min_fan_speed = Config.settings['afterburner']['gpus'][context.args[0]]['min_fan_speed']
                if min_fan_speed <= int(context.args[1]) <= 100:
                    ret_str = be_set_gpu_speed_fan(context.args[0], context.args[1])
                else:
                    ret_str = "LA VELOCITA DEVE AVERE UN VALORE COMPRESO TRA " + str(min_fan_speed) + " E 100"
            except ValueError:
                ret_str = "LA VELOCITA DEVE ESSERE UN NUMERO INTERO"
        else:
            ret_str = "GPU INESISTENTE\nIL NOME DELLA GPU PUO ESSERE: " + ', '.join(gpu_list)
    else:
        ret_str = "È NECESSARIO SPECIFICARE DUE PARAMETRI: NOME GPU E VELOCITA\nIL NOME DELLA GPU PUO ESSERE: " + ', '.join(gpu_list) + "\nLA VELOCITA DEVE ESSERE UN NUMERO INTERO"
    update.message.reply_text(ret_str)


def get_link(update, context):
    initial_log("get_link", context.args)
    if len(context.args) == 2:
        update.message.reply_text(be_get_link(context.args[0], context.args[1]))


def my_add_handler(struct_commands, disp, cmd_filter):
    ret_str = ""
    for key, value in struct_commands.items():
        ret_str += key + " - " + value + "\n"
        disp.add_handler(CommandHandler(key, eval(key), cmd_filter))
    return ret_str


def main():
    basicConfig(
        filename=None,  # "bot.log",
        format="%(asctime)s|%(levelname)s|%(filename)s:%(lineno)s|%(message)s",
        level=INFO)
    Config()
    upd = Updater(Config.settings['bot_telegram']['token'], use_context=True)
    commands = {
        "mining": {
            "get_balance_status": "Restituisce il bilancio di tutte le crypto",
            "get_mining_status": "Restituisce lo stato del miner",
            "start_miner": "Avvia il miner",
            "stop_miner": "Arresta il miner",
            "set_gpu_speed_fan": "Setta la velocità della ventola della GPU",
            "get_trex_profiles": "Restituisce la lista dei profili t-rex",
            "set_trex_profile": "Imposta il profilo per t-rex"
        },
        "vpn": {
            "get_status_server_vpn": "Restituisce lo stato del server VPN",
            "start_server_vpn": "Avvia il server VPN",
            "stop_server_vpn": "Arreta il server VPN",
            "get_file_ovpn": "Restituisce il file per il client Open VPN"
        },
        "ap": {
            "start_access_point": "Avvia l'access point",
            "stop_access_point": "Arresta l'access point",
            "get_access_point_status": "Restituisce lo stato dell'access point"
        },
        "cross": {
            "get_apy_defi": "Recupera APY DeFi",
            "get_binance_status": "Riepilogo Binance",
            "shutdown_system": "Arresta il sistema",
            "get_public_ip": "Restituisce IP pubblico del server"
        },
        "football": {
            "get_link": "Recupera link per partite"
        }
    }
    cmd_str = ""
    for key, value in Config.settings['function'].items():
        if value is True:
            cmd_str += my_add_handler(commands[key], upd.dispatcher, Filters.user(username=set(Config.settings['users_abil'])))
    upd.dispatcher.add_handler(CallbackQueryHandler(set_trex_profile, pattern=r'^set_trex_profile'))
    with Client("my_account", Config.settings['client_telegram']['api_id'], Config.settings['client_telegram']['api_hash'], phone_number=Config.settings['client_telegram']['phone_number']) as app:
        app.send_message("@BotFather", "/setcommands")
        sleep(1)
        app.send_message("@BotFather", "@" + Config.settings['bot_telegram']['username'])
        sleep(1)
        app.send_message("@BotFather", cmd_str)
    upd.start_polling()
    upd.idle()


if __name__ == '__main__':
    main()

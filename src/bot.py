from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, Filters, CommandHandler, CallbackQueryHandler, MessageHandler
from logging import basicConfig, INFO, exception
from utility import make_cmd, markdown_text, Config, get_separator, initial_log, make_button_list
from logic import be_get_public_ip, be_get_file_ovpn, get_nvidia_info, be_stop_miner, be_stop_server_vpn, get_program_status, be_set_trex_profile, be_start_access_point, be_stop_access_point, be_get_access_point_status, be_set_gpu_speed_fan, be_shutdown_system, get_meross_info, get_trex_info, get_miner_info, be_get_link_event, be_get_token_defi_value, be_get_link_acestream, be_status_generali, be_youtube_download
from binance import get_open_orders, get_order_history, get_wallet
from pyrogram import Client
from time import sleep
from re import escape
from os import remove

commands = {
    "crypto": {
        "icon": 'Crypto 💰',
        "row_size": 3,
        "desc": "Funzioni crypto",
        "commands": {
            "get_invest_status": {
                "icon": "Total Balance 💰",
                "desc": "Riepilogo degli investimenti"
            },
            "get_balance_defi": {
                "icon": "DeFi Balance 💰",
                "desc": "Restituisce il bilancio di tutte le crypto"
            },
            "get_value_token_defi": {
                "icon": "Token DeFi 💰",
                "desc": "Recupera il valore dei token DeFi",
            }
        }
    },
    "mining": {
        "icon": 'Mining ⛏',
        "row_size": 3,
        "desc": "Funzioni mining",
        "commands": {
            "get_mining_status": {
                "icon": "Status ⛏",
                "desc": "Restituisce lo stato del miner"
            },
            "start_miner": {
                "icon": "Start ⛏",
                "desc": "Avvia il miner"
            },
            "stop_miner": {
                "icon": "Stop ⛏",
                "desc": "Arresta il miner"
            },
            "set_gpu_speed_fan": {
                "icon": "Set Fan ⛏",
                "desc": "Setta la velocità della ventola della GPU"
            },
            "get_trex_profiles": {
                "icon": "Get Profiles ⛏",
                "desc": "Restituisce la lista dei profili t-rex"
            },
            "set_trex_profile": {
                "icon": "Set Profiles ⛏",
                "desc": "Imposta il profilo per t-rex"
            }
        }
    },
    "vpn": {
        "icon": "VPN 🔐",
        "desc": "Funzioni VPN",
        "row_size": 2,
        "commands": {
            "get_status_server_vpn": {
                "icon": "Status 🔐",
                "desc": "Restituisce lo stato del server VPN"
            },
            "get_file_ovpn": {
                "icon": "Client File 🔐",
                "desc": "Restituisce il file per il client Open VPN"
            },
            "start_server_vpn": {
                "icon": "Start 🔐",
                "desc": "Avvia il server VPN"
            },
            "stop_server_vpn": {
                "icon": "Stop 🔐",
                "desc": "Arreta il server VPN"
            }
        }
    },
    "ap": {
        "icon": "Access Point 📡",
        "row_size": 3,
        "desc": "Funzioni AP",
        "commands": {
            "get_access_point_status": {
                "icon": "Status 📡",
                "desc": "Restituisce lo stato dell'access point"
            },
            "start_access_point": {
                "icon": "Start 📡",
                "desc": "Avvia l'access point"
            },
            "stop_access_point": {
                "icon": "Stop 📡",
                "desc": "Arresta l'access point"
            }
        }
    },
    "football": {
        "icon": "Football ⚽",
        "row_size": 1,
        "desc": "Funzioni football",
        "commands": {
            "get_link": {
                "icon": "Link ⚽",
                "desc": "Recupera link per partite"
            }
        }
    },
    "cross": {
        "icon": "Cross 🔮",
        "row_size": 3,
        "desc": "Funzioni cross",
        "commands": {
            "status_generali": {
                "icon": "Generali 🔮",
                "desc": "Recupera lo stato dell'investimetno in generali"
            },
            "download_youtube_music": {
                "icon": "Download Music 🔮",
                "desc": "Scarica canzoni da youtube (max 50 alla volta)"
            },
            "shutdown_system": {
                "icon": "Shutdown 🔮",
                "desc": "Arresta il sistema"
            },
            "get_public_ip": {
                "icon": "Public IP 🔮",
                "desc": "Restituisce IP pubblico del server"
            },
            "get_config": {
                "icon": "Get Config 🔮",
                "desc": "Restituisce il file di configurazione del bot"
            },
            "update_config": {
                "icon": "Update Config 🔮",
                "desc": "Aggiorna il file di configurazione del bot"
            },
            "reload_config": {
                "icon": "Reload Config 🔮",
                "desc": "Ricarica il file di configurazione del bot"
            }
        }
    }
}


def download_youtube_music(update, context):
    initial_log("download_youtube_music", context.args)
    Config.download = True
    update.message.reply_text("INVIARE LISTA CANZONI")


def download_music(update, context):
    initial_log("download_music", context.args)
    if Config.download:
        file_name = "canzoni.zip"
        Config.download = False
        be_youtube_download(update.message.text)
        update.message.reply_document(open(file_name, 'rb'), timeout=10000)
        remove(file_name)


def update_config(update, context):
    initial_log("update_config", context.args)
    Config.update_conf = True
    update.message.reply_text("INVIARE IL FILE")


def doc_handler(update, context):
    initial_log("doc_handler", context)
    if update.message.document.file_name in Config.settings['config_doc'] and update.message.document.mime_type == "application/json":
        if Config.update_conf:
            f = context.bot.getFile(update.message.document.file_id)
            f.download(f"../config/{update.message.document.file_name}")
            Config.update_conf = False
            to_ret = "FILE DI CONFIGURAZIONE AGGIORNATO!"
        else:
            to_ret = "AGGIORNAMENTO FILE DI CONFIGURAZIONE NON ABILITATO!"
        update.message.reply_text(to_ret)


def reload_config(update, context):
    initial_log("reload_config", context.args)
    Config().reload()
    update.message.reply_text("FILE DI CONFIGURAZIONE RICARICATI!")


def get_config(update, context):
    initial_log("get_config", context.args)
    for d in Config.settings['config_doc']:
        update.message.reply_document(open(f'../config/{d}', 'r'))


def status_generali(update, context):
    initial_log("status_generali", context.args)
    update.message.reply_text(be_status_generali())


def get_public_ip(update, context):
    initial_log("get_public_ip", context.args)
    update.message.reply_text(be_get_public_ip())


def get_file_ovpn(update, context):
    initial_log("get_file_ovpn", context.args)
    file_name = "client.ovpn"
    response = be_get_file_ovpn(file_name)
    if response == "OK":
        update.message.reply_document(open(file_name, 'r'))
        remove(file_name)
    else:
        update.message.reply_text(response)


def get_value_token_defi(update, context):
    initial_log("get_value_token_defi", context.args)
    response = ""
    for key, value in be_get_token_defi_value(Config.token.copy()).items():
        response += f"*{key}:* {str(value)}$\n"
    update.message.reply_text(markdown_text(response), parse_mode='MarkdownV2')


def get_invest_status(update, context):
    initial_log("get_invest_status", context.args)
    order_file = 'order-wallet.txt'
    pdf_file = 'wallet-allocation.pdf'
    get_open_orders(order_file)
    buy_sell_orders = get_order_history(order_file)
    update.message.reply_text(get_wallet(buy_sell_orders, order_file, pdf_file))
    update.message.reply_document(open(order_file, 'r'))
    update.message.reply_document(open(pdf_file, 'rb'))
    remove(order_file)
    remove(pdf_file)


def get_balance_defi(update, context):
    initial_log("get_balance_defi", context.args)
    ret_str = ""
    total_usd = 0
    update.message.reply_text('funzione sospesa')
    '''
    for key, value in Config.settings['wallet_defi'].items():
        balance_info = {}
        total_usd += balance_info['tot_usd_value']
        ret_str += get_separator(key.replace("_", " ").upper()) + "*ID:* " + value['id'] + "\n*VALUE:* " + str(balance_info['tot_usd_value']) + " $\n"
        for key_c, value_c in balance_info["chain"].items():
            ret_str += get_separator()
            ret_str += "*CHAIN:* " + key_c.upper() + "\n"
            for key_cry, value_cry in value_c.items():
                ret_str += "*" + key_cry + ":* " + str(value_cry['crypto']) + " *FIAT:* " + str(value_cry['fiat']) + " $\n"
    ret_str += get_separator("FINAL RECAP") + "*TOTAL DOLLAR:* " + str(round(total_usd, 2)) + " $"
    update.message.reply_text(markdown_text(ret_str), parse_mode='MarkdownV2')
    '''


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
        immature_balance = ""
        if 'immature_balance' in miner_info:
            immature_balance = "*IMMATURE:* " + miner_info['immature_balance'] + "\n"
        unpaid_balance = "*UNPAID:* " + miner_info['unpaid_balance']
        estimated_earning = "*EST:* " + miner_info['estimated_earning']
        pay_str = get_separator("PAYOUT") + immature_balance + unpaid_balance + " " + estimated_earning + "\n"  # + total_earning + " " + total_earning_euro + "\n"
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
        ret_str += f"{name} {crypto}\n{intensity}\n{pool_url}\n{wallet_id}\n"
    update.message.reply_text(markdown_text(ret_str), parse_mode='MarkdownV2')


def start_miner(update, context):
    initial_log("start_miner", context.args)
    make_cmd(f"start t-rex.exe -c {Config.settings['trex']['path_config']}", sys=True)
    update.message.reply_text("MINER ATTIVATO")


def set_trex_profile(update, context):
    if context.args is not None or (update.message is not None and update.message.text[:1] != '/'):
        initial_log("set_trex_profile", context.args)
        update.message.reply_text("SCEGLI UN PROFILO", reply_markup=make_button_list(list(Config.settings['trex']['profiles'].keys()), "set_trex_profile "))
    else:
        callback_data = update.callback_query.data
        initial_log("set_trex_profile", callback_data.split(" ")[1:])
        update.callback_query.answer()
        ret_str = be_set_trex_profile(callback_data.replace("set_trex_profile ", ""))
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
    if context.args is not None or (update.message is not None and update.message.text[:1] != '/'):
        initial_log("set_gpu_speed_fan", context.args)
        update.message.reply_text("SCEGLI UNA GPU", reply_markup=make_button_list(list(Config.settings['afterburner']['gpus'].keys()), "set_gpu_speed_fan "))
    else:
        callback_data = update.callback_query.data
        initial_log("set_gpu_speed_fan", callback_data.split(" ")[1:])
        update.callback_query.answer()
        if len(callback_data.split(" ")) == 2:
            update.callback_query.message.edit_text("SCEGLI UNA VELOCITA", reply_markup=make_button_list(Config.settings['afterburner']['gpus'][callback_data.replace("set_gpu_speed_fan ", "")]['fan_speeds'], "set_gpu_speed_fan " + callback_data.replace("set_gpu_speed_fan ", "") + " "))
        else:
            update.callback_query.message.edit_text(be_set_gpu_speed_fan(callback_data.split(" ")[1], callback_data.split(" ")[2]))


def get_link(update, context):
    if context.args is not None or (update.message is not None and update.message.text[:1] != '/'):
        initial_log("get_link", context.args)
        update.message.reply_text("SCEGLI UNA COMPETIZIONE", reply_markup=make_button_list(list(Config.settings['football']['competizioni'].keys()), "get_link "))
    else:
        callback_data = update.callback_query.data
        initial_log("get_link", callback_data.split(" ")[1:])
        update.callback_query.answer()
        if callback_data.split(" ")[1].find("EVLI") == -1:
            update.callback_query.message.edit_text("SCEGLI UNA PARTITA", reply_markup=make_button_list(be_get_link_event(Config.settings['football']['competizioni'][callback_data.replace("get_link ", "")]), "get_link "))
        else:
            update.callback_query.message.edit_text(be_get_link_acestream(callback_data.split(" ")[1].replace("EVLI", "")))


def start(update, context):
    initial_log("start", context.args)
    keyboard = []
    temp_list = []
    desc = ""
    for key, value in Config.settings['function'].items():
        if value['active']:
            desc += commands[key]['icon'] + ": " + commands[key]['desc'] + "\n"
            temp_list.append(commands[key]['icon'])
        if len(temp_list) == 2:
            keyboard.append(temp_list)
            temp_list = []
    if temp_list:
        keyboard.append(temp_list)
    update.message.reply_text(desc, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))


def generate_key(update, context):
    initial_log("generate_key", str(update.message.text))
    keyboard = []
    temp_list = []
    desc = ""
    for value in commands.values():
        if value['icon'] == update.message.text:
            desc += str(update.message.text) + "\n"
            for value_command in value['commands'].values():
                desc += value_command['icon'] + ": " + value_command['desc'] + "\n"
                temp_list.append(value_command['icon'])
                if len(temp_list) == value['row_size']:
                    keyboard.append(temp_list)
                    temp_list = []
    if temp_list:
        keyboard.append(temp_list)
    keyboard.append(['Main Menu 🔙'])
    update.message.reply_text(desc, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))


def my_add_handler(struct_commands, disp, cmd_filter):
    ret_str = ""
    disp.add_handler(MessageHandler(Filters.text(struct_commands['icon']) & cmd_filter, generate_key))
    for key, value in struct_commands['commands'].items():
        ret_str += key + " - " + value["desc"] + "\n"
        disp.add_handler(MessageHandler(Filters.text(value['icon']) & cmd_filter, eval(key)))
        disp.add_handler(CommandHandler(key, eval(key), cmd_filter))
    return ret_str


def main():
    Config().reload()
    basicConfig(
        filename=None,#Config.settings['log']['path_file'],
        format="%(asctime)s|%(levelname)s|%(filename)s:%(lineno)s|%(message)s",
        level=INFO)
    upd = Updater(Config.settings['bot_telegram']['token'], use_context=True)
    value = {}
    users_list = []
    for key, value in Config.settings['function'].items():
        for usr in value['users_abil']:
            if usr not in users_list:
                users_list.append(usr)
    cmd_str = "start - Avvia il bot e genera la tastiera"
    upd.dispatcher.add_handler(CommandHandler("start", start, Filters.user(username=set(users_list))))
    upd.dispatcher.add_handler(MessageHandler(Filters.text('Main Menu 🔙') & Filters.user(username=set(users_list)), start))
    for key, value in Config.settings['function'].items():
        if value['active']:
            cmd_str += my_add_handler(commands[key], upd.dispatcher, Filters.user(username=set(value['users_abil'])))
    upd.dispatcher.add_handler(CallbackQueryHandler(set_trex_profile, pattern=r'^set_trex_profile'))
    upd.dispatcher.add_handler(CallbackQueryHandler(set_gpu_speed_fan, pattern=r'^set_gpu_speed_fan'))
    upd.dispatcher.add_handler(CallbackQueryHandler(get_link, pattern=r'^get_link'))
    upd.dispatcher.add_handler(MessageHandler(Filters.document, doc_handler))
    upd.dispatcher.add_handler(MessageHandler(Filters.regex(r'^' + escape('https://www.youtube.com/watch?v=')) & Filters.user(username=set(value['users_abil'])), download_music))
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

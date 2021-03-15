from telegram.ext import Updater, CommandHandler
from logging import basicConfig, info, INFO, exception
from utility import make_cmd, markdown_text, Config
from logic import be_get_public_ip, be_get_file_ovpn, get_nvidia_info, be_stop_miner, be_stop_server_vpn, get_program_status, be_set_trex_profile, be_start_access_point, be_stop_access_point, be_get_access_point_status, be_set_gpu_speed_fan, be_shutdown_system, get_meross_info, get_trex_info, get_miner_info, get_balance_info
from pyrogram import Client
from time import sleep


separator = "-------------------------------------------------------------------\n"


def get_public_ip(update, context):
    info("REQUEST: get_public_ip")
    update.message.reply_text(be_get_public_ip())


def get_file_ovpn(update, context):
    info("REQUEST: get_file_ovpn")
    response = be_get_file_ovpn()
    if response == "OK":
        update.message.reply_document(open('ovpn/client.ovpn', 'r'))
    else:
        update.message.reply_text(response)


def get_balance_status(update, context):
    info("REQUEST: get_balance_status")
    ret_str = ""
    total_euro = 0
    for key, value in Config.settings['cryptos'].items():
        balance_info = get_balance_info(key, value['wallets'])
        total_euro = total_euro + balance_info['tot_eur_value']
        ret_str = ret_str + "------------------------ *" + key.upper() + "* ------------------------\n*VALUE:* " + balance_info['conv_eur'] + "   *WALLET NUMBER:* " + str(len(balance_info['walletts'].keys())) + "\n" + separator
        for key_b, value_b in balance_info['walletts'].items():
            ret_str = ret_str + "*WALLET:* " + key_b.replace("_", " ").title() + "\n*ID*: " + value_b['id'] + "\n*CRYPTO:* " + value_b['crypto_value'] + " *FIAT:* " + value_b['eur_value'] + "\n" + separator
        ret_str = ret_str + "*TOT CRYPTO:* " + balance_info['tot_crypto_value'] + " *FIAT:* " + str(balance_info['tot_eur_value']) + " €\n"
    ret_str = ret_str + "------------------------ *FINAL RECAP* ------------------------\n*TOTAL EURO:* " + str(round(total_euro, 2)) + " €"
    update.message.reply_text(markdown_text(ret_str), parse_mode='MarkdownV2')


def union_nvidia_trex(nvidia, trex):
    gpu_list = []
    for t in trex:
        for n in nvidia:
            if n['uuid'] == t['uuid']:
                gpu_list.append(n | t)
    return gpu_list


def get_mining_status(update, context):
    info("REQUEST: get_mining_status")
    try:
        ret_str = ""
        if Config.settings['meross'] != {}:
            meross_info = get_meross_info()
            if meross_info['state'] is True:
                ret_str = "*TOTAL POWER CONSUME:* " + meross_info['power'] + "\n"
        trex_info = get_trex_info()
        general_str = "------------------------ *GENERAL* ------------------------\n"
        uptime = "*UPTIME:* " + trex_info['uptime']
        pool_url = "*POOL:* " + trex_info['pool_url']
        wallet_id = "*WALLET:* " + trex_info['wallet_id']
        total_share = "*SHA TOT:* " + trex_info['total_share']
        share_min = "*MIN:* " + trex_info['share_min']
        share_min_avg = "*AVG:* " + trex_info['share_min_avg']
        general_str = general_str + uptime + "\n" + wallet_id + "\n" + pool_url + "\n" + total_share + " " + share_min + " " + share_min_avg + "\n"
        gpu_str = "------------------------ *GPU LIST* ------------------------\n"
        first = True
        for gpu in union_nvidia_trex(get_nvidia_info(), trex_info['gpus']):
            if not first:
                gpu_str = gpu_str + separator
            else:
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
        pay_str = "------------------------ *PAYOUT* ------------------------\n"
        immature_balance = ""
        if 'immature_balance' in miner_info:
            immature_balance = "*IMMATURE:* " + miner_info['immature_balance'] + "\n"
        unpaid_balance = "*UNPAID:* " + miner_info['unpaid_balance']
        estimated_earning = "*EST:* " + miner_info['estimated_earning']
        total_earning = "*TOT CRYPTO*: " + balance_info['tot_crypto_value']
        total_earning_euro = "*FIAT*: " + str(balance_info['tot_eur_value']) + " €"
        pay_str = pay_str + immature_balance + unpaid_balance + " " + estimated_earning + "\n" + total_earning + " " + total_earning_euro + "\n"
        work_str = "------------------------ *WORKER* ------------------------\n"
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
        work_str = work_str + total_reported_hashrate + " " + current_hashrate + " " + average_hashrate + "\n"
        work_str = work_str + active_worker + " " + valid_shares + " " + stale_shares + " " + invalid_shares
        ret_str = ret_str + general_str + gpu_str + pay_str + work_str
        update.message.reply_text(markdown_text(ret_str), parse_mode='MarkdownV2')
    except Exception as e:
        exception(e)
        update.message.reply_text("ERRORE: " + str(e))


def stop_miner(update, context):
    info("REQUEST: stop_miner")
    update.message.reply_text(be_stop_miner())


def shutdown_system(update, context):
    info("REQUEST: shutdown_system")
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
    info("REQUEST: start_server_vpn")
    make_cmd("start openvpn-gui --connect server.ovpn", sys=True)
    update.message.reply_text("SERVER VPN ACCESO")


def stop_server_vpn(update, context):
    info("REQUEST: stop_server_vpn")
    update.message.reply_text(be_stop_server_vpn())


def get_status_server_vpn(update, context):
    info("REQUEST: get_status_server_vpn")
    update.message.reply_text(get_program_status("openvpn-gui", "OPENVPN"))


def get_trex_profiles(update, context):
    info("REQUEST: get_trex_profile")
    ret_str = ""
    for key, value in Config.settings['trex']['profiles'].items():
        name = "*NAME:* " + key
        crypto = "*CRYPTO:* " + value['crypto']
        intensity = "*INTENSITY:* " + str(value['intensity'])[1:-1]
        pool_url = "*POOL URL:* " + value['pool_url']
        wallet_id = "*WALLET ID:* " + value['wallet']
        ret_str = ret_str + name + " " + crypto + "\n" + intensity + "\n" + pool_url + "\n" + wallet_id + "\n" + separator
    update.message.reply_text(markdown_text(ret_str), parse_mode='MarkdownV2')


def start_miner(update, context):
    info("REQUEST: start_miner")
    make_cmd("start /d trex t-rex.exe -c config.json", sys=True)
    update.message.reply_text("MINER ATTIVATO")


def set_trex_profile(update, context):
    info("REQUEST: set_trex_profile")
    trex_profile_list = Config.settings['trex']['profiles'].keys()
    if len(context.args) == 1:
        if context.args[0] in trex_profile_list:
            ret_str = be_set_trex_profile(context.args[0])
        else:
            ret_str = "PROFILO INESISTENTE\nIL PROFILO PUO ESSERE: " + ', '.join(trex_profile_list)
    else:
        ret_str = "È NECESSARIO PASSARE IL PROFILO COME PARAMETRO\nIL PROFILO PUO ESSERE: " + ', '.join(trex_profile_list)
    update.message.reply_text(ret_str)


def start_access_point(update, context):
    info("REQUEST: start_access_point")
    update.message.reply_text(be_start_access_point())


def stop_access_point(update, context):
    info("REQUEST: stop_access_point")
    update.message.reply_text(be_stop_access_point())


def get_access_point_status(update, context):
    info("REQUEST: get_access_point_status")
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
    info("REQUEST: set_gpu_speed_fan")
    gpu_list = Config.settings['afterburner']['gpus'].keys()
    if len(context.args) == 2:
        if context.args[0] in gpu_list:
            try:
                min_fan_speed = Config.settings['afterburner']['gpus'][context.args[0]]['min_fan_speed']
                if min_fan_speed <= int(context.args[1]) <= 100:
                    ret_str = be_set_gpu_speed_fan(context.args[0], context.args[1])
                else:
                    ret_str = "LA VELOCITA DEVE AVERE UN VALORE COMPRESO TRA " + str(min_fan_speed) + " E 100"
            except ValueError as e:
                ret_str = "LA VELOCITA DEVE ESSERE UN NUMERO INTERO"
        else:
            ret_str = "GPU INESISTENTE\nIL NOME DELLA GPU PUO ESSERE: " + ', '.join(gpu_list)
    else:
        ret_str = "È NECESSARIO SPECIFICARE DUE PARAMETRI: NOME GPU E VELOCITA\nIL NOME DELLA GPU PUO ESSERE: " + ', '.join(gpu_list) + "\nLA VELOCITA DEVE ESSERE UN NUMERO INTERO"
    update.message.reply_text(ret_str)


def main():
    basicConfig(
        filename=None,  # "bot.log",
        format="%(asctime)s|%(levelname)s|%(filename)s:%(lineno)s|%(message)s",
        level=INFO)
    Config()
    cmd_str = ""
    upd = Updater(Config.settings['bot_telegram']['token'], use_context=True)
    disp = upd.dispatcher
    disp.add_handler(CommandHandler("shutdown_system", shutdown_system))
    if Config.settings['function']['mining'] is True:
        cmd_str = cmd_str + "get_balance_status - Restituisce il bilancio di tutte le crypto\n"
        disp.add_handler(CommandHandler("get_balance_status", get_balance_status))
        cmd_str = cmd_str + "get_mining_status - Restituisce lo stato del miner\n"
        disp.add_handler(CommandHandler("get_mining_status", get_mining_status))
        cmd_str = cmd_str + "start_miner - Avvia il miner\n"
        disp.add_handler(CommandHandler("start_miner", start_miner))
        cmd_str = cmd_str + "stop_miner - Arresta il miner\n"
        disp.add_handler(CommandHandler("stop_miner", stop_miner))
        cmd_str = cmd_str + "set_gpu_speed_fan - Setta la velocità della ventola della GPU\n"
        disp.add_handler(CommandHandler("set_gpu_speed_fan", set_gpu_speed_fan))
        cmd_str = cmd_str + "get_trex_profiles - Restituisce la lista dei profili t-rex\n"
        disp.add_handler(CommandHandler("get_trex_profiles", get_trex_profiles))
        cmd_str = cmd_str + "set_trex_profile - Imposta il profilo per t-rex\n"
        disp.add_handler(CommandHandler("set_trex_profile", set_trex_profile))
    if Config.settings['function']['vpn'] is True:
        cmd_str = cmd_str + "get_status_server_vpn - Restituisce lo stato del server VPN\n"
        disp.add_handler(CommandHandler("get_status_server_vpn", get_status_server_vpn))
        cmd_str = cmd_str + "start_server_vpn - Avvia il server VPN\n"
        disp.add_handler(CommandHandler("start_server_vpn", start_server_vpn))
        cmd_str = cmd_str + "stop_server_vpn - Arreta il server VPN\n"
        disp.add_handler(CommandHandler("stop_server_vpn", stop_server_vpn))
        cmd_str = cmd_str + "get_file_ovpn - Restituisce il file per il client Open VPN\n"
        disp.add_handler(CommandHandler("get_file_ovpn", get_file_ovpn))
        cmd_str = cmd_str + "get_public_ip - Restituisce IP pubblico del server\n"
        disp.add_handler(CommandHandler("get_public_ip", get_public_ip))
    if Config.settings['function']['ap'] is True:
        cmd_str = cmd_str + "start_access_point - Avvia l'access point\n"
        disp.add_handler(CommandHandler("start_access_point", start_access_point))
        cmd_str = cmd_str + "stop_access_point - Arresta l'access point\n"
        disp.add_handler(CommandHandler("stop_access_point", stop_access_point))
        cmd_str = cmd_str + "get_access_point_status - Restituisce lo stato dell'access point\n"
        disp.add_handler(CommandHandler("get_access_point_status", get_access_point_status))
    cmd_str = cmd_str + "shutdown_system - Arresta il sistema"
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

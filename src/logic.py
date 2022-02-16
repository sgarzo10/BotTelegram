from utility import make_cmd, make_request, Config, make_driver_selenium
from json import loads
from meross_iot.api import MerossHttpClient
from logging import exception
from time import sleep
from tabulate import tabulate
from os import listdir, remove, walk, path, makedirs, popen
from shutil import rmtree
from html import unescape
from pytube import YouTube
from pydub import AudioSegment
from zipfile import ZipFile


def be_youtube_download(canzoni):
    makedirs("canzoni", exist_ok=True)
    for c in canzoni.split("\n"):
        link = "https://www.youtube.com/watch?v=" + c.split("watch?v=")[1]
        try:
            YouTube(link).streams.filter(only_audio=True, subtype='mp4').first().download()
        except Exception as e:
            exception(e)
        try:
            for f in listdir("."):
                if f.__contains__("mp4"):
                    AudioSegment.from_file(f).export('canzoni/' + f.replace(".mp4", "") + '.mp3', format="mp3")
                    remove(f)
        except Exception as e:
            exception(e)
    try:
        zip_file = ZipFile('canzoni.zip', 'w')
        for folderName, subfolders, filenames in walk("canzoni"):
            for filename in filenames:
                zip_file.write(path.join(folderName, filename), path.basename(path.join(folderName, filename)))
        zip_file.close()
    except Exception as e:
        exception(e)
    rmtree("canzoni")


def be_status_generali():
    resp = unescape(str(make_request("https://www.generali.it/quotazioni/genera-sviluppo-sostenibile")['response']))
    nomi = []
    valori = []
    for r in resp.split("<h2 class=\"h4 font-weight-bold\">")[1:]:
        nomi.append(r.split("</h2>")[0])
    for r in resp.split("quotazioni-specifiche__value__number\">")[1:]:
        valori.append(r.split(" </span>")[0])
    i = 0
    generali_now = {}
    while i < len(nomi):
        generali_now[nomi[i]] = float(valori[i].replace(",", "."))
        i += 1
    tot_profit = 0
    tot_invest = 0
    sell_all = 0
    assets_list = []
    for key, value in Config.generali['investimenti'].items():
        qty_total = 0
        invst_total = 0
        for o in value:
            qty_total += o['amount']
            invst_total += o['amount'] * o['value']
        k = ""
        for k in generali_now.keys():
            if k.find(key.upper()) != -1:
                break
        sell = round(qty_total * generali_now[k], 2)
        medium_buy = round(invst_total / qty_total, 4)
        profit = round(sell - invst_total, 2)
        tot_profit += profit
        tot_invest += invst_total
        sell_all += sell
        assets_list.append([k, round(qty_total, 2), medium_buy, generali_now[k], round(invst_total, 2), sell, profit])
    rel_tot_invest = round(tot_invest * 2 + sum(Config.generali['fee']), 2)
    balance = round(tot_invest + sell_all, 2)
    margin = round(tot_profit - sum(Config.generali['fee']), 2)
    return tabulate(assets_list, headers=['FONDO', 'TOT BUY', 'AVG BUY', 'ACTUAL', 'TOT INVEST', 'SELL NOW', 'MARGIN'], tablefmt='orgtbl', floatfmt=".2f") + "\n\nTOTAL BALANCE: " + str(balance) + "   TOTAL INVEST: " + str(rel_tot_invest) + "   TOTAL MARGIN: " + str(margin)


def be_get_token_defi_value(tokens_chain):
    to_ret = {}
    to_ret_tmp = {}
    order = ''
    if 'order' in tokens_chain:
        order = tokens_chain['order']
        del tokens_chain['order']
    for key, value in tokens_chain.items():
        tool = Config.settings[Config.chain[key]['token_price']]
        base_url = tool['url_token_price']\
            .replace("{chain_id}", Config.chain[key]['chain_id'])\
            .replace("{chiave}", tool['key'])
        if tool['multi_token']:
            payload = loads(make_request(base_url + ','.join(x for x in value.keys()))['response'])['data']
            key_sort = list(value.keys())
            key_sort.sort(reverse=True)
            i = 0
            for p in payload:
                to_ret_tmp[value[key_sort[i]]] = round(float(p[tool['key_token_price']]), 5)
                i += 1
        else:
            for tk_key, tk_value in value.items():
                payload = loads(make_request(base_url + tk_key)['response'])['data']
                to_ret_tmp[tk_value] = round(float(payload[tool['key_token_price']]), 5)
    if order != '':
        for k in order:
            to_ret[k] = to_ret_tmp[k]
    else:
        to_ret = to_ret_tmp
    return to_ret


def get_nvidia_info():
    exclude_list = ["", "|", "/"]
    gpus = []
    response = make_cmd("nvidia-smi -L")
    if response['cmd_err'] == "":
        rows = response["cmd_out"].split("\n")
        for r in rows[:-1]:
            gpu_info = {
                'uuid': r.split("GPU-")[1].split(")")[0].replace("-", "")
            }
            gpus.append(gpu_info)
    response = make_cmd("nvidia-smi")
    if response['cmd_err'] == "":
        rows = response["cmd_out"].split("\n")
        i = 0
        j = 0
        for r in rows:
            if r.__contains__("%"):
                gpus[j]['indice'] = i
                j += 1
            i += 1
        for gpu in gpus:
            value = []
            for r in rows[gpu['indice']].split(" "):
                if r not in exclude_list:
                    value.append(r)
            gpu['fan'] = value[0]
            gpu['temp'] = value[1]
            gpu['power'] = value[3]
            gpu['mem_used'] = value[5].replace("MiB", "") + "MB"
            gpu['mem_free'] = str(int(value[6].replace("MiB", "")) - int(value[5].replace("MiB", ""))) + "MB"
            gpu['load'] = value[7]
    return gpus


def calculate_uptime(total_second):
    day = total_second // 86400
    remaning = total_second - (day * 86400)
    hour = remaning // 3600
    remaning = remaning - (hour * 3600)
    minute = remaning // 60
    sec = remaning - (minute * 60)
    uptime = ''
    if day > 0:
        uptime = str(day) + " days "
    if hour > 0:
        uptime = uptime + str(hour) + " hours "
    if minute > 0:
        uptime = uptime + str(minute) + " minutes "
    if sec > 0:
        uptime = uptime + str(sec) + " seconds"
    return uptime


def get_trex_info():
    response = make_request("http://127.0.0.1:4067/summary")
    trex_info = {}
    if response['state'] is True:
        trex = loads(response['response'])
        trex_info['uptime'] = calculate_uptime(trex['uptime'])
        trex_info['pool_url'] = trex['active_pool']['url']
        trex_info['wallet_id'] = trex['active_pool']['user']
        trex_info['total_reported_hashrate'] = str(round(trex['hashrate'] / 1000000, 1)) + " MH/s"
        trex_info['total_share'] = str(trex['accepted_count'])
        trex_info['share_min'] = str(trex['sharerate'])
        trex_info['share_min_avg'] = str(trex['sharerate_average'])
        trex_info['cur_trex_profile'] = find_trex_profile(trex_info['pool_url'], trex_info['wallet_id'])
        trex_info['gpus'] = []
        i = 0
        for gpu in trex['gpus']:
            gpu_info = {
                'intensity': str(gpu['intensity']),
                'reported_hashrate': str(round(gpu['hashrate'] / 1000000, 1)) + " MH/s",
                'gpu_name': gpu['vendor'] + " " + gpu['name'],
                'gpu_efficency': 'N/A',
                'accepted_count': str(gpu['shares']['accepted_count']),
                'uuid': gpu['uuid']
            }
            if 'efficiency' in gpu:
                gpu_info['gpu_efficency'] = gpu['efficiency']
            trex_info['gpus'].append(gpu_info)
            i += 1
    return trex_info


def get_miner_info(cur_trex_profile, wallet_id):
    if Config.settings['trex']['profiles'][cur_trex_profile]['api_domain'].find("2miners") != -1:
        to_ret = get_2miners_info(cur_trex_profile, wallet_id)
    else:
        to_ret = get_ethermine_info(cur_trex_profile, wallet_id)
    return to_ret


def calculate_avg_hasrate(current_time, stats, time_key, hashrate_key):
    old_time = current_time - 21600
    sum_hash = 0
    i = 0
    for stat in stats:
        if stat[time_key] >= old_time:
            sum_hash = sum_hash + stat[hashrate_key]
            i += 1
    return str(round(sum_hash / (i * 1000000), 1))


def get_ethermine_info(cur_trex_profile, wallet_id):
    ethermine_info = {}
    trex_profile = Config.settings['trex']['profiles'][cur_trex_profile]
    crypto = Config.chain[trex_profile['crypto']]
    response_dash = make_request(trex_profile['api_domain'] + "/miner/" + wallet_id + "/dashboard")
    response_pay = make_request(trex_profile['api_domain'] + "/miner/" + wallet_id + "/dashboard/payouts")
    if response_dash['state'] is True and response_pay['state'] is True:
        dashboard = loads(response_dash['response'])
        payouts = loads(response_pay['response'])
        if 'unconfirmed' in dashboard['data']['currentStatistics']:
            ethermine_info['immature_balance'] = str(round(dashboard['data']['currentStatistics']['unconfirmed'] / pow(10, crypto['pow_divisor']), 5)) + " " + crypto['crypto']
        ethermine_info['unpaid_balance'] = str(round(dashboard['data']['currentStatistics']['unpaid'] / pow(10, crypto['pow_divisor']), 5)) + " " + crypto['crypto']
        ethermine_info['estimated_earning'] = str(round(payouts['data']['estimates']['coinsPerMin'] * 1440, 5)) + " " + crypto['crypto']
        ethermine_info['current_hashrate'] = str(round(dashboard['data']['currentStatistics']['currentHashrate'] / 1000000, 1)) + " MH/s"
        ethermine_info['average_hashrate'] = calculate_avg_hasrate(dashboard['data']['currentStatistics']['time'], dashboard['data']['statistics'], 'time', 'currentHashrate') + " MH/s"
        ethermine_info['active_worker'] = str(dashboard['data']['currentStatistics']['activeWorkers'])
        ethermine_info['valid_shares'] = str(dashboard['data']['currentStatistics']['validShares'])
        ethermine_info['stale_shares'] = str(dashboard['data']['currentStatistics']['staleShares'])
        ethermine_info['invalid_shares'] = str(dashboard['data']['currentStatistics']['invalidShares'])
    return ethermine_info


def get_2miners_info(cur_trex_profile, wallet_id):
    two_miners_info = {}
    trex_profile = Config.settings['trex']['profiles'][cur_trex_profile]
    crypto = Config.chain[trex_profile['crypto']]
    response_dash = make_request(trex_profile['api_domain'] + "/" + wallet_id)
    if response_dash['state'] is True:
        dashboard = loads(response_dash['response'])
        if 'immature' in dashboard['stats']:
            two_miners_info['immature_balance'] = str(round(dashboard['stats']['immature'] / pow(10, crypto['pow_divisor']), 5)) + " " + crypto['crypto']
        two_miners_info['unpaid_balance'] = str(round(dashboard['stats']['balance'] / pow(10, crypto['pow_divisor']), 5)) + " " + crypto['crypto']
        two_miners_info['estimated_earning'] = str(round((dashboard['sumrewards'][0]['reward'] / pow(10, crypto['pow_divisor'])) * 24, 5)) + " " + crypto['crypto']
        two_miners_info['current_hashrate'] = str(round(dashboard['currentHashrate'] / 1000000, 1)) + " MH/s"
        two_miners_info['average_hashrate'] = calculate_avg_hasrate(dashboard['updatedAt'] // 1000, dashboard['minerCharts'], 'x', 'minerHash') + " MH/s"
        two_miners_info['active_worker'] = str(dashboard['workersOnline'])
    return two_miners_info


def get_meross_info():
    device_info = {'state': False}
    try:
        http_handler = MerossHttpClient(email=Config.settings['meross']['email'], password=Config.settings['meross']['password'])
        devices = http_handler.list_devices()
        i = 0
        for dev in devices:
            if dev['devName'] == Config.settings['meross']['device_name'] and dev['onlineStatus'] == 1:
                devices = http_handler.list_supported_devices()
                device_info['power'] = str(round(devices[i].get_electricity()['electricity']['power'] / 1000, 2)) + " W"
                device_info['state'] = True
                break
            i += 1
    except Exception as e:
        exception(e)
    return device_info


def be_stop_miner():
    response = make_request(Config.settings['trex']['shutdown_url'])
    if response['state'] is True:
        if loads(response['response'])['success'] == 1:
            ret_str = "SPENTO MINER"
        else:
            ret_str = "ERRORE DURANTE L'ARRESTO DEL MINER"
    else:
        ret_str = response['response']
    return ret_str


def find_trex_profile(pool_url, wallet_id):
    key = ""
    for key, value in Config.settings['trex']['profiles'].items():
        if value['pool_url'] == pool_url and value['wallet'] == wallet_id:
            break
    return key


def be_set_trex_profile(profile):
    try:
        f = open(Config.settings['trex']['path_config_temp'], 'r')
        data_file = f.read()
        f.close()
        trex_profile = Config.settings['trex']['profiles'][profile]
        zero_string = ""
        dev_string = ""
        for i in range(Config.settings['trex']['gpu_number']):
            zero_string = zero_string + "0, "
            dev_string = dev_string + str(i) + ", "
        zero_string = zero_string[:-2]
        dev_string = dev_string[:-2]
        crypto = Config.chain[trex_profile['crypto']]
        data_file = data_file.replace("BUILD_MODE", zero_string)
        data_file = data_file.replace("DEVICES_ID", dev_string)
        data_file = data_file.replace("KERNEL_LIST", zero_string)
        data_file = data_file.replace("LOW_LOAD_LIST", zero_string)
        data_file = data_file.replace("ALGORITMO", crypto['algo'])
        data_file = data_file.replace("POOL_URL", trex_profile['pool_url'])
        data_file = data_file.replace("WALLET_ID", trex_profile['wallet'])
        data_file = data_file.replace("INTENSITA", str(trex_profile['intensity'])[1:-1])
        data_file = data_file.replace("WORKER_NAME", Config.settings['trex']['worker_name'])
        f = open(Config.settings['trex']['path_config'], 'w')
        f.write(data_file)
        f.close()
        ret_str = "SETTATO PROFILO: %s" % profile
    except Exception as e:
        exception(e)
        ret_str = "ERRORE: " + str(e)
    return ret_str


def be_set_gpu_speed_fan(name, speed):
    try:
        file_path = Config.settings['afterburner']['path'] + 'Profiles\\' + Config.settings['afterburner']['gpus'][name]['config_file']
        f = open(file_path, 'r')
        data_file = f.read()
        f.close()
        actual_speed = data_file.split("[Profile1]")[1].split("FanSpeed=")[1].split("\n")[0]
        data_file = data_file.replace("FanSpeed=" + actual_speed, "FanSpeed=" + speed)
        f = open(file_path, 'w')
        f.write(data_file)
        f.close()
        make_cmd("start \"\" \"" + Config.settings['afterburner']['path'] + "MSIAfterburner.exe\" -Profile1", sys=True)
        sleep(5)
        response = make_cmd("taskkill /F /IM MSIAfterburner.exe /T")
        if response['cmd_err'] == "" and response["cmd_out"].find("terminato") > 0:
            ret_str = "VELOCITA DELLA VENTOLA MODIFICATA"
        else:
            ret_str = "ERRORE NELLA MODIFICA DELLA VELOCITA DELLA VENTOLA"
    except Exception as e:
        exception(e)
        ret_str = "ERRORE: " + str(e)
    return ret_str


def get_program_status(program, name):
    response = make_cmd("tasklist | find \"" + program + "\"")
    if response['cmd_err'] == "":
        if response['cmd_out'] == "":
            ret_str = "SERVIZIO " + name + " SPENTO"
        else:
            ret_str = "SERVIZIO " + name + " ACCESO"
    else:
        ret_str = "ERRORE: " + response['cmd_err']
    return ret_str


def be_shutdown_system():
    response = make_cmd("shutdown /s /t 3")
    if response['cmd_err'] == "":
        ret_str = "SERVER SPENTO"
    else:
        ret_str = "ERRORE: " + response["cmd_err"]
    return ret_str


def be_get_public_ip():
    response = make_cmd("nslookup myip.opendns.com resolver1.opendns.com")
    if response['cmd_err'] == "":
        ret_str = response["cmd_out"].split("Address:")[2].strip()
    else:
        ret_str = "ERRORE: " + response["cmd_err"]
    return ret_str


def be_get_file_ovpn(filename):
    try:
        f = open(Config.settings['vpn']['path_client_temp'], 'r')
        data_file = f.read()
        f.close()
        response = be_get_public_ip()
        if response.find("ERRORE") == -1:
            data_file = data_file.replace("IPADDRESS", response)
            f = open(filename, 'w')
            f.write(data_file)
            f.close()
            response = "OK"
    except Exception as e:
        exception(e)
        response = "ERRORE: " + str(e)
    return response


def be_stop_server_vpn():
    response = make_cmd("openvpn-gui --command disconnect server.ovpn")
    if response['cmd_err'] == "":
        response = make_cmd("openvpn-gui --command exit")
        if response['cmd_err'] == "":
            ret_str = "SPENTO SERVER VPN"
        else:
            ret_str = "ERRORE: " + response["cmd_err"]
    else:
        ret_str = "ERRORE: " + response["cmd_err"]
    return ret_str


def be_start_access_point():
    response = make_cmd("netsh wlan start hostednetwork")
    if response['cmd_err'] == "":
        response = make_cmd("netsh interface ip set address \"" + Config.settings['access_point']['interface_name'] + "\" static " + Config.settings['access_point']['ip'] + " 255.255.255.0")
        if response['cmd_err'] == "":
            f = open(Config.settings['access_point']['path_ini_temp'], "r")
            data_file = f.read()
            f.close()
            data_file = data_file.replace("SERVER_IP", Config.settings['access_point']['ip'])
            f = open(Config.settings['access_point']['path_ini'], 'w')
            f.write(data_file)
            f.close()
            make_cmd("\"dhcpsrv.exe\" -configfirewall")
            make_cmd("\"dhcpsrv.exe\" -ini " + Config.settings['access_point']['path_ini'])
            make_cmd("start dhcpsrv.exe -runapp", sys=True)
            ret_str = "ACCESS POINT AVVIATO"
        else:
            ret_str = "ERRORE: " + response["cmd_err"]
    else:
        ret_str = "ERRORE: " + response["cmd_err"]
    return ret_str


def be_stop_access_point():
    response = make_cmd("netsh wlan stop hostednetwork")
    if response['cmd_err'] == "":
        response = make_cmd("taskkill /F /IM dhcpsrv.exe")
        if response['cmd_err'] == "":
            ret_str = "ACCESS POINT SPENTO"
        else:
            ret_str = "ERRORE: " + response["cmd_err"]
    else:
        ret_str = "ERRORE: " + response["cmd_err"]
    return ret_str


def get_mac_and_ip(client_number, cmd_out_split):
    to_ret = {}
    clients = {}
    response_arp = make_cmd("arp -an " + Config.settings['access_point']['ip'])
    if response_arp['cmd_err'] == "":
        response_arp_split = response_arp['cmd_out'].split("\n")
        for i in range(client_number):
            mac_adrress = cmd_out_split[i].split("Autenticato")[0].strip()
            mac_address_to_find = mac_adrress.replace(":", "-")
            found = False
            for line in response_arp_split:
                if line.find(mac_address_to_find) != -1:
                    clients[mac_adrress] = line.split(mac_address_to_find)[0].strip()
                    found = True
            if found is False:
                clients[mac_adrress] = 'undefined'
        to_ret['status'] = clients
    return to_ret


def be_get_access_point_status():
    response = make_cmd("netsh wlan show hostednetwork")
    to_ret = {'state': True}
    if response['cmd_err'] == "":
        cmd_out_split = response['cmd_out'].split("\n")
        to_ret['name'] = cmd_out_split[4].split("\"")[1].split("\"")[0]
        to_ret['status'] = cmd_out_split[11].split(":")[1].strip()
        if to_ret['status'] == 'Avviato':
            to_ret['client'] = cmd_out_split[15].split(":")[1].strip()
            if int(to_ret['client']) > 0:
                mac_ip = get_mac_and_ip(int(to_ret['client']), cmd_out_split[16:])
                if 'status' in mac_ip:
                    to_ret['clients'] = mac_ip['status']
        response = make_cmd("netsh wlan show hostednetwork setting=security")
        if response['cmd_err'] == "":
            to_ret['password'] = response['cmd_out'].split("\n")[6].split(":")[1].strip()
        else:
            to_ret['password'] = "ERRORE: " + response["cmd_err"]
    else:
        to_ret['state'] = False
        to_ret['status'] = "ERRORE: " + response["cmd_err"]
    return to_ret


def be_get_link_acestream(event_link):
    event_link = Config.settings['football']['base_url'] + "/enx/eventinfo/" + event_link
    to_ret = "EVENTO: " + event_link + "\n"
    try:
        tor_bin_path = Config.settings['football']['tor_bin_path']
        ace_base_url = Config.settings['football']['ace_base_url']
        ace_on = False
        links = []
        popen(tor_bin_path)
        html_source = make_driver_selenium(event_link, True)
        if html_source.find("AceStream Links") != -1:
            percentages = html_source.split("AceStream Links")[1].split("<span class=\"pc\">%</span>")
            for percentage in percentages[:-1]:
                links.append({'perc': percentage[-2:]})
            i = 0
            contents_id = html_source.split("onclick=\"show_webplayer('acestream', '")
            for content_id in contents_id[1:]:
                links[i]['id'] = content_id.split("',")[0]
                i += 1
        else:
            to_ret += "LINK DI ACESTREAM NON ANCORA DISPONIBILI\n"
        response = make_request(ace_base_url + "webui/api/service?method=get_version&format=jsonp&callback=mycallback")
        if response['state']:
            ace_on = True
            to_ret += "SERVER ACESTREAM RAGGIUNGIBILE\n"
        else:
            to_ret += "SERVER ACESTREAM NON RAGGIUNGIBILE\n"
        for link in links:
            to_ret += "---------------------------------------------\n"
            to_ret += link['id'] + " - " + link['perc'] + "\n"
            if ace_on:
                to_ret += ace_base_url + "ace/manifest.m3u8?id=" + link['id'] + "\n"
    except Exception as e:
        exception(e)
        to_ret = str(e)
    return to_ret


def be_get_link_event(competizione):
    event_list = []
    try:
        tor_bin_path = Config.settings['football']['tor_bin_path']
        popen(tor_bin_path)
        html_source = make_driver_selenium(Config.settings['football']['base_url'] + "/enx/calendar/" + competizione + "/", True)
        main_events = html_source.split("<a class=\"main\" href=\"")
        for event in main_events[1:]:
            event_list.append((event.split("</b>")[0].split("<b>")[1], event.split("\"><b>")[0].replace("/enx/eventinfo/", "")))
    except Exception as e:
        exception(e)
    return event_list

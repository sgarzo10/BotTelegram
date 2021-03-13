from xml_reader import XmlReader
from utility import make_cmd, make_request
from json import loads
from time import sleep
from meross_iot.api import MerossHttpClient
from logging import exception


def get_nvidia_info():
    response = make_cmd("nvidia-smi")
    exclude_list = ["", "|", "/"]
    value = []
    gpu_info = {}
    if response['cmd_err'] == "":
        rows = response["cmd_out"].split("\n")
        i = 0
        for r in rows:
            if r.__contains__("%"):
                break
            i += 1
        for r in rows[i].split(" "):
            if r not in exclude_list:
                value.append(r)
        gpu_info['fan'] = value[0]
        gpu_info['temp'] = value[1]
        gpu_info['power'] = value[3]
        gpu_info['mem_used'] = value[5].replace("MiB", "")
        gpu_info['mem_free'] = str(int(value[6].replace("MiB", "")) - int(value[5].replace("MiB", "")))
        gpu_info['load'] = value[7]
    return gpu_info


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
    response = make_request("http://" + XmlReader.settings['trex_ip'] + ":4067/summary")
    trex_info = {}
    if response['state'] is True:
        trex = loads(response['response'])
        trex_info['uptime'] = calculate_uptime(trex['uptime'])
        trex_info['pool_url'] = trex['active_pool']['url']
        trex_info['wallet_id'] = trex['active_pool']['user']
        trex_info['cur_trex_profile'] = find_trex_profile(trex_info['pool_url'], trex_info['wallet_id'])
        trex_info['intensity'] = str(trex['gpus'][0]['intensity'])
        trex_info['reported_hashrate'] = str(round(trex['gpus'][0]['hashrate'] / 1000000, 1))
        trex_info['gpu_name'] = trex['gpus'][0]['vendor'] + " " + trex['gpus'][0]['name']
        trex_info['gpu_efficency'] = 'N/A'
        if 'efficiency' in trex['gpus'][0]:
            trex_info['gpu_efficency'] = trex['gpus'][0]['efficiency']
        trex_info['total_share'] = str(trex['accepted_count'])
        trex_info['share_min'] = str(trex['sharerate'])
        trex_info['share_min_avg'] = str(trex['sharerate_average'])
    return trex_info


def get_miner_info(cur_trex_profile, wallet_id):
    if XmlReader.settings['trex_profiles'][cur_trex_profile]['api_domain'].find("2miners") != -1:
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
    response_dash = make_request(XmlReader.settings['trex_profiles'][cur_trex_profile]['api_domain'] + "/miner/" + wallet_id + "/dashboard")
    response_pay = make_request(XmlReader.settings['trex_profiles'][cur_trex_profile]['api_domain'] + "/miner/" + wallet_id + "/dashboard/payouts")
    if response_dash['state'] is True and response_pay['state'] is True:
        dashboard = loads(response_dash['response'])
        payouts = loads(response_pay['response'])
        if 'unconfirmed' in dashboard['data']['currentStatistics']:
            ethermine_info['immature_balance'] = str(round(dashboard['data']['currentStatistics']['unconfirmed'] / XmlReader.settings['trex_profiles'][cur_trex_profile]['divisor'], 5)) + " " + XmlReader.settings['trex_profiles'][cur_trex_profile]['crypto']
        ethermine_info['unpaid_balance'] = str(round(dashboard['data']['currentStatistics']['unpaid'] / XmlReader.settings['trex_profiles'][cur_trex_profile]['divisor'], 5)) + " " + XmlReader.settings['trex_profiles'][cur_trex_profile]['crypto']
        ethermine_info['estimated_earning'] = str(round(payouts['data']['estimates']['coinsPerMin'] * 1440, 5)) + " " + XmlReader.settings['trex_profiles'][cur_trex_profile]['crypto']
        ethermine_info['current_hashrate'] = str(round(dashboard['data']['currentStatistics']['currentHashrate'] / 1000000, 1))
        ethermine_info['average_hashrate'] = calculate_avg_hasrate(dashboard['data']['currentStatistics']['time'], dashboard['data']['statistics'], 'time', 'currentHashrate')
        ethermine_info['active_worker'] = str(dashboard['data']['currentStatistics']['activeWorkers'])
        ethermine_info['valid_shares'] = str(dashboard['data']['currentStatistics']['validShares'])
        ethermine_info['stale_shares'] = str(dashboard['data']['currentStatistics']['staleShares'])
        ethermine_info['invalid_shares'] = str(dashboard['data']['currentStatistics']['invalidShares'])
    return ethermine_info


def get_2miners_info(cur_trex_profile, wallet_id):
    two_miners_info = {}
    response_dash = make_request(XmlReader.settings['trex_profiles'][cur_trex_profile]['api_domain'] + "/" + wallet_id)
    response_home = make_request(XmlReader.settings['trex_profiles'][cur_trex_profile]['domain'])
    if response_dash['state'] is True and response_home['state'] is True:
        dashboard = loads(response_dash['response'])
        crypto = loads(response_home['response'])[0]['symbol']
        if 'immature' in dashboard['stats']:
            two_miners_info['immature_balance'] = str(round(dashboard['stats']['immature'] / XmlReader.settings['trex_profiles'][cur_trex_profile]['divisor'], 5)) + " " + crypto
        two_miners_info['unpaid_balance'] = str(round(dashboard['stats']['balance'] / XmlReader.settings['trex_profiles'][cur_trex_profile]['divisor'], 5)) + " " + crypto
        two_miners_info['estimated_earning'] = str(round((dashboard['sumrewards'][0]['reward'] / XmlReader.settings['trex_profiles'][cur_trex_profile]['divisor']) * 24, 5)) + " " + crypto
        two_miners_info['current_hashrate'] = str(round(dashboard['currentHashrate'] / 1000000, 1))
        two_miners_info['average_hashrate'] = calculate_avg_hasrate(dashboard['updatedAt'] // 1000, dashboard['minerCharts'], 'x', 'minerHash')
        two_miners_info['active_worker'] = str(dashboard['workersOnline'])
    return two_miners_info


def get_meross_info():
    device_info = {
        'state': False
    }
    try:
        http_handler = MerossHttpClient(email=XmlReader.settings['meross_credential']['email'], password=XmlReader.settings['meross_credential']['password'])
        devices = http_handler.list_devices()
        i = 0
        for dev in devices:
            if dev['devName'] == XmlReader.settings['meross_credential']['device_name'] and dev['onlineStatus'] == 1:
                devices = http_handler.list_supported_devices()
                device_info['power'] = str(round(devices[i].get_electricity()['electricity']['power'] / 1000, 2))
                device_info['state'] = True
                break
            i += 1
    except Exception as e:
        exception(e)
    return device_info


def be_stop_miner():
    response = make_request("http://" + XmlReader.settings['trex_ip'] + ":4067/control?command=shutdown")
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
    for key, value in XmlReader.settings['trex_profiles'].items():
        if value['pool_url'] == pool_url and value['wallet'] == wallet_id:
            break
    return key


def be_set_trex_profile(profile):
    try:
        f = open('trex/config_temp.json', 'r')
        data_file = f.read()
        f.close()
        data_file = data_file.replace("ALGORITMO", XmlReader.settings['trex_profiles'][profile]['algo'])
        data_file = data_file.replace("POOL_URL", XmlReader.settings['trex_profiles'][profile]['pool_url'])
        data_file = data_file.replace("WALLET_ID", XmlReader.settings['trex_profiles'][profile]['wallet'])
        data_file = data_file.replace("INTENSITA", XmlReader.settings['trex_profiles'][profile]['intensity'])
        f = open('trex/config.json', 'w')
        f.write(data_file)
        f.close()
        ret_str = "PROFILO DI T-REX SETTATO"
    except Exception as e:
        exception(e)
        ret_str = "ERRORE: " + str(e)
    return ret_str


def be_set_gpu_speed_fan(speed):
    try:
        file_path = XmlReader.settings['msi_afterburner_path'] + 'Profiles\\' + XmlReader.settings['msi_afterburner_config']
        f = open(file_path, 'r')
        data_file = f.read()
        f.close()
        actual_speed = data_file.split("[Profile1]")[1].split("FanSpeed=")[1].split("\n")[0]
        data_file = data_file.replace("FanSpeed=" + actual_speed, "FanSpeed=" + speed)
        f = open(file_path, 'w')
        f.write(data_file)
        f.close()
        make_cmd("start \"\" \"" + XmlReader.settings['msi_afterburner_path'] + "MSIAfterburner.exe\" -Profile1", sys=True)
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


def be_get_file_ovpn():
    try:
        f = open('ovpn/client_temp.ovpn', 'r')
        data_file = f.read()
        f.close()
        response = be_get_public_ip()
        if response.find("ERRORE") == -1:
            data_file = data_file.replace("IPADDRESS", response)
            f = open('ovpn/client.ovpn', 'w')
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
        response = make_cmd("netsh interface ip set address \"" + XmlReader.settings['ap_interface_name'] + "\" static " + XmlReader.settings['ap_ip'] + " 255.255.255.0")
        if response['cmd_err'] == "":
            f = open("dhcp/dhcpsrv_temp.ini", "r")
            data_file = f.read()
            f.close()
            data_file = data_file.replace("SERVER_IP", XmlReader.settings['ap_ip'])
            f = open('dhcp/dhcpsrv.ini', 'w')
            f.write(data_file)
            f.close()
            make_cmd("\"dhcp/dhcpsrv.exe\" -configfirewall")
            make_cmd("start /d dhcp dhcpsrv.exe -runapp", sys=True)
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
    if client_number > 0:
        response_arp = make_cmd("arp -an " + XmlReader.settings['ap_ip'])
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
            to_ret['state'] = True
            to_ret['status'] = clients
        else:
            to_ret['state'] = False
            to_ret['status'] = "ERRORE: " + response_arp["cmd_err"]
    else:
        to_ret['state'] = False
        to_ret['status'] = "ERRORE: numero client minore o uguale a zero"
    return to_ret


def be_get_access_point_status():
    response = make_cmd("netsh wlan show hostednetwork")
    to_ret = {
        'state': True
    }
    if response['cmd_err'] == "":
        cmd_out_split = response['cmd_out'].split("\n")
        to_ret['name'] = cmd_out_split[4].split("\"")[1].split("\"")[0]
        to_ret['status'] = cmd_out_split[11].split(":")[1].strip()
        if to_ret['status'] == 'Avviato':
            to_ret['client'] = cmd_out_split[15].split(":")[1].strip()
            mac_ip = get_mac_and_ip(int(to_ret['client']), cmd_out_split[16:])
            if mac_ip['state'] is True:
                to_ret['clients'] = mac_ip['status']
            else:
                to_ret = mac_ip
        if to_ret['state'] is True:
            response = make_cmd("netsh wlan show hostednetwork setting=security")
            if response['cmd_err'] == "":
                to_ret['password'] = response['cmd_out'].split("\n")[6].split(":")[1].strip()
                to_ret['state'] = True
            else:
                to_ret['state'] = False
                to_ret['status'] = "ERRORE: " + response["cmd_err"]
    else:
        to_ret['state'] = False
        to_ret['status'] = "ERRORE: " + response["cmd_err"]
    return to_ret

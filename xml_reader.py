from xml.dom import minidom


class XmlReader:
    settings = {}

    def __init__(self, filename):
        xml = minidom.parse(filename)
        telegram_token = xml.getElementsByTagName('telegram_token')[0].firstChild.data
        phone_number = xml.getElementsByTagName('phone_number')[0].firstChild.data
        bot_username = xml.getElementsByTagName('bot_username')[0].firstChild.data
        ap_ip = xml.getElementsByTagName('ap_ip')[0].firstChild.data
        ap_interface_name = xml.getElementsByTagName('ap_interface_name')[0].firstChild.data
        meross_credential = {}
        if xml.getElementsByTagName('meross_credential')[0].getElementsByTagName('email')[0].firstChild is not None:
            meross_credential = {
                'email': xml.getElementsByTagName('meross_credential')[0].getElementsByTagName('email')[0].firstChild.data,
                'password': xml.getElementsByTagName('meross_credential')[0].getElementsByTagName('password')[0].firstChild.data,
                'device_name': xml.getElementsByTagName('meross_credential')[0].getElementsByTagName('device_name')[0].firstChild.data
            }
        telegram_app = {
            'api_id': xml.getElementsByTagName('telegram_app')[0].getElementsByTagName('api_id')[0].firstChild.data,
            'api_hash': xml.getElementsByTagName('telegram_app')[0].getElementsByTagName('api_hash')[0].firstChild.data
        }
        msi_afterburner_config = xml.getElementsByTagName('msi_afterburner_config')[0].firstChild.data
        msi_afterburner_path = xml.getElementsByTagName('msi_afterburner_path')[0].firstChild.data
        min_gpu_fan_speed = xml.getElementsByTagName('min_gpu_fan_speed')[0].firstChild.data
        trex_ip = xml.getElementsByTagName('trex_ip')[0].firstChild.data
        trex_profiles = {}
        for ind in range(0, len(xml.getElementsByTagName('trex_profiles')[0].getElementsByTagName('profile'))):
            name = xml.getElementsByTagName('trex_profiles')[0].getElementsByTagName('profile')[ind].getElementsByTagName('name')[0].firstChild.data
            profile = {
                'crypto': xml.getElementsByTagName('trex_profiles')[0].getElementsByTagName('profile')[ind].getElementsByTagName('crypto')[0].firstChild.data,
                'algo': xml.getElementsByTagName('trex_profiles')[0].getElementsByTagName('profile')[ind].getElementsByTagName('algo')[0].firstChild.data,
                'intensity': xml.getElementsByTagName('trex_profiles')[0].getElementsByTagName('profile')[ind].getElementsByTagName('intensity')[0].firstChild.data,
                'pool_url': xml.getElementsByTagName('trex_profiles')[0].getElementsByTagName('profile')[ind].getElementsByTagName('pool_url')[0].firstChild.data,
                'wallet': xml.getElementsByTagName('trex_profiles')[0].getElementsByTagName('profile')[ind].getElementsByTagName('wallet')[0].firstChild.data,
                'api_domain': xml.getElementsByTagName('trex_profiles')[0].getElementsByTagName('profile')[ind].getElementsByTagName('api_domain')[0].firstChild.data,
                'divisor': int(xml.getElementsByTagName('trex_profiles')[0].getElementsByTagName('profile')[ind].getElementsByTagName('divisor')[0].firstChild.data)
            }
            trex_profiles[name] = profile
        function = {
            'vpn': True if xml.getElementsByTagName('function')[0].getElementsByTagName('vpn')[0].firstChild.data == "s" else False,
            'ap': True if xml.getElementsByTagName('function')[0].getElementsByTagName('ap')[0].firstChild.data == "s" else False,
            'mining': True if xml.getElementsByTagName('function')[0].getElementsByTagName('mining')[0].firstChild.data == "s" else False
        }
        XmlReader.settings = {
            'telegram_token': telegram_token,
            'phone_number': phone_number,
            'bot_username': bot_username,
            'ap_ip': ap_ip,
            'ap_interface_name': ap_interface_name,
            'meross_credential': meross_credential,
            'telegram_app': telegram_app,
            'msi_afterburner_config': msi_afterburner_config,
            'msi_afterburner_path': msi_afterburner_path,
            'min_gpu_fan_speed': int(min_gpu_fan_speed),
            'trex_ip': trex_ip,
            'trex_profiles': trex_profiles,
            'function': function
        }
        return

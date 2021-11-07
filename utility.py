from subprocess import PIPE, Popen
from os import system
from urllib.request import urlopen, Request
from logging import info, exception
from json import load, dumps
from selenium.webdriver import ChromeOptions, Chrome
from telegram import InlineKeyboardMarkup, InlineKeyboardButton


def make_cmd(cmd, sys=False):
    response = {}
    try:
        info("Eseguo comando: %s", cmd)
        if sys is False:
            cmd_exec = Popen(args=cmd, stdout=PIPE, stderr=PIPE, shell=True)
            out_err = cmd_exec.communicate()
            cmd_out = str(out_err[0])[2:-1].replace("\\t", "\t").replace("\\n", "\n").replace("\\r", "\r")
            cmd_err = str(out_err[1])[2:-1].replace("\\t", "\t").replace("\\n", "\n").replace("\\r", "\r")
            info("Return Code: %s", cmd_exec.returncode)
            info("Output: %s", cmd_out)
            info("Error: %s", cmd_err)
            if cmd_err == "" and cmd_exec.returncode != 0:
                cmd_err = cmd_out
            if cmd_exec.returncode == 0:
                cmd_err = ""
            response = {
                'return_code': cmd_exec.returncode,
                'cmd_out': cmd_out,
                'cmd_err': cmd_err
            }
        else:
            system(cmd)
    except Exception as e:
        exception(e)
        response = {
            'return_code': -1,
            'cmd_out': '',
            'cmd_err': str(e)
        }
    return response


def make_request(url, api_binance=False, body=None):
    info("MAKE REQUEST: %s", url)
    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36'
    }
    if body is not None:
        header['Content-Type'] = 'application/json'
    if api_binance:
        header['X-MBX-APIKEY'] = Config.settings['binance']['binance_info']['key']
    to_return = {}
    try:
        if body is not None:
            to_return['response'] = urlopen(Request(url, data=bytes(dumps(body), encoding="utf-8"), headers=header)).read()
        else:
            to_return['response'] = urlopen(Request(url, headers=header)).read()
        to_return['state'] = True
    except Exception as e:
        exception(e)
        to_return['state'] = False
        to_return['response'] = "ERRORE: " + str(e)
    return to_return


def markdown_text(ret_str):
    char_list = ['_', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for c in char_list:
        ret_str = ret_str.replace(c, '\\' + c)
    return ret_str


def get_separator(title=None):
    ret_str = "-------------------------------------------------------------------\n"
    if title is not None:
        ret_str = "------------------------ *" + title + "* ------------------------\n"
    return ret_str


def initial_log(function_name, param_list):
    if type(param_list) is list:
        info("REQUEST: %s - PARAMETERS NUMBER: %s", function_name, len(param_list))
        for par in param_list:
            info("PARAMETER: %s", par)
    else:
        info("REQUEST: %s - PARAMETER: %s", function_name, param_list)


def make_driver_selenium(url, proxy=False, driver_or_page=True):
    options = ChromeOptions()
    options.binary_location = Config.settings['chromepath']
    options.headless = True
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--no-sandbox")
    if proxy:
        options.add_argument('--proxy-server=%s' % Config.settings['football']['proxy'])
    options.add_experimental_option('useAutomationExtension', False)
    driver = Chrome(options=options)
    driver.get(url)
    if driver_or_page:
        html_source = driver.page_source
        driver.quit()
        to_ret = html_source
    else:
        to_ret = driver
    return to_ret


def make_button_list(string_list, string_callback):
    button_list = []
    row_size = 2
    for i in range(0, len(string_list), row_size):
        profiles = string_list[i:i + row_size]
        row = []
        for profile in profiles:
            if type(profile) is tuple:
                row.append(InlineKeyboardButton(profile[0], callback_data=string_callback + "EVLI" + profile[1]))
            else:
                row.append(InlineKeyboardButton(str(profile), callback_data=string_callback + str(profile)))
        button_list.append(row)
    return InlineKeyboardMarkup(button_list)


class Config:

    settings = {}
    update_conf = False

    @staticmethod
    def reload():
        f = open("settings.json")
        Config.settings = load(f)
        f.close()

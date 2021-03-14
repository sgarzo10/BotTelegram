from subprocess import PIPE, Popen
from os import system
from urllib.request import urlopen, Request
from logging import info, exception
from json import load


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


def make_request(url):
    info("MAKE REQUEST: %s", url)
    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36'
    }
    to_return = {}
    try:
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


class Config:
    settings = load(open("settings.json"))

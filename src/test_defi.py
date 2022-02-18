from urllib.request import urlopen, Request
from logging import info, exception
from json import loads, dumps
from math import pow


def make_request(url, api_apeboard='', body=None):
    # print("MAKE REQUEST: %s", url)
    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36'
    }
    if body is not None:
        header['Content-Type'] = 'application/json'
    if api_apeboard != "":
        header['passcode'] = api_apeboard
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


class DefiBalance:

    def __init__(self):
        self.total_wallet = {'USD': 0}
        self.stablecoin = ['BUSD', 'USDC', 'MIMATIC', 'DAI', 'USDT', 'MIM', 'UST', 'AUST']
        self.wallet_list = []
        self.evm_wallet = {
            'wallet': '0x366f047855cd70e61f6c093af2bd0f3365583081',
            'chain': ['bsc', 'matic', 'ftm']
        }
        self.terra_wallet = {
            'wallet': 'terra1rwamch3gd3urvmd88n77zw6q6wcp5dev3r6khp',
            'chain': 'terra',
            'platform': ["anchorTerra", "loopTerra", "staderTerra"]
        }
        self.solana_wallet = {
            'wallet': 'HCWdk175Ca6uc2HPnFUk92pN7qD3zZEGSaAJ4twtvh8m',
            'chain': 'solana',
            'platform': []
        }
        self.soglia = 0.5

    @staticmethod
    def sum_platform_token(wallet, chain, pt_name, token, amount):
        token_name = str.upper(token)
        if token_name in wallet[chain]['platform'][pt_name]:
            wallet[chain]['platform'][pt_name][token_name] += amount
        else:
            wallet[chain]['platform'][pt_name][token_name] = amount
        return wallet

    def sum_token_aggegate(self, token, value):
        if token in self.stablecoin:
            self.total_wallet['USD'] += value
        else:
            if token in self.total_wallet:
                self.total_wallet[token] += value
            else:
                self.total_wallet[token] = value

    def evm_balance(self):
        evm_wallet = {}
        for c in self.evm_wallet['chain']:
            evm_wallet[c] = {
                'wallet': {},
                "platform": {}
            }
            ctx = loads(make_request(f"https://api.debank.com/token/balance_list?is_all=false&user_addr={self.evm_wallet['wallet']}&chain={c}")['response'])
            for d in ctx['data']:
                bal = d['balance'] / pow(10, d['decimals'])
                if d['price'] == 0.0 or bal * d['price'] > self.soglia:
                    evm_wallet[c]['wallet'][str.upper(d['symbol'])] = bal
        ctx = loads(make_request(f"https://api.debank.com/portfolio/project_list?user_addr={self.evm_wallet['wallet']}")['response'])
        for d in ctx['data']:
            evm_wallet[d['chain']]['platform'][d['name']] = {}
            for p in d['portfolio_list']:
                for t in p['detail']['supply_token_list']:
                    evm_wallet = DefiBalance.sum_platform_token(evm_wallet, d['chain'], d['name'], t['symbol'], t['amount'])
                if 'reward_token_list' in p['detail']:
                    for t in p['detail']['reward_token_list']:
                        evm_wallet = DefiBalance.sum_platform_token(evm_wallet, d['chain'], d['name'], t['symbol'], t['amount'])
        self.wallet_list.append(evm_wallet)
        return

    def ape_wallet_balance(self, wallet):
        ape_wallet = {
            wallet['chain']: {
                'wallet': {},
                "platform": {}
            }
        }
        endpoint_base = "https://apeboard.finance/"
        name = str(make_request(f"{endpoint_base}dashboard")['response']).split('<script src="/_next/static/chunks/pages/_app-')[1].split(".js")[0]
        resp = str(make_request(f"{endpoint_base}_next/static/chunks/pages/_app-{name}.js")['response'])
        passcode = resp.split('passcode="')[1].split('";')[0]
        endpoint_base = "https://api.apeboard.finance/"
        resp = loads(make_request(f"{endpoint_base}wallet/{wallet['chain']}/{wallet['wallet']}", api_apeboard=passcode)['response'])
        for c in resp:
            if c['balance'] * c['price'] > self.soglia:
                ape_wallet[wallet['chain']]['wallet'][str.upper(c['symbol'])] = c['balance']
        for p in wallet['platform']:
            ape_wallet[wallet['chain']]['platform'][p] = {}
            resp = {}
            while resp == {}:
                resp = loads(make_request(f"{endpoint_base}{p}/{wallet['wallet']}", api_apeboard=passcode)['response'])
            nkey = ''
            if 'savings' in list(resp.keys()):
                nkey = 'savings'
            if 'farms' in list(resp.keys()) and nkey == '':
                nkey = 'farms'
            for s in resp[nkey]:
                for t in s['tokens']:
                    if str.upper(t['symbol']) == 'AUST':
                        t['balance'] = t['balance'] * t['price']
                    ape_wallet = DefiBalance.sum_platform_token(ape_wallet, wallet['chain'], p, t['symbol'], t['balance'])
                if 'rewards' in list(s.keys()):
                    for r in s['rewards']:
                        ape_wallet = DefiBalance.sum_platform_token(ape_wallet, wallet['chain'], p, r['symbol'], r['balance'])
        self.wallet_list.append(ape_wallet)
        return

    def aggregate_balance(self):
        for v in self.wallet_list:
            for chain_info in v.values():
                for key, value in chain_info['wallet'].items():
                    self.sum_token_aggegate(key, value)
                for value in chain_info['platform'].values():
                    for key, balance in value.items():
                        self.sum_token_aggegate(key, balance)
        return self.total_wallet


if __name__ == '__main__':
    defi = DefiBalance()
    defi.evm_balance()
    defi.ape_wallet_balance(defi.terra_wallet)
    defi.ape_wallet_balance(defi.solana_wallet)
    print(defi.aggregate_balance())

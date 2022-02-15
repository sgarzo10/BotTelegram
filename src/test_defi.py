from urllib.request import urlopen, Request
from logging import info, exception
from json import loads, dumps
from math import pow


def make_request(url, api_binance=False, body=None):
    info("MAKE REQUEST: %s", url)
    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36'
    }
    if body is not None:
        header['Content-Type'] = 'application/json'
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
        self.stablecoin = ['BUSD', 'USDC', 'MIMATIC', 'DAI', 'USDT', 'MIM']
        self.evm_chain = ['bsc', 'matic', 'ftm']

    @staticmethod
    def sum_platform_token(wallet, chain, pt_name, token):
        token_name = str.upper(token['symbol'])
        if token_name in wallet[chain]['platform'][pt_name]:
            wallet[chain]['platform'][pt_name][token_name] += token['amount']
        else:
            wallet[chain]['platform'][pt_name][token_name] = token['amount']
        return wallet

    def sum_token_aggegate(self, token, value):
        if token in self.stablecoin:
            self.total_wallet['USD'] += value
        else:
            if token in self.total_wallet:
                self.total_wallet[token] += value
            else:
                self.total_wallet[token] = value

    def evm_balance(self, wallet):
        evm_wallet = {}
        for c in self.evm_chain:
            evm_wallet[c] = {
                'wallet': {},
                "platform": {}
            }
            ctx = loads(make_request(f"https://api.debank.com/token/balance_list?is_all=false&user_addr={wallet}&chain={c}")['response'])
            for d in ctx['data']:
                bal = d['balance'] / pow(10, d['decimals'])
                if d['price'] == 0.0 or bal * d['price'] > 0.1:
                    evm_wallet[c]['wallet'][str.upper(d['symbol'])] = bal
        ctx = loads(make_request(f"https://api.debank.com/portfolio/project_list?user_addr={wallet}")['response'])
        for d in ctx['data']:
            evm_wallet[d['chain']]['platform'][d['name']] = {}
            for p in d['portfolio_list']:
                for t in p['detail']['supply_token_list']:
                    evm_wallet = self.sum_platform_token(evm_wallet, d['chain'], d['name'], t)
                if 'reward_token_list' in p['detail']:
                    for t in p['detail']['reward_token_list']:
                        evm_wallet = self.sum_platform_token(evm_wallet, d['chain'], d['name'], t)
        return evm_wallet

    def aggregate_balance(self, defi_balance):
        for chain_info in defi_balance.values():
            for key, value in chain_info['wallet'].items():
                self.sum_token_aggegate(key, value)
            for value in chain_info['platform'].values():
                for key, balance in value.items():
                    self.sum_token_aggegate(key, balance)
        return self.total_wallet


if __name__ == '__main__':
    defi = DefiBalance()
    evm_wall = defi.evm_balance("0x366f047855cd70e61f6c093af2bd0f3365583081")
    print(defi.aggregate_balance(evm_wall))

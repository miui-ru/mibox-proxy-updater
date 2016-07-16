import json
import requests
import re
from os import path

LOCAL_PROXY_FILE = path.join(path.dirname(__file__), 'proxy.json')
GIMME_PROXY_API = 'http://gimmeproxy.com/api/getProxy?country=CN&protocol=http&anonymityLevel=1'


def read_local_list():
    with open(LOCAL_PROXY_FILE, 'r') as f:
        proxy = json.load(f)
    return proxy


def request_proxy():
    response = requests.get(GIMME_PROXY_API)
    if response.ok:
        return response.json()['ipPort']


def test_proxy(proxy):
    try:
        response = requests.get('http://baidu.com', timeout=2, proxies={'http': 'http://%s' % proxy})
        return re.search('www\.baidu\.com', response.text) is not None
    except:
        return False


def collect_proxy_addresses():
    return collect_from_gimme()


def collect_from_gimme():
    fetch_one = request_proxy()
    if fetch_one and test_proxy(fetch_one):
        return [fetch_one]
    else:
        return []


def save_local_list(proxy_list):
    with open(LOCAL_PROXY_FILE, 'w') as f:
        json.dump(proxy_list, f, indent=2)


def filter_broken_proxy(proxy_list):
    return [proxy for proxy in proxy_list if test_proxy(proxy)]


def update_squid_conf(proxy_list):
    lines = ['cache_peer {} parent {} 0 round-robin no-query no-digest'.format(*proxy.split(':')[0:2]) for proxy in proxy_list]
    with open('proxy_server_list.conf', 'w') as f:
        f.write('\n'.join(lines))


def main():
    proxy_list = read_local_list()
    proxy_list = filter_broken_proxy(proxy_list)
    proxy_list += collect_proxy_addresses()
    proxy_list = list(set(proxy_list))

    print('current proxy count: %i' % len(proxy_list))
    save_local_list(proxy_list)
    update_squid_conf(proxy_list)

if __name__ == '__main__':
    main()

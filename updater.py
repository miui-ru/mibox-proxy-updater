import json
import requests
import re
from os import path

LOCAL_PROXY_FILE = path.join(path.dirname(__file__), 'proxy.json')
GIMME_PROXY_API = 'http://gimmeproxy.com/api/getProxy?country=CN&protocol=http&anonymityLevel=1'
INCLOAK_PROXY_PAGE = 'https://incloak.com/proxy-list/?country=CN&anon=34'
TEST_TVMORE = 'http://vod.tvmore.com.cn/Service/TreeSite?code=program_site'


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
        proxies = {'http': 'http://%s' % proxy}
        print('testing %s' % proxy)
        response = requests.get('http://baidu.com', timeout=1, proxies=proxies)
        if not response.ok or re.search('www\.baidu\.com', response.text) is None:
            return False
        response = requests.get(TEST_TVMORE, timeout=1, proxies=proxies)
        if not response.ok or 'json' not in response.headers['Content-Type']:
            return False
        return True
    except requests.RequestException:
        return False


def collect_proxy_addresses():
    total = collect_from_gimme() + collect_from_incloak()
    return [proxy for proxy in list(set(total)) if test_proxy(proxy)]


def collect_from_incloak():
    print('collecting from incloak')
    response = requests.get(INCLOAK_PROXY_PAGE)
    if response.ok:
        proxy_list = re.findall('>\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\s*</td>\s*<td>\s*([0-9]+)\s*</td>', response.text)
        if len(proxy_list):
            return [':'.join(proxy) for proxy in proxy_list]
    return []


def collect_from_gimme():
    print('collecting from gimme')
    fetch_one = request_proxy()
    if fetch_one:
        return [fetch_one]
    return []


def save_local_list(proxy_list):
    with open(LOCAL_PROXY_FILE, 'w') as f:
        json.dump(proxy_list, f, indent=2)


def filter_broken_proxy(proxy_list):
    return [proxy for proxy in proxy_list if test_proxy(proxy)]


def update_squid_conf(proxy_list):
    lines = ['cache_peer {} parent {} 0 round-robin no-query no-digest'.format(*proxy.split(':')[0:2]) for proxy in
             proxy_list]
    with open('proxy_server_list.conf', 'w') as f:
        f.write('\n'.join(lines))


def unique_by_ip(proxy_list):
    filtered_list = []
    ip_list = []
    for proxy in proxy_list:
        ip = proxy.split(':')[0]
        if ip in ip_list:
            continue
        else:
            ip_list.append(ip)
            filtered_list.append(proxy)
    return filtered_list


def main():
    proxy_list = read_local_list()
    proxy_list = filter_broken_proxy(proxy_list)
    proxy_list += collect_proxy_addresses()
    proxy_list = unique_by_ip(proxy_list)

    print('current proxy count: %i' % len(proxy_list))
    save_local_list(proxy_list)
    update_squid_conf(proxy_list)


if __name__ == '__main__':
    main()

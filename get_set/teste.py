import pickle
import http.client
import urllib.parse


def call(cmd):
    conn = http.client.HTTPConnection('gnu-nb3.winet.dcc.ufmg.br', 8080)
    params = {'iface': 'wlan0', 'macs': {'00:18:e7:7c:9c:cd': '150.164.10.50', '54:e6:fc:da:ff:34': 'storm'}}
    q = urllib.parse.urlencode(params)
    url = "{}?{}".format(cmd, q)
    conn.request(method='GET', url=url)
    resp = conn.getresponse()
    r = resp.read()
    if len(r) == 0:
        data = "error"
    else:
        data = pickle.loads(r)
    print(data)


def call_h(cmd='/get_mos_hybrid'):
    call(cmd)


def call_a(cmd='/get_mos_ap'):
    call(cmd)


def call_c(cmd='/get_mos_client'):
    call(cmd)


call_a()
call_c()
call_h()

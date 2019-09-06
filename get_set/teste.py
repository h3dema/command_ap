"""
    Test to get the data to compute: MOS client, hybrid and AP
"""
import pickle
import http.client
import urllib.parse


def call(cmd, ap_name='gnu-nb3.winet.dcc.ufmg.br'):
    """ calls the AP
        @param cmd: valid values are ['/get_mos_hybrid', '/get_mos_ap', '/get_mos_client']
    """
    assert cmd in ['/get_mos_hybrid', '/get_mos_ap', '/get_mos_client'], "invalid command"
    conn = http.client.HTTPConnection(ap_name, 8080)
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
    """ get MOS hybrid data"""
    call(cmd)


def call_a(cmd='/get_mos_ap'):
    """ get MOS AP data"""
    call(cmd)


def call_c(cmd='/get_mos_client'):
    """ get MOS client data"""
    call(cmd)

""" just call all three to test
"""
call_a()
call_c()
call_h()

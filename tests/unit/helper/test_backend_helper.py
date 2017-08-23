import unittest

from haproxy.helper.backend_helper import *
from haproxy.config import HEALTH_CHECK

class BackendHelperTestCase(unittest.TestCase):
    def test_get_backend_routes(self):
        routes = {'HW': [{'container_name': 'HW_1', 'proto': 'tcp', 'port': '80', 'addr': '10.7.0.3', 'health_check': 'check'},
                         {'container_name': 'HW_2', 'proto': 'tcp', 'port': '80', 'addr': '10.7.0.2', 'health_check': 'check'}],
                  'WEB': [{'container_name': 'WEB_2', 'proto': 'tcp', 'port': '8080', 'addr': '10.7.0.4'},
                          {'container_name': 'WEB_1', 'proto': 'tcp', 'port': '8080', 'addr': '10.7.0.5'}]}
        self.assertEqual(["server HW_1 10.7.0.3:80 check", "server HW_2 10.7.0.2:80 check"],
                         get_backend_routes(is_sticky=False, routes=routes, routes_added=[], service_alias="HW"))
        self.assertEqual(["server WEB_1 10.7.0.5:8080 %s" % HEALTH_CHECK, "server WEB_2 10.7.0.4:8080 %s" % HEALTH_CHECK],
                         get_backend_routes(is_sticky=False, routes=routes, routes_added=[], service_alias="WEB"))
        self.assertEqual(["server WEB_1 10.7.0.5:8080 cookie WEB_1 %s" % HEALTH_CHECK, "server WEB_2 10.7.0.4:8080 cookie WEB_2 %s" % HEALTH_CHECK],
                         get_backend_routes(is_sticky=True, routes=routes, routes_added=[], service_alias="WEB"))
        self.assertEqual([],
                         get_backend_routes(is_sticky=False, routes={}, routes_added=[], service_alias="WEB"))
        self.assertEqual(["server WEB_2 10.7.0.4:8080 %s" % HEALTH_CHECK],
                         get_backend_routes(is_sticky=False, routes=routes, routes_added=[
                                 {'container_name': 'WEB_1', 'proto': 'tcp', 'port': '8080', 'addr': '10.7.0.5'}],
                                            service_alias="WEB"))
        self.assertEqual(["server WEB_2 10.7.0.4:8080 cookie WEB_2 %s" % HEALTH_CHECK],
                         get_backend_routes(is_sticky=True, routes=routes, routes_added=[
                                 {'container_name': 'WEB_1', 'proto': 'tcp', 'port': '8080', 'addr': '10.7.0.5'}],
                                            service_alias="WEB"))
        self.assertEqual(["server WEB_1 10.7.0.5:8080 %s" % HEALTH_CHECK, "server WEB_2 10.7.0.4:8080 %s" % HEALTH_CHECK],
                         get_backend_routes(is_sticky=False, routes=routes, routes_added=[
                                 {'container_name': 'WEB_3', 'proto': 'tcp', 'port': '8080', 'addr': '10.7.0.5'}],
                                            service_alias="WEB"))
        self.assertEqual([],
                         get_backend_routes(is_sticky=False, routes=routes, routes_added=[
                                 {'container_name': 'WEB_2', 'proto': 'tcp', 'port': '8080', 'addr': '10.7.0.4'},
                                 {'container_name': 'WEB_1', 'proto': 'tcp', 'port': '8080', 'addr': '10.7.0.5'}],
                                            service_alias="WEB"))
        self.assertEqual(["server HW_1 10.7.0.3:80 check", "server HW_2 10.7.0.2:80 check"],
                         get_backend_routes(is_sticky=False, routes=routes, routes_added=[
                                 {'container_name': 'WEB_3', 'proto': 'tcp', 'port': '8080', 'addr': '10.7.0.5'}],
                                            service_alias="HW"))
        self.assertEqual([],
                         get_backend_routes(is_sticky=False, routes=routes, routes_added=[], service_alias="HELLO"))

    def test_get_websocket_setting(self):
        vhosts = [{'service_alias': 'web-a', 'path': '', 'host': 'a.com', 'scheme': 'http', 'port': '8080'},
                  {'service_alias': 'web-a', 'path': '', 'host': 'ws.a.com', 'scheme': 'ws', 'port': '8080'},
                  {'service_alias': 'web-b', 'path': '', 'host': 'b.com', 'scheme': 'ws', 'port': '443'},
                  {'service_alias': 'web-c', 'path': '', 'host': 'c.com', 'scheme': 'wss', 'port': '80'},
                  {'service_alias': 'web-c', 'path': '', 'host': 'c.com', 'scheme': 'https', 'port': '80'}]

        self.assertEqual(['option http-server-close'], get_websocket_setting(vhosts, 'web-a'))
        self.assertEqual(['option http-server-close'], get_websocket_setting(vhosts, 'web-b'))
        self.assertEqual(['option http-server-close'], get_websocket_setting(vhosts, 'web-c'))
        self.assertEqual([], get_websocket_setting(vhosts, 'web-d'))
        self.assertEqual([], get_websocket_setting(vhosts, 'web-e'))

    def test_get_balance_setting(self):
        details = {'web-a': {'balance': 'balance_a'},
                   'web-b': {'balance': ''},
                   'web-c': {}}

        self.assertEqual(["balance balance_a"], get_balance_setting(details, 'web-a'))
        self.assertEqual([], get_balance_setting(details, 'web-b'))
        self.assertEqual([], get_balance_setting(details, 'web-c'))
        self.assertEqual([], get_balance_setting(details, 'web-d'))

    def test_sticky_setting(self):
        details = {'web-a': {'cookie': 'cookie_b'},
                   'web-b': {'attrB': 'valueB'},
                   'web-c': {'cookie': ''}}

        setting, is_sticky = get_sticky_setting(details, 'web-a')
        self.assertEqual(['cookie cookie_b'], setting)
        self.assertTrue(is_sticky)

        setting, is_sticky = get_sticky_setting(details, 'web-b')
        self.assertEqual([], setting)
        self.assertFalse(is_sticky)

        setting, is_sticky = get_sticky_setting(details, 'web-c')
        self.assertEqual([], setting)
        self.assertFalse(is_sticky)

    def test_get_force_ssl_setting(self):
        details = {'web-a': {'force_ssl': 'True'},
                   'web-b': {'force_ssl': 'False'},
                   'web-c': {'force_ssl': ''},
                   'web-d': {}}

        self.assertEqual(["redirect scheme https code 301 if !{ ssl_fc }"], get_force_ssl_setting(details, 'web-a'))
        self.assertEqual(["redirect scheme https code 301 if !{ ssl_fc }"], get_force_ssl_setting(details, 'web-b'))
        self.assertEqual([], get_force_ssl_setting(details, 'web-c'))
        self.assertEqual([], get_force_ssl_setting(details, 'web-d'))
        self.assertEqual([], get_force_ssl_setting(details, 'web-e'))

    def test_http_check_setting(self):
        details = {'web-a': {'http_check': 'check_a'},
                   'web-b': {'http_check': ''},
                   'web-c': {}}

        self.assertEqual(["option httpchk check_a"], get_http_check_setting(details, 'web-a'))
        self.assertEqual([], get_http_check_setting(details, 'web-b'))
        self.assertEqual([], get_http_check_setting(details, 'web-c'))
        self.assertEqual([], get_http_check_setting(details, 'web-d'))

    def test_get_hsts_max_age_settingg(self):
        details = {'web-a': {'hsts_max_age': '3h'},
                   'web-b': {'hsts_max_age': ''},
                   'web-c': {}}

        self.assertEqual(["rspadd Strict-Transport-Security:\ max-age=3h;\ includeSubDomains"],
                         get_hsts_max_age_setting(details, 'web-a'))
        self.assertEqual([], get_hsts_max_age_setting(details, 'web-b'))
        self.assertEqual([], get_hsts_max_age_setting(details, 'web-c'))
        self.assertEqual([], get_hsts_max_age_setting(details, 'web-d'))

    def test_get_gzip_compression_setting(self):
        details = {'web-a': {'gzip_compression_type': 'type a'},
                   'web-b': {'gzip_compression_type': ''},
                   'web-c': {}}

        self.assertEqual(["compression algo gzip", "compression type type a"],
                         get_gzip_compression_setting(details, 'web-a'))
        self.assertEqual([], get_gzip_compression_setting(details, 'web-b'))
        self.assertEqual([], get_gzip_compression_setting(details, 'web-c'))
        self.assertEqual([], get_gzip_compression_setting(details, 'web-d'))

    def test_get_options_setting(self):
        details = {'web-a': {'option': ['opt1', 'opt2']},
                   'web-b': {'option': ['opt3']},
                   'web-c': {'option': []},
                   'web-d': {}}

        self.assertEqual(["option opt1", "option opt2"], get_options_setting(details, 'web-a'))
        self.assertEqual(["option opt3"], get_options_setting(details, 'web-b'))
        self.assertEqual([], get_options_setting(details, 'web-c'))
        self.assertEqual([], get_options_setting(details, 'web-d'))
        self.assertEqual([], get_options_setting(details, 'web-e'))

    def test_get_extra_settings_setting(self):
        details = {'web-a': {'extra_settings': "setting1 SETTING1"},
                   'web-b': {'extra_settings': "setting2 SETTING2, setting3 SETTING3"},
                   'web-c': {'extra_settings': "set\,ting4 SETTING4,setting5 SETT\,ING5"},
                   'web-d': {'extra_settings': ""},
                   'web-e': {}}

        self.assertEqual(["setting1 SETTING1"], get_extra_settings_setting(details, 'web-a'))
        self.assertEqual(["setting2 SETTING2", "setting3 SETTING3"], get_extra_settings_setting(details, 'web-b'))
        self.assertEqual(["set,ting4 SETTING4", "setting5 SETT,ING5"], get_extra_settings_setting(details, 'web-c'))
        self.assertEqual([], get_extra_settings_setting(details, 'web-d'))
        self.assertEqual([], get_extra_settings_setting(details, 'web-e'))
        self.assertEqual([], get_extra_settings_setting(details, 'web-f'))

    def test_get_basic_auth_setting(self):
        details = {'web-a': {'exclude_basic_auth': 'true'},
                   'web-b': {}}

        self.assertEqual([], get_basic_auth_setting(details, 'something', 'web-a'))
        self.assertEqual(
            ["acl need_auth http_auth(haproxy_userlist)", "http-request auth realm haproxy_basic_auth if !need_auth"],
            get_basic_auth_setting(details, 'something', 'web-b'))
        self.assertEqual([], get_basic_auth_setting(details, "", 'web-b'))

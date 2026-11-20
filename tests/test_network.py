import socket,sys,unittest
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import network
import ai_engine as ai
from test_ai_engine import episode,settings

class NetworkTests(unittest.TestCase):
    def test_ipv4_is_tried_first_without_changing_global_socket(self):
        original=socket.create_connection
        v6=(socket.AF_INET6,socket.SOCK_STREAM,6,'',('::1',443,0,0))
        v4=(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',443))
        sock=Mock()
        with patch('network.socket.getaddrinfo',return_value=[v6,v4]),patch('network.socket.socket',return_value=sock) as create:
            self.assertIs(network.connect(('provider.test',443),60),sock)
            self.assertEqual(create.call_args.args[0],socket.AF_INET)
            sock.connect.assert_called_once_with(v4[4])
        self.assertIs(socket.create_connection,original)
    def test_failed_socket_closes_and_ipv6_can_fallback(self):
        v4=(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',443))
        v6=(socket.AF_INET6,socket.SOCK_STREAM,6,'',('::1',443,0,0))
        failed=Mock();failed.connect.side_effect=TimeoutError();working=Mock()
        with patch('network.socket.getaddrinfo',return_value=[v4,v6]),patch('network.socket.socket',side_effect=[failed,working]):
            self.assertIs(network.connect(('provider.test',443),60),working)
        failed.close.assert_called_once()
    def test_tcp_attempt_is_short_even_if_read_timeout_is_long(self):
        sock=Mock();sock.connect.side_effect=TimeoutError()
        rec=(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',443))
        with patch('network.socket.getaddrinfo',return_value=[rec]),patch('network.socket.socket',return_value=sock):
            with self.assertRaises(TimeoutError):network.connect(('provider.test',443),60)
        self.assertLessEqual(sock.settimeout.call_args.args[0],2)
    def test_transport_failure_stops_batch_not_fifty_retries(self):
        calls=[]
        def fail(*a):calls.append(1);raise ai.ModelError('Connection failed',0)
        run=ai.analyse([episode(1),episode(2)],settings(),transport=fail)
        self.assertEqual(len(calls),1)
        self.assertFalse(run['result']['complete'])
        self.assertEqual(len(run['result']['errors']),2)
    def test_https_context_verifies_certificates(self):
        handler=network.HTTPSHandler()
        self.assertTrue(handler._context.check_hostname)
        self.assertEqual(handler._context.verify_mode,2)

if __name__=='__main__':unittest.main()

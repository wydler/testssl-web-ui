import socket
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


APP_DIR = Path(__file__).resolve().parents[1] / "rootfs" / "var" / "www" / "html" / "testssl"
sys.path.insert(0, str(APP_DIR))

import SSLTestPortal as portal


class SingleIpScanTests(unittest.TestCase):
    def setUp(self):
        portal.application.config.update(TESTING=True)
        self.client = portal.application.test_client()

    def post_scan(self, buffered=False, **overrides):
        form = {
            "host": "example.com",
            "port": "443",
            "scantype": "certonly",
            "confirm": "yes",
            "single_ip": "yes",
        }
        form.update(overrides)
        return self.client.post("/", data=form, buffered=buffered)

    def test_uses_first_dns_address_for_connection_and_result(self):
        first_ip = "192.0.2.10"
        dns_answers = [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (first_ip, 443)),
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("192.0.2.11", 443)),
        ]

        with patch.object(portal.socket, "getaddrinfo", return_value=dns_answers) as getaddrinfo, \
                patch.object(portal.socket, "create_connection") as create_connection:
            response = self.post_scan()
            body = next(response.response).decode("utf-8")
            response.close()

        getaddrinfo.assert_called_once_with("example.com", 443, type=socket.SOCK_STREAM)
        create_connection.assert_called_once_with(
            (first_ip, 443),
            timeout=portal.preflightTimeout,
        )
        self.assertIn(f"IP address used: <strong>{first_ip}</strong>", body)

    def test_manual_ip_takes_precedence_over_single_ip_dns_lookup(self):
        manual_ip = "192.0.2.20"

        with patch.object(portal.socket, "getaddrinfo") as getaddrinfo, \
                patch.object(portal.socket, "create_connection") as create_connection:
            response = self.post_scan(ip=manual_ip)
            body = next(response.response).decode("utf-8")
            response.close()

        getaddrinfo.assert_not_called()
        create_connection.assert_called_once_with(
            (manual_ip, 443),
            timeout=portal.preflightTimeout,
        )
        self.assertIn(f"IP address used: <strong>{manual_ip}</strong>", body)

    def test_dns_lookup_error_is_reported(self):
        with patch.object(
            portal.socket,
            "getaddrinfo",
            side_effect=socket.gaierror("name resolution failed"),
        ), patch.object(portal.socket, "create_connection") as create_connection:
            response = self.post_scan(buffered=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"DNS resolution failed!", response.data)
        create_connection.assert_not_called()

    def test_empty_dns_answer_is_reported(self):
        with patch.object(portal.socket, "getaddrinfo", return_value=[]), \
                patch.object(portal.socket, "create_connection") as create_connection:
            response = self.post_scan(buffered=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No IP address found for the hostname!", response.data)
        create_connection.assert_not_called()


if __name__ == "__main__":
    unittest.main()

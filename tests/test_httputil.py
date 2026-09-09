import unittest
from unittest.mock import patch

from fndzlda.httputil import FetchResult, _fetch_curl, _is_wall, fetch


class _Proc:
    def __init__(self, returncode: int, stdout: bytes, stderr: bytes = b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class TestIsWall(unittest.TestCase):
    def test_empty_body_is_wall_even_on_200(self):
        self.assertTrue(_is_wall(200, ""))
        self.assertTrue(_is_wall(0, ""))

    def test_real_html_is_not_a_wall(self):
        html = "<html>" + ("x" * 9000) + "</html>"
        self.assertFalse(_is_wall(200, html))


class TestCurlStatus(unittest.TestCase):
    def test_http2_reset_is_status_0_not_200(self):
        proc = _Proc(
            92,
            b"\n__FNDZLDA_HTTP__:000",
            b"curl: (92) HTTP/2 stream 1 was not closed cleanly: INTERNAL_ERROR (err 2)",
        )
        with patch("fndzlda.httputil.shutil.which", return_value="/usr/bin/curl"):
            with patch("fndzlda.httputil.subprocess.run", return_value=proc):
                page = _fetch_curl("https://www.bestbuy.com/x", 5)
        self.assertEqual(page.status, 0)
        self.assertIn("HTTP/2", page.error)

    def test_http_200_keeps_body(self):
        proc = _Proc(0, b"<html>ok</html>\n__FNDZLDA_HTTP__:200")
        with patch("fndzlda.httputil.shutil.which", return_value="/usr/bin/curl"):
            with patch("fndzlda.httputil.subprocess.run", return_value=proc):
                page = _fetch_curl("https://example.com/x", 5)
        self.assertEqual(page.status, 200)
        self.assertIn("ok", page.body)
        self.assertEqual(page.error, "")


class TestFetchBestBuy(unittest.TestCase):
    def test_bestbuy_uses_store_app_ua(self):
        html = "<html>" + ("z" * 9000) + "</html>"
        curl_page = FetchResult(url="https://www.bestbuy.com/product/x", status=200, body=html)
        with patch("fndzlda.httputil._fetch_curl", return_value=curl_page) as curl_fetch:
            with patch("fndzlda.httputil._fetch_urllib") as urllib_fetch:
                page = fetch("https://www.bestbuy.com/product/x")
        curl_fetch.assert_called()
        kwargs = curl_fetch.call_args
        self.assertIn("BestBuy", kwargs.kwargs.get("ua") or kwargs[1].get("ua", ""))
        urllib_fetch.assert_not_called()
        self.assertEqual(page.status, 200)

    def test_akamai_reset_skips_urllib(self):
        curl_page = FetchResult(
            url="https://www.bestbuy.com/product/x",
            status=0,
            body="",
            error="curl: (92) HTTP/2 stream 1 was not closed cleanly: INTERNAL_ERROR (err 2)",
        )
        with patch("fndzlda.httputil._fetch_curl", return_value=curl_page):
            with patch("fndzlda.httputil._fetch_urllib") as urllib_fetch:
                page = fetch("https://www.bestbuy.com/product/x")
        urllib_fetch.assert_not_called()
        self.assertEqual(page.status, 0)
        self.assertIn("Akamai", page.error)

    def test_other_hosts_still_try_urllib_first(self):
        html = "<html>" + ("y" * 9000) + "</html>"
        urllib_page = FetchResult(url="https://www.nintendo.com/x", status=200, body=html)
        with patch("fndzlda.httputil._fetch_urllib", return_value=urllib_page) as urllib_fetch:
            with patch("fndzlda.httputil._fetch_curl") as curl_fetch:
                page = fetch("https://www.nintendo.com/x")
        urllib_fetch.assert_called_once()
        curl_fetch.assert_not_called()
        self.assertEqual(page.status, 200)

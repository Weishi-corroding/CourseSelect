"""Offline checks for the course catalog HTTP transport."""
import unittest
from unittest.mock import MagicMock, patch

import requests

import fetch_courses


class FetchTransportTests(unittest.TestCase):
    def tearDown(self):
        fetch_courses.cleanup_fetch_session()

    @staticmethod
    def response(payload=None, *, content=b"{}", url="https://jwgl.dhu.edu.cn/api", history=None):
        response = MagicMock()
        response.url = url
        response.history = [] if history is None else history
        response.content = content
        response.text = content.decode("utf-8", errors="replace")
        response.headers = {"Content-Type": "application/json"}
        response.json.return_value = payload
        return response

    def test_course_list_uses_requests_with_cookie_and_exact_form_body(self):
        payload = {
            "success": True,
            "aaData": [{"kcbh": "010001", "kcmc": "测试课程"}],
            "iTotalDisplayRecords": 1,
        }
        session = MagicMock()
        session.post.return_value = self.response(payload)
        with patch.object(fetch_courses, "_get_session", return_value=session):
            result = fetch_courses.fetch_course_list("JSESSIONID=secret", term_id=99, display_length=20)

        self.assertEqual(result, payload["aaData"])
        _, kwargs = session.post.call_args
        self.assertIn("termId=99", kwargs["data"])
        self.assertIn("iDisplayLength=20", kwargs["data"])
        self.assertEqual(kwargs["headers"]["Cookie"], "JSESSIONID=secret")
        self.assertEqual(kwargs["timeout"], 35)

    def test_course_list_fetches_every_server_page(self):
        first = {
            "success": True,
            "aaData": [{"kcbh": "1"}, {"kcbh": "2"}],
            "iTotalDisplayRecords": "3",
        }
        second = {
            "success": True,
            "aaData": [{"kcbh": "3"}],
            "iTotalDisplayRecords": "3",
        }
        session = MagicMock()
        session.post.side_effect = [self.response(first), self.response(second)]
        with patch.object(fetch_courses, "_get_session", return_value=session):
            result = fetch_courses.fetch_course_list("cookie", display_length=2)

        self.assertEqual([course["kcbh"] for course in result], ["1", "2", "3"])
        self.assertEqual(session.post.call_count, 2)
        first_body = session.post.call_args_list[0].kwargs["data"]
        second_body = session.post.call_args_list[1].kwargs["data"]
        self.assertIn("iDisplayStart=0", first_body)
        self.assertIn("iDisplayStart=2", second_body)
        self.assertIn("iDisplayLength=2", second_body)

    def test_course_list_discards_partial_result_if_later_page_fails(self):
        first = {
            "success": True,
            "aaData": [{"kcbh": "1"}, {"kcbh": "2"}],
            "iTotalDisplayRecords": 3,
        }
        session = MagicMock()
        session.post.side_effect = [
            self.response(first),
            requests.exceptions.Timeout("timeout"),
        ]
        with patch.object(fetch_courses, "_get_session", return_value=session), \
             patch.object(fetch_courses, "log"):
            self.assertEqual(fetch_courses.fetch_course_list("cookie", display_length=2), [])

    def test_timetable_uses_same_transport_and_parses_classes(self):
        html = """
        <table><tr><td>code</td><td>name</td><td>org</td><td>123</td>
        <td>1</td><td>80</td><td>40</td><td>42</td><td>松江校区</td><td>教师</td>
        <td><table><tr><td>1-16周</td><td>周一.1.2节</td><td>松A101</td></tr></table></td></tr></table>
        """
        session = MagicMock()
        session.post.return_value = self.response({"success": True, "content": html})
        with patch.object(fetch_courses, "_get_session", return_value=session):
            result = fetch_courses.fetch_course_timetable("cookie", "010001", term_id=99)

        self.assertEqual(result["class_count"], 1)
        self.assertEqual(result["classes"][0]["cttId"], "123")
        self.assertEqual(result["classes"][0]["maxCnt"], 80)
        self.assertEqual(result["classes"][0]["selection_scope"], "松江校区")
        self.assertIn("kcbh=010001", session.post.call_args.kwargs["data"])

    def test_login_redirect_and_empty_response_are_reported_as_failure(self):
        redirect = self.response({}, url="https://cas.dhu.edu.cn/identity/login", history=[object()])
        login_marker = self.response({}, content=b"/dhu/casLogin")
        empty = self.response({}, content=b"")
        session = MagicMock()
        with patch.object(fetch_courses, "_get_session", return_value=session), \
             patch.object(fetch_courses, "log") as logger:
            session.post.return_value = redirect
            with self.assertRaises(fetch_courses.SessionExpired):
                fetch_courses._post_json("https://example.test", "x=1", "secret")
            self.assertIn("Cookie 已失效", logger.call_args.args[0])
            session.post.return_value = login_marker
            with self.assertRaises(fetch_courses.SessionExpired):
                fetch_courses._post_json("https://example.test", "x=1", "secret")
            self.assertIn("Cookie 已失效", logger.call_args.args[0])
            session.post.return_value = empty
            self.assertIsNone(fetch_courses._post_json("https://example.test", "x=1", "secret"))
            self.assertIn("空响应", logger.call_args.args[0])

    def test_tls_failure_returns_cleanly(self):
        session = MagicMock()
        session.post.side_effect = requests.exceptions.SSLError("handshake failed")
        with patch.object(fetch_courses, "_get_session", return_value=session), \
             patch.object(fetch_courses, "log") as logger:
            self.assertEqual(fetch_courses.fetch_course_list("secret"), [])
        messages = [call.args[0] for call in logger.call_args_list]
        self.assertTrue(any("HTTPS 握手失败" in message for message in messages))

    def test_session_is_reused_and_cleanup_closes_it(self):
        fetch_courses.cleanup_fetch_session()
        with patch.object(fetch_courses.requests, "Session") as session_factory:
            session = session_factory.return_value
            self.assertIs(fetch_courses._get_session(), session)
            self.assertIs(fetch_courses._get_session(), session)
            session_factory.assert_called_once()
            fetch_courses.cleanup_fetch_session()
            session.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()

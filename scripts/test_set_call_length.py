#!/usr/bin/env python3
"""String-level checks for the Autopsy rename. Does not edit the repo."""

from __future__ import annotations

import unittest

import set_call_length as call


class CallLengthTests(unittest.TestCase):
    def test_product_name_and_preserved_bits(self) -> None:
        source = (
            "Start with a free 15-minute call. It gets you your BoFu Autopsy: five searches. "
            "15 minutes to 5x your traffic. Value $4,900. "
            "href=\"/15minutes5xtraffic/\" utm_campaign=15minutes5xtraffic "
            "https://calendly.com/30minutechat/20-minute-content-chat "
            "slug what-the-free-15-minute-call-includes stays. "
            "15 money pages. Book three 20-minute calls with customers who signed. "
            "Twenty minutes. The same three questions, so you can see what changed."
        )
        updated = call.apply_text(source, 20)
        self.assertIn("Start with the free 20 Minute BoFu Autopsy: five searches.", updated)
        self.assertIn("20 minutes to 5x", updated)
        self.assertIn("$4,900", updated)
        self.assertIn("/15minutes5xtraffic/", updated)
        self.assertIn("utm_campaign=15minutes5xtraffic", updated)
        self.assertIn("20-minute-content-chat", updated)
        self.assertIn("what-the-free-15-minute-call-includes", updated)
        self.assertIn("15 money pages", updated)
        self.assertIn("20-minute calls", updated)
        self.assertIn("Twenty minutes. The same three questions", updated)
        self.assertEqual(updated.count("15-minute"), 1)
        self.assertIn("what-the-free-15-minute-call-includes", updated)
        self.assertNotIn("audit", updated.lower())

    def test_nav_agenda_and_quarter_hour(self) -> None:
        source = (
            "15-min Autopsy. Free 15-min Autopsy. "
            "How the 15 minutes goes. 11\u201315 min. "
            "you've lost a quarter of an hour. "
            "it costs you fifteen minutes. "
            "on a fifteen-minute call. "
            "Fifteen minutes against the wait. "
            "Book My 15-Minute Autopsy. "
            "THE FREE 15-MINUTE BOFU AUTOPSY"
        )
        updated = call.apply_text(source, 20)
        self.assertIn("20 Minute BoFu Autopsy.", updated)
        self.assertIn("Free 20 Minute BoFu Autopsy.", updated)
        self.assertIn("How the 20 minutes goes", updated)
        self.assertIn("11\u201320 min", updated)
        self.assertIn("you've lost twenty minutes", updated)
        self.assertIn("costs you twenty minutes", updated)
        self.assertIn("on the 20 Minute BoFu Autopsy", updated)
        self.assertIn("Twenty minutes against", updated)
        self.assertIn("Book the 20 Minute BoFu Autopsy", updated)
        self.assertIn("THE FREE 20 MINUTE BOFU AUTOPSY", updated)
        self.assertNotIn("15-min", updated)
        self.assertNotIn("15 min", updated)

    def test_reverse_restores_call_copy_and_keeps_other_twenty_minutes(self) -> None:
        original = (
            "Start with a free 15-minute call. It gets you your BoFu Autopsy: five. "
            "Twenty minutes. The same three questions. "
            "https://calendly.com/30minutechat/20-minute-content-chat"
        )
        forward = call.apply_text(original, 20)
        back = call.apply_text(forward, 15)
        self.assertIn("Start with a free 15-minute call. It gets you your BoFu Autopsy:", back)
        self.assertIn("Twenty minutes. The same three questions", back)
        self.assertIn("20-minute-content-chat", back)


if __name__ == "__main__":
    unittest.main()

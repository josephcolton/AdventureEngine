import unittest

from engine.report import Report
from engine.textfile import decode, parse_text


def parse(text):
    report = Report()
    return parse_text(text, report), report


class TextFileTests(unittest.TestCase):
    def test_sections_and_settings(self):
        sections, report = parse("[game]\ntitle = Hi\n\n[room: Front Porch]\nname = Porch\n")
        self.assertFalse(report.messages)
        self.assertEqual([s.kind for s in sections], ["game", "room"])
        self.assertEqual(sections[1].name, "Front Porch")
        self.assertEqual(sections[0].value("title"), "Hi")

    def test_case_insensitive_types_and_keys(self):
        sections, _ = parse("[ROOM: x]\nNAME = Big\n")
        self.assertEqual(sections[0].kind, "room")
        self.assertEqual(sections[0].value("name"), "Big")

    def test_continuation_lines_join_with_spaces(self):
        sections, _ = parse("[room: x]\nfirst = One\n    two\n\tthree\n")
        self.assertEqual(sections[0].value("first"), "One two three")

    def test_tilde_paragraph(self):
        sections, _ = parse("[room: x]\nfirst = One\n    ~\n    Two\n")
        self.assertEqual(sections[0].value("first"), "One\n\nTwo")

    def test_blank_line_then_indent_is_paragraph(self):
        sections, report = parse("[room: x]\nfirst = One\n\n    Two\nname = N\n")
        self.assertFalse(report.messages)
        self.assertEqual(sections[0].value("first"), "One\n\nTwo")
        self.assertEqual(sections[0].value("name"), "N")

    def test_comments(self):
        sections, report = parse("# top\n[item: x]\n  # indented comment\n"
                                 "points = 5   # five\nlocation = here  # where\n"
                                 "examine = A #1 hat.  # not a comment\n")
        self.assertFalse(report.messages)
        s = sections[0]
        self.assertEqual(s.value("points"), "5")
        self.assertEqual(s.value("location"), "here")
        self.assertEqual(s.value("examine"), "A #1 hat.  # not a comment")

    def test_comment_after_section_header(self):
        sections, report = parse("[room: hall]   # the front hall\nname = Hall\n")
        self.assertFalse(report.messages)
        self.assertEqual(sections[0].name, "hall")

    def test_bom_and_crlf(self):
        text = decode("﻿[game]\r\ntitle = T\r\n    more\r\n".encode("utf-8"), Report())
        sections, report = parse(text)
        self.assertFalse(report.messages)
        self.assertEqual(sections[0].value("title"), "T more")

    def test_when_line_with_equals_in_condition(self):
        sections, report = parse("[room: x]\nwhen score = 50 = Half way!\n"
                                 "when score >= 10, flag y = Text = with equals\n")
        self.assertFalse(report.messages)
        a, b = sections[0].all("when")
        self.assertEqual((a.condition_text, a.value), ("score = 50", "Half way!"))
        self.assertEqual((b.condition_text, b.value), ("score >= 10, flag y",
                                                       "Text = with equals"))

    def test_conditional_item_text(self):
        sections, _ = parse("[item: x]\nexamine when flag fed = Happy.\n    Very.\n")
        entry = sections[0].all("examine when")[0]
        self.assertEqual(entry.condition_text, "flag fed")
        self.assertEqual(entry.value, "Happy. Very.")

    def test_ending_when_is_a_plain_setting(self):
        sections, _ = parse("[ending: e]\nwhen = has x, in y\n")
        entry = sections[0].last("when")
        self.assertIsNone(entry.condition_text)
        self.assertEqual(entry.value, "has x, in y")

    def test_text_before_first_section(self):
        _, report = parse("hello\n[game]\n")
        self.assertTrue(report.has_errors)
        self.assertEqual(report.errors[0].line, 1)

    def test_unindented_text_gets_indent_hint(self):
        _, report = parse("[room: x]\nfirst = One\nforgot to indent\n")
        self.assertIn("start it with a space", report.errors[0].text)
        self.assertEqual(report.errors[0].line, 3)

    def test_unknown_section_type_suggests(self):
        _, report = parse("[rooom: x]\n")
        self.assertIn("Did you mean [room]", report.errors[0].text)

    def test_section_needs_id(self):
        _, report = parse("[room]\n")
        self.assertTrue(report.has_errors)

    def test_malformed_when(self):
        _, report = parse("[room: x]\nwhen flagg y = hi\n")
        self.assertTrue(report.has_errors)

    def test_vocabulary_keys_may_be_phrases(self):
        sections, report = parse("[vocabulary]\nlook at = peer at, gaze at\n")
        self.assertFalse(report.messages)
        self.assertEqual(sections[0].entries[0].key, "look at")


if __name__ == "__main__":
    unittest.main()

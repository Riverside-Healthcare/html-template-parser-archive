"""Tests for AttributeParser."""
# pylint: disable=C0115

import pprint
import unittest

from HtmlTemplateParser import AttributeParser


class EventCollector(AttributeParser):
    def __init__(self, *args, **kw):
        self.events = []
        self.append = self.events.append
        AttributeParser.__init__(self, *args, **kw)

    def get_events(self):
        # Normalize the list of events so that buffer artefacts don't
        # separate runs of contiguous characters.
        L = []
        prevtype = None
        for event in self.events:
            type = event[0]
            if type == prevtype == "data":
                L[-1] = ("data", L[-1][1] + event[1])
            else:
                L.append(event)
            prevtype = type
        self.events = L
        return L

    def handle_starttag_curly_perc(self, tag, attrs, props):
        self.append(("starttag_curly_perc", tag, attrs, props))

    def handle_endtag_curly_perc(self, tag, attrs, props):
        self.append(("endtag_curly_perc", tag, attrs, props))

    def handle_comment_curly_hash(self, value):
        self.append(("comment_curly_hash", value))

    def handle_comment_curly_two_exclaim(self, value, props):
        self.append(("comment_curly_two_exclaim", value, props))

    def handle_comment_at_star(self, value):
        self.append(("comment_at_star", value))

    def handle_starttag_comment_curly_perc(self, tag, attrs, props):
        self.append(("starttag_comment_curly_percent", tag, attrs, props))

    def handle_endtag_comment_curly_perc(self, tag, attrs, props):
        self.append(("endtag_comment_curly_percent", tag, attrs, props))

    def handle_starttag_curly_two_hash(self, tag, attrs, props):
        self.append(("starttag_curly_two_hash", tag, attrs, props))

    def handle_endtag_curly_two_slash(self, tag, props):
        self.append(("endtag_curly_two_slash", tag, props))

    def handle_slash_curly_two(self, tag, attrs):
        self.append(("slash_curly_two", tag, attrs))

    def handle_endtag_curly_four_slash(self, tag, attrs, props):
        self.append(("endtag_curly_four_slash", tag, props))

    def handle_starttag_curly_four(self, tag, attrs, props):
        self.append(("starttag_curly_four", tag, attrs, props))

    def handle_curly_three(self, value):
        self.append(("curly_three", value))

    def handle_curly_two(self, tag, attrs, props):
        self.append(("curly_two", tag, attrs, props))

    def handle_name(self, name, props):
        self.append(("name", name, props))

    def handle_value(self, value):
        self.append(("value", value))

    def handle_value_start(self):
        self.append("value start/end")

    def handle_space(self):
        self.append("space")


class TestCaseBase(unittest.TestCase):
    def get_collector(self, source):
        return EventCollector(source)

    def _run_check(self, source, expected_events):
        parser = self.get_collector(source)
        parser.parse()

        events = parser.get_events()
        if events != expected_events:
            self.fail(
                "received events did not match expected events"
                + "\nSource:\n"
                + repr(source)
                + "\nExpected:\n"
                + pprint.pformat(expected_events)
                + "\nReceived:\n"
                + pprint.pformat(events)
            )


class AttributeCaseBase(TestCaseBase):
    def test_simple_class(self):
        self._run_check(
            'class="mercy"',
            [
                ("name", "class", ["has-value"]),
                "value start/end",
                ("name", "mercy", []),
                "value start/end",
            ],
        )

    def test_handlebars_escape(self):
        self._run_check(
            r"""
            \{{escaped attr}}
{{{{raw}}}}
  {{escaped}}data-src={%-url "tag:tag" pk=a.B.c 123    -%}
{{{{/raw}}}}""",
            [
                "space",
                ("slash_curly_two", "escaped", "attr"),
                "space",
                ("starttag_curly_four", "raw", "", []),
                "space",
                ("curly_two", "escaped", "", []),
                ("name", "data-src", ["has-value"]),
                (
                    "starttag_curly_perc",
                    "url",
                    '"tag:tag" pk=a.B.c 123',
                    ["spaceless-left", "spaceless-right"],
                ),
                "space",
                ("endtag_curly_four_slash", "raw", []),
            ],
        )

    def test_handlebars_if(self):
        self._run_check(
            """
            {{#if test}}
      {{title}}
    {{^}}
      Empty
    {{/if}}""",
            [
                "space",
                ("starttag_curly_two_hash", "if", "test", []),
                "space",
                ("curly_two", "title", "", []),
                "space",
                ("curly_two", "^", "", []),
                "space",
                ("name", "Empty", []),
                "space",
                ("endtag_curly_two_slash", "if", []),
            ],
        )

    def test_handlebars_whitespace_control(self):
        self._run_check(
            """
            {{~#if test}}
      {{~title}}
    {{~^~}}
      Empty
    {{~/if~}}
            """,
            [
                "space",
                ("starttag_curly_two_hash", "if", "test", ["spaceless-left"]),
                "space",
                ("curly_two", "title", "", ["spaceless-left"]),
                "space",
                ("curly_two", "^", "", ["spaceless-left", "spaceless-right"]),
                "space",
                ("name", "Empty", []),
                "space",
                ("endtag_curly_two_slash", "if", ["spaceless-left", "spaceless-right"]),
                "space",
            ],
        )

    def test_handlebars_each(self):
        self._run_check(
            """
            {{#each people}}
    {{../prefix}} {{firstname}}
{{/each}}
            """,
            [
                "space",
                ("starttag_curly_two_hash", "each", "people", []),
                "space",
                ("curly_two", "../prefix", "", []),
                "space",
                ("curly_two", "firstname", "", []),
                "space",
                ("endtag_curly_two_slash", "each", []),
                "space",
            ],
        )

    def test_handlebars_expressions(self):
        self._run_check(
            """
            {{person.firstname}} {{person.lastname}}
            """,
            [
                "space",
                ("curly_two", "person.firstname", "", []),
                "space",
                ("curly_two", "person.lastname", "", []),
                "space",
            ],
        )

    def test_handlebars_special_char(self):
        self._run_check(
            """
            {{{specialChars}}}
            """,
            ["space", ("curly_three", "specialChars"), "space"],
        )

    def test_handlebars_attributes(self):
        self._run_check(
            """
            {{loud lastname}}
            """,
            ["space", ("curly_two", "loud", "lastname", []), "space"],
        )

    def test_set(self):
        self._run_check(
            """
            {% set cool=[{loud:"lastname"}] %}
            """,
            [
                "space",
                ("starttag_curly_perc", "set", 'cool=[{loud:"lastname"}]', []),
                "space",
            ],
        )

    def test_nested_if_for(self):
        self._run_check(
            """
            {% if something %}
                data-src={{ one }}
                src="{% url "a:1" p#=q -%}
            {%- else %}
                {% for a in b +%}
                    {% set a=b %}
                    {%+ with x = b %}
                        class={{-x-}}
                    {% endwith %}
                    {% if a = b %}
                        data--x------xt-1-fs = "wO1"{{^no}}
                        {{#each one~}}
                            {{a}}
                            {{{{~raw}}}}
                            {{{{~/raw}}}}
                            {{{{raw~}}}}
                            {{{{/raw~}}}}
                        {{~/each~}}
                    {% endif %}
                {% endfor %}
            {% set cool=[{loud:"lastname"}] %}
            {# skip #}{{! handlebars comment }}@* c# comment *@
            {% comment %}{% endcomment %}
            {{!-- wow--}}{{~wow~}}
            hi, joe!
            {%
            """,
            [
                "space",
                ("starttag_curly_perc", "if", "something", []),
                "space",
                ("name", "data-src", ["has-value"]),
                ("curly_two", "one", "", []),
                "space",
                ("name", "src", ["has-value"]),
                "value start/end",
                ("starttag_curly_perc", "url", '"a:1" p#=q', ["spaceless-right"]),
                "space",
                ("starttag_curly_perc", "else", "", ["spaceless-left"]),
                "space",
                ("starttag_curly_perc", "for", "a in b", ["disable-spaceless-right"]),
                "space",
                ("starttag_curly_perc", "set", "a=b", []),
                "space",
                ("starttag_curly_perc", "with", "x = b", ["disable-spaceless-left"]),
                "space",
                ("name", "class", ["has-value"]),
                ("curly_two", "-x-", "", []),
                "space",
                ("endtag_curly_perc", "with", "", []),
                "space",
                ("starttag_curly_perc", "if", "a = b", []),
                "space",
                ("name", "data--x------xt-1-fs", ["has-value"]),
                "space",
                "space",
                "value start/end",
                ("name", "wO1", []),
                "value start/end",
                ("curly_two", "^no", "", []),
                "space",
                ("starttag_curly_two_hash", "each", "one", ["spaceless-right"]),
                "space",
                ("curly_two", "a", "", []),
                "space",
                ("starttag_curly_four", "raw", "", ["spaceless-left"]),
                "space",
                ("endtag_curly_four_slash", "raw", ["spaceless-left"]),
                "space",
                ("starttag_curly_four", "raw", "", ["spaceless-right"]),
                "space",
                ("endtag_curly_four_slash", "raw", ["spaceless-right"]),
                "space",
                (
                    "endtag_curly_two_slash",
                    "each",
                    ["spaceless-left", "spaceless-right"],
                ),
                "space",
                ("endtag_curly_perc", "if", "", []),
                "space",
                ("endtag_curly_perc", "for", "", []),
                "space",
                ("starttag_curly_perc", "set", 'cool=[{loud:"lastname"}]', []),
                "space",
                ("comment_curly_hash", "skip"),
                ("comment_curly_two_exclaim", "handlebars comment ", []),
                ("comment_at_star", "c# comment"),
                "space",
                ("starttag_comment_curly_percent", "comment", "", []),
                ("endtag_comment_curly_percent", "comment", "", []),
                "space",
                ("comment_curly_two_exclaim", "wow", ["safe-left", "safe-right"]),
                ("curly_two", "wow", "", ["spaceless-left", "spaceless-right"]),
                "space",
                ("name", "hi,", []),
                "space",
                ("name", "joe!", []),
                "space",
                ("name", "{%", []),
                "space",
            ],
        )

    def test_bad_stuff(self):
        self._run_check(
            "{% {{ ok }}", [("name", "{%", []), "space", ("curly_two", "ok", "", [])]
        )
        self._run_check(
            "{# {% ok %}",
            [("name", "{#", []), "space", ("starttag_curly_perc", "ok", "", [])],
        )
        self._run_check(
            "{{ {% ok %}",
            [("name", "{{", []), "space", ("starttag_curly_perc", "ok", "", [])],
        )
        self._run_check(
            "{{! {% ok %}",
            [("name", "{{!", []), "space", ("starttag_curly_perc", "ok", "", [])],
        )
        self._run_check(
            "@* {% ok %}",
            [("name", "@*", []), "space", ("starttag_curly_perc", "ok", "", [])],
        )
        self._run_check(
            "{{# {% ok %}",
            [("name", "{{#", []), "space", ("starttag_curly_perc", "ok", "", [])],
        )
        self._run_check(
            "{{/ {% ok %}",
            [("name", "{{/", []), "space", ("starttag_curly_perc", "ok", "", [])],
        )
        self._run_check(
            "\\{{ {% ok %}",
            [("name", "\\{{", []), "space", ("starttag_curly_perc", "ok", "", [])],
        )
        self._run_check(
            "{{{ {% ok %}",
            [("name", "{{{", []), "space", ("starttag_curly_perc", "ok", "", [])],
        )
        self._run_check(
            "{{{{ {% ok %}",
            [("name", "{{{{", []), "space", ("starttag_curly_perc", "ok", "", [])],
        )
        self._run_check(
            "{{{{/ {% ok %}",
            [("name", "{{{{/", []), "space", ("starttag_curly_perc", "ok", "", [])],
        )
        self._run_check(
            '" {% ok %}',
            ["value start/end", "space", ("starttag_curly_perc", "ok", "", [])],
        )
        self._run_check(
            "' {% ok %}",
            ["value start/end", "space", ("starttag_curly_perc", "ok", "", [])],
        )
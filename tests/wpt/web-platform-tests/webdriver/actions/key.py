# META: timeout=long

import pytest

from support.keys import Keys
from support.refine import get_keys, filter_dict, get_events


def test_lone_keyup_sends_no_events(session, key_reporter, key_chain):
    key_chain.key_up("a").perform()
    assert len(get_keys(key_reporter)) == 0
    assert len(get_events(session)) == 0
    session.actions.release()
    assert len(get_keys(key_reporter)) == 0
    assert len(get_events(session)) == 0


# TODO - the harness bails with TIMEOUT before all these subtests complete
# The timeout is per file, so move to separate file with longer timeout?
# Need a way to set timeouts in py files (since can't do html meta)
# @pytest.mark.parametrize("name,expected", ALL_EVENTS.items())
# def test_webdriver_special_key_sends_keydown(session,
#                                              key_reporter,
#                                              key_chain,
#                                              name,
#                                              expected):
#     key_chain.key_down(getattr(Keys, name)).perform()
#     # only interested in keydown
#     first_event = get_events(session)[0]
#     # make a copy so we throw out irrelevant keys and compare to events
#     expected = dict(expected)
#     del expected["value"]
#     # check and remove keys that aren't in expected
#     assert first_event["type"] == "keydown"
#     assert first_event["repeat"] == False
#     first_event = filter_dict(first_event, expected)
#     assert first_event == expected
#     # check that printable character was recorded in input field
#     if len(expected["key"]) == 1:
#         assert get_keys(key_reporter) == expected["key"]


@pytest.mark.parametrize("value,code", [
    (u"a", "KeyA",),
    ("a", "KeyA",),
    (u"\"", "Quote"),
    (u",", "Comma"),
    (u"\u00E0", ""),
    (u"\u0416", ""),
    (u"@", "Digit2"),
    (u"\u2603", ""),
    (u"\uF6C2", ""),  # PUA
])
def test_single_printable_key_sends_correct_events(session,
                                                   key_reporter,
                                                   key_chain,
                                                   value,
                                                   code):
    key_chain \
        .key_down(value) \
        .key_up(value) \
        .perform()
    expected = [
        {"code": code, "key": value, "type": "keydown"},
        {"code": code, "key": value, "type": "keypress"},
        {"code": code, "key": value, "type": "keyup"},
    ]
    events = [filter_dict(e, expected[0]) for e in get_events(session)]
    assert events == expected
    assert get_keys(key_reporter) == value


@pytest.mark.parametrize("value", [
    (u"\U0001F604"),
    (u"\U0001F60D"),
])
def test_single_emoji_records_correct_key(session, key_reporter, key_chain, value):
    # Not using key_chain.send_keys() because we always want to treat value as
    # one character here. `len(value)` varies by platform for non-BMP characters,
    # so we don't want to iterate over value.
    key_chain \
        .key_down(value) \
        .key_up(value) \
        .perform()
    # events sent by major browsers are inconsistent so only check key value
    assert get_keys(key_reporter) == value


@pytest.mark.parametrize("value,code,key", [
    (u"\uE050", "ShiftRight", "Shift"),
    (u"\uE053", "OSRight", "Meta"),
    (Keys.CONTROL, "ControlLeft", "Control"),
])
def test_single_modifier_key_sends_correct_events(session,
                                                  key_reporter,
                                                  key_chain,
                                                  value,
                                                  code,
                                                  key):
    key_chain \
        .key_down(value) \
        .key_up(value) \
        .perform()
    all_events = get_events(session)
    expected = [
        {"code": code, "key": key, "type": "keydown"},
        {"code": code, "key": key, "type": "keyup"},
    ]
    events = [filter_dict(e, expected[0]) for e in all_events]
    assert events == expected
    assert len(get_keys(key_reporter)) == 0


@pytest.mark.parametrize("value,code,key", [
    (Keys.ESCAPE, "Escape", "Escape"),
    (Keys.RIGHT, "ArrowRight", "ArrowRight"),
])
def test_single_nonprintable_key_sends_events(session,
                                              key_reporter,
                                              key_chain,
                                              value,
                                              code,
                                              key):
    key_chain \
        .key_down(value) \
        .key_up(value) \
        .perform()
    expected = [
        {"code": code, "key": key, "type": "keydown"},
        {"code": code, "key": key, "type": "keypress"},
        {"code": code, "key": key, "type": "keyup"},
    ]
    events = [filter_dict(e, expected[0]) for e in get_events(session)]
    if len(events) == 2:
        # most browsers don't send a keypress for non-printable keys
        assert events == [expected[0], expected[2]]
    else:
        assert events == expected
    assert len(get_keys(key_reporter)) == 0


def test_sequence_of_keydown_printable_keys_sends_events(session,
                                                         key_reporter,
                                                         key_chain):
    key_chain \
        .key_down("a") \
        .key_down("b") \
        .perform()
    expected = [
        {"code": "KeyA", "key": "a", "type": "keydown"},
        {"code": "KeyA", "key": "a", "type": "keypress"},
        {"code": "KeyB", "key": "b", "type": "keydown"},
        {"code": "KeyB", "key": "b", "type": "keypress"},
    ]
    events = [filter_dict(e, expected[0]) for e in get_events(session)]
    assert events == expected
    assert get_keys(key_reporter) == "ab"


def test_sequence_of_keydown_character_keys(session, key_reporter, key_chain):
    key_chain.send_keys("ef").perform()
    expected = [
        {"code": "KeyE", "key": "e", "type": "keydown"},
        {"code": "KeyE", "key": "e", "type": "keypress"},
        {"code": "KeyE", "key": "e", "type": "keyup"},
        {"code": "KeyF", "key": "f", "type": "keydown"},
        {"code": "KeyF", "key": "f", "type": "keypress"},
        {"code": "KeyF", "key": "f", "type": "keyup"},
    ]
    events = [filter_dict(e, expected[0]) for e in get_events(session)]
    assert events == expected
    assert get_keys(key_reporter) == "ef"

# -*- coding: utf-8 -*-

"""
    radish
    ~~~~~~

    Behavior Driven Development tool for Python - the root from red to green

    Copyright: MIT, Timo Furrer <tuxtimo@gmail.com>
"""

import os
import re
import tempfile

import pytest

import colorful

import radish.testing.matches as matches


@pytest.fixture(scope='module', autouse=True)
def disable_colors():
    """
    Fixture to disable colors
    """
    colorful.disable()
    yield
    colorful.use_8_ansi_colors()


def test_unreasonable_min_coverage(capsys):
    """
    Test unreasonable minimum test coverage
    """
    # given
    min_coverage = 101
    expected_returncode = 3

    # when
    actual_returncode = matches.test_step_matches_configs(None, [], min_coverage)
    _, err = capsys.readouterr()

    # then
    assert actual_returncode == expected_returncode
    assert err == 'You are a little cocky to think you can reach a minimum coverage of 101.00%\n'


def test_no_steps_found(mocker, capsys):
    """
    Test if basedir does not contain any Steps to test against
    """
    # given
    mocker.patch('radish.testing.matches.load_modules')
    expected_returncode = 4

    # when
    actual_returncode = matches.test_step_matches_configs(None, [])
    _, err = capsys.readouterr()

    # then
    assert actual_returncode == expected_returncode
    assert err == 'No step implementations found in [], thus doesn\'t make sense to continue'


def test_empty_matches_config(mocker, capsys):
    """
    Test empty matches config file
    """
    # given
    expected_returncode = 5

    fd, tmpfile = tempfile.mkstemp()
    os.close(fd)

    mocker.patch('radish.testing.matches.load_modules')
    steps_mock = mocker.patch('radish.testing.matches.StepRegistry.steps')
    steps_mock.return_value = [1, 2]

    # when
    actual_returncode = matches.test_step_matches_configs([tmpfile], [])
    out, _ = capsys.readouterr()

    # then
    assert actual_returncode == expected_returncode
    assert out == 'No sentences found in {0} to test against\n'.format(tmpfile)


@pytest.mark.parametrize('given_invalid_config', [
    [{'sentence': None}],
    [{'should_match': None}],
    [{}]
], ids=[
    'test config with missing should_match function attribute',
    'test config with missing sentence attribute',
    'test empty config'
])
def test_step_matches_invalid_config(given_invalid_config):
    """
    Test match config without a sentence and a should_match attribute
    """
    # given & when
    with pytest.raises(ValueError) as exc:
        matches.test_step_matches(given_invalid_config, [])

    # then
    assert str(exc.value) == 'You have to provide a sentence and the function name which should be matched (should_match)'


def test_sentence_no_step_match(capsys):
    """
    Test if sentence does not match any Step Pattern
    """
    # given
    steps = {}
    config = [{
        'sentence': 'foo', 'should_match': 'bar'
    }]
    expected_returncode = (1, 0)

    # when
    actual_returncode = matches.test_step_matches(config, steps)
    out, _ = capsys.readouterr()

    # then
    assert 'Expected sentence didn\'t match any step implemention' in out
    assert actual_returncode == expected_returncode


def test_sentence_match_wrong_step(capsys):
    """
    Test if sentence matched wrong step
    """
    # given
    def foo(): pass

    steps = {'foo': foo}
    config = [{
        'sentence': 'foo', 'should_match': 'bar'
    }]
    expected_returncode = (1, 0)

    # when
    actual_returncode = matches.test_step_matches(config, steps)
    out, _ = capsys.readouterr()

    # then
    assert 'Expected sentence matched foo instead of bar' in out
    assert actual_returncode == expected_returncode


def test_sentence_argument_errors(capsys):
    """
    Test if sentence arguments do not match
    """
    # given
    def foo(step, foo, bar): pass

    steps = {re.compile(r'What (.*?) can (.*)'): foo}
    config = [{
        'sentence': 'What FOO can BAR', 'should_match': 'foo',
        'with_arguments': [
            {'foo': 'foooooooo'},
            {'bar': 'baaaaaaar'}
        ]
    }]
    expected_returncode = (1, 0)

    # when
    actual_returncode = matches.test_step_matches(config, steps)
    out, _ = capsys.readouterr()

    # then
    assert 'Expected argument "foo" with value "foooooooo" does not match value "FOO"' in out
    assert 'Expected argument "bar" with value "baaaaaaar" does not match value "BAR"' in out
    assert actual_returncode == expected_returncode


@pytest.mark.parametrize('given_actual_arguments, expected_messages', [
    (
        {'FOO': None},
        ['Expected argument "foo" is not in matched arguments [\'FOO\']']
    ),
    (
        {'foo': 42},
        ['Expected argument "foo" is of type "int" instead "str"']
    ),
    (
        {'foo': 'foo'},
        ['Expected argument "foo" with value "fooo" does not match value "foo"']
    )
], ids=[
    'Missing argument',
    'Wrong type argument',
    'Wrong value argument'
])
def test_checking_step_arguments_errors(given_actual_arguments, expected_messages):
    """
    Test step argument checking errors
    """
    # given
    expected_arguments = {'foo': 'fooo'}

    # when
    messages = matches.check_step_arguments(expected_arguments, given_actual_arguments)

    # then
    assert messages == expected_messages


def test_checking_step_arguments():
    """
    Test sentence step arguments match
    """
    # given
    expected_arguments = {
        'foo': 'foo',
        'bar': 42
    }

    actual_arguments = {
        'foo': 'foo',
        'bar': 42
    }

    # when
    messages = matches.check_step_arguments(expected_arguments, actual_arguments)

    # then
    assert messages == []
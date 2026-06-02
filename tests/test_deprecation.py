"""Tests for the @with_deprecation decorator."""

import cmd2
from cmd2 import (
    CommandDeprecation,
    with_deprecation,
)

from .conftest import (
    run_cmd,
)


class DeprecationApp(cmd2.Cmd):
    """App with a variety of deprecated commands for testing."""

    @with_deprecation()
    def do_bare(self, _: cmd2.Statement) -> None:
        """Bare deprecated command."""
        self.poutput('bare ran')

    @with_deprecation(replacement='bare')
    def do_replaced(self, _: cmd2.Statement) -> None:
        """Has a replacement."""
        self.poutput('replaced ran')

    @with_deprecation(removal_version='3.0')
    def do_removed(self, _: cmd2.Statement) -> None:
        """Will be removed."""
        self.poutput('removed ran')

    @with_deprecation(message='See the changelog.', replacement='bare', removal_version='3.0')
    def do_everything(self, _: cmd2.Statement) -> None:
        """All options at once."""
        self.poutput('everything ran')


def test_command_deprecation_warning_text() -> None:
    assert CommandDeprecation().warning_text('foo') == "Command 'foo' is deprecated."
    assert CommandDeprecation(replacement='bar').warning_text('foo') == ("Command 'foo' is deprecated. Use 'bar' instead.")
    assert CommandDeprecation(removal_version='3.0').warning_text('foo') == (
        "Command 'foo' is deprecated and will be removed in version 3.0."
    )
    assert CommandDeprecation(message='Extra detail.', replacement='bar', removal_version='3.0').warning_text('foo') == (
        "Command 'foo' is deprecated and will be removed in version 3.0. Use 'bar' instead. Extra detail."
    )


def test_decorator_sets_metadata() -> None:
    deprecation = getattr(DeprecationApp.do_everything, cmd2.constants.CMD_ATTR_DEPRECATED)
    assert isinstance(deprecation, CommandDeprecation)
    assert deprecation.message == 'See the changelog.'
    assert deprecation.replacement == 'bare'
    assert deprecation.removal_version == '3.0'


def test_bare_deprecation_warns_and_still_runs() -> None:
    app = DeprecationApp()
    out, err = run_cmd(app, 'bare')
    assert out == ['bare ran']
    assert err == ["Command 'bare' is deprecated."]


def test_deprecation_with_replacement() -> None:
    app = DeprecationApp()
    out, err = run_cmd(app, 'replaced')
    assert out == ['replaced ran']
    assert err == ["Command 'replaced' is deprecated. Use 'bare' instead."]


def test_deprecation_with_removal_version() -> None:
    app = DeprecationApp()
    out, err = run_cmd(app, 'removed')
    assert out == ['removed ran']
    assert err == ["Command 'removed' is deprecated and will be removed in version 3.0."]


def test_deprecation_with_everything() -> None:
    app = DeprecationApp()
    out, err = run_cmd(app, 'everything')
    assert out == ['everything ran']
    assert err == [
        "Command 'everything' is deprecated and will be removed in version 3.0. Use 'bare' instead. See the changelog."
    ]


def test_non_deprecated_command_does_not_warn() -> None:
    app = DeprecationApp()
    _out, err = run_cmd(app, 'help')
    assert err == []


def test_verbose_help_annotates_deprecated_commands() -> None:
    app = DeprecationApp()
    out, _ = run_cmd(app, 'help --verbose')
    joined = '\n'.join(out)
    # Each deprecated command's description is annotated with the marker
    assert '(deprecated) Bare deprecated command.' in joined
    assert '(deprecated) Has a replacement.' in joined


def test_with_deprecation_combines_with_argparser() -> None:
    """The deprecation attribute must survive functools.wraps from with_argparser."""
    parser = cmd2.Cmd2ArgumentParser()

    class ArgparseDeprecationApp(cmd2.Cmd):
        @with_deprecation(replacement='other')
        @cmd2.with_argparser(parser)
        def do_thing(self, _: object) -> None:
            self.poutput('thing ran')

    app = ArgparseDeprecationApp()
    out, err = run_cmd(app, 'thing')
    assert out == ['thing ran']
    assert err == ["Command 'thing' is deprecated. Use 'other' instead."]

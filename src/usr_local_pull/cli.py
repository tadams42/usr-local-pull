import logging
import logging.config
import textwrap

import click

from .app import DEFAULT_PREFIX
from .supported_apps import (
    Bat,
    Dasel,
    Eza,
    FdFind,
    Fzf,
    GoJq,
    Jid,
    Jq,
    Jqp,
    Lazygit,
    Mdbook,
    Neovide,
    Ripgrep,
    Starship,
    Stylua,
    Xq,
    YamlQ,
)


class AppNameContext(logging.Filter):
    def filter(self, record):
        if not getattr(record, "app_name", None):
            record.app_name = "installer"
        return True


_CLI_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "filters": {"app_name_context": {"()": AppNameContext}},
    "formatters": {
        "logfmt": {"format": "lvl=%(levelname)s app=%(app_name)s msg=%(message)s"}
    },
    "handlers": {
        "console": {
            "filters": ["app_name_context"],
            "formatter": "logfmt",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        # root logger
        "": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "usr_local_pull": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

_PREFIX_HELP = textwrap.dedent(
    """
    Install prefix for everything.

    Usually `/usr/local`.

    Installing into `/usr/local` doesn't interfere with the rest of the system. Ie. you
    can have `ripgrep` installed from both, official distro package and this script and
    updating any of them will not overwrite the other. Which one gets used when you call
    `ripgrep` from your shell, depends on your `$PATH`. In most modern distros, stuff
    from `/usr/local` has priority.
    """
)


@click.command()
@click.option(
    "-p",
    "--prefix",
    type=click.Path(
        exists=False, dir_okay=True, file_okay=False, writable=True, resolve_path=True
    ),
    default=DEFAULT_PREFIX.as_posix(),
    show_default=True,
    help=_PREFIX_HELP,
)
def cli(prefix):
    """
    Installs or updates bunch of cmdline utilities directly from GitHub releases.
    """

    logging.config.dictConfig(_CLI_LOGGING_CONFIG)

    logging.info("Installing into: %s", prefix)

    installed = []

    for app in [
        Bat(prefix=prefix),
        Dasel(prefix=prefix),
        Eza(prefix=prefix),
        FdFind(prefix=prefix),
        Fzf(prefix=prefix),
        Ripgrep(prefix=prefix),
        Starship(prefix=prefix),
        YamlQ(prefix=prefix),
        Mdbook(prefix=prefix),
        Neovide(prefix=prefix),
        Lazygit(prefix=prefix),
        Stylua(prefix=prefix),
        GoJq(prefix=prefix),
        Jid(prefix=prefix),
        Jqp(prefix=prefix),
        Xq(prefix=prefix),
        Jq(prefix=prefix),
    ]:
        installed.extend(app.install())

    if installed:
        print("Installed files:")
        for _ in installed:
            print(f"- {_}")

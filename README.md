# usr-local-pull

[![PyPI Status](https://badge.fury.io/py/usr-local-pull.svg)](https://badge.fury.io/py/usr-local-pull)
[![license](https://img.shields.io/pypi/l/usr-local-pull.svg)](https://opensource.org/licenses/MIT)
[![python_versions](https://img.shields.io/pypi/pyversions/usr-local-pull.svg)](https://pypi.org/project/usr-local-pull/)

Installs bunch of cmdline utilities into `/usr/local` directly from GitHub releases.

Installing into `/usr/local` doesn't interfere with the rest of the system. Ie. you can
have `ripgrep` installed from both, official distro package and this script and updating
any of them will not overwrite the other. Which one gets used when you call `ripgrep`
from your shell, depends on your `$PATH`. In most modern distros, stuff from
`/usr/local` has priority.

Supported operating systems:

- any and only Linux
- only `x86_64` architecture

Supported shells:

- ZSH

Supported apps:

- [bat](https://github.com/TomWright/dasel)
- [dasel](https://github.com/starship/starship)
- [eza](https://github.com/eza-community/eza)
- [fd](https://github.com/sharkdp/fd)
- [fzf](https://github.com/junegunn/fzf)
- [goyq](https://github.com/itchyny/gojq)
- [jid](https://github.com/simeji/jid)
- [jq](https://github.com/jqlang/jq)
- [jqp](https://github.com/noahgorstein/jqp)
- [lazygit](https://github.com/jesseduffield/lazygit)
- [mdbook](https://github.com/rust-lang/mdBook)
- [neovide](https://github.com/neovide/neovide)
- [ripgrep](https://github.com/BurntSushi/ripgrep)
- [starship](https://github.com/starship/starship)
- [stylua](https://github.com/JohnnyMorganz/StyLua)
- [xq](https://github.com/sibprogrammer/xq)
- [yq](https://github.com/starship/starship)

## How to use it?

Install or update:

```sh
sudo su -
mkdir ~/usr-local-pull
cd usr-local-pull
python -m venv .venv
source .venv/bin/activate
pip install -U usr-local-pull
```

- needs to be run as `root` to be able to write into `/usr/local`

Install or update apps:

```sh
sudo su -
cd usr-local-pull
source .venv/bin/activate
usr-local-pull --help
usr-local-pull --prefix /tmp/try_it_out
usr-local-pull --prefix /usr/local
```

Other side-effects:

- uses `~/.cache` for stuff downloaded from `GitHub`

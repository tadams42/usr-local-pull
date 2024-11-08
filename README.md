# usr_local_utils

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

- [bat](https://github.com/sharkdp/bat)
- [eza](https://github.com/eza-community/eza)
- [fd](https://github.com/eza-community/eza)

## How to use it?

Install:

```sh
sudo su -
git clone https://github.com/tadams42/usr_local_utils.git
cd usr_local_utils
python -m venv .venv
source .venv/bin/activate
pip install -U pip wheel setuptools
pip install .
```

- needs to be run as `root` to be able to write into `/usr/local`

Update:

```sh
sudo su -
cd usr_local_utils
git pull
source .venv/bin/activate
pip install .
```

Install or update apps:

```sh
sudo su -
cd usr_local_utils
source .venv/bin/activate
usr_local_utils
```

Other side-effects:

- uses `~/.cache` for stuff downloaded from `GitHub`

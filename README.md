# A CLI client for Infoblox

Depends on: requests

## Installation
* Pull the git repo
* Copy `config.ini.example` to `config.ini` and make necessary changes
* Use the `dump` command to create an initial DNS file. You may want to manually split it into parts.
* Run the `update` command. It should report that everything is in sync.
* Done.

## Usage
### Commands
There are two commands: dump and update

    hostdb dump

This will print the current running DNS configuration to stdout, according to the DNS file format.

    hostdb update

This will read the configuration from the zonefile(s) and the running DNS configuration, calculate changes and try to apply them.

### Switches
Switches are documented in the program itself, please run `hostdb --help` for more information.

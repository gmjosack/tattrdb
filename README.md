# tattrdb

### Description
TattrDB is a simple way to add Tags and Attributes to hostnames
for use as a very generic service management database.

### Installation

```bash
pip install tattrdb
```

### Database Creation

Tattr uses sqlalchemy underneath and those uses a database url to
connect. Once you've constructed your url you can plugin it into the
example below:

```python
from tattrdb import models
models._sync(models.connect("sqlite:///tattr.sqlite"))
```

### Configuration

Using the same url from the example above you'll need to create a configuration
file at /etc/tattr.yaml as follows:

```yaml
db_uri: "sqlite:///tattr.sqlite"
```

### Command-line

Once you've finished installing and configuring tattr you can use the
tattr command line tool to add/rm/modify hosts/tags/attributes. Tattr
uses subcommands and each individual subcommand has it's own help
messages.

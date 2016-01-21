# nightshades

A Pomodoro library written with Python 3 and postgresql for storage.

## Why “nightshades”?

* Because this isn’t affiliated with The Pomodoro Technique™
* Because “tomatoes” is the common work around for this
* Because tomatoes are part of the [nightshade family](https://en.wikipedia.org/wiki/Solanaceae) (Solanacea)
* Because I’m not very creative…

## Goals

Eventually this will serve a REST API over HTTP which any client could use.

I’m thinking of using something like
[maxogden/menubar](https://github.com/maxogden/menubar)
to create a decoupled web client that could plop into a menu bar.

## Development

### Getting Started

`requirements.txt` contains all that’s needed to use the library traditionally,
but `requirements.dev.txt` contains packages needed for `playground.py`

```
$ git clone https://github.com/emilyhorsman/nightshades-python.git nightshades
$ cd nightshades
$ mkvirtualenv nightshades --python=python3
$ pip install -r requirements.dev.txt
$ psql -d nightshades -f sql/1453331350_migration.sql
$ python playground.py
```

These instructions assume that you’ve created a database called `nightshades`
and have correctly configured your roles. Unfortunately, the migration SQL
currently has a `CREATE EXTENSION` call. This means your current role will need
to have `superuser` privileges.

## dotenv

`nightshades` will attempt to load environment variables from a `.env` file
located in your current working directory. You can specify a different dotenv
path like so:

```
$ NIGHTSHADES_DOTENV=~/config/.nightshades.env python playground.py
```

Your `.env` should look something like this:

```
NIGHTSHADES_POSTGRESQL_DB_STR='dbname=somedatabasename'
```

## pypi

There is no usable version deployed yet, but this is registered on pypi as
`nightshades`:

https://pypi.python.org/pypi/nightshades

```
$ pip install nightshades
```
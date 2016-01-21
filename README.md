# nightshades

[![Coverage Status](https://coveralls.io/repos/github/emilyhorsman/nightshades-python/badge.svg?branch=development)](https://coveralls.io/github/emilyhorsman/nightshades-python?branch=development) [![Build Status](https://travis-ci.org/emilyhorsman/nightshades-python.svg?branch=development)](https://travis-ci.org/emilyhorsman/nightshades-python)

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

```
$ git clone https://github.com/emilyhorsman/nightshades-python.git nightshades
$ cd nightshades
```

### virtualenv

[virtualenvwrapper](https://virtualenvwrapper.readthedocs.org/en/latest/) makes
things pretty handy.

```
$ mkvirtualenv nightshades --python=python3
```

### Install packages

`requirements.txt` contains all production requirements.
`requirements.test.txt` contains all packages required for testing. Right now
this is only necessary for [Coveralls](http://coveralls.io/) and
[Coverage.py](https://coverage.readthedocs.org)

```
$ pip install -r requirements.txt
```

### Create database and run migrations

```
postgres=# CREATE DATABASE nightshades

$ find sql/*_migration.sql -exec psql -d nightshades -f {} \;
```

These instructions assume that you’ve created a database called `nightshades`
and have correctly configured your roles. Unfortunately, the migration SQL
currently has a `CREATE EXTENSION` call. This means your current role will need
to have `superuser` privileges.

### Testing

Note that `.test.env` has a database string set for testing.

```
postgres=# CREATE DATABASE nightshades_test;

$ find sql/*_migration.sql -exec psql -d nightshades_test -f {} \;
$ python tests.py
```

## dotenv

`nightshades` will attempt to load environment variables from a `.env` file
located in your current working directory. You can specify a different dotenv
path like so:

```
$ NIGHTSHADES_DOTENV=~/config/.nightshades.env python tests.py
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

## Coveralls.io

Make sure you have a `.coveralls.yml` with the `repo_token` from Coveralls.io.

```
$ pip install -r requirements.test.txt
$ coverage run tests.py
$ coverage report -m
$ coveralls
```

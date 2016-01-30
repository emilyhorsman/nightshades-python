# nightshades

[![Coverage Status](https://coveralls.io/repos/github/emilyhorsman/nightshades-python/badge.svg?branch=development)](https://coveralls.io/github/emilyhorsman/nightshades-python?branch=development)
[![Build Status](https://travis-ci.org/emilyhorsman/nightshades-python.svg?branch=development)](https://travis-ci.org/emilyhorsman/nightshades-python)
[![Code Climate](https://codeclimate.com/github/emilyhorsman/nightshades-python/badges/gpa.svg)](https://codeclimate.com/github/emilyhorsman/nightshades-python)
[![Python ≥ 3.3](https://img.shields.io/badge/python-%E2%89%A5%203.3-blue.svg)](https://docs.python.org/3/)
[![Contributor Covenant](https://img.shields.io/badge/code%20of%20conduct-v1.4.0-4C1161.svg)](CODE_OF_CONDUCT.md)

A [JSON API](http://jsonapi.org/) for productivity tracking (using Pomodoros).
Written for Python 3+ with [Flask](http://flask.pocoo.org/) handling HTTP
requests and postgresql for storage.

This repo contains both an internal and external API. The external JSON API
uses token-based authentication to interact with a client. The internal API
consists of some Python classes that interact with postgresql. The external
API lives entirely in `nightshades/http/` and the internal API at the root of
`nightshades/`.

## Why “nightshades”?

* Because this isn’t affiliated with The Pomodoro Technique™
* Because “tomatoes” is the common work around for this
* Because tomatoes are part of the [nightshade family](https://en.wikipedia.org/wiki/Solanaceae) (Solanacea)
* Because I’m not very creative…

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
$ createdb nightshades
$ python migration.py
```

Unfortunately, the migration SQL currently has a `CREATE EXTENSION` call. This
means your current role will need to have `superuser` privileges.

### Testing

Note that `.test.env` has a database string set for testing.

```
$ createdb nightshades_test
$ NIGHTSHADES_POSTGRESQL_DB_URI='postgresqlext:///nightshades_test' python migration.py
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
NIGHTSHADES_POSTGRESQL_DB_URI='postgresqlext:///nightshades_test'
NIGHTSHADES_APP_SECRET=somerandomlygeneratedsecretkey
ENVIRONMENT=development

TWITTER_CONSUMER_KEY=key
TWITTER_CONSUMER_SECRET=secret

FACEBOOK_APP_ID=key
FACEBOOK_APP_SECRET=secret
```

## pypi

There is no usable version deployed yet, but this is registered on pypi as
`nightshades`:

https://pypi.python.org/pypi/nightshades

```
$ pip install nightshades
```

## Style

Configuration already exists in `tox.ini`, using `flake8`:

```
$ pip install flake8
$ flake8
```

## Coveralls.io

Make sure you have a `.coveralls.yml` with the `repo_token` from Coveralls.io.

```
$ pip install -r requirements.test.txt
$ coverage run tests.py
$ coverage report -m
$ coveralls
```

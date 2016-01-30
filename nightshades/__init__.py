# -*- coding: utf-8 -*-

"""
nightshades
~~~~~~~~~~~

A Pomodoro library using postgres.
"""

__title__   = 'nightshades'
__version__ = '0.1.0'
__author__  = 'Emily Horsman'

from .session import load_dotenv, connection
from . import models
from . import api

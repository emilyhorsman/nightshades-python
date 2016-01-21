# This is just a playground for the library during development.

import tabulate
import colorama
from colorama import Fore, Style
import nightshades

colorama.init()

date_fmt = '%a %b %-m %Y'
time_fmt = '%H:%M'

def unit_row(unit):
    if unit[1]:
        completion = '{hi}complete{end}'.format(
            hi  = Style.BRIGHT + Fore.GREEN,
            end = Style.RESET_ALL,)
    else:
        completion = '{hi}incomplete{end}'.format(
            hi  = Style.BRIGHT + Fore.RED,
            end = Style.RESET_ALL,)

    return (
        completion,
        unit[2].strftime(time_fmt),
        unit[3].strftime(time_fmt),
        unit[2].strftime(date_fmt),)

with nightshades.connection() as conn:
    user  = nightshades.api.User(conn, 1)
    units = user.get_units(show_incomplete = True)

    print('{hi}{n}{end} nightshades on record!'.format(
        hi  = Style.BRIGHT + Fore.MAGENTA,
        end = Style.RESET_ALL,
        n   = len(units),))
    print()
    print(tabulate.tabulate(map(unit_row, units),
        headers  = ['Status', 'Start', 'End', 'Date'],
        tablefmt = 'orgtbl',))

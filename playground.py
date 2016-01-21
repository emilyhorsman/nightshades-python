# This is just a playground for the library during development.

import sys

import tabulate
import colorama
from colorama import Fore, Style
import nightshades

colorama.init()

date_fmt = '%a %b %-d %Y'
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

        incomplete_unit = nightshades.api.Unit(conn, 1, unit[0])
        print('{} remaining on incomplete unit.'.format(
            incomplete_unit.time_left()))
        print()

        if sys.argv[-1] == 'c':
            print(incomplete_unit.mark_complete())

    return (
        completion,
        unit[2].strftime(time_fmt),
        unit[3].strftime(time_fmt),
        unit[2].strftime(date_fmt),)

with nightshades.connection() as conn:
    user = nightshades.api.User(conn, 1)
    new_unit = user.start_unit()
    if not new_unit[0]:
        print('{hi}Error:{end} {error}'.format(
            hi    = Fore.RED,
            end   = Style.RESET_ALL,
            error = new_unit[1],))


    units = user.get_units(show_incomplete = True)

    print('{hi}{n}{end} nightshades on record!'.format(
        hi  = Style.BRIGHT + Fore.MAGENTA,
        end = Style.RESET_ALL,
        n   = len(units),))
    print()
    print(tabulate.tabulate(map(unit_row, units),
        headers  = ['Status', 'Start', 'End', 'Date'],
        tablefmt = 'orgtbl',))

#!/usr/bin/env python

import os

import click

from app.management import prepare_database


@click.group()
def main():
    pass


@main.command(help='Run web app')
@click.option('--debug', help='Turn on debug toolbar')
def runserver(debug):
    opts = []
    if debug:
        opts.append(['--debug-toolbar'])

    os.system('adev runserver --host `hostname` {}'.format(' '.join(opts)))


@main.command(help='Initialize database')
def initdb():
    prepare_database(delete_existing=True)


if __name__ == '__main__':
    main()

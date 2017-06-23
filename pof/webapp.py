from aiohttp import web
import click

from pof.views.index import index

app = web.Application()


@click.command(help='Start webapp')
@click.option('--port', type=int, default=8080, help='Port to run app on')
def main(port):
    app.router.add_get('/', index)

    web.run_app(app, port=port)

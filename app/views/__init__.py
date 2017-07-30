from aiohttp_jinja2 import template

from .user import UserSession
from ..models import sa_users


@template('index.jinja')
async def index(request):
    """
    This is the view handler for the "/" url.

    :param request: the request object see http://aiohttp.readthedocs.io/en/stable/web_reference.html#request
    :return: context for the template.
    """
    user_id = await UserSession(request).user_id()
    name = None
    user = None

    if user_id:
        async with request.app['pg_engine'].acquire() as conn:
            result = await conn.execute(sa_users.select(sa_users.c.id == user_id))
            user = await result.fetchone()
            name = user.name

    return {
        'intro': "Welcome to Part of Family" + (', ' + name if name else ''),
        'user': user,
    }

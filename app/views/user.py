from datetime import datetime
import logging

from aiohttp.web import View, HTTPFound
from aiohttp_jinja2 import template
from passlib.hash import pbkdf2_sha256
from psycopg2 import IntegrityError

from ..models import sa_users
from ..user import UserSession

log = logging.getLogger(__name__)


class Join(View):
    """
    This is the view handler for the "/join" url.
    """
    title = 'Be Part of The Family'

    @template('join.jinja')
    async def get(self):
        return {
            'title': self.title
        }

    @template('join.jinja')
    async def post(self):
        data = await self.request.post()

        error = ''
        required_fields = ['name', 'email', 'password']
        missing_fields = []

        for field in required_fields:
            if field not in data or not data[field].strip():
                missing_fields.append(field)

        if missing_fields:
            error = 'Please fill out ' + ', '.join(missing_fields)
        elif len(data['password']) < 5:
            error = 'Password must have at least 5 characters'

        if not error:
            try:
                async with self.request.app['pg_engine'].acquire() as conn:
                    result = await conn.execute(sa_users.insert().values(
                        name=data['name'],
                        email=data['email'],
                        password=pbkdf2_sha256.hash(data['password']),
                        created_on=datetime.utcnow(),
                    ))
                    user_id = await result.scalar()

            except IntegrityError as e:
                log.debug(e)
                # TODO: Password reset
                error = 'There is already an account using that email.<br/>Password reset feature coming soon!'

            else:
                await UserSession(self.request).create(user_id)

                return HTTPFound(self.request.app.router['index'].url())

        if error:
            return {
                'warn': error,
                'title': self.title,
                'name': data['name'],
                'email': data['email'],
                'password': data['password'],
            }


class Login(View):
    """
    This is the view handler for the "/login" url.
    """
    @template('login.jinja')
    async def get(self):
        return {
            'title': 'Login'
        }

    @template('login.jinja')
    async def post(self):
        data = await self.request.post()

        return {
            'title': 'Login',
            'email': data['email'],
            'password': data['password'],
        }

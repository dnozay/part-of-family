from aiohttp.web import View, HTTPFound
from aiohttp_jinja2 import template


class Join(View):
    """
    This is the view handler for the "/join" url.
    """
    title = 'Be Part of the Family'

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

        if error:
            return {
                'warn': error,
                'title': self.title,
                'name': data['name'],
                'email': data['email'],
                'password': data['password'],
            }

        else:
            return HTTPFound(self.request.app.router['index'].url())


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

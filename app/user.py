from datetime import datetime
import logging
import uuid

from aiohttp_session import get_session
import sqlalchemy as sa

from app.models import sa_user_sessions

log = logging.getLogger(__name__)


class UserSession:
    def __init__(self, request):
        """
        :param aiohttp.web.Request request:
        """
        self.request = request

    async def user_id(self):
        """ Returns the user ID of the session """
        session = await get_session(self.request)
        session_id = session.get('session_id')

        if session_id:
            client_ip = self.client_ip()

            async with self.request.app['pg_engine'].acquire() as conn:
                result = await conn.execute(
                    sa.select([sa_user_sessions.c.user_id]).where(sa_user_sessions.c.id == session_id)
                                                           .where(sa_user_sessions.c.client_ip == client_ip))
                return await result.scalar()

    async def create(self, user_id):
        """ Creates the session ID """
        session = await get_session(self.request)

        session_id = str(uuid.uuid4())
        client_ip = self.client_ip()[:32]
        client_agent = self.request.headers.get('User-Agent', '')[:256]

        async with self.request.app['pg_engine'].acquire() as conn:
            await conn.execute(sa_user_sessions.insert().values(
                id=session_id,
                user_id=user_id,
                client_ip=client_ip,
                client_agent=client_agent,
                created_on=datetime.utcnow(),
            ))

        session['session_id'] = session_id

    async def delete(self):
        """ Deletes the session ID """
        session = await get_session(self.request)

        session_id = session.pop('session_id', None)
        client_ip = self.client_ip()[:32]

        if session_id:
            try:
                async with self.request.app['pg_engine'].acquire() as conn:
                    await conn.execute(sa_user_sessions.delete().where(sa.and_(
                        id=session_id,
                        client_ip=client_ip,
                    )))
            except Exception as e:
                log.error(e)

    def client_ip(self):
        """ Returns the user client IP """
        host = '0.0.0.0'

        peername = self.request.transport.get_extra_info('peername')
        if peername is not None:
            host, _ = peername

        return host

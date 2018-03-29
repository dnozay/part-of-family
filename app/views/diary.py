from collections import defaultdict
import datetime
import logging
import re

from aiohttp.web import View, HTTPFound
from aiohttp_jinja2 import template
from psycopg2 import IntegrityError
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound

from ..models import sa_diary_entries
from ..user import UserSession

log = logging.getLogger(__name__)
DOUBLE_NEWLINE_RE = re.compile('(?:\r?\n){2}')
ENDING_CHARS_RE = re.compile('[!.]')
TRAIL_CHARS_RE = re.compile('[:-]')


class DiaryView(View):
    def entry_date(self):
        """ Date for requested diary entry """
        # TODO: Need to account for timezone
        if self.request.match_info:
            year = int(self.request.match_info['year'])
            month = int(self.request.match_info.get('month', 1))
            day = int(self.request.match_info.get('day', 1))
            d = datetime.date(year, month, day)
        else:
            d = datetime.date.today()

        return d


class Day(DiaryView):
    """
    This is the view handler for the "/diary/{year}/{month}/{day}" url.
    """
    title = '{:%b %d}'

    @template('diary_entry.jinja')
    async def get(self):
        date = self.entry_date()
        user_id = await UserSession(self.request).user_id()

        async with self.request.app['pg_engine'].acquire() as conn:
            result = await conn.execute(sa_diary_entries.select(and_(
                sa_diary_entries.c.user_id == user_id,
                sa_diary_entries.c.created_on == date,
            )))
            entry = await result.first()

        next_day = date + datetime.timedelta(days=1) if date < datetime.date.today() else None

        return {
            'success': self.request.query.get('success'),
            'title': self.title.format(date),
            'moments': entry.moments if entry else '',
            'day': date,
            'prev_day': date - datetime.timedelta(days=1),
            'next_day': next_day,
        }

    @template('diary_entry.jinja')
    async def post(self):
        date = self.entry_date()
        user_id = await UserSession(self.request).user_id()
        data = await self.request.post()

        error = ''
        required_fields = ['moments']
        missing_fields = []

        for field in required_fields:
            if field not in data or not data[field].strip():
                missing_fields.append(field)

        if missing_fields:
            error = 'Please fill out ' + ', '.join(missing_fields)

        if not error:
            highlights = []
            for moment in DOUBLE_NEWLINE_RE.split(data['moments']):
                m = ENDING_CHARS_RE.search(moment)
                hl_index = m.start() if m else -1

                m = TRAIL_CHARS_RE.search(moment)
                trail_index = m.start() if m else -1
                if trail_index > 0 and (hl_index < 0 or trail_index < hl_index):
                    hl_index = trail_index
                else:
                    trail_index = 100

                if hl_index < 0 or hl_index >= trail_index:
                    highlights.append(moment[:trail_index].strip() + ('...' if len(moment) > trail_index else ''))
                else:
                    highlights.append(moment[:hl_index+1].strip())

            try:
                async with self.request.app['pg_engine'].acquire() as conn:
                    result = await conn.execute(sa_diary_entries.select(and_(
                        sa_diary_entries.c.user_id == user_id,
                        sa_diary_entries.c.created_on == date
                    )))
                    entry = await result.first()
                    if not entry:
                        raise NoResultFound()

                    await conn.execute(sa_diary_entries.update()
                                       .where(sa_diary_entries.c.id == entry.id)
                                       .values(
                                           highlights=' '.join(highlights),
                                           moments=data['moments']
                    ))

            except NoResultFound:
                try:
                    async with self.request.app['pg_engine'].acquire() as conn:
                        await conn.execute(sa_diary_entries.insert().values(
                            user_id=user_id,
                            created_on=date,
                            highlights=' '.join(highlights),
                            moments=data['moments'],
                        ))

                except IntegrityError as e:
                    log.error(e)
                    error = "Oops! Couldn't save for some reason. Please try again later"

        if error:
            return {
                'warn': error,
                'title': self.title.format(date),
                'moments': data['moments'],
            }

        else:
            return HTTPFound(self.request.app.router['diary-month'].url_for(year=date.year, month=date.month))


class Month(DiaryView):
    """
    This is the view handler for the "/diary/{year}/{month}" url.
    """
    title = '{:%B}'

    @template('diary_month.jinja')
    async def get(self):
        start_date, end_date = self.date_range()
        user_id = await UserSession(self.request).user_id()
        highlights = []
        warn = None

        try:
            async with self.request.app['pg_engine'].acquire() as conn:
                result = await conn.execute(sa_diary_entries.select(and_(
                    sa_diary_entries.c.user_id == user_id,
                    sa_diary_entries.c.created_on >= start_date,
                    sa_diary_entries.c.created_on < end_date,
                )))
                async for entry in result:
                    highlights.append((entry.created_on.day, entry.highlights))

        except Exception as e:
            log.error(e, exc_info=1)
            warn = 'Oops. Something is wrong. Please try again later'

        return {
            'warn': warn,
            'title': self.title.format(start_date),
            'highlights': highlights,
            'date': start_date,
        }

    def date_range(self):
        """ Start and end day of the month (exclusive) for a given date """
        date = self.entry_date()
        start_date = datetime.date(date.year, date.month, 1)
        end_date = datetime.date(date.year, date.month + 1, 1) if date.month < 12 else datetime.date(date.year + 1, 1, 1)
        return start_date, end_date


class Year(DiaryView):
    """
    This is the view handler for the "/diary/{year}" url.
    """
    title = '{:%B}'

    @template('diary_year.jinja')
    async def get(self):
        start_date, end_date = self.date_range()
        user_id = await UserSession(self.request).user_id()
        highlights = defaultdict(lambda: defaultdict(int))
        warn = None

        try:
            async with self.request.app['pg_engine'].acquire() as conn:
                result = await conn.execute(sa_diary_entries.select(and_(
                    sa_diary_entries.c.user_id == user_id,
                    sa_diary_entries.c.created_on >= start_date,
                    sa_diary_entries.c.created_on < end_date,
                )).with_only_columns([sa_diary_entries.c.created_on]))
                async for entry in result:
                    highlights[entry.created_on.month][entry.created_on.strftime('%B')] += 1

        except Exception as e:
            log.error(e, exc_info=1)
            warn = 'Oops. Something is wrong. Please try again later'

        return {
            'warn': warn,
            'title': start_date.year,
            'highlights': highlights,
            'date': start_date,
        }

    def date_range(self):
        """ Start and end day of the year (exclusive) for a given date """
        date = self.entry_date()
        start_date = datetime.date(date.year, 1, 1)
        end_date = datetime.date(date.year + 1, 1, 1)
        return start_date, end_date


class MyDiary(DiaryView):
    """
    This is the view handler for the "/diary" url.
    """
    title = '{:%B}'

    @template('diary.jinja')
    async def get(self):
        user_id = await UserSession(self.request).user_id()
        highlights = defaultdict(int)
        warn = None

        try:
            async with self.request.app['pg_engine'].acquire() as conn:
                result = await conn.execute(
                    sa_diary_entries.select(
                        sa_diary_entries.c.user_id == user_id
                    ).with_only_columns(
                        [sa_diary_entries.c.created_on]))
                async for entry in result:
                    highlights[entry.created_on.year] += 1

        except Exception as e:
            log.error(e, exc_info=1)
            warn = 'Oops. Something is wrong. Please try again later'

        return {
            'warn': warn,
            'title': 'My Diary',
            'highlights': highlights,
        }


class FamilyDiaries(DiaryView):
    """
    This is the view handler for the "/diary/family" url.
    """
    title = '{:%B}'

    @template('diary.jinja')
    async def get(self):
        user_id = await UserSession(self.request).user_id()
        highlights = defaultdict(int)
        warn = None

        try:
            async with self.request.app['pg_engine'].acquire() as conn:
                result = await conn.execute(
                    sa_diary_entries.select(
                        sa_diary_entries.c.user_id == user_id
                    ).with_only_columns(
                        [sa_diary_entries.c.created_on]))
                async for entry in result:
                    highlights[entry.created_on.year] += 1

        except Exception as e:
            log.error(e, exc_info=1)
            warn = 'Oops. Something is wrong. Please try again later'

        return {
            'warn': warn,
            'title': 'My Diary',
            'highlights': highlights,
        }


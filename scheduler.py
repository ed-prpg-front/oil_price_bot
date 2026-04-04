from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config import MOSCOW_TZ;

def setup_scheduler(application,loop):
    scheduler = AsyncIOScheduler (timezone=MOSCOW_TZ,event_loop=loop);

    scheduler.add_job(
    morning_report_job,
    trigger = CronTrigger(hour=8,minute=0,timezone=MOSCOW_TZ),
    args=[application],
    id = 'morning_report'
        )
    scheduler.add_job(
        afternoon_check_job,
        trigger=CronTrigger(hour=15,minute=35,timezone=MOSCOW_TZ),
        args=[application],
        id='afternoon_check',
        )
    scheduler.start()



async def morning_report_job(app):
    from bot import morning_report
    await morning_report(app.bot, app)

async def afternoon_check_job(app):
    from bot import afternoon_check
    await afternoon_check(app.bot, app)

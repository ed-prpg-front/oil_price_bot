from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config import MOSCOW_TZ;

def setup_scheduler(application,loop):
    scheduler = AsyncIOScheduler (timezone=MOSCOW_TZ,event_loop=loop);

    scheduler.add_job(
    morning_report_job,
    trigger = CronTrigger(hour=17 minute=15,timezone=MOSCOW_TZ),
    args=[application],
    id = 'morning_report'
        )
    scheduler.add_job(
        afternoon_check_job,
        trigger=CronTrigger(hour=20,minute=45,timezone=MOSCOW_TZ),
        args=[application],
        id='afternoon_check',
        )
    scheduler.start()



async def morning_report_job(app):
    from bot import morning_report
    await morning_report(app)          # ← только app

async def afternoon_check_job(app):
    from bot import afternoon_check
    await afternoon_check(app)         # ← только app

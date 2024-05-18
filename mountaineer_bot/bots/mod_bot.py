from mountaineer_bot import main, core
from mountaineer_bot.components import CountdownMixin, LevelAdderMixin, SchedulerMixin

class CustomBot(CountdownMixin, LevelAdderMixin, SchedulerMixin, core.Bot):
    pass

if __name__ == "__main__":
    main.main_instantiator(CustomBot)
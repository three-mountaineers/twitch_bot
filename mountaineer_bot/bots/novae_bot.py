from mountaineer_bot import main, core
from mountaineer_bot.components import CountdownMixin, LevelAdderMixin, SchedulerMixin, TextCommand

class CustomBot(CountdownMixin, LevelAdderMixin, SchedulerMixin):
    pass

if __name__ == "__main__":
    main.main_instantiator(CustomBot)
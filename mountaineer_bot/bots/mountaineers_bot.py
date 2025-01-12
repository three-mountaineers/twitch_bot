from mountaineer_bot import main, core
from mountaineer_bot.components import CountdownMixin, LevelAdderMixin, TextCommandRepeat, FirstIdentifier

class CustomBot(FirstIdentifier, TextCommandRepeat, CountdownMixin, LevelAdderMixin):
    pass

if __name__ == "__main__":
    main.main_instantiator(CustomBot)
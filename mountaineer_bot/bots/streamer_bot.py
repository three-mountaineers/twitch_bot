from mountaineer_bot import main, core
from mountaineer_bot.components import SoundReactor, TextCommand, FirstIdentifier

class CustomBot(SoundReactor, core.Bot):
    pass

if __name__ == "__main__":
    main.main_instantiator(CustomBot)
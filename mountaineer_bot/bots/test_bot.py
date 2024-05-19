from mountaineer_bot import main, core
from mountaineer_bot.components import SoundReactor

class CustomBot(core.Bot, SoundReactor):
    pass

if __name__ == "__main__":
    main.main_instantiator(CustomBot)
from mountaineer_bot import main, core
from mountaineer_bot.components import SoundReactor, TextCommand

class CustomBot(TextCommand, core.Bot):
    pass

if __name__ == "__main__":
    main.main_instantiator(CustomBot)
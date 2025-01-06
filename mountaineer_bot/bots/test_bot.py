from mountaineer_bot import main, core
from mountaineer_bot.components import FirstIdentifier

class CustomBot(FirstIdentifier, core.BotEventListener):
    pass

if __name__ == "__main__":
    main.main_instantiator(CustomBot)
from mountaineer_bot import main, core
from mountaineer_bot.components import SoundReactor, TextCommand
from mountaineer_bot.tw_events import TwitchWebSocket, PredictionMixin, StreamStatusMixin


class CustomBot(SoundReactor, core.Bot):
    pass

class CustomListener(TwitchWebSocket, StreamStatusMixin):
    pass

if __name__ == "__main__":
    main.main_instantiator(CustomBot, TwitchWebSocket)
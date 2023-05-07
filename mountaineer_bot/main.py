from mountaineer_bot import windows_auth, core

def main(config, user):
    configs = windows_auth.get_password(windows_auth.read_config(config))
    bot = core.create_bot(config=configs, user=user)
    print(configs['CHANNELS'])
    print('Starting bot...')
    bot.run()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config', type=str)
    parser.add_argument('-u','--user', type=str)
    args = vars(parser.parse_args())
    bot = main(**args)
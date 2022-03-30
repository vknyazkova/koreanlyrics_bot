from koreanlyricsbot import bot, scheduled_funcs
import threading


def main():
    func_thread = threading.Thread(target=scheduled_funcs, daemon=True)
    func_thread.start()
    bot.polling(none_stop=True, interval=0)


if __name__ == '__main__':
    main()

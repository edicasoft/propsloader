from cement.core.foundation import CementApp
from cement.core.controller import CementBaseController, expose
import sources as src
import os
import pwd
from cement.core.exc import FrameworkError, CaughtSignal
import requests

# fix os.getlogin problem for docker
os.getlogin = lambda: pwd.getpwuid(os.getuid())[0]


class BaseController(CementBaseController):
    class Meta:
        label = 'base'
        description = "Bunch of commands to load, parse and save private properties of Bulgaria"

    @expose(hide=True)
    def default(self):
        self.app.args.print_help()


class Loader(CementApp):

    class Meta:
        label = 'Loader'
        base_controller = 'base'
        handlers = [BaseController, src.ImotbgController]
        extensions = ['daemon']
        # plugin_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'plugins')
        plugin_bootstrap = 'parsebets.bootstrap',
        plugin_config_dirs = [
            os.path.join(os.path.dirname(os.path.realpath(__file__)), 'plugins')
        ]
        plugin_dirs = [
            os.path.join(os.path.dirname(os.path.realpath(__file__)), 'plugins')
        ]
        debug = True

    def log_message(self, level, msg):
        """
        save log message
        :param level:
        :param msg:
        :return:
        """
        self.db.save_log(level, msg)
        pass

    def telegram_send_property(self, data):
        token = self.config.get('telegrambot', 'access_token')
        method = "sendMessage"
        payload = dict()
        payload["chat_id"] = self.config.get('telegrambot', 'chat_id')
        payload["parse_mode"] = 'HTML'
        text = '<b>%s</b>\nURL: <a href="%s">%s</a>\n\nPhone: %s'
        payload["text"] = text % (data['title'], data['url'], data['url'], data['phone'])
        api_url = "https://api.telegram.org/bot{0}/{1}".format(token, method)
        response = requests.post(api_url, data=payload)
        self.log.info("result of sending msg to tg chat: %s" % response.text)


with Loader() as app:
    conf_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'loader.conf')
    app.config.parse_file(conf_path)
    try:
        app.run()
    except CaughtSignal as e:
        # determine what the signal is, and do something with it?
        from signal import SIGINT, SIGABRT
        print("CaughtSignal => %s" % e.signum)
        if e.signum == SIGINT:
            # do something... maybe change the exit code?
            app.exit_code = 110
            print("Normal exit")
        elif e.signum == SIGABRT:
            # do something else...
            app.exit_code = 111
            print("Abort exit")

    except FrameworkError as e:
        # do something when a framework error happens
        print("FrameworkError => %s" % e)
        # and maybe set the exit code to something unique as well
        app.log_message("error", "FrameworkError => %s" % e)
        app.exit_code = 129
        if app.debug:
            import traceback
            traceback.print_exc()

    except Exception as e:
        print("Unknown exception => %s" % e)
        app.log_message("error", "Unknown exception => %s" % e)
        app.exit_code = 130
        import traceback
        traceback.print_exc()

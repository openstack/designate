from moniker.tests import TestCase


class PluginTestCase(TestCase):
    __test__ = False

    __plugin_base__ = None
    __plugin_name__ = None

    def setUp(self):
        super(PluginTestCase, self).setUp()

        self.invoke_args = []
        self.invoke_kwds = {}

        # NOTE: In case overrider of _pre_invoke forgets to return {}
        plugin_opts = self.pre_invoke() or {}

        # NOTE: Load plugin and register it's opts
        plugin_cls = self.get_plugin()

        self.config(group=plugin_cls.get_canonical_name(), **plugin_opts)

        self.plugin = self.get_plugin(
            invoke_args=self.invoke_args,
            invoke_kwds=self.invoke_kwds,
            invoke_on_load=True)

    def get_plugin(self, **kw):
        """
        Override me
        """
        print self.__plugin_base__.__plugin_ns__, self.__plugin_name__
        return self.__plugin_base__.get_plugin(self.__plugin_name__, **kw)

    def pre_invoke(self):
        """
        Do something before invoking the actual plugin, returned hash will
        be passed to self.config()

        Also you can manipulate self.invoke_args and self.invoke_kwds to your
        likings here
        """
        return {}

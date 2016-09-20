from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager


class QuestionsPlugin(IPlugin):
    def check_answer(self, question, answer):
        pass

    def render(self, event_id):
        pass


questionsmanager = PluginManager(
    categories_filter={"Default": QuestionsPlugin},
    directories_list=['./questions'],
    plugin_info_ext='plugin')
questionsmanager.collectPlugins()

import yapsy

class ExampleQuestions(yapsy.IPlugin.IPlugin):
    def check_answer(self, question, answer):
        return True


from flask import render_template
import yapsy

class ExampleQuestions(yapsy.IPlugin.IPlugin):
    def check_answer(self, question, answer):
        return True

    # TODO: Better stuff than this - maybe register routes with the app?
    def render(self):
        return render_template('example.html')




from flask import render_template
import yapsy

class ExampleQuestions(yapsy.IPlugin.IPlugin):
    def check_answer(self, question, answer):
        if question == 1 and answer == 'foo':
            return True

        return False

    # TODO: Better stuff than this - maybe register routes with the app?
    def render(self, event_id):
        return render_template('example.html', event_id=event_id)




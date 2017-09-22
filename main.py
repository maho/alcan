from kivy.app import App
from kivy.uix.widget import Widget

class Wizard(Widget):
    pass

class AlcanGame(Widget):
    pass

class AlcanApp(App):
    def build(self):
        return AlcanGame()


if __name__ == '__main__':
    AlcanApp().run()

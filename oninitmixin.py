from kivy.clock import Clock


class OnInitMixin(object):
    """ mixin which gives on_init callback """

    def __init__(self, *args, **kwargs):
        super(OnInitMixin, self).__init__(*args, **kwargs)

    def wait_for_parent(self, dt=None):
        if self.parent:
            # finally
            self.on_init()
            return

        Clock.schedule_once(self.wait_for_parent)

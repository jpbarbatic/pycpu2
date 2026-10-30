import sys
import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

from ui import SimulatorWindow


class Application(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.example.cpusimulator")

    def do_activate(self):
        win = SimulatorWindow(application=self)
        win.present()
        win.update_ui()


if __name__ == "__main__":
    app = Application()
    app.run(sys.argv)
__version__ = '0.4'


def run_gui():
    """
    Launch the graphical user interface of SimSo. This requires a working
    installation of PyQt4.
    """
    import sys
    import optparse
    from PyQt4.QtGui import QApplication
    from simso.gui import SimulatorWindow

    parser = optparse.OptionParser()
    parser.add_option('-t', '--text', help='run script instead of a GUI',
                      action='store', dest='script')
    (opts, args) = parser.parse_args()

    if opts.script:
        import imp
        script = imp.load_source("", opts.script)
        script.main(args)
    else:
        app = QApplication(args)
        app.setOrganizationName("SimSo")
        app.setApplicationName("SimSo")
        aw = SimulatorWindow(args[0:])
        aw.show()
        sys.exit(app.exec_())

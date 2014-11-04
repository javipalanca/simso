from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QWidget, QVBoxLayout, QToolBar, QStyle, qApp, \
    QMessageBox, QFileDialog
Qt = QtCore.Qt
import codecs
import os

from .codeeditor import CodeEditor
from .codeeditor.parsers.python_parser import Python3Parser


class TextEditor(CodeEditor):
    def __init__(self, *args, **kwds):
        super(TextEditor, self).__init__(*args, **kwds)
        self.setIndentUsingSpaces(True)
        self.setIndentWidth(4)
        self.parser = Python3Parser

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Backtab:  # Shift + Tab
            self.dedentSelection()
            return

        super(TextEditor, self).keyPressEvent(event)


class Editor(QWidget):
    def __init__(self, model_window, filename=None):
        QWidget.__init__(self)
        self._model_window = model_window
        self._filename = None
        style = qApp.style()
        self._title = "Scheduler Editor - " + os.path.basename(filename)
        self.setWindowTitle(self._title)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(450, 200)
        self.setLayout(layout)

        self._saveAction = QtGui.QAction(
            style.standardIcon(QStyle.SP_DialogSaveButton), 'Save', self)
        self._saveAction.setStatusTip('Save file')
        self._saveAction.triggered.connect(self.save)

        self.toolbar = QToolBar("ToolBar")
        self.toolbar.addAction(self._saveAction)
        layout.addWidget(self.toolbar)

        self.editor = TextEditor(
            highlightCurrentLine=True, longLineIndicatorPosition=80,
            showIndentationGuides=False, showWhitespace=False,
            showLineEndings=False, wrap=True, showLineNumbers=True)
        layout.addWidget(self.editor)

        if filename:
            self.load(filename)
        if not self._filename:
            self.editor.setPlainText("\n")
            self.editor.setPlainText("")

        self.editor.textChanged.connect(self.text_changed)
        self._saveAction.setEnabled(False)
        self.ignore_next_change = True

    def closeEvent(self, event):
        if self._saveAction.isEnabled():
            ret = QMessageBox.warning(
                self, "Close without saving?",
                "The last modifications on the scheduler will be lost.\n"
                "Are you sure you want to close the editor?",
                QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
            if ret == QMessageBox.Cancel:
                event.ignore()

    def text_changed(self):
        if not self.ignore_next_change:
            self.setWindowTitle('* ' + self._title)
            self._saveAction.setEnabled(True)
        else:
            self.ignore_next_change = False

    def load(self, filename):
        try:
            f = codecs.open(filename, 'r', 'utf-8')
            filedata = f.read()
            self.ignore_next_change = True
            self.editor.setPlainText(filedata)
            self._filename = filename
            f.close()
        except:
            QMessageBox.warning(
                self, "Opening failed.",
                "The file {} cannot be read.\n".format(filename),
                QMessageBox.Ok)
            return

        try:
            f = codecs.open(filename, 'a', 'utf-8')
            f.close()
        except:
            self.editor.setReadOnly(True)
            self._title += ' (read-only)'
            self.setWindowTitle(self._title)

    def save(self):
        if self._filename:
            f = codecs.open(self._filename, 'w', 'utf-8')
            plain_text = self.editor.toPlainText()
            if type(plain_text) is str:
                f.write(plain_text)
            else:
                f.write(unicode(plain_text))
            f.close()
            self._saveAction.setEnabled(False)
        else:
            self.save_as()
        self._model_window.check_whole_config()
        self.setWindowTitle(self._title)

    def save_as(self):
        scheduler_file = QFileDialog.getSaveFileName(
            filter="*.py", caption="Save Scheduler.")
        try:
            scheduler_file = unicode(scheduler_file)
        except NameError:
            pass
        if scheduler_file:
            if scheduler_file[-3:] != '.py':
                scheduler_file += '.py'
            self._filename = scheduler_file
            self._model_window.set_scheduler(scheduler_file)
            self.save()

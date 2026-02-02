from PyQt5.QtWidgets import QComboBox, QMainWindow, QApplication
import sys


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # Keep a reference to combobox on self, so we can access it in our methods.
        self.combobox = QComboBox()
        self.combobox.addItems(['One', 'Two', 'Three', 'Four'])

        # Connect signal to our methods.
        self.combobox.activated.connect(self.check_index)
        self.combobox.activated.connect(self.current_text)
        self.combobox.activated.connect(self.current_text_via_index)
        self.combobox.activated.connect(self.current_count)

        self.setCentralWidget(self.combobox)

    def check_index(self, index):
        cindex = self.combobox.currentIndex()
        print(f"Index signal: {index}, currentIndex {cindex}")

    def current_text(self, _): # We receive the index, but don't use it.
        ctext = self.combobox.currentText()
        print("Current text", ctext)

    def current_text_via_index(self, index):
        ctext = self.combobox.itemText(index)  # Get the text at index.
        print("Current itemText", ctext)

    def current_count(self, index):
        count = self.combobox.count()
        print(f"Index {index+1}/{count}")


app = QApplication(sys.argv)
w = MainWindow()
w.show()
app.exec_()
from PyQt5.QtWidgets import QComboBox, QMainWindow, QApplication, QWidget, QVBoxLayout
import sys


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # Keep a reference to combobox on self, so we can access it in our methods.
        self.combobox = QComboBox()
        self.combobox.addItems(['One', 'Two', 'Three', 'Four'])
        self.combobox.setEditable(True)

        self.combobox.currentTextChanged.connect(self.current_text_changed)

        # Insert policies
        self.insertpolicy = QComboBox()
        self.insertpolicy.addItems([
            'NoInsert',
            'InsertAtTop',
            'InsertAtCurrent',
            'InsertAtBottom',
            'InsertAfterCurrent',
            'InsertBeforeCUrrent',
            'InsertAlphabetically'
        ])
        # The index in the insertpolicy combobox (0-6) is the correct flag value to set
        # to enable that insert policy.
        self.insertpolicy.currentIndexChanged.connect(self.combobox.setInsertPolicy)

        layout = QVBoxLayout()
        layout.addWidget(self.combobox)
        layout.addWidget(self.insertpolicy)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

    def current_text_changed(self, s):
        print("Current text: ", s)


app = QApplication(sys.argv)
w = MainWindow()
w.show()
app.exec_()
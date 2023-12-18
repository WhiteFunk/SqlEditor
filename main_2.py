from PyQt5 import QtSql, QtPrintSupport
from PyQt5.QtGui import QTextDocument, QIcon, QTextCursor, QTextTableFormat
from PyQt5.QtCore import QFileInfo, Qt, QSettings, QSize, QFile, QTextStream
from PyQt5.QtWidgets import (QMainWindow, QTableView, QDialog, QGridLayout, QPushButton,QLineEdit, QWidget, QFileDialog, QComboBox, QMessageBox, QApplication)
import sys

class MyWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__()
        self.setObjectName("SqliteEditor")
        root = QFileInfo(__file__).absolutePath()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.settings = QSettings('Axel Schneider', self.objectName())
        self.viewer = QTableView()
        self.database = QtSql.QSqlDatabase.addDatabase('QSQLITE')
        self.model = QtSql.QSqlTableModel()
        self.row_to_delete = -1
        self.database_file = ""
        self.table_name = ""
        self.headers = []
        self.results = ""
        self.mycolumn = 0
        self.viewer.verticalHeader().setVisible(False)
        self.setStyleSheet(stylesheet(self))        
        self.viewer.setModel(self.model)
        self.viewer.clicked.connect(self.find_row)
        self.viewer.selectionModel().selectionChanged.connect(self.cell_get_text)
         
        self.dialig_window = QDialog()
        self.layout = QGridLayout()
        self.layout.addWidget(self.viewer,0, 0, 1, 4)
         
        add_database_button = QPushButton("insert row")
        add_database_button.setIcon(QIcon.fromTheme("add"))
        add_database_button.setFixedWidth(120)
        add_database_button.clicked.connect(self.add_row)
        self.layout.addWidget(add_database_button, 1, 0)
         
        delete_button = QPushButton("delete row")
        delete_button.setIcon(QIcon.fromTheme("remove"))
        delete_button.setFixedWidth(120)
        delete_button.clicked.connect(self.deleteRow)
        self.layout.addWidget(delete_button,1, 2)
 
        self.editor = QLineEdit()
        self.editor.returnPressed.connect(self.edit_cell)
        self.editor.setStatusTip("ENTER new value")
        self.editor.setToolTip("ENTER new value")
        self.layout.addWidget(self.editor,1, 3)
 
        self.myWidget = QWidget()
        self.myWidget.setLayout(self.layout)
 
        self.createToolbar()
        self.statusBar().showMessage("Ready")
        self.setCentralWidget(self.myWidget)
        self.setWindowIcon(QIcon.fromTheme("office-database"))
        self.setGeometry(20,20,600,450)
        self.setWindowTitle("SqliteEditor")
        self.read_settings()
        self.show_message("Ready")
        self.viewer.setFocus()
 
    def createToolbar(self):
        self.open_button = QPushButton("Open database")
        self.open_button.clicked.connect(self.open_file)
        self.open_button.setObjectName("open_button")
        self.open_button.setStatusTip("Open Database")
        self.open_button.setToolTip("Open Database")
 
        self.hide_button = QPushButton()
        self.hide_button.clicked.connect(self.toggle_vertical_headers)
        self.hide_button.setIcon(QIcon("show-less-fold-button.png"))
        self.hide_button.setFixedWidth(25)
        self.hide_button.setFixedHeight(25)
        self.hide_button.setStatusTip("toggle vertical Headers")
 
        self.preview_print_button = QPushButton()
        self.preview_print_button.clicked.connect(self.handle_preview)
        self.preview_print_button.setIcon(QIcon("preview.png"))
        self.preview_print_button.setFixedWidth(25)
        self.preview_print_button.setFixedHeight(25)
        self.preview_print_button.setObjectName("preview_print_button")
        self.preview_print_button.setStatusTip("Print Preview")
        self.preview_print_button.setToolTip("Print Preview")
 
        self.print_button = QPushButton()
        self.print_button.clicked.connect(self.handle_print)
        self.print_button.setIcon(QIcon("printing.png"))
        self.print_button.setFixedWidth(25)
        self.print_button.setFixedHeight(25)
        self.print_button.setObjectName("print_button")
        self.print_button.setStatusTip("Print")
        self.print_button.setToolTip("Print")
 
 
        self.toolbar = self.addToolBar("ToolBar")
        self.toolbar.setIconSize(QSize(16, 16))
        self.toolbar.setMovable(False)
        self.toolbar.addWidget(self.open_button)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.preview_print_button)
        self.toolbar.addWidget(self.print_button)
        
        self.toolbar.addSeparator()
        
        self.tables_list = QComboBox()
        self.tables_list.setFixedWidth(200)
        self.tables_list.currentIndexChanged.connect(self.set_table_name)
        self.toolbar.addWidget(self.tables_list)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.hide_button)
        self.addToolBar(self.toolbar)
 
    def deleteRow(self):
        row = self.viewer.currentIndex().row()
        self.model.removeRow(row)
        self.initialize_model()
        self.viewer.selectRow(row)

 
    def toggle_vertical_headers(self):
        if self.viewer.verticalHeader().isVisible() == False:
            self.viewer.verticalHeader().setVisible(True)
        else:
            self.viewer.verticalHeader().setVisible(False)
 
    def open_file(self):
        tablelist = []
        fileName, _ = QFileDialog.getOpenFileName(None, "Open Database File", "/home/brian/Dokumente/database", "database (*.sqlite *.database *.sql3);; All Files (*.*)")
        if fileName:
            self.open_file_startup(fileName)
 
    def open_file_startup(self, fileName):
        tablelist = []
        if fileName:
            self.database.close()
            self.database_file = fileName
            self.database.setDatabaseName(self.database_file)
            self.database.open()
            print("Tables:", self.database.tables())
            tablelist = self.database.tables()
            self.fill_combobox(tablelist)
            self.show_message("please choose Table from the ComboBox")
 
    def set_width(self):
        self.viewer.resizeColumnsToContents()
 
    def fill_combobox(self, tablelist):
        self.tables_list.clear()
        self.tables_list.insertItem(0, "choose Table ...")
        self.tables_list.setCurrentIndex(0)
        for row in tablelist:
            self.tables_list.insertItem(self.tables_list.count(), row)
        if self.tables_list.count() > 1:
            self.tables_list.setCurrentIndex(1)
            self.set_table_name()
 
    def cell_get_text(self):
        if self.viewer.selectionModel().hasSelection():
            item = self.viewer.selectedIndexes()[0]
            if not item == None:
                temp = item.data()
            else:
                temp = ""
            self.editor.setText(str(temp))
        else:
            self.editor.clear()
 
    def edit_cell(self):
        item = self.viewer.selectedIndexes()[0]
        row = self.selected_row()
        column = self.selected_column()
        self.model.setData(item, self.editor.text())
 
    def set_table_name(self):
        if not self.tables_list.currentText() == "choose Table ...":
            self.table_name = self.tables_list.currentText()
            print("database is:", self.database_file)
            self.show_message("initialize")
            self.initialize_model()
 
    def initialize_model(self):
        print("Table selected:", self.table_name)
        self.model.setTable(self.table_name)
        self.model.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
        self.model.select()
        self.set_width()
        self.show_message(self.table_name + " loaded *** " + str(self.model.rowCount()) + " records")
 
    def add_row(self):
        row =  self.viewer.selectionModel().selectedIndexes()[0].row()
        #row = self.model.rowCount()
        ret = self.model.insertRow(row)
        print(ret)
        if ret:
            self.viewer.selectRow(row)
            item = self.viewer.selectedIndexes()[0]
            self.model.setData(item, str(row))
            self.model.submitAll()
            
    def add_column(self):
        ftext = self.findfield.text()
        column = self.model.columnCount()
        #self.viewer.selectionModel().selected_columns()[0].column()
        ret = self.model.insertColumn(column)
        if ret:
            self.viewer.selectColumn(column)
            item = self.viewer.selectedIndexes()[0]
            self.model.setData(item, str(ftext))
            
            
         
    def find_row(self, i):
        self.row_to_delete = i.row()
 
    def selected_row(self):
        if self.viewer.selectionModel().hasSelection():
            row =  self.viewer.selectionModel().selectedIndexes()[0].row()
            return int(row)
 
    def selected_column(self):
        column =  self.viewer.selectionModel().selectedIndexes()[0].column()
        return int(column)
 
    def close(self, e):
        self.write_settings()
        e.accept()
 
    def read_settings(self):
        if self.settings.contains('geometry'):
            self.setGeometry(self.settings.value('geometry'))
 
    def write_settings(self):
        self.settings.setValue('geometry', self.geometry())
 
    def show_message(self, message):
        self.statusBar().showMessage(message)
 
    def handle_print(self):
        if self.model.rowCount() == 0:
            self.show_message("no rows")
        else:
            dialog = QtPrintSupport.QPrintDialog()
            if dialog.exec_() == QDialog.Accepted:
                self.handlePaintRequest(dialog.printer())
                self.show_message("Document printed")
 
    def handle_preview(self):
        if self.model.rowCount() == 0:
            self.show_message("no rows")
        else:
            dialog = QtPrintSupport.QPrintPreviewDialog()
            dialog.setFixedSize(1000,700)
            dialog.paintRequested.connect(self.handlePaintRequest)
            dialog.exec_()
            self.show_message("Print Preview closed")
 
    def handle_paint_request(self, printer):
        printer.setDocName(self.table_name)
        document = QTextDocument()
        cursor = QTextCursor(document)
        model = self.viewer.model()
        tableFormat = QTextTableFormat()
        tableFormat.setoolbarorder(0.2)
        tableFormat.setoolbarorderStyle(3)
        tableFormat.setCellSpacing(0);
        tableFormat.setTopMargin(0);
        tableFormat.setCellPadding(4)
        table = cursor.insertTable(model.rowCount() + 1, model.columnCount(), tableFormat)
        model = self.viewer.model()
        
        myheaders = []
        for i in range(0, model.columnCount()):
            myheader = model.headerData(i, Qt.Horizontal)
            cursor.insertText(myheader)
            cursor.movePosition(QTextCursor.NextCell)
        
        for row in range(0, model.rowCount()):
           for col in range(0, model.columnCount()):
               index = model.index( row, col )
               cursor.insertText(str(index.data()))
               cursor.movePosition(QTextCursor.NextCell)
        document.print_(printer)
 
def stylesheet(self):
        return """
        QWidget {
            background-color: qlineargradient(spread:pad, x1:0.585, y1:1, x2:0.506, y2:0, stop:0 rgba(150, 150, 150, 255), stop:1 rgba(202, 202, 202, 255));    
         font: 12pt \"MS Shell dialig_window 2\";
        font: bold;
        border-radius:7px;
        border:1px solid #aaa;
        color:#1a1a1a;
        }
    QHeaderView {
            background-color: qlineargradient(spread:pad, x1:0.585, y1:1, x2:0.506, y2:0, stop:0 rgba(150, 150, 150, 255), stop:1 rgba(202, 202, 202, 255));    
        border:1px solid #aaa;
        color:#1a1a1a;
        }
        QHeaderView::section {
            background-color: qlineargradient(spread:pad, x1:0.585, y1:1, x2:0.506, y2:0, stop:0 rgba(150, 150, 150, 255), stop:1 rgba(202, 202, 202, 255));    
        border:1px solid #aaa;
        color:#1a1a1a;
        }
        QTableView
        {
            font-size: 8pt;
            background-color: qlineargradient(spread:pad, x1:0.585, y1:1, x2:0.506, y2:0, stop:0 rgba(150, 150, 150, 255), stop:1 rgba(202, 202, 202, 255));    
        border-radius:7px;
        border:1px solid #aaa;
        color:#1a1a1a;
        }
        QTableView::item:hover
        {   
            color: black;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #729fcf, stop:1 #d3d7cf);           
        }
         
        QTableView::item:selected 
        {
            color: #F4F4F4;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6169e1, stop:1 #3465a4);
        } 
 
        QStatusBar
        {
           font-size: 8pt;
            background-color: qlineargradient(spread:pad, x1:0.585, y1:1, x2:0.506, y2:0, stop:0 rgba(150, 150, 150, 255), stop:1 rgba(202, 202, 202, 255));    
        border-radius:7px;
        border:1px solid #aaa;
        color:#1a1a1a;
        }
 
        QPushButton
        {
        background-color: qlineargradient(spread:pad, x1:0.585, y1:1, x2:0.506, y2:0, stop:0 rgba(150, 150, 150, 255), stop:1 rgba(202, 202, 202, 255));    
        border-radius:7px;
        border:1px solid #8c8c8c;
        color:#1a1a1a;
        icon-size: 16px;
        }
 
        QPushButton:hover
        {   
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #729fcf, stop:1 #d3d7cf);        
        border-radius:7px;
        border:1px solid #0078d7 inset;
        color:#111;
        }
        
        QComboBox
        {
            font-size: 8pt;
        }
    """
###################################     
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName('Sqlite Editor')
    main = MyWindow("")
    main.show()
    if len(sys.argv) > 1:
        print(sys.argv[1])
        main.open_file_startup(sys.argv[1])
    sys.exit(app.exec_())
from PyQt5 import QtSql, QtPrintSupport
from PyQt5.QtGui import QTextDocument, QIcon, QTextCursor, QTextTableFormat
from PyQt5.QtCore import QFileInfo, Qt, QSettings, QSize, QFile, QTextStream
from PyQt5.QtWidgets import (QMainWindow, QTableView, QDialog, QGridLayout, QPushButton,QLineEdit, QWidget, QFileDialog, QComboBox, QMessageBox, QApplication)
import sys

###################################
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
        self.delrow = -1
        self.database_file = ""
        self.table_name = ""
        self.headers = []
        self.results = ""
        self.mycolumn = 0
        self.viewer.verticalHeader().setVisible(False)
        self.setStyleSheet(stylesheet(self))        
        self.viewer.setModel(self.model)
        self.viewer.clicked.connect(self.findrow)
        self.viewer.selectionModel().selectionChanged.connect(self.getCellText)
         
        self.dlg = QDialog()
        self.layout = QGridLayout()
        self.layout.addWidget(self.viewer,0, 0, 1, 4)
         
        addatabasetn = QPushButton("insert row")
        addatabasetn.setIcon(QIcon.fromTheme("add"))
        addatabasetn.setFixedWidth(110)
        addatabasetn.clicked.connect(self.addRow)
        self.layout.addWidget(addatabasetn, 1, 0)
        
        # addColBtn = QPushButton("insert column")
        # addColBtn.setIcon(QIcon.fromTheme("add"))
        # addColBtn.setFixedWidth(110)
        # addColBtn.clicked.connect(self.addColumn)
        # self.layout.addWidget(addColBtn, 1, 1)
         
        delBtn = QPushButton("delete row")
        delBtn.setIcon(QIcon.fromTheme("remove"))
        delBtn.setFixedWidth(110)
        delBtn.clicked.connect(self.deleteRow)
        self.layout.addWidget(delBtn,1, 2)
 
        self.editor = QLineEdit()
        self.editor.returnPressed.connect(self.editCell)
        self.editor.setStatusTip("ENTER new value")
        self.editor.setToolTip("ENTER new value")
        self.layout.addWidget(self.editor,1, 3)
 
        # self.findfield = QLineEdit()
        # self.findfield.addAction(QIcon.fromTheme("edit-find"), 0)
        # self.findfield.returnPressed.connect(self.findCell)
        # self.findfield.setFixedWidth(200)
        # self.findfield.setPlaceholderText("find")
        # self.findfield.setStatusTip("ENTER to find")
        # self.findfield.setToolTip("ENTER to find")
        # self.layout.addWidget(self.findfield,1, 3)
 
        self.myWidget = QWidget()
        self.myWidget.setLayout(self.layout)
 
        self.createToolbar()
        self.statusBar().showMessage("Ready")
        self.setCentralWidget(self.myWidget)
        self.setWindowIcon(QIcon.fromTheme("office-database"))
        self.setGeometry(20,20,600,450)
        self.setWindowTitle("SqliteEditor")
        self.readSettings()
        self.msg("Ready")
        self.viewer.setFocus()
 
    def createToolbar(self):
        self.actionOpen = QPushButton("Open database")
        self.actionOpen.clicked.connect(self.open_file)
        icon = QIcon.fromTheme("document-open")
        self.actionOpen.setShortcut("Ctrl+O")
        self.actionOpen.setShortcutEnabled(True)
        self.actionOpen.setIcon(icon)
        self.actionOpen.setObjectName("actionOpen")
        self.actionOpen.setStatusTip("Open Database")
        self.actionOpen.setToolTip("Open Database")
 
        self.actionHide = QPushButton()
        self.actionHide.clicked.connect(self.toggleVerticalHeaders)
        self.actionHide.setIcon(QIcon("show-less-fold-button.png"))
        self.actionHide.setToolTip("toggle vertical Headers")
        self.actionHide.setShortcut("F3")
        self.actionHide.setShortcutEnabled(True)
        self.actionHide.setStatusTip("toggle vertical Headers")
 
        # self.actionHeaders = QPushButton()
        # self.actionHeaders.clicked.connect(self.selectedRowToHeaders)
        # icon = QIcon.fromTheme("ok")
        # self.actionHeaders.setIcon(QIcon("preview.png"))
        # self.actionHeaders.setToolTip("selected row to headers")
        # self.actionHeaders.setShortcut("F5")
        # self.actionHeaders.setShortcutEnabled(True)
        # self.actionHeaders.setStatusTip("selected row to headers")
 
        self.actionPreview = QPushButton()
        self.actionPreview.clicked.connect(self.handlePreview)
        self.actionPreview.setShortcut("Shift+Ctrl+P")
        self.actionPreview.setShortcutEnabled(True)
        self.actionPreview.setIcon(QIcon("preview.png"))
        self.actionPreview.setObjectName("actionPreview")
        self.actionPreview.setStatusTip("Print Preview")
        self.actionPreview.setToolTip("Print Preview")
 
        self.actionPrint = QPushButton()
        self.actionPrint.clicked.connect(self.handlePrint)
        self.actionPrint.setShortcut("Shift+Ctrl+P")
        self.actionPrint.setShortcutEnabled(True)
        self.actionPrint.setIcon(QIcon("printing.png"))
        self.actionPrint.setObjectName("actionPrint")
        self.actionPrint.setStatusTip("Print")
        self.actionPrint.setToolTip("Print")
 
 
        self.tb = self.addToolBar("ToolBar")
        self.tb.setIconSize(QSize(16, 16))
        self.tb.setMovable(False)
        self.tb.addWidget(self.actionOpen)
        self.tb.addSeparator()
        self.tb.addWidget(self.actionPreview)
        self.tb.addWidget(self.actionPrint)
        
        self.tb.addSeparator()
        self.tb.addSeparator()
        
        self.pop = QComboBox()
        self.pop.setFixedWidth(200)
        self.pop.currentIndexChanged.connect(self.setTable_Name)
        self.tb.addWidget(self.pop)
        self.tb.addSeparator()
        self.tb.addWidget(self.actionHide)
        self.addToolBar(self.tb)
 
    def deleteRow(self):
        row = self.viewer.currentIndex().row()
        self.model.removeRow(row)
        self.initializeModel()
        self.viewer.selectRow(row)
 
    def selectedRowToHeaders(self):
        if self.model.rowCount() > 0:
            headers = []
            row = self.selectedRow()
            for column in range(self.model.columnCount()):
                headers.append(self.model.data(self.model.index(row, column)))
                self.model.setHeaderData(column, Qt.Horizontal, headers[column], Qt.EditRole)
            print(headers)
 
    def findCell(self):
        column = 0
        ftext = self.findfield.text()
        model = self.viewer.model()
        if self.viewer.selectionModel().hasSelection():
            row =  self.viewer.selectionModel().selectedIndexes()[0].row() 
            row = row + 1
        else:
            row = 0
        start = model.index(row, column)
        matches = model.match(start, Qt.DisplayRole,ftext, 1, Qt.MatchContains)
        if matches:
            print("found", ftext, matches)
            index = matches[0]
            self.viewer.selectionModel().select(index, QItemSelectionModel.Select)
        else:
            column = column + 1
            self.findNextCell(column)
 
    def findNextCell(self, column):
        self.viewer.clearSelection()
        ftext = self.findfield.text()
        model = self.viewer.model()
        if self.viewer.selectionModel().hasSelection():
            row =  self.viewer.selectionModel().selectedIndexes()[0].row()
            row = row + 1
        else:
            row = 0
        start = model.index(row, column)
        matches = model.match(start, Qt.DisplayRole,ftext, 1, Qt.MatchContains)
        if matches:
            print("found", ftext)
            index = matches[0]
            self.viewer.selectionModel().select(index, QItemSelectionModel.Select)
        else:
            column = column + 1
            self.findNextCell(column)
 
    def toggleVerticalHeaders(self):
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
            self.fillComboBox(tablelist)
            self.msg("please choose Table from the ComboBox")
 
    def setAutoWidth(self):
        self.viewer.resizeColumnsToContents()
 
    def fillComboBox(self, tablelist):
        self.pop.clear()
        self.pop.insertItem(0, "choose Table ...")
        self.pop.setCurrentIndex(0)
        for row in tablelist:
            self.pop.insertItem(self.pop.count(), row)
        if self.pop.count() > 1:
            self.pop.setCurrentIndex(1)
            self.setTable_Name()
 
    def getCellText(self):
        if self.viewer.selectionModel().hasSelection():
            item = self.viewer.selectedIndexes()[0]
            if not item == None:
                name = item.data()
            else:
                name = ""
            self.editor.setText(str(name))
        else:
            self.editor.clear()
 
    def editCell(self):
        item = self.viewer.selectedIndexes()[0]
        row = self.selectedRow()
        column = self.selectedColumn()
        self.model.setData(item, self.editor.text())
 
    def setTable_Name(self):
        if not self.pop.currentText() == "choose Table ...":
            self.table_name = self.pop.currentText()
            print("database is:", self.database_file)
            self.msg("initialize")
            self.initializeModel()
 
    def initializeModel(self):
        print("Table selected:", self.table_name)
        self.model.setTable(self.table_name)
        self.model.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
        self.model.select()
        self.setAutoWidth()
        self.msg(self.table_name + " loaded *** " + str(self.model.rowCount()) + " records")
 
    def addRow(self):
        row =  self.viewer.selectionModel().selectedIndexes()[0].row()
        #row = self.model.rowCount()
        ret = self.model.insertRow(row)
        print(ret)
        if ret:
            self.viewer.selectRow(row)
            item = self.viewer.selectedIndexes()[0]
            self.model.setData(item, str(row))
            self.model.submitAll()
            
    def addColumn(self):
        ftext = self.findfield.text()
        column = self.model.columnCount()
        #self.viewer.selectionModel().selectedColumns()[0].column()
        ret = self.model.insertColumn(column)
        if ret:
            self.viewer.selectColumn(column)
            item = self.viewer.selectedIndexes()[0]
            self.model.setData(item, str(ftext))
            
            
         
    def findrow(self, i):
        self.delrow = i.row()
 
    def selectedRow(self):
        if self.viewer.selectionModel().hasSelection():
            row =  self.viewer.selectionModel().selectedIndexes()[0].row()
            return int(row)
 
    def selectedColumn(self):
        column =  self.viewer.selectionModel().selectedIndexes()[0].column()
        return int(column)
 
    def closeEvent(self, e):
        self.writeSettings()
        e.accept()
 
    def readSettings(self):
        print("reading settings")
        if self.settings.contains('geometry'):
            self.setGeometry(self.settings.value('geometry'))
 
    def writeSettings(self):
        print("writing settings")
        self.settings.setValue('geometry', self.geometry())
 
    def msg(self, message):
        self.statusBar().showMessage(message)
 
    def handlePrint(self):
        if self.model.rowCount() == 0:
            self.msg("no rows")
        else:
            dialog = QtPrintSupport.QPrintDialog()
            if dialog.exec_() == QDialog.Accepted:
                self.handlePaintRequest(dialog.printer())
                self.msg("Document printed")
 
    def handlePreview(self):
        if self.model.rowCount() == 0:
            self.msg("no rows")
        else:
            dialog = QtPrintSupport.QPrintPreviewDialog()
            dialog.setFixedSize(1000,700)
            dialog.paintRequested.connect(self.handlePaintRequest)
            dialog.exec_()
            self.msg("Print Preview closed")
 
    def handlePaintRequest(self, printer):
        printer.setDocName(self.table_name)
        document = QTextDocument()
        cursor = QTextCursor(document)
        model = self.viewer.model()
        tableFormat = QTextTableFormat()
        tableFormat.setBorder(0.2)
        tableFormat.setBorderStyle(3)
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
         font: 12pt \"MS Shell Dlg 2\";
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
    app.setApplicationName('MyWindow')
    main = MyWindow("")
    main.show()
    if len(sys.argv) > 1:
        print(sys.argv[1])
        main.open_file_startup(sys.argv[1])
    sys.exit(app.exec_())
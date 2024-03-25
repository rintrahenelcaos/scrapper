from bs4 import BeautifulSoup
import requests

import sqlite3

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (
    QMainWindow,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QComboBox,
    QSpinBox,
)

from PyQt5.QtGui import QIcon, QPixmap, QPainter, QBrush, QPen, QMouseEvent, QHoverEvent, QFont, QColor,QPalette
from PyQt5.QtCore import Qt, QTimer, QTime, QThread, QObject, pyqtSignal

import sys

url = "https://www.cohen.com.ar/Bursatil/Especie/AAL"
information = []

code_list = ["tdSimbolo","tdDescripcionNombre", "tdCotizEspecie", "tdVariacion",  "lblFechaHora","lblPrecioCierrer", "lblApertura", "lblVolumen", "lblMaximo", "lblMinimo"]
urls = ["https://www.cohen.com.ar/Bursatil/Especie/AAL", "https://www.cohen.com.ar/Bursatil/Especie/AALD", "https://www.cohen.com.ar/Bursatil/Especie/AMX", "https://www.cohen.com.ar/Bursatil/Especie/GOLD"]
code_list2 = ["tdDescripcionNombre", "tdCotizEspecie", "tdVariacion",  "lblFechaHora","lblPrecioCierrer", "lblApertura", "lblVolumen", "lblMaximo", "lblMinimo"]
species = ["AAL", "AALD", "AMX", "GOLD", "BIOX" ]
dollar_urls = "https://dolarhoy.com/cotizacion-dolar-ccl"
dollar_code = "sell-value"






#### SCRAPPING AND DB FUNCTIONS #####

def conection_sql():
    """Conection to sqlite

    Returns:
        conector: sqlite conector
    """
    global conector
    conector = sqlite3.connect("cedearsdb.db")
    return conector



def dollar_scrapper(dollarurl):
    """ Scrappes Dollar-CCL Values from https://dolarhoy.com/cotizacion-dolar-ccl

    Args:
        dollarurl (str): url

    Returns:
        int: Dollar-CCL exchange rate vs AR$
    """
    
    req = requests.get(dollarurl)
    soupdollar = BeautifulSoup(req.text, 'html.parser')
    dollar_value = soupdollar.find_all(class_ = "value")[1].contents[0]
    
    dollar_ccl = dollar_value[1:]
    
    
    
    
    return dollar_ccl
    
def cedears_list_scrapper():
    """Scrappes full list of available CEDEArs in the market from https://www.cohen.com.ar/Bursatil/Especie/AAL

    Returns:
        list: list of CEDEArs symbols/species
    """
    
    cedears_complete_list = []
    req = requests.get(url)
    soup = BeautifulSoup(req.text, 'html.parser')
    cedears = soup.findAll("option")
    
    for ind in cedears:
        cedears_complete_list.append(ind.string)
    cedears_complete_list = list(set(cedears_complete_list))
    cedears_complete_list.sort()
    cedears_complete_list.remove("Ninguna")
    cedears_complete_list.insert(0, "")
    return cedears_complete_list         
    
        

def scrapper(url_list, codes_list):
    """Scrappes individual CEDEAr information from https://www.cohen.com.ar/Bursatil/Especie/

    Args:
        url_list (list): list of urls
        codes_list (list): list of str used as codes to scrap

    Returns:
        list: list containing lists of informtion scrapped
    """
    scrapped=[]
    
    for ind_url in url_list:
        info = []
        req = requests.get(ind_url)
        soup = BeautifulSoup(req.text, 'html.parser')
        
        for code in codes_list:
            try:
                inf = soup.find(class_ = code).text
                if inf.find("$") != -1:
                    inf = inf[inf.rfind(" ")+1:]
                elif inf.find("%") != -1:
                    inf = inf[1:inf.rfind(" ")]
                info.append(inf)
            except:
                inf = soup.find(id = code).text
                #print(code, inf)
                inf = inf[inf.rindex(" ")+1:]
                if inf.isdigit():
                    info.append(inf)
                else:
                    
                    while inf[0].isalpha():
                        inf = inf[1:]
                    else: info.append(inf)
        scrapped.append(info)
    return scrapped


def actualize_scrapper(code_list, dollar):
    """Connects scrapper to sqlite db prior to cleaning data

    Args:
        code_list (list): list of str used as codes to scrap, used for scrapper
        dollar (int): Dollar-CCL exchange rate to AR$ 

    """
     
    pointer = conector.cursor() 
    scrapped = "SELECT symbol,amount FROM cedears"
    pointer.execute(scrapped)
    existing_scrapped = pointer.fetchall()
    already_scrapped = []
    
    for scrap in existing_scrapped:
        already_scrapped.append(scrap[0])
        
    urls_list = []
    
    
    for symbol in already_scrapped:
        urls_list.append("https://www.cohen.com.ar/Bursatil/Especie/"+symbol)
    data = comma_dot_cleaner(scrapper(urls_list,code_list))
    #print("DATA: ",data)
    
    for dat in data:
        updater = "UPDATE cedears SET description = ?, value = ?, variation = ?, lastoperation = ?, opening = ?, closing = ?, volume = ?, minimun = ?, maximun = ? WHERE symbol = ?;"
        setter = (dat[1], round(float(dat[2])/dollar, 2), dat[3], dat[4], round(float(dat[5])/dollar,2), round(float(dat[6])/dollar, 2), dat[7], round(float(dat[8])/dollar,2), round(float(dat[9])/dollar,2), dat[0])
        pointer.execute(updater, setter)
        conector.commit()
        
        update_total = "SELECT amount FROM cedears WHERE symbol = ?;"
        pointer.execute(update_total, (dat[0],))
        total_to_update = pointer.fetchall()[0][0]
        updater = "UPDATE cedears SET total = ? WHERE symbol = ?"
        setter = (round(total_to_update*float(dat[2])/dollar, 2), dat[0])
        pointer.execute(updater, setter)
        conector.commit()
    
    
def specie_loader(specie):
    """Loads new species to db

    Args:
        specie (str): identifying code of specie - symbol
    """
    
    to_add = (specie)
    pointer = conector.cursor() 
    adding = "INSERT INTO cedears (symbol, amount) VALUES (?, ?) ;"
    pointer.execute(adding, to_add)
    conector.commit()
      
def species_loader(species):   #temporal, used for testing
    for sp in species:
        specie_loader(sp)    
    

def comma_dot_cleaner(scrapped):
    """Cleans data fromm comma and point to prevent crash due to the spanish usage of both

    Args:
        scrapped (str): original value

    Returns:
        str: reformed value
    """
    for info in scrapped: 
        for ind in range(2, len(info)):
            info[ind] = info[ind].replace(".","")
            info[ind] = info[ind].replace(",",".")
        
    return scrapped


def tableconstructor(conection):
    """Constructs table in db

    Args:
        conection (any): sqlite conector
    """
    pointer = conection.cursor()
    table = "CREATE TABLE IF NOT EXISTS cedears(symbol TEXT NOT NULL, description TEXT, value REAL, variation REAL,  lastoperation TEXT, opening REAL, closing REAL, volume INTEGER, minimun REAL, maximun REAL, amount INTEGER, total FLOAT)"
    pointer.execute(table)
    conection.commit()

def total_holding():
    
    pointer = conector.cursor()
    calculator = "SELECT SUM(total) FROM cedears;"
    pointer.execute(calculator)
    total = round(pointer.fetchall()[0][0], 2)
    
    return total
    
##### THREAD CLASS ######

# implemented so that GUI doesn't freeze during updates

class Updater(QObject):
    
    updated = pyqtSignal()
    progress = pyqtSignal(int)
    
    def update(self):
        pass






###### USER INTERFACE ####

class Main_window(QMainWindow):
    
    
    def __init__(self):
        super(Main_window, self).__init__()
        
        self.setObjectName("MainWindow")
        self.resize(1000, 800)
        self.setWindowTitle("MainWindow")
        self.setWindowTitle("CEDEAr - Scrapper")
        
        self.table = QTableWidget(self)
        self.table.setGeometry(10,50,980,700)
        self.column_names = ["Symbol", "Description", "$", "Var.", "last op.", "opening $", "closing $", "Volume", "Min.$", "Max.$", "Owned", "Holding $", "Del."]
        self.table.setColumnCount(len(self.column_names))
        self.table.setHorizontalHeaderLabels(self.column_names)
        
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.itemDoubleClicked.connect(lambda: self.mod_specie(self.table.currentRow()))
        
        self.dollar_label = QLabel(self)
        self.dollar_label.setGeometry(QtCore.QRect(10, 10, 200, 30))
        self.dollar_label.setText("CCL-Dollar: $")
        
        
        
        self.specie_loader = QPushButton(self)
        self.specie_loader.setText("Add specie")
        self.specie_loader.setGeometry(QtCore.QRect(300, 10, 100, 30))
        self.specie_loader.clicked.connect(lambda: self.to_add_specie())
        
        
        self.specie_combobox = QComboBox(self)
        self.specie_combobox.addItems(cedears_list_scrapper())
        self.specie_combobox.setGeometry(QtCore.QRect(450,10, 200, 30))
        
        self.owned = QSpinBox(self)
        self.owned.setGeometry(QtCore.QRect(650, 10, 100, 30))
        
        self.infolabel = QLabel(self)
        self.infolabel.setGeometry(QtCore.QRect(10,760,600,30))
        self.infolabel.setText("To edit the amount owned, double click on the row")
        self.infolabel.setStyleSheet("color: red")
        
        self.total_hold = QLabel(self)
        self.total_hold.setGeometry(QtCore.QRect(800,760,150,30))
        
        self.now = QtCore.QTime() # Used to prevent updates in Stock Value off hours
        
        self.thread = QThread()
        self.timed_update = Updater()
        self.timed_update.moveToThread(self.thread)
        self.thread.started.connect(self.timed_update.update)
        self.timed_update.updated.connect(self.thread.quit)
        self.timed_update.updated.connect(self.timed_update.deleteLater)
        self.timed_update.updated.connect(self.thread.deleteLater)
        
        
        timer = QtCore.QTimer(self) # Used to actualize data every 30 min
        timer.setInterval(1800000)
        timer.timeout.connect(self.timer_updater)
        
        self.table.setWordWrap(True)
        
        self.dollar = dollar_scrapper(dollar_urls)
        actualize_scrapper(code_list, float(self.dollar))
        self.dollar_label.setText("CCL-Dollar: $"+str(self.dollar))
        self.table_loader()
        self.total_hold.setText("Total holding: U$S"+str(total_holding()))
        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(1, 360)
        self.show()
        timer.start()
        
    def table_loader(self):
        """Loads table from db
        """
        pointer = conector.cursor()
        loader = "SELECT * FROM cedears"
        pointer.execute(loader)
        data = pointer.fetchall()
        self.table.setRowCount(len(data))
        
        row = 0
        for dat in data:
            column = 0
            for individual in dat:
                self.table.setItem(row, column, QTableWidgetItem(str(individual)))
                column += 1
            delete_button = QPushButton("DEL.")
            delete_button.setFixedWidth(40)        
            
            self.table.setCellWidget(row,12,delete_button)
            delete_button.clicked.connect(self.delete_specie)
            
            row += 1
            
    def to_add_specie(self):
        """Adds specie to db and table through adding specie
        """
        
        if self.specie_combobox.currentText() == "" :
            self.infolabel.setText("Must choose a symbol to add")
        else: 
            self.infolabel.setText("Adding specie, please wait")
            timerint = QtCore.QTimer(self)
            timerint.singleShot(1000, self.adding_specie)
            
    def adding_specie(self):
        """Operates adding specie
        """
        # Capture data #
        new_specie = str(self.specie_combobox.currentText()), str(self.owned.value())
        specie_loader(new_specie)
        actualize_scrapper(code_list, float(dollar_scrapper(dollar_urls)))
        pointer = conector.cursor()
        new_specie_symbol =  new_specie[0]
        
        # to db #
        updater = "SELECT * FROM cedears WHERE symbol = ?"
        pointer.execute(updater, (new_specie_symbol,))
        data = pointer.fetchall()[0]
        
        # to table #
        row = self.table.rowCount()
        self.table.insertRow(row)
        column =0
        for dat in data:
            self.table.setItem(row, column, QTableWidgetItem(str(dat)))
            column += 1
        delete_button = QPushButton("DEL.")
        delete_button.setFixedWidth(40)
        self.table.setCellWidget(row,12,delete_button)
        delete_button.clicked.connect(self.delete_specie)
        self.specie_combobox.setCurrentText("")
        self.owned.setValue(0)
        self.infolabel.setText(new_specie_symbol+" added")
     
    
    def mod_specie(self, row):
        """Allows to modify the amount owned

        Args:
            row (int): doubleclicked row
        """
                
        item_to_mod = self.table.item(row, 10)
        
        self.table.setCurrentItem(item_to_mod)
        self.table.editItem(item_to_mod)
        
        self.table.itemChanged.connect(self.to_change_amount) # sends signal to change and triggers modification
        
    def to_change_amount(self, item):
        """Modify Function

        Args:
            item (QtablewidgetItem): Item reference to amount owned
        """
        try :  # prevents crash when adding new specie #
            # collect data #
            row = item.row()
            value = self.table.item(row, 10).text()
            specie = self.table.item(row, 0).text()
            price = self.table.item(row, 2).text()

            # update amount in db #    
            pointer2 = conector.cursor()
            updater = "UPDATE cedears SET amount = ? WHERE symbol = ?"
            setter = (value, specie)
            pointer2.execute(updater, setter)
            conector.commit()

            # update holding in db #
            updater2 = "UPDATE cedears SET total = ? WHERE symbol = ?"
            setter = (float(value)*float(price), specie)
            pointer2.execute(updater2,setter)
            conector.commit()

            # change table #
            loader = "SELECT total FROM cedears WHERE symbol = ?;"
            selector = (specie,)
            pointer2.execute(loader, selector)
            new_holding = pointer2.fetchall()[0][0]
            item_holding = self.table.item(row,11)
            item_holding.setText(str(new_holding))
        except: pass
        
    def delete_specie(self):
        """Removes specie from db and table
        """
        button = self.sender()
        if button:
            row = self.table.indexAt(button.pos()).row()
            specie = self.table.item(row, 0).text()
            deleter = "DELETE FROM cedears WHERE symbol = ?"
            pointer3 = conector.cursor()
            pointer3.execute(deleter, (specie,))
            conector.commit()
            self.table.removeRow(row)
            
    def timer_updater(self):
        """Data updater triggerer
        """
        if self.now.hour() < 9 or self.now.hour() > 15: pass
        else:
            self.infolabel.setText("Actualizing information, please wait")
            print("timer")
            timerint = QtCore.QTimer(self)
            timerint.singleShot(1000,self.info_actualizer)
        
    def info_actualizer(self):
        """Updates all data re-scrapping and restarting table
        """
        # re-scrapp #        
        self.dollar = dollar_scrapper(dollar_urls, dollar_code)
        actualize_scrapper(code_list, float(self.dollar))
        
        # restart ui
        self.table.clearContents()
        self.dollar_label.setText("CCL-Dollar: $"+str(self.dollar))
        self.table_loader()
        self.infolabel.setText("Information actualized")
        print("timerout")
        
            
        
        
        
    
        
        
        
        
        



if __name__ == "__main__":
    conector = conection_sql()
    tableconstructor(conector)
    
    app = QtWidgets.QApplication(sys.argv)
    
    ui = Main_window()
    
    
    
    sys.exit(app.exec_())
    
   
   
   
    
    
    
    

    

    
     

     

       


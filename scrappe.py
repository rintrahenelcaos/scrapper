######################################################
### CEDEARs Web Scraper                           ####
### Author: Leonardo Mario Mazzeo                 ####
######################################################


from bs4 import BeautifulSoup
import requests

import sqlite3

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QMainWindow,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QComboBox,
    QSpinBox,
)


from PyQt5.QtCore import QThread, QObject, pyqtSignal

import sys

url = "https://www.cohen.com.ar/Bursatil/Especie/AAL"
urls_to_get_cedears_list = ["https://www.cohen.com.ar/Bursatil/Especie/AAL", "https://iol.invertironline.com/mercado/cotizaciones/argentina/cedears/todos", "https://www.bancopiano.com.ar/Inversiones/Cotizaciones/Cedears/"]
information = []

code_list = ["tdSimbolo","tdDescripcionNombre", "tdCotizEspecie", "tdVariacion",  "lblFechaHora","lblPrecioCierrer", "lblApertura", "lblVolumen", "lblMaximo", "lblMinimo"] #outdated
code_list = ['detailSimbolo', 'detailDescripcionNombre','detailCotizacion','detailVariacion'] #updated 6/13/2024
code_list_keys = ['Apertura', 'Cierre Anterior', 'Volumen', 'Mínimo','Máximo'] # New codes for scrapping list
urls = ["https://www.cohen.com.ar/Bursatil/Especie/AAL", "https://www.cohen.com.ar/Bursatil/Especie/AALD", "https://www.cohen.com.ar/Bursatil/Especie/AMX", "https://www.cohen.com.ar/Bursatil/Especie/GOLD"] #testing only
#code_list2 = ["tdDescripcionNombre", "tdCotizEspecie", "tdVariacion",  "lblFechaHora","lblPrecioCierrer", "lblApertura", "lblVolumen", "lblMaximo", "lblMinimo"]
species = ["AAL", "AALD", "AMX", "GOLD", "BIOX" ] #testing only

#### codes to be used with https://iol.invertironline.com/mercado/cotizaciones/argentina/cedears/todos ####

codes_list_iol = ["UltimoPrecio", "Variacion", "Apertura", "UltimoCierre", "Minimo", "Maximo"]

#### codes to be used with https://www.bancopiano.com.ar/Inversiones/Cotizaciones/Cedears/  ###

codes_list_piano = []


dollar_urls = "https://dolarhoy.com/cotizacion-dolar-ccl" # url to scrap CCL exchange rate
dollar_code = "sell-value" # code to get scrapped CCL exchange rate







#### SCRAPPING AND DB FUNCTIONS #####

def conection_sql():
    """Conection to sqlite

    Returns:
        conector: sqlite conector
    """
    global conector
    conector = sqlite3.connect("cedearsdb.db", check_same_thread=False)
    
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
    """Scrapes full list of available CEDEARs in the market from any of the available urls

    Returns:
        list: list of CEDEArs symbols/species
    """
    
    
    cedears_complete_list = []   # list to return
    
    try:   # Original function 
        req = requests.get(urls_to_get_cedears_list[0])   # first option to scrap from
        soup = BeautifulSoup(req.text, 'html.parser')
        cedears = soup.findAll("option")   # all CEDEARs are identified as option

        for ind in cedears:
            cedears_complete_list.append(ind.string)
        cedears_complete_list = list(set(cedears_complete_list))  # eliminates duplicates
        cedears_complete_list.sort()
        cedears_complete_list.remove("Ninguna")  # "Ninguna" is included in the middle of the list for some reason
        
    except: # First safety option: uses iol web
        try:
            req = requests.get(urls_to_get_cedears_list[1])  # Second option to scrap from
            soup = BeautifulSoup(req.text, 'html.parser')  
            cedears = soup.tbody  # get the complete table.  

            cedears_list = (cedears.find_all("b"))  # all species codes are contained in b>

            for cedear in cedears_list:
                if cedear.string == None:  # eliminates EFTs from teh list as the are signaled a string
                    pass

                else:
                    cedears_complete_list.append((cedear.text).strip())    # list of stripped cedears 
                
        except:  # Second safety option: uses piano web
            req = requests.get(urls_to_get_cedears_list[2])   # third option to scrap from // not recommended as EFTS are mixed and can generate issues when the sources are mixed
            soup = BeautifulSoup(req.text, 'html.parser')  

            cedears_list = soup.tbody.find_all("tr")

            for cedear in cedears_list:
                
                for cedind in cedear.find_all("td"):    
                    
                    if "title" in cedind.attrs.keys():  # CEDEARs are marked in the table by a code
                        cedears_complete_list.append(cedind.text)
        
        
        
    cedears_complete_list.insert(0, "") # adds white first 
    return cedears_complete_list
       
    
        

def scrapper_old(url_list, codes_list):  #Old function outdated due to changes in the scrapped website, name changed to prevent issues
    """Scrappes individual CEDEAR information from https://www.cohen.com.ar/Bursatil/Especie/

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
            print("code: ",code)
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

def scrapper_kohen(url_list, codes_list): #New function as of 6/10/2024 /// Not working as of 7/31/2024
    """Scrappes individual CEDEAR information from https://www.cohen.com.ar/Bursatil/Especie/

    Args:
        url_list (list): list of urls
        codes_list (list): list of str used as codes to scrap

    Returns:
        list: list containing lists of information scrapped
    """
    scrapped=[]
    
    for ind_url in url_list:
        info = []
        req = requests.get(ind_url)
        soup = BeautifulSoup(req.text, 'html.parser')
        
        for code in codes_list:  # scrap from class
            
            try:
                inf = soup.find(class_ = code).string    # first option
                inf = inf.replace("$","")    # cleans numbers
                inf = inf.replace("%","")   # cleans numbers
                inf = inf.strip()   #strips string
                info.append(inf)
            except:
                inf = soup.find(class_ = code).text     # second option as sometimes first fails
                inf = inf.replace("$","")
                inf = inf.replace("%","")
                inf = inf.strip()
                info.append(inf)
            
        
        outing = soup.find(class_ = 'detailDescripcion')        # complete name of the company that issues the CEDEAR
        exit_data1 = BeautifulSoup(str(outing), 'html.parser')      
        scrap_exit_data = exit_data1.find_all('span')
        outedlist = []
        for outed in scrap_exit_data: # data scrapped from list
            outedlist.append(outed.text)
        scrap_dict = {}
        for li in range(0,len(outedlist),2):  # clean the list of symbols
            outedlist[li+1] = outedlist[li+1].replace("$ ","")
            outedlist[li+1] = outedlist[li+1].replace("U$S ","")
            scrap_dict.update({outedlist[li]:outedlist[li+1]})
        
        for key in code_list_keys:
            print(key,": ",scrap_dict[key])
            info.append(scrap_dict[key])
        scrapped.append(info)    
            
    
    return scrapped

def scrapper_iol(species_list, codes_list):   # added 7/28/2024 as a security option in case the first url is down
    """Scrapes individual CEDEAR information from https://iol.invertironline.com/mercado/cotizaciones/argentina/cedears/todos

    Args:
        species_list (list): list of species
        codes_list (list): list of str used as codes to scrap

    Returns:
        list: list containing lists of information scrapped
    """
    scrapped = []
    
    req = requests.get(urls_to_get_cedears_list[1])  
    soup = BeautifulSoup(req.text, 'html.parser') 
    cedear_soup = soup.tbody   # all data is concentrated in a table
    
    cedears_list = cedear_soup.find_all("b")   # get all the species in the list
    
    
    
    for specie in species_list:
        tituloid = str
        for cedear in cedears_list:
            if(cedear.text).strip() == specie:    # finding the correct table block. Data is presented in rows under a code identified a data-tituloid
                tituloid = cedear.parent.parent.parent["data-tituloid"]  # going up the tree  
                raw_data = cedear_soup.find(attrs={"data-tituloid": tituloid})  # get the complete data
                
                info = []
                info.append((raw_data.find("b").text).strip())   # adding specie
                info.append(raw_data.i["title"])   # adding company issuer
                for code in codes_list:   # looping through codes of data requiered
                    info.append((raw_data.find(attrs = {"data-field":code}).text.strip()).replace("%",""))
                
                info.append((raw_data.find_all("td")[-2].text).strip())  # Volume is presented in unlabel td
                scrapped.append(info)
    print(scrapped)
    
    return scrapped

def scrapper_piano(species_list): 
    """Scrapes individual CEDEAR information from https://www.bancopiano.com.ar/Inversiones/Cotizaciones/Cedears/ 
    Not recommended because of missing data 

    Args:
        species_list (_type_): list of species

    Returns:
        list: list containing lists of information scrapped
    """
    
    scrapped = []
    
    req = requests.get(urls_to_get_cedears_list[2])  # 
    soup = BeautifulSoup(req.text, 'html.parser')
     
    cedear_list = soup.tbody.find_all("tr") # scrap the table into workable pieces each representing a stock
    
    for specie in species_list:  # Data is presented in a sequential block with little differentiation betwen each item so it's scraped by list index
        for cedear in cedear_list:
            data = (cedear.find_all("td"))
            
            if data[0].text == specie:
                #print(specie)
                info = []
                info.append(data[0].text)
                info.append("No data")
                info.append(data[1].text)
                info.append((data[5].text).replace("%",""))
                info.append("0")
                info.append(data[4].text)
                info.append("0")
                info.append(data[3].text)
                info.append(data[2].text)
        scrapped.append(info)
    
    return scrapped
                 

def actualize_scrapper(code_list, codes_iol, dollar):
    """Connects scraper to sqlite db prior to cleaning data

    Args:
        code_list (list): list of str used as codes to scrap, used for scrapper
        dollar (int): Dollar-CCL exchange rate to AR$ 

    """
     
    pointer_th = conector.cursor() 
    scrapped = "SELECT symbol,amount FROM cedears"  # get the species to scrap // symbol serves as reference to the scraping functions, amount is used latter to calculate the real value of the portfolio
    pointer_th.execute(scrapped)
    existing_scrapped = pointer_th.fetchall()
    already_scrapped = []
    
    for scrap in existing_scrapped:
        already_scrapped.append(scrap[0])  #fill the list
    
    #print(already_scrapped)    # Used for control
    urls_list = []
       
    
    # first try from the original web 
    try:
        for symbol in already_scrapped:   # constructs the urls to pass as arguments in the scraping function
            urls_list.append("https://www.cohen.com.ar/Bursatil/Especie/"+symbol)
        #print("urls_list: ", urls_list)  # Control only
        data = comma_dot_cleaner(scrapper_kohen(urls_list,code_list))
    
    # Second option in case the conection failed or the scraping is impossible
    except:
        try:
            #print(already_scrapped) # Control only
            data = comma_dot_cleaner(scrapper_iol(already_scrapped, codes_iol))
            #print(data)
        
        # Third and last option /// not prefered because it's not consistent in data contents with the previous two and generates incomplete information and may create issues on some options
        except:
            #print(already_scrapped)   # Control only
            data = comma_dot_cleaner(scrapper_piano(already_scrapped))
    #print("DATA: ",data)   # Control only
    
    for dat in data:   # Scraped data is turn into information to be diplayed 
        updater = "UPDATE cedears SET description = ?, value = ?, variation = ?, opening = ?, closing = ?, volume = ?, minimun = ?, maximun = ? WHERE symbol = ?;"
        # Tuple of data is created and curated, all values in AR$ are turn into U$S on CCL exchange rate 
        setter = (dat[1], round(float(dat[2])/dollar, 2), dat[3], round(float(dat[4])/dollar,2), round(float(dat[5])/dollar, 2), dat[6], round(float(dat[7])/dollar,2), round(float(dat[8])/dollar,2), dat[0])
        pointer_th.execute(updater, setter)
        conector.commit()
        
        update_total = "SELECT amount FROM cedears WHERE symbol = ?;"   # Getting amount to update total value of portfolio
        pointer_th.execute(update_total, (dat[0],))  
        try:
            total_to_update = pointer_th.fetchall()[0][0]
            updater = "UPDATE cedears SET total = ? WHERE symbol = ?"
            setter = (round(total_to_update*float(dat[2])/dollar, 2), dat[0])
            pointer_th.execute(updater, setter)
            conector.commit()   # Update total value of stocks owned
        except: pass

def partial_scrapper(new_specie, dollar, code_list, codes_iol):
    """ Scrappes only one specie. Used for adding specie and preventing re-loading everything from db

    Args:
        new_specie (string): specie code as str
        dollar (float): CCL dollar exchange rate. Scrapped automatically
        code_list (list): codes to be scrapped. reference to class
    """
    # Works exactly like actualize_scrapper, only difference is that it adds a specie instead of update the values of existing ones
    pointer = conector.cursor()
    url = ["https://www.cohen.com.ar/Bursatil/Especie/"+new_specie]
    try:
        data = comma_dot_cleaner(scrapper_kohen(url, code_list))
    except:
        try: 
            data = comma_dot_cleaner(scrapper_iol([new_specie],codes_iol))
        except:
            data = comma_dot_cleaner(scrapper_piano([new_specie]))
        
    
    for dat in data:
        #updater = "UPDATE cedears SET description = ?, value = ?, variation = ?, lastoperation = ?, opening = ?, closing = ?, volume = ?, minimun = ?, maximun = ? WHERE symbol = ?;" #outdated
        updater = "UPDATE cedears SET description = ?, value = ?, variation = ?, opening = ?, closing = ?, volume = ?, minimun = ?, maximun = ? WHERE symbol = ?;"
        # Tuple of data is created and curated, all values in AR$ are turn into U$S on CCL exchange rate 
        setter = (dat[1], round(float(dat[2])/dollar, 2), dat[3], round(float(dat[4])/dollar,2), round(float(dat[5])/dollar, 2), dat[6], round(float(dat[7])/dollar,2), round(float(dat[8])/dollar,2), dat[0])
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
    """Loads new species to db. Used when adding a new stock

    Args:
        specie (tuple): (identifying code of specie (str), amount owned (int))
    """
    
    to_add = (specie)
    pointer = conector.cursor() 
    adding = "INSERT INTO cedears (symbol, amount) VALUES (?, ?) ;"
    pointer.execute(adding, to_add)
    conector.commit()
      

    

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
    table = "CREATE TABLE IF NOT EXISTS cedears(symbol TEXT NOT NULL, description TEXT, value REAL, variation REAL, opening REAL, closing REAL, volume INTEGER, minimun REAL, maximun REAL, amount INTEGER, total FLOAT)"
    pointer.execute(table)
    conection.commit()

def total_holding():
    """ Calculates the total value of the portfolio

    Returns:
        float: total value
    """
    pointer = conector.cursor()
    calculator = "SELECT SUM(total) FROM cedears;"
    pointer.execute(calculator)
    try:
        total = round(pointer.fetchall()[0][0], 2)
    except:
        total = 0
    
    return total
    
##### THREAD CLASS ######

# implemented so that GUI doesn't freeze during updates

           
class Updater(QObject):
    """ Thread Class. Prevents the app from freezing when updating stock data

    Args:
        QObject (Qobject): Generic PyQt5 object
    """
    
    updated = pyqtSignal()  # signals data is updated
    progress = pyqtSignal()  # signals data is being updated, is launched every 30 minutes 
    retry = pyqtSignal()    # if the update fails this is launched to try to fix it after 5 seconds
    failed = pyqtSignal()      # after three trys it lauches indicating data is outdated
    
    def update(self):
        """ Manages the thread. Sets the timer that launches periodical updates
        """
        timer = QtCore.QTimer(self) # Used to actualize data every 30 min
        timer.setInterval(1800000)
        #timer.setInterval(30000) testing only
        timer.timeout.connect(self.timer_updater)  # launches the update after 30 min
        self.now = QtCore.QTime.currentTime()   #used for indicating time of update
        print("initial load")
        self.dollar = dollar_scrapper(dollar_urls)  # get the exchange rate
        actualize_scrapper(code_list, codes_list_iol,float(self.dollar))    # update data
        self.updated.emit()     # updated data signal emited
        print("initial load finished")
        timer.start()   # initiates the countdown to update
        
    def timer_updater(self):
        """Data updater triggerer
        """
        print(self.now.hour())
        if self.now.hour() < 9 or self.now.hour() > 15: pass  # no updates due to stock exchange hours
        else:
            self.progress.emit()   # sigmnals update in progress
            print("timer")
            timerint = QtCore.QTimer(self)
            timerint.singleShot(1000,self.info_actualizer)  # launches data update
        
    
    def info_actualizer(self):
        """Updates all data re-scrapping and restarting table
        """
        retries = 1
        if retries < 6:   #prevents infinite loop
            # re-scrapp # 
            try:       

                self.dollar = dollar_scrapper(dollar_urls)
                actualize_scrapper(code_list, codes_list_iol, float(self.dollar))
                # restart ui

                print("timerout")
                self.updated.emit()   # signals the update is finished
            except: 
                self.retry.emit()
                timer_retry = QtCore.QTimer(self)   # Delay before retrying scrapping after 5 sec.
                timer_retry.singleShot(5000, self.info_actualizer)
                retries += 1
        else: self.failed.emit()
        retries = 1
            
        
        




###### USER INTERFACE ####

class Main_window(QMainWindow):
    
    
    def __init__(self):
        super(Main_window, self).__init__()
        
        self.setObjectName("MainWindow")
        self.resize(1000, 800)
        self.setWindowTitle("MainWindow")
        self.setWindowTitle("CEDEAR - Scraper")
        
        self.table = QTableWidget(self)
        self.table.setGeometry(10,50,980,670)
        self.column_names = ["Symbol", "Description", "Price", "Variation", "Opening$", "Closing$", "Volume", "Minimun$", "Maximun$", "Owned", "Holding$", "Del."]  # creates the columns
        self.table.setColumnCount(len(self.column_names))
        self.table.setHorizontalHeaderLabels(self.column_names)
        
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)  # blocks individual changes in table cells
        self.table.itemDoubleClicked.connect(lambda: self.mod_specie(self.table.currentRow()))  # allows to modify the amount of individual stocks owned by double-clicking
        
        self.dollar_label = QLabel(self)
        self.dollar_label.setGeometry(QtCore.QRect(10, 10, 200, 30))
        self.dollar_label.setText("CCL-Dollar: $")     # exchange rate indicator
        
        
        
        self.specie_loader = QPushButton(self)   # specie adding button
        self.specie_loader.setText("Add specie")
        self.specie_loader.setGeometry(QtCore.QRect(580, 10, 100, 30))
        self.specie_loader.clicked.connect(lambda: self.to_add_specie())
        self.specie_loader.setEnabled(False)   # blocked while first loading data
        
        
        self.specie_combobox = QComboBox(self)   # species to choose from
        self.specie_combobox.addItems(cedears_list_scrapper())   
        self.specie_combobox.setGeometry(QtCore.QRect(700,10, 200, 30))
        
        self.owned = QSpinBox(self)  
        self.owned.setGeometry(QtCore.QRect(900, 10, 90, 30))
        
        self.infolabel = QLabel(self)   # Label to inform data updates
        self.infolabel.setGeometry(QtCore.QRect(10,760,600,30))
        self.infolabel.setText("Loading data, please wait")
        self.infolabel.setStyleSheet("color: red")
        
        self.infolabel2 = QLabel(self)  # Label with instructions
        self.infolabel2.setGeometry(QtCore.QRect(10,720,600,30))
        self.infolabel2.setText("To edit the amount owned, double click on the row")
        
        
        self.total_hold = QLabel(self)  # total value of portfolio label
        self.total_hold.setGeometry(QtCore.QRect(800,720,150,30))
        
        self.now = QtCore.QTime() 
        
        # thread ##
        self.thread = QThread()
        self.timed_update = Updater()
        self.timed_update.moveToThread(self.thread)
        self.thread.started.connect(self.timed_update.update)
        self.timed_update.updated.connect(lambda: self.infolabel.setText("Data last updated: "+QtCore.QTime.toString(QtCore.QTime.currentTime())))  # bounding thread to label
        self.timed_update.updated.connect(lambda: self.info_actualizer())   # launches changes in table so as to maintain it updated
        self.timed_update.progress.connect(lambda: self.infolabel.setText("Updating data")) # informing situation
        self.timed_update.failed.connect(lambda: self.infolabel.setText("Failed to stablish connection with internet data after 5 attemps"))
        self.timed_update.retry.connect(lambda: self.infolabel2.setText("Failed connection, retrying"))
        
        ### stting table ##
        
        self.table.setWordWrap(True)
        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(1, 360)
        self.show()
        
        ## Launch thread ##
        self.thread.start()
      
    def table_loader(self):
        """Loads table from db. Used for update data in table
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
            delete_button = QPushButton("DEL.") # Delete button
            delete_button.setFixedWidth(35)        
            
            self.table.setCellWidget(row,11,delete_button)
            delete_button.clicked.connect(self.delete_specie)
            
            row += 1
            
    def to_add_specie(self):
        """Adds specie to db and table through adding_specie
        """
        already_scrapped = []
        pointer = conector.cursor()
        symbols = "SELECT symbol FROM cedears"
        pointer.execute(symbols)
        scrapped = pointer.fetchall()
        
        for scrp in scrapped:
            already_scrapped.append(scrp[0])
            
        if self.specie_combobox.currentText() == "" :
            self.infolabel2.setText("Must choose a symbol to add")   # prevents blank loading // accidental load 
            
        elif str(self.specie_combobox.currentText()) in already_scrapped:
            self.infolabel2.setText("Specie "+str(self.specie_combobox.currentText())+" already in db")   # prevents duplicates of stocks
                                                                                                
        else:   # propper loading after checking for previous issues
            self.infolabel2.setText("Adding specie, please wait")
            timerint = QtCore.QTimer(self)
            timerint.singleShot(1000, self.adding_specie) ## leting some time pass to permit transsition
            
    def adding_specie(self):
        """Operates adding specie
        """
        # Capture data #
        
        
        new_specie = str(self.specie_combobox.currentText()), str(self.owned.value())
        specie_loader(new_specie)
        partial_scrapper(new_specie[0], float(dollar_scrapper(dollar_urls)), code_list, codes_list_iol)
        
        # from db #
        pointer = conector.cursor()
        new_specie_symbol =  new_specie[0]
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
        self.table.setCellWidget(row,11,delete_button)
        delete_button.clicked.connect(self.delete_specie)
        self.specie_combobox.setCurrentText("")
        self.owned.setValue(0)
        self.total_hold.setText("Total holding: U$S"+str(total_holding()))
        self.infolabel2.setText(new_specie_symbol+" added")
     
    
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
            self.total_hold.setText("Total holding: U$S"+str(total_holding()))
            self.infolabel2.setText(specie+" modified")
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
            self.total_hold.setText("Total holding: U$S"+str(total_holding()))
            self.infolabel2.setText(specie+" removed")
       
    def info_actualizer(self):
        """Updates all data re-scrapping and restarting table
        """
        # re-scrapp # 
                
        self.dollar = dollar_scrapper(dollar_urls)
                
        # restart ui
        self.table.clearContents()
        self.dollar_label.setText("CCL-Dollar: $"+str(self.dollar))
        self.table_loader()
        self.total_hold.setText("Total holding: U$S"+str(total_holding()))
        self.specie_loader.setEnabled(True)
        
        print("info out")
        


if __name__ == "__main__":
    conector = conection_sql()
    tableconstructor(conector)
    
    app = QtWidgets.QApplication(sys.argv)
    
    ui = Main_window()
    
    
    
    sys.exit(app.exec_())
    
   
   
   
    
    
    
    

    

    
     

     

       



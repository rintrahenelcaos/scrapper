from bs4 import BeautifulSoup
import requests

import sys

url = "https://www.cohen.com.ar/Bursatil/Especie/AAL"
information = []

req = requests.get(url)
soup = BeautifulSoup(req.text, 'html.parser')
class_list = set() 
# get all tags 
"""tags = {tag.name for tag in soup.find_all()} 
  
# iterate all tags 
for tag in tags: 
  
    # find all element of tag 
    for i in soup.find_all( tag ): 
  
        # if tag has attribute of class 
        if i.has_attr( "class" ): 
  
            if len( i['class'] ) != 0: 
                class_list.add(" ".join( i['class'])) 
  
print( class_list ) """
outing = soup.find(class_ = 'detailDescripcion')


print(outing)
exit_data1 = BeautifulSoup(str(outing), 'html.parser')
print(exit_data1)
out_exit_data1 = exit_data1.find_all('span')
print(out_exit_data1)
outedlist = []
for outed in out_exit_data1:
    outedlist.append(outed.text)
print(outedlist)   
for data in outing: 
    exit_data = BeautifulSoup(str(data), 'html.parser')
    
    print(data)
    out_exit_data = exit_data.find('span')
    print(str(exit_data), type(exit_data))
    for dato in exit_data.text:
        pass
        #print(dato, type(dato))
        #new_data = dato.text
    if type(data) == "NavigableString":
        print("data")
    #uni_data = unicode(data)
    #print((uni_data))"""
    
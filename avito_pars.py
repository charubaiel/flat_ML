import pandas as pd
from bs4 import BeautifulSoup as bs
import re
from selenium import webdriver
import time
from tqdm import tqdm
from collections import defaultdict

one= 'https://www.avito.ru/volgograd/kvartiry/prodam/1-komnatnye/vtorichka-ASgBAQICAUSSA8YQAkDmBxSMUsoIFIBZ?cd=1'
two = 'https://www.avito.ru/volgograd/kvartiry/prodam/2-komnatnye/vtorichka-ASgBAQICAUSSA8YQAkDmBxSMUsoIFIJZ?cd=1'
three = 'https://www.avito.ru/volgograd/kvartiry/prodam/3-komnatnye/vtorichka-ASgBAQICAUSSA8YQAkDmBxSMUsoIFIRZ?cd=1'
other = 'https://www.avito.ru/volgograd/kvartiry/prodam/vtorichka-ASgBAQICAUSSA8YQAUDmBxSMUg?cd=1&f=ASgBAQICAUSSA8YQAkDmBxSMUsoIlPzPMv5YilmarAGYrAGWrAGUrAGIWYZZ'

d = defaultdict(list)
for bedrooms in [one,two,three,other]:
    url = bedrooms
    driver = webdriver.Chrome()
    driver.get(url)
    soap = bs(driver.page_source,'html.parser')
    pages = int(soap.findAll('span',{'class':'pagination-item-1WyVp'})[-2].text)
    
    for i in tqdm(range(pages)):
        time.sleep(3)
        soap = bs(driver.page_source,'html.parser')
        if soap.find('div',{'id':'main-message'}) == None:
            pass
        else:
            time.sleep(5)
            driver.refresh()
        adress=soap.find_all('div',{'itemprop':'address'})
        for i in adress:
            d['adress'].append(i.find('span',{'class':'item-address__string'}).get_text(strip=True))

        inf=soap.find_all('div',{'class':'snippet-title-row'})
        for i in inf:
            d['info'].append(i.h3.text)

        price = soap.find_all('span',{'class':'snippet-price'})
        for i in price:
            d['price'].append(i.get_text(strip=True))

        neigh=soap.find_all('div',{'class':'item-address'})
        for i in neigh:
            if i.find_all('div',{'class':'item-address-georeferences'})== []:
                d['district'].append('Missed')
            else:
                d['district'].append(i.find('div',{'class':'item-address-georeferences'}).get_text(strip=True))

        data=soap.findAll('div',{'class':'snippet-date-info'})
        for i in data:
            d['date'].append(i['data-tooltip'])
        for key in d.keys():
            print(key,len(d[key]))
        driver.find_element_by_xpath('//span[@data-marker="pagination-button/next"]').click()



df=pd.DataFrame(d)

print(df.shape)

#adress fixing
df.adress=df.adress.str.replace(r'\.|-','')

df.adress = df.adress.str.replace(' улица|^улица| ул|^ул|поселок|посёлок','')

df.adress = df.adress.str.replace(' дом| д| стр','')

df.adress = df.adress.str.replace('Маршала','маршала')

df.adress = df.adress.str.replace('8й','8')

df.adress = df.adress.str.replace('51й','51')

df.adress = df.adress.str.replace('64й','64')

df.adress = df.adress.str.replace('95й','95')
df.adress = df.adress.str.replace('35й','35')

df.adress = df.adress.str.replace('7й','7')

df.adress = df.adress.str.replace('ё','е')

df.adress = df.adress.str.replace('Генерала','генерала')

df.adress = df.adress.str.replace('Академика','академика')

df.adress = df.adress.str.replace('маршала Советского Союза Г К','пр-кт Г.К.')

df.adress = df.adress.str.replace(' им |имени|^пер| пер','')

df.adress = df.adress.str.replace('Дивизии','дивизии')

df.adress = df.adress.str.replace('^прт| прт|проспект','пр-кт')
df.adress = df.adress.str.replace('^бр| бр|бульвар','б-р')

df.adress = df.adress.str.replace('ВИ','В.И.')

df.adress = df.adress.str.replace('  ',' ')

df=df.drop(df.query('district =="Волгоград"').index)

df['street']=df.adress.apply(lambda x: re.findall(r'(.*?),',x)[-1:]).replace(' ,|,','').apply(lambda x: x[0] if x else 'None')

df['street'] = df['street'].str.replace('^ ','')

df['dom']=df.adress.apply(lambda x: re.findall(r',\s+\d+',x)[-1:]).apply(lambda x: x[0] if x else 'None').str.replace(' ','')
df.dom=df.dom.str.replace(',','')

df['clean']=df[['street','dom']].sum(axis=1).str.replace(' ,',',').str.replace('^ ','')

df['clean'] = df['clean'].str.replace('^ ','')

df = df.drop(df[df['dom']=='None'].index)

df[['rooms','m2','floor']]=df['info'].str.split(',',expand=True).fillna('Broke')
df.rooms=df.rooms.str.replace('-к квартира','')
df.loc[:,'price']=df.loc[:,'price'].replace(regex=r'\D*',value='').astype(int)
df=df.drop(df.query('m2 == "Broke"').index)
df.loc[:,'m2']=df.loc[:,'m2'].replace(regex=r' \D+',value='').astype(float)
df[['floor','max_floors']]=df['floor'].str.split('/',expand=True)
df['floor'] = df['floor'].astype(int)
df['max_floors'] = df['max_floors'].replace(regex=r'\D+',value='').astype(int)
df['rubm2'] = df['price']/df['m2']
df.clean = df.street + ' '+ df.dom.astype('str')
df.district=df.district.fillna('Missed')
df.to_csv(f'avito_data_{time.localtime().tm_yday}.csv',index=False)
base_df = pd.read_csv('data/avito_data_clean.csv')
print('old_shape :', base_df.shape)

new_df = pd.concat([base_df,df])
new_df = new_df.drop_duplicates()
df.district=df.district.fillna('Missed')
df.clean = df.street + ' '+ df.dom.astype('str')
new_df.to_csv('data/avito_data_clean.csv',index=False)
print('new_df shape:',new_df.shape)
driver.close()
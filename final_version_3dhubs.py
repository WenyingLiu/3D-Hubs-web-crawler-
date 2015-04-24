import urllib2
import bs4
import requests
import pandas as pd
import json
from StringIO import StringIO

def find_hub_lists(URL):
    hub_lists = []
    response = requests.get(URL)
    soup = bs4.BeautifulSoup(response.text)
    cell = soup.findAll('span', {'class':"station-hub-title"})
    for i in cell:
        hub_name = i.text[:-6]
        hub_lists.append(hub_name)
    
    return hub_lists

def read_hub_info(h, soup):
    # First, we want to get the information from the sidebar.
    # This contains information such as 'Specialties', 'About', 'Invoice', 'Invoices', 'Delivery', 'Active since'
    # 'Response time' and 'hub location'
    hub_info = []
    hub_info.append(str(h))
    
    sidebar = soup.findAll(('aside', {'id':'sidebar'}))
    
    try:
        specialties = filter(None, sidebar[0].findAll('div', {'id':'block-hubs3d-hub-hub-specialties' })[0].findAll('div', {'class': 'field-items'})[0].text.split('\n'))
        specialties = [x.encode('UTF8') for x in specialties]
        hub_info.append(specialties)
    except:
        hub_info.append([])
    
    try:
        about = filter(None, sidebar[0].findAll('div', {'id':'block-hubs3d-hub-hub-about' })[0].findAll('div', {'class': 'field-items'})[0].text.split('\n'))
        about = [x.encode('UTF8') for x in about]
        hub_info.append(about)
    except:
        hub_info.append([])
    
    try:
        properties = filter(None, sidebar[0].findAll('div', {'class':'hub-properties' })[0].findAll('div', {'class': 'field-item'}))
        property_list = []
        for p in properties:
            property_list.append(str(p.text))
        hub_info.append(property_list)
    except:
        hub_info.append([])
    
    # The location is used in one of the scripts, so we first find all scripts and then filter them by contents.
    try:
        for s in soup.findAll('script'):
            if 'Drupal.settings' in str(s.contents):
                text = s.text[31:-2]
                io = StringIO(text)
                text = json.load(io)
                #print text
                for loc in text['getlocations']['key_1']['latlons']:
                    if 'default' in filter(None, loc):
                        hub_info.append(loc[:2])
    except:
        hub_info.append([])
        
    # This part is to extract number of reviews and reviews content.
    try:
        review = soup.findAll('div', {'id': 'block-hubs3d-review-hubs3d-hub-reviews-full'})
        review_count = review[0].findAll('span', {'class': 'votecount'})[0].text.split()[2]
        hub_info.append(review_count.encode('UTF8'))
        
        review_list = []
        for r in review[0].findAll('div', {'class': 'review-content'}):
            review_list.append(r.text.replace('\n', '').lstrip().encode('UTF8'))
        hub_info.append(review_list)
    except:
        hub_info.append(0)
        hub_info.append([])
             
    return hub_info

def read_printer_info(h, soup):
    
    # Get information on printers and store it
    # It contains information such as printerName, offlineStatus, deliveryTime, startupCost and material properties (materialName, materialCost and materialColor)

    printers_info = []
    
    printers_offline = []
    for i in soup.findAll('div', {'class': 'field-name-field-printers'}):
        if i.findAll('span') == []:
            printers_offline.append('online')
        else:
            printers_offline.append('offline')
    
    printerDetails = soup.find_all("div", class_="group-printer-details")
    materialDetails= soup.find_all("div", class_="field-name-field-material-collection")
    numberPrinters = len(printerDetails)
    
    for n in range(numberPrinters):
        printer_info = []
        printer_info.append(str(h))
        printer_info.append(printers_offline[n])
        printerName = printerDetails[n].findAll('h2')[0].text.split('\n')
        printer_info.append(printerName)
        
        deliveryTime = printerDetails[n].find_all("div", class_="field-item item-1 even")[0].text
        startupCost = printerDetails[n].find_all("div", class_="field-item item-1 even")[1].text
        printResolution = printerDetails[n].find_all("div", class_="field-item item-1 even")[2].text
        
        printer_info.extend([deliveryTime, startupCost, printResolution])
        
        material_info = []
        for i in materialDetails[n].find_all("div", class_="entity entity-field-collection-item field-collection-item-field-material-collection clearfix"):
            material_info.append(filter(None, i.text.split('\n')))
        
        printer_info.append(material_info)
        
        printers_info.append(printer_info)
     
    return printers_info
	
def main():
    
    # Focusing on NYC at the moment
    URL = 'https://www.3dhubs.com/3dprint?hf[data][location][search]=New%20York%20City&hf[data][location][lat]=40.7143&hf[data][location][lon]=-74.006&hf[data][location][radius]=50'
    response = requests.get(URL)
    soup = bs4.BeautifulSoup(response.text)
    
	# Find how many pages are there for the hub lists.
    pages = soup.findAll('li', {'class': 'pager-current'})
    num_page = int(pages[0].text.split('of')[-1])

    # The structure of the URL: 
    # For the first page is 'https://www.3dhubs.com/3dprint?hf[data][location][search]=New%20York%20City&hf[data][location][lat]=40.7143&hf[data][location][lon]=-74.006&hf[data][location][radius]=50'
    # The latter page has the format like 'https://www.3dhubs.com/3dprint?page={}&hf[data][location][search]=New%20York%20City&hf[data][location][lat]=40.7143&hf[data][location][lon]=-74.006&hf[data][location][radius]=250'.format(num_page)

    # Given a URL, crawl all the hubs' names.
    hub_lists = []
    for i in range(num_page):
        if i == 0:
            URL = 'https://www.3dhubs.com/3dprint?hf[data][location][search]=New%20York%20City&hf[data][location][lat]=40.7143&hf[data][location][lon]=-74.006&hf[data][location][radius]=50'
        else:
            URL = 'https://www.3dhubs.com/3dprint?page={}&hf[data][location][search]=New%20York%20City&hf[data][location][lat]=40.7143&hf[data][location][lon]=-74.006&hf[data][location][radius]=50'.format(i)
        hub_lists.extend(find_hub_lists(URL))

    ################### Now we have all unique hub names.#####################
    hub_lists = set(hub_lists)
    ##########################################################################

    # The URL for each hub has the format as 'https://www.3dhubs.com/new-york/hubs/{}'.format(hub_name)
    # For example, hub name 'Olivero Design' has the URL 'https://www.3dhubs.com/new-york/hubs/olivero-design'
    # Thus, we here clean each hub name so that it can be directly used to track the hub's website.
    clean_hub_lists = []
    for i in hub_lists:
        clean_hub_lists.append('-'.join(i.replace('+', '').replace('_', '').replace("'", '').replace('.', '').replace('The', '').strip().split()))
		
    all_hub_info = pd.DataFrame()
    all_hub_printer_info = pd.DataFrame()

    for h in clean_hub_lists:
        hubURL = 'https://www.3dhubs.com/new-york/hubs/{}'.format(h)
        response = requests.get(hubURL)
        soup = bs4.BeautifulSoup(response.text)
        
        print 'Save information for hub {}'.format(h)
        all_hub_info = pd.concat([all_hub_info, pd.DataFrame(read_hub_info(h, soup)).T])
        
        print 'Save information for all printers in hub {}'.format(h)
        all_hub_printer_info = pd.concat( [all_hub_printer_info, pd.DataFrame(read_printer_info(h, soup))])
    
    print '******Save all hub information to file all_hub_info.csv*********'
    all_hub_info.columns = ['hub_name', 'specialties', 'about', 'properties', 'location', 'num_reviews', 'reviews content']
    all_hub_info.to_csv('all_hub_info.csv')
	
    print '******Save all hub information to file all_hub_printer_info.csv*********'
    all_hub_printer_info.columns = ['hub_name', 'offline', 'printer_name', 'deliveryTime', 'startupCost', 'printResolution', 'material']
    all_hub_printer_info.to_csv('all_hub_printer_info.csv')

if __name__ == '__main__':
    main()
		
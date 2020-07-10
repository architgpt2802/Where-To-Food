# -*- coding: utf-8 -*-
"""
Created on Wed Jun 17 18:44:52 2020

@author: ARCHIT
"""

"""
***WHERE TO FOOD***
a program to scrape the zomato website and look for restaurants providing the best deals.
it will calculate a score based on the rating of the restaurant and discount available.
the restaurants will be listed on the bases of a higher WTF Score. 
"""


from bs4 import BeautifulSoup as BS
import json
import requests
import re
from conf import account_sid, auth_token, twilio_num, my_num    #module to store the api keys and phone numbers form twilio
from twilio.rest import Client
import time
import threading


#client stores twilio api keys and tokens
client = Client(account_sid, auth_token)


cookie_jar = dict()

#to read the cookies saved
def getcookies():
    
    global cookie_jar
    
    cFile = open("cookies.json", "r")
    cData = cFile.read()
    cFile.close()
    
    cData = json.loads(cData)
    
    for i in cData:
        name = i["name"]
        value = i["value"]
        cookie_jar[name] = value
        

#providing zomato user agent of a chrome user on windows        
headersUA = dict()
headersUA["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"

#providing zomato the cookies to skip the logging in process
def connect_zomato():
  
    r = requests.get("https://www.zomato.com", cookies = cookie_jar, headers = headersUA)
    
    if "Log out" in (r.text):
        print("logged in to zomato")
    else:
        print("not logged in to zomato")
        
allRest = [] 
       
#calculating the restaurant score from rating and offers available
def scorecal(rating, offer):
    rating = rating * 10
    offer = offer * 2
    return(rating + offer)
    

#scraping the restaurants for online orders      
def scrape_online_delv(pageNo):
   
    r = requests.get("https://www.zomato.com/ncr/west-delhi-order-online?page=%d"%pageNo, cookies = cookie_jar, headers = headersUA)

    soup = BS(r.text, "html.parser")
    my_divs = soup.find_all("div", {"class" : "search-o2-card"})
    
    for div in my_divs:
        #name of the rest
        rstName = div.findChildren("a", {"class" : "result-order-flow-title"})[0].text.strip()
        
        #link to the direct page of the rest on zomato
        link = []
        link = div.findChildren("a", attrs = {'href' : re.compile("^https://")})
        rstLink = link[0].get('href')
        
        #rating of the rest
        if (div.findChildren("span",{"class" : "rating-value"})): 
            rstRating = div.findChildren("span",{"class" : "rating-value"})[0].text.strip()
    
            rstRating = float(rstRating)
    
        else:
            rstRating = 0.0
            
        #category of the rest
        rstCatg = div.findChildren("div", {"class" : "grey-text"})[0].text.strip()
        
        #finding the offers available
        rstOffer = "No Offer"
        rstOfferValue = 0
        
        if(div.findChildren("span", {"class" : "offer-text"})):
            rstOffer = div.findChildren("span", {"class" : "offer-text"})[0].text.strip()
            
            #if u"\u20b9" in rstOffer:
                #rstOfferValue = rstOffer[rstOffer.index(u"\u20b9")+1:rstOffer.index(" ")]
            if "%" in rstOffer:
                rstOfferValue = int((rstOffer[0:rstOffer.index("%")]).strip())
           
        #calling the func to calculate the rest score
        rstScore = scorecal(rstRating, rstOfferValue)
        #print(rstScore)
        
        rstInfo = dict()
        
        rstInfo['rstName'] = rstName
        rstInfo['rstRating'] = rstRating
        rstInfo['rstCatg'] = rstCatg
        rstInfo['rstOffer'] = rstOffer
        rstInfo['rstScore'] = rstScore
        rstInfo['rstLink'] = rstLink
        
        allRest.append(rstInfo)
        
        sortedAllRest = sorted(allRest, key = lambda i: i['rstScore'], reverse = True)
        
    return sortedAllRest
 


dineOffer = 'no offer'   
dineOfferValue = 0    

allDine = []

#scraping the restaurants for dinnig out
def scrape_dine_out(pageNo):
    
    global dineOffer
    global dineOfferValue

    r = requests.get("https://www.zomato.com/ncr/west-delhi-restaurants?table_booking=1&page=%d"%pageNo, cookies = cookie_jar, headers = headersUA)
    #print(r.text)
        
    soup = BS(r.text, "html.parser")
    my_divs = soup.find_all("div", {"class" : "search-snippet-card"})
    for div in my_divs:
        
        #name of the rest
        dineName = div.findChildren("a", {"class" : "result-title"})[0].text.strip()
           
        #direct link to the rest page on zomato
        link = []
        link = div.findChildren("a", attrs = {'href' : re.compile("^https://")})
        dineLink = link[0].get('href')
            
        #rating of the rest
        if(div.findChildren("span", {"class" : "rating-value"})):
            
            dineRating = div.findChildren("span", {"class" : "rating-value"})[0].text.strip()
            dineRating = float(dineRating)
                
        else:
            dineRating = 0.0
                
        #category of the rest
        dineCatg = div.findChildren("span", {"class" : "col-m-12"})[0].text.strip()
            
        #finding the offers available
        if(div.findChildren("a", {"class" : "zgreen"})):
            
            dineOffer = div.findChildren("a", {"class" : "zgreen"})[0].text.strip()
            
            if "%" in dineOffer:
                dineOfferValue = int((dineOffer[0:dineOffer.index("%")]).strip())
            
        #open timings   
        dineTime = div.findChildren("div", {"class" : "col-s-11"})[0].text.strip()

        #calling the function to calculate the rest score
        dineScore = scorecal(dineRating, dineOfferValue)
        #print(rstScore)
        
        dineInfo = dict()
        
        dineInfo['dineName'] = dineName
        dineInfo['dineRating'] = dineRating
        dineInfo['dineCatg'] = dineCatg
        dineInfo['dineOffer'] = dineOffer
        dineInfo['dineTime'] = dineTime
        dineInfo['dineScore'] = dineScore
        dineInfo['dineLink'] = dineLink
        
        allDine.append(dineInfo)
        
        sortedAllDine = sorted(allDine, key = lambda i: i['dineScore'], reverse = True)
        
    return sortedAllDine
 

#main function
def main():
    
    getcookies()
    connect_zomato()
    
    #option to choose to order online or dine out
    opt = int(input("Wanna DINE OUT or ORDER ONLINE\n(1 or 2): "))
    
    #online order
    if (opt == 2):
        
        cont = 1
        while (cont):
            for i in range(1,2): #range of the pages to look into
                Rests = scrape_online_delv(i)
            
                for Rest in Rests:
                
                    if (Rest['rstScore'] > 30.0): #rest below the score of 30 should not be listed
                        print("\nRestaurant Details")
                        print("Name: %s"%Rest['rstName'])
                        print("Rating: %s"%Rest['rstRating'])
                        print("Category: %s"%Rest['rstCatg'])
                        print("Offer: %s"%Rest['rstOffer'])
                        print("Score: %s"%Rest['rstScore'])
                        print("Link: %s"%Rest['rstLink'])
                        print("*****\n")
                    
                    #sms notification
                    if (Rest['rstScore'] > 120.0):
                        msg = '\nOffer alert from WHERE TO FOOD\n' +str(Rest['rstName']) +'\n' +str(Rest['rstRating']) +'\n' +str(Rest['rstCatg']) +'\n' +str(Rest['rstOffer']) +'\n' +str(Rest['rstLink'])
                        sms = client.messages.create(to = my_num, from_ = twilio_num, body = msg)
                    
                time.sleep(3600)
                
                """
                answer = None
                    
                def check():
                    time.sleep(30)
                    if answer != None:
                        cont = 0
                        return
                        
                Thread(target = check).start()
                answer = int(input("Press any key to exit: "))
                """
                    
                    
    #dine out
    elif (opt == 1):

        for i in range(1,2): #range of the pages to look into
            Dines = scrape_dine_out(i)
            
            for Dine in Dines:
                
                if (Dine['dineScore'] > 35.0): #rest below the score of 35 should not be listed
                    print("\nRestaurant Details")
                    print("Name: %s"%Dine['dineName'])
                    print("Rating: %s"%Dine['dineRating'])
                    print("Category: %s"%Dine['dineCatg'])
                    print("Offer: %s"%Dine['dineOffer'])
                    print("Open Timings: %s"%Dine['dineTime'])
                    print("Score: %s"%Dine['dineScore'])
                    print("Link: %s"%Dine['dineLink'])
                    print("*****\n")     
        
    #wrong choice
    else:
        print("choice not accepted")
        

#calling the main func
if __name__ == "__main__":
    print("\nWELCOME TO\nWHERE TO FOOD\n")
    main()
        
        
        
        
        
        
    
        

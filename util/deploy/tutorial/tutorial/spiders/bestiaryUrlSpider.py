import scrapy

#Grabs all the monsters listed in the bestiary sorted by CR on d20pfsrd and
#stores their information in a .json file, which can be easily modified into a csv
#with your favorite text editor to upload to a database
#to run: scrapy runspider bestiaryUrlSpider.py -o bestiary.json
class BestiarySpider(scrapy.Spider):
    name = 'd20pfsrd'
    start_urls = ['http://www.d20pfsrd.com/bestiary/-bestiary-alphabetical','http://www.d20pfsrd.com/bestiary/-bestiary-by-challenge-rating','http://www.d20pfsrd.com/bestiary/-bestiary-by-terrain', 'http://www.d20pfsrd.com/bestiary/monster-listings']

    def parse(self, response):
        #this ignores the 3PP external website link, but will still scrape 3PP data from its monster link.  It also ignores templates and traps (such as oozes)
        urlList = response.selector.xpath('//*[@id="sites-toc-undefined"]/div/ul').xpath('.//a[not(contains(@href,\'traps-hazards-and-special-terrains\')) and not(contains(@href,\'templates\'))]/@href').extract() 

        if(response.url == 'http://www.d20pfsrd.com/bestiary/monster-listings'):
            #No intermediate subpage listing, do direct monster scraping
            for href in urlList:
                href = 'http://www.d20pfsrd.com' + href
                yield scrapy.Request(href, callback=self.parse_monster_page)
        else:
            #Do intermediate subpage scraping
            for href in urlList:
                href = 'http://www.d20pfsrd.com' + href
                yield scrapy.Request(href, callback=self.parse_subpage_list)

    def parse_subpage_list(self, response):
            subpageContainer = response.selector.xpath('//*[@id="sites-canvas-main-content"]')
            #this ignores the 3PP external website link, but will still scrape 3PP data from its monster link.  It also ignores templates and traps (such as oozes)
            subpageUrls = subpageContainer.xpath('.//a[not(contains(text(), \'3PP\')) and not(contains(text(),\'Back to Top\')) and not(contains(@href,\'traps-hazards-and-special-terrains\')) and not(contains(@href,\'templates\'))]/@href').extract()
            for href in subpageUrls:
                yield scrapy.Request(href, callback=self.parse_monster_page)

    def parse_monster_page(self, response):
        nameRaw = response.selector.xpath('//*[@id="sites-page-title"]/text()').extract()
        crRaw = response.selector.xpath('//*[@id="sites-canvas-main-content"]//*[contains(text(),"CR")][1]/text()').extract()
        initRaw = response.selector.xpath('//*[@id="sites-canvas-main-content"]//*[contains(text(),"Init")][1]/following-sibling::text()[1]').extract()
        hpRaw = response.selector.xpath('//*[@id="sites-canvas-main-content"]//*[contains(text(),"hp")][1]/following-sibling::text()[1]').extract()
        
        #only do these if we are on an actual monster page (i.e. crRaw and initRaw are something)
        if crRaw and initRaw:
            #sometimes differently formatted on their site, hence try excepts
            name = str(nameRaw)[3:-2]
            cr = str(crRaw).split("'")[1].split("CR")[1].strip()
            try:
                init = str(initRaw).split("'")[1].split(";")[0].strip().replace("\\u2013","-").replace(",","")
            except IndexError:
                initRaw = response.selector.xpath('//*[@id="sites-canvas-main-content"]//*[contains(text(),"Init")][1]/parent::b/following-sibling::*[position()=1]/text()').extract()
                init = str(initRaw).split("'")[1].split(";")[0].strip().replace("\\u2013","-").replace(",","")

            #Needed for creatures like Summoned Creature: Fire Beetle
            try:
                try:
                    hp = str(hpRaw).split("'")[1].split("(")[0].strip()
                except IndexError:
                    hp = str(hpRaw).split("xa0")[1].split("'")[0]
                try:
                    hd = str(hpRaw).split("(")[1].split(")")[0]
                except IndexError:
                    hdRaw = response.selector.xpath('//*[@id="sites-canvas-main-content"]//*[contains(text(),"hp")][1]/following-sibling::*[position()=1]/text()').extract()
                    hd = str(hdRaw).split("(")[1].split(")")[0]
            except IndexError:
                #Needed for creatures like Mephit, Air
                hpRaw = response.selector.xpath('//*[@id="sites-canvas-main-content"]//*[contains(text(),"hp")][1]/../following-sibling::*[1]/text()').extract()
                hp = str(hpRaw).split("'")[1].split("(")[0].strip()
                hd = str(hpRaw).split("(")[1].split(")")[0]

        #return these so we can see if there are other errors in script.  Delete values where name=None with database manager
        else:
            name = None
            cr = None
            init = None
            hp = None
            hd = None

        yield {
            'url': response.url,
            'name' : name,
            'cr' : cr,
            'init' : init,
            'hp' : hp,
            'hd' : hd
        }

#After script is run the following must be done:
#select only unique values from mysql
#remove None element name
#deleted summoned creatures for now
#added 8 by hand
#Add familiar creatures later...?
#Error cases added in by hand
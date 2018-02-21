from lxml import html
from base import Base


class Message(Base):
    '''
    This class extract messages from `obj:lxml.tree` User's UMS Homepage Data Object 
    and returns all the messages in `obj:list` list.

    Attributes::

    mesgList (`obj:list`): Contains all the extracted messages.
    msgPth (`obj:list`): Containes xpath to those values are need to get extracted from UMS page itself.
    

    Args::
    
    page_data (`obj:lxml.html`): Represents an pre intialized instance of html tree object.
    data_xpath (`obj:list`): Containes xpath to those values are need to get extracted from UMS page itself.
    data_category (`obj:int`): It will determine which html element is need to extract 
    Raises:
        ValueError: If page_num is not an acceptable int.
    '''

    def __init__(self, page_data):
        self.mesgList = []
        self.msgPath = [
            '//div[@id ="owl-demo"]/div/div[@class="Announcement_Subject"]/text()',
            '//div[@id ="owl-demo"]/div/div[@class="Announcement_Name"]/text()',
            '//div[@id ="owl-demo"]/div/div/div[@class="Announcement"]/text()'
        ]
        self.pageData = page_data

    def dataExtractor(self, page_data, data_xpath, data_category):
        '''
        This method will extract html elements from a pre html tree `obj:lxml.html` obj.
        '''

        items = page_data.xpath(data_xpath)
        fault_list = []

        for k, item in enumerate(items):
            item = item.strip("\r\n")
            item = item.strip()
            fault_list.append(item)
            #print("{} : {}\n".format(k, item))
            #print("Item Length: {}".format(len(item)))
            #print("ItemType: {}".format(type(item)))

        #print("Length: {}".format(len(items)))
        #print('\n\n')

        refined_items = list(filter(None, fault_list))
        print(len(refined_items))

        if len(self.mesgList) == 0:
            for itemk in refined_items:
                self.mesgList.append("")

        if data_category == 0:
            for i, item in enumerate(refined_items):
                self.mesgList[i] = [item, '', '']

        elif data_category == 1:
            for j, item in enumerate(refined_items):

                self.mesgList[j][1] = 'By: ' + item
        elif data_category == 2:
            for k, item in enumerate(refined_items):
                self.mesgList[k][2] = item

    def msgExtractor(self, page_data, data_xpath):
        '''
        This method will extract html elements from a pre html tree `obj:lxml.html` obj
        '''
        for index, item in enumerate(data_xpath):
            self.dataExtractor(page_data, item, index)
        return None

    def initiater(self):
        '''
        This Method will instantiate a Messages instance and fetch the messages in a `obj:list` list.
        
        Args::

        page_data (`class:lxml.html`): Represents an pre intialized instance of html tree object.
        '''
        self.msgExtractor(self.pageData, self.msgPath)
        return self.mesgList

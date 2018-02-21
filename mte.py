from lxml import html
import requests
import urllib
from base import Base
import io

class Midterm(Base):

    def __init__(self, session):
        self.session = session
        self.base_url = 'https://ums.lpu.in/lpuums/frmMarksView.aspx'
        self.base_page = self.getRequest(self.session,self.base_url)
        self.var_token = {'ctl00_RadScriptManager1_TSM':'',
            "__VSTATE":'',
            '__EVENTVALIDATION':'',
            }
        self.term_list = None

    def token_creator(self,page_data):
        tokenList = list(self.var_token.keys())
        tokenList.remove('ctl00_RadScriptManager1_TSM')
        self.tokenGetter(page_data,tokenList,self.var_token)
        self.term_list = page_data.xpath('//li[@class="rcbItem"]/text()')
        self.term_list[0] = None
        self.speToken(page_data)
    
    def speToken(self,page_data):
        v = '/LpuUms/Telerik.Web.UI.WebResource.axd?_TSM_HiddenField_=ctl00_RadScriptManager1_TSM&compress=1&_TSM_CombinedScripts_='
        items = page_data.xpath('//script/@src')
        for i in items:
            if v in i:
                v = i[len(v):]
        v = urllib.parse.unquote_plus(v)
        self.var_token['ctl00_RadScriptManager1_TSM'] = v
    
    def mte_detail_page(self,term_code,term_index):
        self.token_creator(self.base_page)
        token = {'ctl00_RadScriptManager1_TSM':(None,self.var_token['ctl00_RadScriptManager1_TSM'],None,None),
            '__EVENTTARGET': (None,'ctl00$cphHeading$rdTerm',None,None),
            '__EVENTARGUMENT': (None,str({"Command":"Select","Index":term_index}),None,None),
            "__VSTATE":(None,self.var_token["__VSTATE"],None,None),
            "__VIEWSTATE":(None,'',None,None),
            '__EVENTVALIDATION':(None,self.var_token['__EVENTVALIDATION'],None,None),
            'ctl00$WcHeaderforStudent1$hdnType':(None,'S',None,None),
            "ctl00_WcHeaderforStudent1_radStudentMenu_ClientState":(None,'',None,None),
            "ctl00$WcHeaderforStudent1$WUCStudentIdea1$txtProject":(None,'',None,None),
            "ctl00$WcHeaderforStudent1$WUCStudentIdea1$TextBoxWatermarkExtender1_ClientState":(None,'',None,None),
            "ctl00$WcHeaderforStudent1$WUCStudentIdea1$ddlAim":(None,'Select aim',None,None),
            "ctl00$WcHeaderforStudent1$WUCStudentIdea1$txtDescription":(None,'',None,None),
            "ctl00$WcHeaderforStudent1$WUCStudentIdea1$TextBoxWatermarkExtender2_ClientState":(None,'',None,None),
            "ctl00$WcHeaderforStudent1$WUCStudentIdea1$rdStatus":(None,'N',None,None),
            "ctl00$WcHeaderforStudent1$WUCStudentIdea1$txtSupervisourDetail":(None,''),
            "ctl00$WcHeaderforStudent1$WUCStudentIdea1$TextBoxWatermarkExtender3_ClientState":(None,'',None,None),
            "ctl00$WcHeaderforStudent1$WUCStudentIdea1$fuAttachementforidea":('', '','application/octet-stream',None),
            "ctl00$cphHeading$rdTerm":(None,term_code,None,None),
            "ctl00_cphHeading_rdTerm_ClientState":(None,
            str({"logEntries":[],"value":term_code,"text":term_code,"enabled":'true',"checkedIndices":[],"checkedItemsTextOverflows":'false'})
            ,None,None)
            }
        return self.postRequest(self.session,self.base_url,upload_stream=token)
    
    def get_mte_marks(self,sub_tr):
        na = 'NA'
        '''
        Subjects and then marks are found in <tr> elements
        MTE marks need to extracted from those

        sub_tr is the <tr> element in the tree where the subject string is found
        na is the string to return for subjects for which there was no mte

        - Theory MTE marks are found in the 1st following sibling of this <tr> element
        - Objective MTE marks are found in the 3rd following sibling of this <tr> element
        '''

        # storing all the following siblings in a list:
        following_siblings = sub_tr.xpath('./following-sibling::*')
        n_siblings = len(following_siblings)

        # checking for theory MTE:
        if n_siblings>=1:
            theory_title = following_siblings[0].xpath('./child::*[3]/font/text()')[0].strip()
            if theory_title == 'Theory Mid Term':   # checking if this is the actual <tr> required
                return following_siblings[0].xpath('./child::*[5]/font/text()')[0]
        else: return na

        # checking for objective MTE:
        if n_siblings>=3:
            obj_title = following_siblings[2].xpath('./child::*[3]/font/text()')[0].strip()
            if obj_title == 'Objective Type Mid Term':
                return following_siblings[2].xpath('./child::*[5]/font/text()')[0]
            else: return na
        else: return na

    def extract_all(self,tree):
        '''
        Stores the subject and MTE marks as pairs in a dictionary and returns that dictionary
        '''
        marks_dict = {}
        sub_trs=tree.xpath('//tr[@class="rgRow" and .//span/text()]|//tr[@class="rgAltRow" and .//span/text()]')
        # ^ tr elements with subjects and CA marks in them
        for sub_tr in sub_trs:
            subject_name = sub_tr.xpath(".//span/text()")[0]
            marks_dict[subject_name] = self.get_mte_marks(sub_tr)
        return marks_dict
        pass


    def initiater(self,term_code,term_index):
        mte_marks_page = self.mte_detail_page(term_code,term_index)
        marks_dict = self.extract_all(mte_marks_page)
        return marks_dict

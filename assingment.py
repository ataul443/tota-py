import urllib
import shutil
from lxml import html
from base import Base
import cgi
import io
from multiprocessing import Pool

class Resources(Base):
    
    def __init__(self, session, course=None):
        self.baseUrl = 'https://ums.lpu.in/lpuums/frmstudentdownloadassignment.aspx'
        self.varToken = {'ctl00_RadScriptManager1_TSM':'',
            "__VSTATE":'',
            '__EVENTVALIDATION':'',
            }
        self.session = session
        self.courseDict = None
        self.basePage = self.getRequest(self.session,self.baseUrl)
        self.course = course
        self.finalToken = None
        
    #couse_codes retriever and detail_page's token setter 
    def token_creator(self,page_data):
        tokenList = list(self.varToken.keys())
        tokenList.remove('ctl00_RadScriptManager1_TSM')
        self.tokenGetter(page_data,tokenList,self.varToken)
        self.speToken(page_data)

    def speToken(self,page_data):
        v = '/LpuUms/Telerik.Web.UI.WebResource.axd?_TSM_HiddenField_=ctl00_RadScriptManager1_TSM&compress=1&_TSM_CombinedScripts_='
        items = page_data.xpath('//script/@src')
        for i in items:
            if v in i:
                v = i[len(v):]
        v = urllib.parse.unquote_plus(v)
        self.varToken['ctl00_RadScriptManager1_TSM'] = v

    def course_button_binding(self,page_data):
        course_code_button = {}
        x = page_data.xpath("//*[@id='ctl00_cphHeading_GridView1']/tr/td[2]/text()")
        y = page_data.xpath("//*[@id='ctl00_cphHeading_GridView1']/tr/td[1]/input/@name")
        for i in range(0,len(x)):
            course_code_button[x[i]] = y[i]
        return course_code_button
    
    def course_code_validator(self,course_code,courses_data):
        try:
            if course_code in courses_data.keys():
                return courses_data[course_code]
            else:
                raise KeyError('Course is not available')
        except KeyError as error:
            print(error)

    def course_codes(self):
        ##token setting for next detail page
        self.token_creator(self.basePage)
        ## course codes retrieval
        self.courseDict = self.course_button_binding(self.basePage)
        return self.courseDict
    ## course detail page for extracting data--
    def course_detail_page(self,course_code_value):
        token = {'ctl00_RadScriptManager1_TSM':(None,self.varToken['ctl00_RadScriptManager1_TSM'],None,None),
            '__EVENTTARGET': (None,'',None,None),
            '__EVENTARGUMENT': (None,'',None,None),
            "__VSTATE":(None,self.varToken["__VSTATE"],None,None),
            "__VIEWSTATE":(None,'',None,None),
            '__EVENTVALIDATION':(None,self.varToken['__EVENTVALIDATION'],None,None),
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
            course_code_value:(None,'View Details',None,None),
            "ctl00$cphHeading$HiddenField1":(None,'',None,None)
            }
        return self.postRequest(self.session,self.baseUrl,payload=None,upload_stream=token)
    
    def course_content_extractor(self,page_detail_data):
            items = page_detail_data.xpath('//table[@id="ctl00_cphHeading_rgAssignment_ctl00"]/tbody/tr[@class="rgRow"]')
            items1 = page_detail_data.xpath('//table[@id="ctl00_cphHeading_rgAssignment_ctl00"]/tbody/tr[@class="rgAltRow"]')
            k = items + items1
            res = []
            for count,j in enumerate(k):
                it = j.xpath('.//td[13]/font/input/@name')
                for i in it:
                    if i != '':
                        upload_date = ''.join(j.xpath('.//td[4]/font/text()'))
                        topic = ''.join(j.xpath('.//td[7]/font/text()'))
                        comment = ''.join(j.xpath('.//td[8]/font/text()'))
                        res_button = ''.join(j.xpath('.//td[13]/font/input/@name'))
                        res.append([upload_date,topic,comment,res_button])
            return res
    
    def course_content_list(self):
        self.course_codes()
        detailPage = self.course_detail_page(self.courseDict[self.course])
        self.token_creator(detailPage)
        course_content = self.course_content_extractor(detailPage)
        return course_content
    #ctl14$lblFileUplaodByTeacher
    def res_down_token(self,res_button_value):
        k = {'ctl00_RadScriptManager1_TSM':(None,self.varToken['ctl00_RadScriptManager1_TSM'],None,None),
            '__EVENTTARGET': (None,'',None,None),
            '__EVENTARGUMENT': (None,'',None,None),
            "__VSTATE":(None,self.varToken["__VSTATE"],None,None),
            "__VIEWSTATE":(None,'',None,None),
            '__EVENTVALIDATION':(None,self.varToken['__EVENTVALIDATION'],None,None),
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
            "{}.x".format(res_button_value):(None,'5',None,None),
            "{}.y".format(res_button_value):(None,'6',None,None),
            "ctl00_cphHeading_rgAssignment_ClientState":(None,'',None,None),
            "ctl00$cphHeading$HiddenField1":(None,'',None,None)
            }
        return k

    def initiater(self,res_button_value):
        return_var = None
        print("starting Initiator....")
        self.course_codes()
        detailPage = self.course_detail_page(self.courseDict[self.course])
        tokenList = list(self.varToken.keys())
        tokenList.remove('ctl00_RadScriptManager1_TSM')
        self.tokenGetter(detailPage,tokenList,self.varToken)
        self.speToken(detailPage)
        self.finalToken = self.res_down_token(res_button_value)
        data = self.session.post(self.baseUrl,files=self.finalToken,stream=True)
        filename = cgi.parse_header(data.headers['content-disposition'])[-1]['filename']
        print(filename)
        buff = io.BytesIO()
        with open('{}'.format(filename),'wb') as target:
            data.raw.decode_content = True
            shutil.copyfileobj(data.raw, target)
        return filename

        
    


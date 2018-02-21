
import threading
from lxml import html
from abc import ABCMeta,abstractmethod




class Base(object):
    '''
    Base Object for providing various essential methods.

    Args::

    session (`class:requests.session`): Represents an session object in which all the requests are made.
    base_url (`obj:str`): Url of UMS
    payload (`obj:dict`): Containes those variable whose values are need to get extracted from UMS page itself.
    token_list (`obj:dict`): Containes esseential variables to simulate login page request.

    '''

    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    
    
    def getRequest(self,session, base_url):
        '''
        It will return an html tree `obj:lxml.html` parsed by `class:lxml.html`.
        Http requests are made in `class:requests.session`.

        Args::

        session (`class:requests.session`): Represents an pre intialized instance of session object in which all the requests are made.
        base_url (`class:str`): Url to get fetched.

        '''
        
        homeData_response = session.get(base_url)
        homeData_tree = html.fromstring(homeData_response.content)
        return homeData_tree
        

    
    def postRequest(self, session, base_url, payload=None, upload_stream=None):
        '''
        It will return an html tree `obj:lxml.html` parsed by `class:lxml.html`.
        Http requests are made in `class:requests.session`.

        Args::

        session (`class:requests.session`): Represents an pre intialized instance of session object in which all the requests are made.
        base_url (`class:str`): Url to get fetched.
        payload (`class:dict`): Essential data to use in request payload or request body.
        meta_stream ('class:tuple): Essential data to use in upload stream of a request.

        Raises:

        ValueError: If something wrong with base_url or payload.
        '''

        tree = session.post(base_url, data=payload, files=upload_stream,)
        tree = html.fromstring(tree.content)
        return tree
        


    def attrGetter(self, page_data, name, payload):
        '''
        It will find values of specific html element with specific attributes and 
        assings these values to corresponding payload `obj:dict` variables.

        Args::

        page_data (`class:lxml.html`): Represents an pre intialized instance of html tree object.
        name (`class:str`): Value of `name` attribute of a specific html element.
        payload (`class:dict`): Essential data to use in request payload or request body.

        Raises:

        ValueError: If payload values are same already.
        '''
        try:
            if page_data is not None:
                items = page_data.xpath('//input[@name="' + name +
                                '" and @type="hidden"]/@value')
                for item in items:
                    try:
                        if payload[name] != item:
                            payload[name] = item
                            return
                        else:
                            raise ValueError("Attribute {} Value is SAME!".format(name))
                    except ValueError as error:
                        print('Error: ' + str(error))
            else:
                raise ValueError("page_data is NoneType")
        except ValueError as e:
            print("Method: attrGetter | Error: {}".format(e))


    def tokenGetter(self, page_data, token_list, payload):
        '''
        It will extract value of a specific html element from html tree `obj:lxml.html` and assign it to corresponding
        payload variable.

        Args::

        page_data (`class:lxml.html`): Represents an pre intialized instance of html tree object.
        token_list (`class:list`): List of specific element name attribute `class:str` which are gonna be extracted. 
        payload (`class:dict`): Essential data to use in request payload or request body.
        '''
        for item in token_list:
            self.attrGetter(page_data, item, payload)
        return

    @abstractmethod
    def initiater(self):
        '''
        Abstract Method to re-defined in other child class.
        It will be the main method of other class.
        '''
        pass
    

    

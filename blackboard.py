#!/usr/local/bin/python
# coding: UTF-8

'''blackboard.py

    :author:    Eduardo A. Bustamante López
    :contact:   dualbus@gmail.com
    :version:   0.9
    :copyright: none
    :abstract:  core BlackBoard client classes.
    :depends:   - Python 2.x
                - lxml
    
'''

from lxml.html import parse
from hashlib import md5
from urllib import urlencode
from urllib2 import build_opener, HTTPCookieProcessor
from urlparse import urljoin
from cookielib import CookieJar


def clean_string(string):
    '''Remove leading/trailing whitespace and encode bytes into UTF-8.'''
    
    return string.strip().encode('UTF-8', 'ignore')
    
def xp(element, xpath):
    '''Execute XPath query and return list of text elements.'''
    
    return [clean_string(e.text_content())
                for e in element.xpath(xpath)]

def xp_text_single(element, xpath):
    '''Execute XPath query and return the first text element.'''
    
    elements = element.xpath(xpath)
    if 0 < len(elements):
        return clean_string(elements[0])
    else:
        return ''
        
def xp_text_content_single(element, xpath):
    '''Execute XPath query and return the text content of the first element.'''
    
    elements = element.xpath(xpath)
    if 0 < len(elements):
        return clean_string(elements[0].text_content())
    else:
        return ''

        
        
class InvalidCredentialsException(Exception): pass


    
class Login:
    '''Login to a BlackBoard application.'''
    
    url = '/webapps/login/'
    new_loc = '/webapps/portal/frameset.jsp'
    xp_nonce = '//input[@name="one_time_token"]/@value'

    def __init__(self, base_url, user, password):
        '''`Login` constructor.
        
        Takes the base URL of the BlackBoard application, and the user/password
        pair.
        
        '''

        self._base_url = base_url
        self._user = user
        self._password = password
        self._opener = build_opener(HTTPCookieProcessor(CookieJar()))
        self._nonce = self._fetch_nonce()
        encoded_pw, encoded_pw_u = self._challenge_login(self._nonce)
        parameters = {
            'user_id': self._user,
            'password': '',
            'login': 'Iniciar sesión',
            'action': 'login',
            'remote-user': '',
            'new_loc': Login.new_loc,
            'auth_type': '',
            'one_time_token': self._nonce,
            'encoded_pw': encoded_pw,
            'encoded_pw_unicode': encoded_pw_u,
        }
        urlopen = self._opener.open
        url = urljoin(self._base_url, Login.url)
        previous_url = urlopen(url, urlencode(parameters)).url
        if url == previous_url:
            raise InvalidCredentialsException()
    
    def _fetch_nonce(self):
        '''Fetch a unique token or "nonce" from BlackBoard.
        
        BlackBoard uses a challenge login (it has other types of login, but 
        the BlackBoard I use is configured to work with the challenge), which
        requires a "nonce" or unique token, used to encode the password, 
        which disables the "Replay" attack and the need of sending the
        password.
        
        '''
        
        urlopen = self._opener.open
        fp = urlopen(urljoin(self._base_url, Login.url))
        html = parse(fp)
        return xp_text_single(html, Login.xp_nonce)

    def _challenge_login(self, token):
        '''Generate a password pair to perform a challenge login.
        
        BlackBoard's challenge login consists in the "encoding" of the
        password, using the md5 hash function, a unique token (previously
        retrieved with _fetch_nonce()) and two character set encodings.
        
        Pseudo-code for the `encoded_pw` is:
        
        pw_md5 := md5(pw)
        seed := concatenate(pw_md5, token)
        encoded_pw := md5(seed)
        
        Pseudo-code for the `encoded_pw_unicode` is:
        
        pw_unicode := encode(pw, 'UTF-16-LE')
        pw_unicode_md5 := md5(pw_unicode)
        seed_unicode := concatenate(pw_unicode_md5, token)
        encoded_pw_unicode := md5(seed_unicode)
       
        '''
        
        def d(s): return md5(s).hexdigest().upper()
        enc_p = d(self._password)
        enc_pu = d(self._password.encode('UTF-16-LE'))
        return d(enc_p + token), d((enc_pu + token).encode('UTF-16-LE'))
        
    def get_base_url(self):
        '''Getter for `base_url`.'''
    
        return self._base_url        

    def get_opener(self):
        '''Getter for `opener`.'''
    
        return self._opener.open


class Courses:
    '''Retrieve the list of enabled courses.
    
        This is just a sample class, used to demonstrate an application of the
        `Login` class. It's not meant to be used seriously.
        
    '''
    
    url = '/webapps/portal/execute/tabs/tabAction'
    qs = 'action=refreshAjaxModule&modId=_25_1&tabId=_2_1&tab_tab_group_id=_2_1'
    xp_li = '//ul[contains(@class,"courseListing")]/li'
    xp_name = 'a[1]'
    xp_prof = 'div[@class="courseInformation"]/span[@class="name"]'

    def __init__(self, login):
        '''`Courses` constructor.
        
            The `login` parameter is an instance of the `Login` class.
        
        '''
        
        self._login = login

    def get_courses(self):
        '''Getter for `courses`'''
        
        courses = {}
        base_url = self._login.get_base_url()
        urlopen = self._login.get_opener()
        fp = urlopen(urljoin(base_url, Courses.url), Courses.qs)
        html = parse(fp)
        lis = html.xpath(Courses.xp_li)
        for li in lis:
            courses[xp_text_content_single(li, 
                        Courses.xp_name)] = ' '.join(xp(li, Courses.xp_prof))
        return courses

        
if __name__ == '__main__':
    import sys
    from getpass import getpass
    base_url = 'http://cetys.blackboard.com'
    user = raw_input('User: ')
    password = getpass('Password: ')
    login = Login(base_url, user, password)
    for k, v in Courses(login).get_courses().iteritems():
        print 'Course: {0}\nProfessor: {1}'.format(k, v)

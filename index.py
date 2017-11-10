#!/usr/bin/python2.7
#Terminal command to force kill twisted-website
#kill -9 $(lsof -i:8080 -t)
__author__="Sledjama"
__date__ ="$Nov 10, 2017 10:04:55 AM$"

#import useful modules, comment out unused to make twisted more lightweight
from twisted.enterprise import adbapi
import MySQLdb, os
from twisted.web.resource import Resource
from twisted.python import log
from twisted.internet import ssl, reactor, task,  threads
from twisted.web.server import Site, Session
from twisted.web.static import File
import twisted.web.error as error
from twisted.web.template import Element, XMLString, renderer, XMLFile, flatten
from twisted.python.filepath import FilePath
from jinja2 import Environment, PackageLoader, FileSystemLoader
from twisted.web.client import getPage #helper to call remote path asynchronously
from email.mime.text import MIMEText
from twisted.mail.smtp import sendmail #helper to send email asynchronously

from zope.interface import Interface, Attribute, implements
from twisted.python.components import registerAdapter


site_root=os.path.join("\python_projects","twisted-website")
log_path=os.path.join(site_root, "logs", "requests.txt")
template_path=os.path.join(site_root,"templates")
public_path = os.path.join(site_root,"public")
jinja_extensions=['jinja2.ext.autoescape']
server_port=8080

print(public_path)
public_resource=File(public_path)


#database params
db_module = "MySQLdb"
db="sms"
database_user="root"
database_password=""
database_host="localhost"
database_port="3306"


#lets use twisted's asynchronous approach
dbpool = adbapi.ConnectionPool(db_module, database=db, user=database_user, password=database_password, host=database_host, port=database_port)#

#define functions to use within html templates e.g
curr = lambda amount, currency: "%s%s%s" %("-" if amount < 0 else "",currency,('{:%d,.2f}'%(len(str(amount))+3)).format(abs(amount)).lstrip())

#Define sessions (optional)
class IAPIsessions(Interface):
    value = Attribute("A dict which stores session info of a user.")

class APIsessions(object):
    implements(IAPIsessions)
    def __init__(self, session):
        self.value = dict()

registerAdapter(APIsessions, Session, IAPIsessions)



#convenient functions to serve pages site-wide
def serve_page(request, page='index.html', data="", session=""):
    env= Environment(loader=FileSystemLoader(template_path),extensions=jinja_extensions,autoescape=True)
    env.globals['converter'] = curr #make function available in template
    template = env.get_template(page)
    return str(template.render(session=session, data=data ))


#incase your website has to API to open to the public
class APIserver(Resource):
    isLeaf=True

    def render_GET(self, request):
        return "API GET server working\n"

    def render_POST(self, request):
        return "API POST server working\n"


class WebsiteServer(Resource):
    """This is the HTTP website server  which is a Resource object"""
    isLeaf = False

    def getChild(self, name, request):
        if name == '':
            self.isLeaf = True
            return self
        return Resource.getChild(self, name, request)

    def render_GET(self, request):
        #initialize session first (optional)
        session = request.getSession()
        api_session = IAPIsessions(session)

        #if GET request contains logout, i.e http://yoursite.com:8080/?logout=1
        if "logout" in request.args and request.args['logout']=='1':
            session.expire() #nice way to logout
            return serve_page(request)
        elif 'signup' in request.args:
            serve_page(request,  session=api_session.value)
        else:
            return serve_page(request)

    def render_POST(self, request):
        return serve_page(request)




# Build the server factory
root=WebsiteServer()
root.putChild("api",APIserver())
root.putChild("public",public_resource)
factory = Site(root)

#if logging is needed
log.startLogging(open(log_path, 'w'))

#map port to factory
reactor.listenTCP(server_port, factory)
print "Server running on port "+str(server_port)

#start the reactor
reactor.run()
exit()



"""Site Bootstrap template gotten from https://startbootstrap.com/template-overviews/freelancer/
"""

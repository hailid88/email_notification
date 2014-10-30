__author__ = 'hailid'
##this python script is used to parse the status of the hosts in nagios every week and automatically generate the report in table format. 

from re import sub
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import urllib2, base64
import time, datetime
from datetime import datetime
from HTMLParser import HTMLParser
from sys import stderr
from traceback import print_exc
import csv



##this Parser is used to transform HTML into simple text by removing all the tags. 
class _DeHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.__text = []

    def handle_data(self, data):
        text = data.strip()
        if len(text) > 0:
            text = sub('[ \t\r\n]+', ' ', text)
            self.__text.append(text + ' ')

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.__text.append('\n\n')
        elif tag == 'br':
            self.__text.append('\n')

    def handle_startendtag(self, tag, attrs):
        if tag == 'br':
            self.__text.append('\n\n')

    def text(self):
        return ''.join(self.__text).strip()


def dehtml(text):
    try:
        parser = _DeHTMLParser()
        parser.feed(text)
        parser.close()
        return parser.text()
    except:
        print_exc(file=stderr)
        return text


def send_email():
    gmail_user = "****@gmail.com"   #if you want to use gmail to send the email, specify your email address. 
    gmail_pwd = "****"              #specify your gmail password. 
    username = "nagiosadmin"        #specify the nagios website's username, by default is is nagiosadmin 
    password = "****"               #the password of nagios website. 
    url_address = "http://(IP_address)/nagios/cgi-bin/outages.cgi"            #the url which shows the status of the hosts, add the IP_address where Nagios is installed. 
    
    #url_address = "file:///C:/Users/Helli/Desktop/Network%20Outages.htm"      #test case. 

    FROM = 'no_reply@**.dc.gov'                                          
    #FROM = 'dhldxy@gmail.com'
   
    TO = ['dhldxy@gmail.com', 'hailid88@gmail.com']     #must be a list.. if you have any question, you can contact me via these two emails. 
    SUBJECT = "Weekly Nagios Report"

    # request html file
    request = urllib2.Request(url_address)
    base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)
    response = urllib2.urlopen(request)
    html = response.read()
    deResult =  dehtml(html)

    ##deResult_content includes the table data. 
    deResult_content = deResult.split("Actions ",1)[1]

    ##the format of nagios table information, two columns are appended: IP address and Location. 
    table_info = '''<TABLE cellpadding="4" style="border: 1px solid #000000; border-collapse: collapse;" border="1">
                  <TR>  
                    <TH>Severity</TH>  
                    <TH>Host</TH>  
                    <TH>State</TH>
                    <TH>Notes</TH>
                    <TH>Duration</TH>
                    <TH># Hosts Affected</TH>
                    <TH># Services Affected</TH>
                    <TH>IP address</TH>
                    <TH>Location</TH>
                  </TR>'''

    items = deResult_content.split(" ");
    rowNum = len(items)/10

    rowCount = 0

    
    #based on host_name to get the IP address and Location Information.
    
    resultIP={}
    try:
        #three columns in csv file: host_name, IP. 
      reader = csv.reader(open('C:/Users/Helli/Documents/Visual Studio 2010/Projects/SendReport/SendReport/hostIP.csv', 'rb'))
      resultIP = dict(x for x in reader)    #note: Everything turned to be string after reading from csv
      print "hostIP.csv found, to get the IP address of each host."
    except:
      print "hostIP.csv not found.IP address could not be added."

    
    resultLocation={}
    try:
        #two columns in txt file: ACISA, Location.
        reader = csv.reader(open('C:/Users/Helli/Documents/Visual Studio 2010/Projects/SendReport/SendReport/acisaLocation.txt', 'rb'), delimiter='\t')
        resultLocation = dict(x for x in reader)    #note: Everything turned to be string after reading from csv
        print "acisaLocation.txt found, to get the location of each ACISA."
    except:
        print "acisaLocation.txt not found. Location could not be added."


    for currentRow in range(0, rowNum):
        duaration = items[10*currentRow+4:10*currentRow+8]
        duration= ''.join(duaration)
        host_name = str(items[10*currentRow+1])
        #then parse the host_name to get the ACISA number. 
        host_name_items = host_name.split("_");
        if(len(host_name_items)==3 and len(host_name_items[1])==4):
            ACISA = host_name_items[1]
            try:
                location = resultLocation[ACISA]
            except:
                location = '0'
        else:
            location = '0'

        try:
            IPaddress = resultIP[host_name]
        except:
            IPaddress = '0'

        
        table_info = table_info + ' <TR><TH>' + str(items[10*currentRow]) + '</TH><TH>' + host_name + \
            '</TH><TH>' + str(items[10*currentRow+2]) + '</TH><TH>' + str(items[10*currentRow+3]) + \
            '</TH><TH>' + str(duration) + '</TH><TH>' + str(items[10*currentRow+8]) + '</TH><TH>' + str(items[10*currentRow+9]) + \
            '</TH><TH>' + IPaddress + '</TH><TH>' + location + '</TH></TR>'
    

    table_info = table_info + '</TABLE>'
    
    appendURL = "You can see more detailed information by Clicking http://10.41.20.219/nagios/cgi-bin/outages.cgi"
    table_info = table_info + '<p>' + appendURL + '</p>'    
    
    

    # prepare message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = SUBJECT
    msg['From'] = FROM
    str_to = ''
    for to in TO:
        if(str_to != ''):
            str_to += ',' + to
        else:
            str_to = to
    msg['To'] = str_to

    nagiosTable = MIMEText(table_info, 'html')


    msg.attach(nagiosTable)
    
    
    try:

        '''
        ##Following is for ddot domain. 
        server="****.dc.gov"                      
        smtp = smtplib.SMTP(server)
        smtp.sendmail(FROM, TO, msg.as_string())
        smtp.close()
        '''

        ##The mail is sent via gmail.
        server = smtplib.SMTP("smtp.gmail.com", 587) #or port 465 doesn't seem to work!
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(FROM, TO, msg.as_string())
        server.close()
        print 'successfully sent the mail'
    except Exception as e:
        print "failed to send mail \n\n\n"
        print e



def main():
    interval_check = 12*3600  # check every 12 hours, so that no timer is needed. 
    #send_email()
    condition = True
    while(condition):
        try:
            time.sleep(interval_check)
            datetime_now = datetime.now()
            if(datetime_now.day == 1 or datetime_now.day==8 or datetime_now.day ==15 or datetime_now.day ==22 or datetime_now.day ==29):  # send email every week
                send_email()
                pass
            pass
        except Exception as e:
            print e
            condition = False

if __name__ =='__main__':
   main()

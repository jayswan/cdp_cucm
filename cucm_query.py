from getpass import getpass
from lxml import etree
from lxml.etree import tostring
import requests
import re
import sys

"""
cucm_query.py

The primary use of this script is to provide an interface by which to pull
device descriptions from Cisco Unified Communications Manager, based on the 
device name.

This allows the companion script (cdp_cucm.py) to configure a switch's
interface descriptions based on the attached phone's description field.

A secondary use of the script is to interactively query CUCM via
the SOAP XML API, and to provide an example of doing this via the Python
requests module.
"""
soap_nsuri = 'http://schemas.xmlsoap.org/soap/envelope/'
soap_ns = '{%s}' % soap_nsuri
soap_axuri = 'http://www.cisco.com/AXL/API/8.5'
soap_axns = '{%s}' % soap_axuri
soap_nsmap = {'soapenv' : soap_nsuri}
soap_sqlnsmap = {'ns' : soap_axuri}
soap_env = etree.Element(soap_ns+'Envelope', nsmap=soap_nsmap)
soap_h = etree.SubElement(soap_env, soap_ns+'Header')
soap_b = etree.SubElement(soap_env, soap_ns+'Body')
soap_sql = etree.SubElement(soap_b, soap_axns+'executeSQLQuery', nsmap=soap_sqlnsmap)
sql_e = etree.SubElement(soap_sql, 'sql')

# HTTP headers requried by SOAP API
header = {
          'Content-type' : 'text/xml',
          'SOAPAction' : 'CUCM:DB ver=8.5',
         }

def run_sql(cmserver,username,password,sql,cmport='8443'):
    """ run arbitrary SQL command via CUCM XML API, return XML result"""

    url = 'https://%s:%s/axl/' % (cmserver,cmport)
    sql_e.text = sql
    msg = etree.tostring(soap_env, pretty_print=True)
    
    r = requests.post(url,headers=header,data=msg,verify=False,auth=(username,password))

    if r.status_code == 200:
        # print raw result without parsing XML
        print r.text
        sys.exit()
    else:
        print r.status_code
        print r.headers
        print r.text
        sys.exit()

def get_description_by_name(cmserver,username,password,device,cmport='8443'):
    """ return CUCM device description given its CUCM name"""

    url = 'https://%s:%s/axl/' % (cmserver,cmport)


    sql = "<sql>select description from device where name = '%s'</sql>" % device.upper()
    sql_e = sql
    msg = etree.tostring(soap_env, pretty_print=True)
    
    # change verify=TRUE if you want to check the CUCM SSL certificate
    r = requests.post(url,headers=header,data=msg,verify=False,auth=(username,password))

    if r.status_code == requests.codes.ok:
        # couldn't figure out how to parse SOAP response w/o regex...
        try:
            m = re.search('<description>(.*?)</description>',r.text)
            return m.group(1)
        except:
            print "regex match of description failed: "
            print 'device %s' % device
            print 
            print msg
            print r.text
            sys.exit()
    else:
        print 'got bad status code:'
        print r.status_code
        print r.headers
        print r.text
        sys.exit()

def get_descriptions_from_list(cmserver,cmuser,cmpass,device_list):
    """ given a list of devices, return a dict of their descriptions """

    phone_descriptions = {}
    for device in device_list:
        phone_descriptions[device] = get_description_by_name(cmserver,cmuser,cmpass,device)

    return phone_descriptions

def main():
    global soap_env, sql_e
    """ If called as the main script, accept options and print results """
    import pprint
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('--cmserver',dest='cmserver',help='IP of CUCM Server')
    parser.add_option('--cmuser',dest='username',help='CUCM username')
    parser.add_option('--cmpass',dest='cmpass',help='CUCM password; leave out this opt to be prompted')
    parser.add_option('--devname',dest='devname',help='device name')
    parser.add_option('--sql',dest='sql',help='text of SQL query (unparsed output)')

    (options,args) = parser.parse_args()

    # if user leaves out CUCM password, prompt for it
    # this keeps password from showing in shell history, but we don't mask it during input
    if options.cmpass:
        cmpass = options.cmpass
    else:
        cmpass = getpass('enter CUCM password: ')

    if not options.sql:
        pprint.pprint(get_description_by_name(options.cmserver,options.username,cmpass,options.devname))
    else:
        run_sql(options.cmserver,options.username,cmpass,options.sql)

if __name__ == '__main__':
    main()

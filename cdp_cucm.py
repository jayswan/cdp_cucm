from getpass import getpass
import requests
import re
import sys
import cucm_query

"""
cdp_cucm.py

This script queries a Cisco switch for its CDP neighbor table and extracts
the device names of the attached IP phones.

It then uses the companion module cucm_query.py to query the CUCM database
via its XML SOAP API for the descriptions of those phones.

Finally, it either:

    a) interactively prints an interface configuration for the switch that 
       uses the description field as an interface description (suitable for
       copy and paste), or
    b) configures the switch with those interface descriptions via the switch
       HTTPS interface.

Thus, if a phone's description in the CUCM database is "Alice's Phone", the
new interface configuration would be:

    interface {type/number}
      description Alice's Phone

You need to set up your switch to allow configuration via the HTTPS interface,
through whatever authentication mechanism your switch uses (TACACS+, etc.).

This has been tested only on reasonably recent versions of IOS for 
Catalyst 3560/3750 switches and CUCM 8.6.
"""

# dict used to expand abbreviations from CDP table into full names for configuration
NAME_EXPANSIONS = {
        'Fas' : 'FastEthernet',
        'Gig' : 'GigabitEthernet',
        }

def build_description_url(int_type,int_num,description):
    """ build part of URL used to access interface config """

    int_type = NAME_EXPANSIONS[int_type]
    int_num = int_num.replace('/','\/')
    description = re.sub('\s+','/',description)
    url = '/level/15/interface/%s%s/-/description/%s' % (int_type,int_num,description)
    return url

def configure_interface_desc(switch_ip,int_type,int_num,description,username,password):
    """ configure interface description """
    base_url = build_description_url(int_type,int_num,description)
    full_url = 'https://%s%s' % (switch_ip,base_url)
    r = requests.get(full_url, verify=False,auth=(username,password))
    
    # this will catch only HTTP errors, not errors returned in HTML pages
    if r.status_code == 200:
        return True
    else:
        return False
    
def get_phone_info(switch,username,password):
    """ get phone device names and neighbor interfaces from switch CDP table """
    r = requests.get('https://%s/level/15/exec/-/show/cdp/neighbors/|/include/^SEP/CR' % switch, verify=False,auth=(username,password))

    items = re.findall('(SEP............)\s+(\S+)\s+(\S+)',r.text)

    phones_ints = {}
    for (name,int_type,num) in items:
        phones_ints[name] = '%s %s' % (int_type,num)

    return phones_ints

def main():
    from optparse import OptionParser
    parser = OptionParser()

    parser.add_option('--switch',dest='switch',help='IP address of switch')
    parser.add_option('--user',dest='username',help='username for switch')
    parser.add_option('--password',dest='password',help='password for switch; omit option for interactive prompt')

    parser.add_option('--cmserver',dest='cmserver',help='IP of CUCM Server')
    parser.add_option('--cmuser',dest='cmuser',help='CUCM username')
    parser.add_option('--cmpass',dest='cmpass',help='CUCM password; omit option for interactive prompt')

    parser.add_option('--auto',dest='auto',action='store_true',help='autoconfigure interface descriptions (requires config privilege on switch)')

    (options,args) = parser.parse_args()

    # if user omits password option, prompt interactively
    # this hides password from screen and from shell history
    if options.password:
        password = options.password
    else:
        password = getpass('enter switch password: ')

    if options.cmpass:
        cmpass = options.cmpass
    else:
        cmpass = getpass('enter CUCM password: ')

    phone_neighbor_data = get_phone_info(options.switch,options.username,password)

    device_names = phone_neighbor_data.keys()

    phone_descriptions = cucm_query.get_descriptions_from_list(options.cmserver,options.cmuser,cmpass,device_names)
    
    for phone, interface in phone_neighbor_data.items():
        if options.auto:
            try:
                (int_type,int_num) = interface.split()
                print "configuring %s" % interface
                print configure_interface_desc(options.switch,int_type,int_num,phone_descriptions[phone],options.username,password)
            except Exception as e:
                print Exception,e
                sys.exit()
        else:
            try:
                print 'interface %s\n  description phone - %s' % (interface,phone_descriptions[phone])
            except KeyError:
                continue

if __name__ == '__main__':
    main()

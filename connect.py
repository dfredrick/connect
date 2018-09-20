__author__ = 'dazfre'
import time
import pexpect

run_time = time.strftime("%Y%m%d-%H%M%S")
connection_error_filename = 'connection_errors_' + run_time + '.txt'
error_filename = 'errors_' + run_time + '.txt'

prompt_last_chars = ['>', '#']

ssh_newkey = '(?i)are you sure you want to continue connecting'

auth_fail = 'Command authorization failed.'

save_filename = 'Destination filename \[startup-config\]?'
save_done = '[OK]'


def normal(username, password, hostname, telnet_fallback=True):
    '''
    Make a communication session to a device.

    The object's hostname, username, and password will be used to attempt and ssh session to the device.
    If telnet_fallback is True then a telnet session will be attempted if the ssh session fails.

    state = String representing the current cli mode
    self.pexpect_child = pexpect object for communicating with the device
    self.prompt = String to expect when sending commands to the device
    '''

    ssh = 'n/a'


    #Try SSH
    child = pexpect.spawn('ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ' + username + '@' + hostname)
    # child.logfile_read = sys.stdout
    #child = pexpect.spawn('ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o UserKnownHostsFile=/dev/null ' + username + '@' + hostname)

    output = child.expect(['[P|p]assword:', ssh_newkey, 'Connection refused', pexpect.EOF, 'nodename', pexpect.TIMEOUT])
    ssh = 'yes'
    if output == 5 and telnet_fallback == False:
        raise Exception('NotResponding')


    if output == 4:
        raise Exception('NotinDNS')


    #If we get the ssh new key message, send 'yes', if SSH fails, try telnet
    if output == 1:
        ssh = 'yes'
        child.sendline('yes')
        output = child.expect(['[P|p]assword:', ssh_newkey])
        if output != 0:
            raise Exception('Problem with ssh key trying to normal to {device}'.format(device=hostname))

    elif output > 1:
        if not telnet_fallback:
            raise Exception('Unable to make an ssh connection to {device}'.format(device=hostname))
        child = pexpect.spawn('telnet {device}'.format(device=hostname))
        ssh = 'no'
        output = child.expect(['[U|u]sername:',pexpect.TIMEOUT])
        if output == 0:
            child.sendline(username)
        elif output == 1:
            raise Exception('NotResponding')
        output = child.expect(['[P|p]assword:', '[U|u]sername:'])
        if output == 1:
            raise Exception('Problem with credentials trying to normal to {device}'.format(device=hostname))


    child.sendline(password)


    #If the password fails, we won't see one of the prompt characters, so throw an exception
    output = child.expect(prompt_last_chars + ['[P|p]assword:'])

    if output == len(prompt_last_chars):
        raise Exception('BadPassword')

# Test for JUNOS
    if "JUNOS" in child.before:
        prompt = child.before.split('\n')[-1] + prompt_last_chars[output]
        state = 'Enable'
        OStype = 'JUNOS'
        return (child,prompt,state, OStype, ssh)
    # Test for HP OS
    elif "HP" in child.before:
        child.expect('->')
        prompt = "->"
        state = 'Enable'
        OStype = 'HP'
        return (child,prompt,state, OStype, ssh)

    elif "NX-OS" in child.before:
        OStype = 'NXOS'
        state = 'Enable'
        prompt = child.before.split()[-1] + prompt_last_chars[output]
        return (child,prompt,state, OStype, ssh)

    state = 'Enable' if output else 'Connected'

    # If we're not in enable mode, get to enable mode
    if state == 'Connected':
      child.sendline('enable')
      output = child.expect(['[P|p]assword:',pexpect.EOF])
      if output == 1:
        raise Exception('Problem with credentials trying to enable {device}'.format(device=hostname))
      child.sendline(password)
      output = child.expect(prompt_last_chars)
      state == 'Enable'


    prompt = child.before.split()[-1] + prompt_last_chars[output]
    try:
        child.sendline('term pager 0')
        child.expect(prompt)
        if '^' in child.before:
            child.sendline('term len 0')
            child.expect(prompt)
            child.sendline('show version')
            child.expect(prompt)
            if 'IOS' in child.before:
                OStype = "IOS"
                return (child, prompt, state, OStype, ssh)
        else:
            child.sendline('show version')
            child.expect(prompt)
            if 'ASA' in child.before:
                OStype = 'ASA'
                return (child, prompt, state, OStype, ssh)
            else:
                OStype = 'Unknown'
                return (child, prompt, state, OStype, ssh)

    except:
        raise Exception('Problem running "show version" on {device}'.format(device=hostname))



def line(linepw, enablepw, hostname, telnet_fallback=True):
    '''
    Make a communication session to a device.

    The object's hostname, username, and password will be used to attempt and ssh session to the device.
    If telnet_fallback is True then a telnet session will be attempted if the ssh session fails.

    state = String representing the current cli mode
    self.pexpect_child = pexpect object for communicating with the device
    self.prompt = String to expect when sending commands to the device
    '''


    connection_error_file = open(connection_error_filename,'a')


    #Try SSH
    child = pexpect.spawn('ssh doesntmatter@' + hostname)

    output = child.expect(['[P|p]assword:', ssh_newkey, 'Connection refused', pexpect.EOF, 'nodename', pexpect.TIMEOUT])

    if output == 5:
        connection_error_file.write(hostname + ' not responding\n')
        raise Exception('NotResponding')
        return None

    if output == 4:
        connection_error_file.write(hostname + ' failed due to DNS lookup issue\n')
        raise Exception('NotinDNS')
        return None

    #If we get the ssh new key message, send 'yes', if SSH fails, try telnet
    if output == 1:
        child.sendline('yes')
        output = child.expect(['[P|p]assword:', ssh_newkey])
        if output != 0:
            #raise Exception('Problem with ssh key trying to normal to {device}'.format(device=hostname))
            print('Problem with ssh key trying to normal to {device}'.format(device=hostname))
            connection_error_file.write('{device} failed due to ssh key\n'.format(device=hostname))
            return None

    elif output > 1:
        if not telnet_fallback:
            raise Exception('Unable to make an ssh connection to {device}'.format(device=hostname))
        child = pexpect.spawn('telnet {device}'.format(device=hostname))
        output = child.expect(['[P|p]assword:', '[U|u]sername:'])
        if output == 0:
            child.sendline(linepw)




    #If the password fails, we won't see one of the prompt characters, so throw an exception
    output = child.expect(prompt_last_chars + ['[P|p]assword:'])

    if output == len(prompt_last_chars):

        #print('Incorrect password trying to normal to {device}'.format(device=hostname))
        connection_error_file.write(hostname + ' failed due to credentials in ssh\n')
        raise Exception('BadPassword')
        return None
# Test for JUNOS

    print child.before
    if "JUNOS" in child.before:
        prompt = child.before.split('\n')[-1] + prompt_last_chars[output]
        state = 'Enable'
        OStype = 'JUNOS'
        return (child,prompt,state, OStype)
    # Test for HP OS
    elif "HP" in child.before:
        child.expect('->')
        prompt = "->"
        state = 'Enable'
        OStype = 'HP'
        return (child,prompt,state, OStype)
    elif "NX-OS" in child.before:

        OStype = 'NXOS'


    state = 'Enable' if output else 'Connected'

    # If we're not in enable mode, get to enable mode
    if state == 'Connected':
      child.sendline('enable')
      output = child.expect(['[P|p]assword:',pexpect.EOF])
      if output == 1:
        raise Exception('Problem with credentials trying to enable {device}'.format(device=hostname))
      child.sendline(enablepw)
      output = child.expect(prompt_last_chars)
      state == 'Enable'

    connection_error_file.close()

    prompt = child.before.split()[-1] + prompt_last_chars[output]
    if OStype == 'NXOS':
        return (child,prompt,state, OStype)
    else:
        OStype = "IOS"
        return (child,prompt,state, OStype)


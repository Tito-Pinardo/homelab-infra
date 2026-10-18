#!/usr/bin/python3
import pathlib,subprocess,stat,sys,xml.etree.ElementTree as E
    ...
def secure(p,mask):
    ...
def ssh():
    ...
    ...
def auth():
    ...
def limits():
    ...
def macs():
    ...
def remote_commands():
    ...
checks={
 'shadowed':lambda:all(l.split(':')[1]=='x' for l in text('/etc/passwd').splitlines()),
 'empty_passwords':lambda:not any(l.split(':')[1]=='' for l in text('/etc/shadow').splitlines()),
 'uid0':lambda:[l.split(':')[0] for l in text('/etc/passwd').splitlines() if l.split(':')[2]=='0']==['root'],
 'gid0':lambda:[l.split(':')[0] for l in text('/etc/group').splitlines() if l.split(':')[2]=='0']==['root'],
 'shadow_permissions':lambda:secure('/etc/shadow',0o027),
 'ssh_permissions':lambda:secure('/etc/ssh/sshd_config',0o077),
 'cron_permissions':lambda:secure('/etc/crontab',0o077) and all(secure('/etc/cron.'+x,0o077) for x in ['d','hourly','daily','weekly','monthly']),
 'pam_nullok':lambda:not any('nullok' in l.split() for p in pathlib.Path('/etc/pam.d').glob('common-*') for l in p.read_text().splitlines() if not l.lstrip().startswith('#')),
 'ssh_auth':auth,'ssh_limits':limits,'ssh_macs':macs,
 'active_response':lambda:bool(xml().findall('.//active-response')) and all(x.findtext('disabled')=='yes' for x in xml().findall('.//active-response')),
 'remote_commands':remote_commands,
 'fim':lambda:xml().find('.//syscheck') is not None and xml().findtext('.//syscheck/disabled')!='yes' and all(x.get('report_changes','no')=='no' for x in xml().findall('.//syscheck/directories')),
}
try:print('PASS' if checks[sys.argv[1]]() else 'FAIL')
except Exception:print('ERROR: no verificado');sys.exit(1)

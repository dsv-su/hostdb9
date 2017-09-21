# coding=utf-8

import sys

def read(client, tld):
    cname_dict = {}
    for cname in client.list_cnames(tld):
        alias = cname['name']
        canonical = cname['canonical']
        if canonical not in cname_dict:
            cname_dict[canonical] = []
        cname_dict[canonical].append(alias)
    lines = []
    for vlan in client.list_vlans():
        net = vlan['network']
        lines.append('')
        lines.append('network\t' + net)
        for ip in client.list_vlan_ips(net):
            addr = ip['ip_address']
            lines.append('')
            lines.append('host\t' + addr)
            names = ip['names']
            name = ''
            if len(names) > 0:
                name = names[0]
                if len(names) > 1:
                    print('Warning! Ignoring additional names for ' + addr, file=sys.stderr)
            if name:
                lines.append('name\t' + name)
                (comment, aliases) = client.get_host_info(name)
                if comment:
                    lines.append('comment\t' + comment)
                for alias in aliases:
                    lines.append('alias\t' + alias)
            mac = ip['mac_address']
            if mac:
                lines.append('mac\t' + mac)
    for canonical, aliases in cname_dict.items():
        for alias in aliases:
            lines.append('')
            lines.append('cname\t' + alias)
            lines.append('target\t' + canonical)
    return lines

# coding=utf-8

def read(client, print_warnings):
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
                if len(names) > 1 and print_warnings:
                    print('Warning! Ignoring additional names for ' + addr)
            if name:
                lines.append('name\t' + name)
                (comment, aliases) = client.get_host_info(name)
                if comment:
                    lines.append('comment\t' + comment)
                for alias in aliases:
                    lines.append('alias\t' + alias)
            mac = ip['mac_address']
            if mac and not name.startswith('dhcp'):
                lines.append('mac\t' + mac)
    for cname in client.list_cnames():
        lines.append('')
        lines.append('cname\t' + cname['name'])
        lines.append('target\t' + cname['canonical'])
    return lines

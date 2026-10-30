import math
import re
from ansible.errors import AnsibleFilterError

millnames = ['','k','M','G','T', 'P']

def unhuman(s):
    # return a number from a human readable number
    # like 1k would be 1000
    try:
        upper_millnames = [n.upper() for n in millnames]
        match = re.match(r"([0-9.]+)\s*([a-z]+)?",s, re.I)
        digits = match.group(1)
        factors = match.group(2)
        index = 0
        if factors:
            for factor in factors:
                index += upper_millnames.index(factor.upper())
        return round(float(digits) * 2**(index*10))
    except Exception as err:
        return 'ERROR: Cannot unhuman {}: {}'.format(s, err)
    
def human(n, digits=0):
    # return a human readable string
    # like 1000 would be 1k
    n = float(n)
    i = 0
    while n >= 1024:
        i += 1
        n = n / 1024
    return '{0:.{1}f}{2}'.format(n, digits, millnames[i])

def percent(n, f=100, minimum=0, digits=0):
    result = float(n) * float(f) / 100
    if result < float(minimum):
        return minimum
    return '{0:.{1}f}'.format(result, digits)

def nagios_stolon_clusters(clusters):
    """Translate Stolon definitions into named local monitoring targets."""
    if not isinstance(clusters, dict):
        raise AnsibleFilterError("stolon_clusters must be a dictionary")
    targets = {}
    for name, cluster in clusters.items():
        try:
            port = cluster["sysconfig"]["stkeeper"]["pg_port"]
        except (KeyError, TypeError):
            raise AnsibleFilterError(
                "Stolon cluster {!r} must define sysconfig.stkeeper.pg_port".format(name)
            )
        targets[name] = {
            "service": "{}-master".format(name),
            "port": port,
            "ssl_mode": "verify-full",
        }
    return targets


class FilterModule(object):
    def filters(self):
        return {
            'nagios_stolon_clusters': nagios_stolon_clusters,
            'human': human,
            'unhuman': unhuman,
            'percent': percent
        }

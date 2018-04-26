# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info', 'passgate.yaml'))


# noinspection PyPep8Naming
class bag_digital_ec__passgate(Module):
    """Module for library bag_digital_ec cell passgate.

    Fill in high level description here.
    """

    def __init__(self, bag_config, parent=None, prj=None, **kwargs):
        Module.__init__(self, bag_config, yaml_file, parent=parent, prj=prj, **kwargs)

    @classmethod
    def get_params_info(cls):
        # type: () -> Dict[str, str]
        return dict(
            lch='channel length.',
            wp='PMOS width.',
            wn='NMOS width.',
            thp='PMOS threshold.',
            thn='NMOS threshold.',
            segp='PMOS segments.',
            segn='NMOS segments.',
        )

    def design(self, lch, wp, wn, thp, thn, segp, segn):
        self.instances['XP'].design(w=wp, l=lch, nf=segp, intent=thp)
        self.instances['XN'].design(w=wn, l=lch, nf=segn, intent=thn)

# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info', 'dff_ck2.yaml'))


# noinspection PyPep8Naming
class bag_digital_ec__dff_ck2(Module):
    """Module for library bag_digital_ec cell dff_ck2.

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
            seg_m='Master latch segments dictionary.',
            seg_s='Slave latch segments dictionary.',
        )

    def design(self, lch, wp, wn, thp, thn, seg_m, seg_s):
        self.instances['XM'].design(lch=lch, wp=wp, wn=wn, thp=thp, thn=thn, seg_dict=seg_m)
        self.instances['XS'].design(lch=lch, wp=wp, wn=wn, thp=thp, thn=thn, seg_dict=seg_s)

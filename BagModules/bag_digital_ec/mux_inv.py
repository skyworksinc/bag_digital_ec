# -*- coding: utf-8 -*-

from typing import Dict, Any

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info', 'mux_inv.yaml'))


# noinspection PyPep8Naming
class bag_digital_ec__mux_inv(Module):
    """Module for library bag_digital_ec cell mux_inv.

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
            seg_dict='Segments dictionary.',
        )

    @classmethod
    def get_default_param_values(cls):
        # type: () -> Dict[str, Any]
        return {}

    def design(self, lch, wp, wn, thp, thn, seg_dict):
        pt0 = seg_dict['pt0']
        nt0 = seg_dict['nt0']
        segp = seg_dict['pinv']
        segn = seg_dict['ninv']
        self.instances['XT0'].design(lch=lch, wp=wp, wn=wn, thp=thp, thn=thn, segp=pt0, segn=nt0)
        self.instances['XT1'].design(lch=lch, wp=wp, wn=wn, thp=thp, thn=thn, segp=pt0, segn=nt0)
        self.instances['XINV'].design(lch=lch, wp=wp, wn=wn, thp=thp, thn=thn, segp=segp, segn=segn)

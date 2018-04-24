# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info',
                                                                   'latch_ck2.yaml'))


# noinspection PyPep8Naming
class bag_digital_ec__latch_ck2(Module):
    """Module for library bag_digital_ec cell latch_ck2.

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

    def design(self, lch, wp, wn, thp, thn, seg_dict):
        self.instances['XTBUF'].design(lch=lch, wp=wp, wn=wn, thp=thp, thn=thn,
                                       segp=seg_dict['pt0'], segn=seg_dict['nt0'])
        self.instances['XTFB'].design(lch=lch, wp=wp, wn=wn, thp=thp, thn=thn,
                                      segp=seg_dict['pt1'], segn=seg_dict['nt1'])
        self.instances['XBUF'].design(lch=lch, wp=wp, wn=wn, thp=thp, thn=thn,
                                      segp=seg_dict['pinv'], segn=seg_dict['ninv'])

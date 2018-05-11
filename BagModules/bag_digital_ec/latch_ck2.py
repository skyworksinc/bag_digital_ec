# -*- coding: utf-8 -*-

from typing import Dict, Any

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
            pass_zero='True to allow a 0 input to pass straight through.',
        )

    @classmethod
    def get_default_param_values(cls):
        # type: () -> Dict[str, Any]
        return dict(
            pass_zero=False,
        )

    def get_master_basename(self):
        # type: () -> str
        if self.params['pass_zero']:
            return 'latch_ck2_pass0'
        else:
            return 'latch_ck2'

    def design(self, lch, wp, wn, thp, thn, seg_dict, pass_zero):
        self.instances['XTBUF'].design(lch=lch, wp=wp, wn=wn, thp=thp, thn=thn,
                                       segp=seg_dict['pt0'], segn=seg_dict['nt0'],
                                       pmos_switch=not pass_zero)
        self.instances['XTFB'].design(lch=lch, wp=wp, wn=wn, thp=thp, thn=thn,
                                      segp=seg_dict['pt1'], segn=seg_dict['nt1'],
                                      pmos_switch=True)
        self.instances['XBUF'].design(lch=lch, wp=wp, wn=wn, thp=thp, thn=thn,
                                      segp=seg_dict['pinv'], segn=seg_dict['ninv'])

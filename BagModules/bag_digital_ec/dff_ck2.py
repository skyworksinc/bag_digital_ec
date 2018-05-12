# -*- coding: utf-8 -*-

from typing import Dict, Any

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
            pass_zero='True to allow a 0 input to pass straight through.',
            wpen='PMOS enable width.',
            wnen='NMOS enable width.',
            thpen='PMOS enable threshold.',
            thnen='NMOS enable threshold.',
        )

    @classmethod
    def get_default_param_values(cls):
        # type: () -> Dict[str, Any]
        return dict(
            pass_zero=False,
            wpen=None,
            wnen=None,
            thpen=None,
            thnen=None,
        )

    def get_master_basename(self):
        # type: () -> str
        if self.params['pass_zero']:
            return 'dff_ck2_pass0'
        else:
            return 'dff_ck2'

    def design(self, lch, wp, wn, thp, thn, seg_m, seg_s, pass_zero, wpen, wnen, thpen, thnen):
        self.instances['XM'].design(lch=lch, wp=wp, wn=wn, thp=thp, thn=thn, seg_dict=seg_m,
                                    pass_zero=pass_zero, wpen=wpen, wnen=wnen, thpen=thpen,
                                    thnen=thnen)
        self.instances['XS'].design(lch=lch, wp=wp, wn=wn, thp=thp, thn=thn, seg_dict=seg_s,
                                    pass_zero=pass_zero, wpen=wpen, wnen=wnen, thpen=thpen,
                                    thnen=thnen)

# -*- coding: utf-8 -*-

from typing import Dict, Any

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info',
                                                                   'inv_chain.yaml'))


# noinspection PyPep8Naming
class bag_digital_ec__inv_chain(Module):
    """Module for library bag_digital_ec cell inv_chain.

    Fill in high level description here.
    """

    def __init__(self, bag_config, parent=None, prj=None, **kwargs):
        Module.__init__(self, bag_config, yaml_file, parent=parent, prj=prj, **kwargs)

    @classmethod
    def get_params_info(cls):
        # type: () -> Dict[str, str]
        return dict(
            lch='channel length.',
            wp_list='PMOS widths.',
            wn_list='NMOS widths.',
            thp='PMOS threshold.',
            thn='NMOS threshold.',
            segp_list='PMOS segments.',
            segn_list='NMOS segments.',
            stack_list='list of stack parameters for each inverter.',
            dum_info='Dummy information data structure.',
        )

    @classmethod
    def get_default_param_values(cls):
        # type: () -> Dict[str, Any]
        return dict(
            stack_list=None,
            dum_info=None,
        )

    def get_master_basename(self):
        segn_list = self.params['segn_list']
        return 'inv_chain_n%d_%dx' % (len(segn_list), segn_list[-1])

    def design(self, lch, wp_list, wn_list, thp, thn, segp_list, segn_list, stack_list, dum_info):
        ninv = len(wp_list)
        if not stack_list:
            stack_list = [False] * ninv
        name_list, term_list = [], []
        for idx in range(ninv):
            name_list.append('XINV%d' % idx)
            if idx == 0:
                in_name = 'in'
            else:
                in_name = 'mid<%d>' % (idx - 1)
            if idx == ninv - 1:
                out_name = 'out'
            else:
                out_name = 'mid<%d>' % idx
            term_list.append({'in': in_name, 'out': out_name})

        self.array_instance('XINV', name_list, term_list=term_list)
        for idx, (wp, wn, segp, segn, stack) in enumerate(zip(wp_list, wn_list, segp_list,
                                                              segn_list, stack_list)):
            self.instances['XINV'][idx].design(lch=lch, wp=wp, wn=wn, thp=thp, thn=thn,
                                               segp=segp, segn=segn, stack=stack)

        self.design_dummy_transistors(dum_info, 'XDUM', 'VDD', 'VSS')

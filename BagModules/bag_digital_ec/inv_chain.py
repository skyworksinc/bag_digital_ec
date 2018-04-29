# -*- coding: utf-8 -*-

from typing import Dict

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
        )

    def design(self, lch, wp_list, wn_list, thp, thn, segp_list, segn_list):
        ninv = len(wp_list)
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
        for wp, wn, segp, segn in zip(wp_list, wn_list, segp_list, segn_list):
            self.instances['XINV'][0].design(lch=lch, wp=wp, wn=wn, thp=thp, thn=thn,
                                             segp=segp, segn=segn)

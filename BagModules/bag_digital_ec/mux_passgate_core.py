# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info',
                                                                   'mux_passgate_core.yaml'))


# noinspection PyPep8Naming
class bag_digital_ec__mux_passgate_core(Module):
    """Module for library bag_digital_ec cell mux_passgate_core.

    Fill in high level description here.
    """

    def __init__(self, bag_config, parent=None, prj=None, **kwargs):
        Module.__init__(self, bag_config, yaml_file, parent=parent, prj=prj, **kwargs)

    @classmethod
    def get_params_info(cls):
        # type: () -> Dict[str, str]
        return dict(
            nin='number of inputs.',
            lch='channel length.',
            wp='PMOS width.',
            wn='NMOS width.',
            thp='PMOS threshold.',
            thn='NMOS threshold.',
            segp='PMOS segments.',
            segn='NMOS segments.',
        )

    def design(self, nin, lch, wp, wn, thp, thn, segp, segn):
        if nin < 2:
            raise ValueError('num_in = %d must be greater than 1.' % nin)

        suffix = '<%d:0>' % (nin - 1)
        for name in ['in', 'sel', 'selb']:
            self.rename_pin(name, name + suffix)

        name_list = ['XPG' + suffix]
        term_list = [{'en': 'sel' + suffix, 'enb': 'selb' + suffix, 's': 'in' + suffix}]
        self.instances['XPG'].design(lch=lch, wp=wp, wn=wn, thp=thp, thn=thn, segp=segp, segn=segn)
        self.array_instance('XPG', name_list, term_list=term_list)

# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info',
                                                                   'mux_passgate_2d_core.yaml'))


# noinspection PyPep8Naming
class bag_digital_ec__mux_passgate_2d_core(Module):
    """Module for library bag_digital_ec cell mux_passgate_2d_core.

    Fill in high level description here.
    """

    def __init__(self, bag_config, parent=None, prj=None, **kwargs):
        Module.__init__(self, bag_config, yaml_file, parent=parent, prj=prj, **kwargs)

    @classmethod
    def get_params_info(cls):
        # type: () -> Dict[str, str]
        return dict(
            num0='number of inputs for mux level 0.',
            num1='number of inputs for mux level 1.',
            lch='channel length.',
            wp='PMOS width.',
            wn='NMOS width.',
            thp='PMOS threshold.',
            thn='NMOS threshold.',
            segp='PMOS segments.',
            segn='NMOS segments.',
        )

    def design(self, num0, num1, lch, wp, wn, thp, thn, segp, segn):
        if num0 < 2 or num1 < 2:
            raise ValueError('(num0, num1) = (%d, %d) must be both greater than 1.' % (num0, num1))

        suf0 = '<%d:0>' % (num0 - 1)
        suf1 = '<%d:0>' % (num1 - 1)
        in_name = 'in<%d:0>' % (num0 * num1 - 1)
        mid_name = 'mid<%d:0>' % (num1 - 1)
        self.rename_pin('in', in_name)
        for idx, suf in enumerate([suf0, suf1]):
            base = 'sel%d' % idx
            self.rename_pin(base, base + suf)
            base = 'selb%d' % idx
            self.rename_pin(base, base + suf)

        name_list = ['XMUX0<%d:0>' % (num1 - 1)]
        term_list = [{'sel': 'sel0' + suf0, 'selb': 'selb0' + suf0, 'in': in_name, 'out': mid_name}]
        self.instances['XMUX0'].design(num_in=num0, lch=lch, wp=wp, wn=wn, thp=thp, thn=thn,
                                       segp=segp, segn=segn)
        self.array_instance('XMUX0', name_list, term_list=term_list)

        self.instances['XMUX1'].design(num_in=num1, lch=lch, wp=wp, wn=wn, thp=thp, thn=thn,
                                       segp=segp, segn=segn)
        self.reconnect_instance_terminal('XMUX1', 'in', mid_name)
        self.reconnect_instance_terminal('XMUX1', 'sel', 'sel1' + suf1)
        self.reconnect_instance_terminal('XMUX1', 'selb', 'selb1' + suf1)

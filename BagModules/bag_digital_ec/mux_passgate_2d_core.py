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
            nin0='number of inputs for mux level 0.',
            nin1='number of inputs for mux level 1.',
            lch='channel length.',
            wp='PMOS width.',
            wn='NMOS width.',
            thp='PMOS threshold.',
            thn='NMOS threshold.',
            segp='PMOS segments.',
            segn='NMOS segments.',
        )

    def design(self, nin0, nin1, lch, wp, wn, thp, thn, segp, segn):
        if nin0 < 2 or nin1 < 2:
            raise ValueError('(num0, num1) = (%d, %d) must be both greater than 1.' % (nin0, nin1))

        suf0 = '<%d:0>' % (nin0 - 1)
        suf1 = '<%d:0>' % (nin1 - 1)
        in_name = 'in<%d:0>' % (nin0 * nin1 - 1)
        mid_name = 'mid' + suf1
        self.rename_pin('in', in_name)
        for idx, suf in enumerate([suf0, suf1]):
            base = 'sel%d' % idx
            self.rename_pin(base, base + suf)
            base = 'selb%d' % idx
            self.rename_pin(base, base + suf)

        name_list = ['XMUX0<%d:0>' % (nin1 - 1)]
        term_list = [{'sel' + suf0: 'sel0' + suf0, 'selb' + suf0: 'selb0' + suf0,
                      'in' + suf0: in_name, 'out': mid_name}]
        self.instances['XMUX0'].design(nin=nin0, lch=lch, wp=wp, wn=wn, thp=thp, thn=thn,
                                       segp=segp, segn=segn)
        self.array_instance('XMUX0', name_list, term_list=term_list)

        self.instances['XMUX1'].design(nin=nin1, lch=lch, wp=wp, wn=wn, thp=thp, thn=thn,
                                       segp=segp, segn=segn)
        self.reconnect_instance_terminal('XMUX1', 'in' + suf1, mid_name)
        self.reconnect_instance_terminal('XMUX1', 'sel' + suf1, 'sel1' + suf1)
        self.reconnect_instance_terminal('XMUX1', 'selb' + suf1, 'selb1' + suf1)

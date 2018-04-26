# -*- coding: utf-8 -*-

from typing import Dict, Any

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info', 'nor.yaml'))


# noinspection PyPep8Naming
class bag_digital_ec__nor(Module):
    """Module for library bag_digital_ec cell nor.

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

    @classmethod
    def get_default_param_values(cls):
        # type: () -> Dict[str, Any]
        return dict(
            nin=2,
        )

    def design(self, nin, lch, wp, wn, thp, thn, segp, segn):
        if segp < 1 or segn < 1:
            raise ValueError('number of segments must be >= 1.')
        if nin < 2:
            raise ValueError('nin must be >= 2.')

        if nin != 2:
            self.rename_pin('in<1:0>', 'in<%d:0>' % (nin - 1))

        name_list = ['XN<%d:0>' % (nin - 1)]
        term_list = [dict(G='in<%d:0>' % (nin - 1))]
        self.instances['XN'].design(w=wn, l=lch, nf=segn, intent=thn)
        self.array_instance('XN', name_list, term_list=term_list)

        name_list, term_list = [], []
        suf = '' if segn == 1 else '<%d:0>' % (segn - 1)
        for idx in range(nin):
            name_list.append('XP%d' % idx + suf)
            if idx == 0:
                s_name = 'VDD'
            else:
                s_name = ('mid%d' % (idx - 1)) + suf
            if idx == nin - 1:
                d_name = 'out'
            else:
                d_name = ('mid%d' % idx) + suf
            term_list.append(dict(G='in<%d>' % idx, D=d_name, S=s_name))

        self.instances['XP'].design(w=wp, l=lch, nf=1, intent=thp)
        self.array_instance('XP', name_list, term_list=term_list)

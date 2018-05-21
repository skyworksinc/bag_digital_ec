# -*- coding: utf-8 -*-

from typing import Dict, Any

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info', 'inv.yaml'))


# noinspection PyPep8Naming
class bag_digital_ec__inv(Module):
    """Module for library bag_digital_ec cell inv.

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
            segp='PMOS segments.',
            segn='NMOS segments.',
            stack='True if transistors are stacked.',
        )

    @classmethod
    def get_default_param_values(cls):
        # type: () -> Dict[str, Any]
        return dict(
            stack=False,
        )

    def design(self, lch, wp, wn, thp, thn, segp, segn, stack):
        self.instances['XP'].design(w=wp, l=lch, nf=segp, intent=thp)
        self.instances['XN'].design(w=wn, l=lch, nf=segn, intent=thn)
        if stack:
            self._stack_transistors('XP', 'midp', 'VDD', 'out', wp, lch, thp, segp, 2)
            self._stack_transistors('XN', 'midn', 'VSS', 'out', wn, lch, thn, segn, 2)
        else:
            self.instances['XP'].design(w=wp, l=lch, nf=segp, intent=thp)
            self.instances['XN'].design(w=wn, l=lch, nf=segn, intent=thn)

    def _stack_transistors(self, name, mid_name, sbot, dtop, w, lch, th, seg, num_stack):
        name_list, term_list = [], []
        suf = '' if seg == 1 else '<%d:0>' % (seg - 1)
        for idx in range(num_stack):
            name_list.append(('%s%d' % (name, idx)) + suf)
            if idx == 0:
                s_name = sbot
            else:
                s_name = ('%s%d' % (mid_name, idx - 1)) + suf
            if idx == num_stack - 1:
                d_name = dtop
            else:
                d_name = ('%sd%d' % (mid_name, idx)) + suf
            term_list.append(dict(D=d_name, S=s_name))

        self.instances[name].design(w=w, l=lch, nf=1, intent=th)
        self.array_instance(name, name_list, term_list=term_list)

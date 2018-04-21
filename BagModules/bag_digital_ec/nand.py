# -*- coding: utf-8 -*-

from typing import Dict, Any

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info', 'nand.yaml'))


# noinspection PyPep8Naming
class bag_digital_ec__nand(Module):
    """Module for library bag_digital_ec cell nand.

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
        if nin > 2:
            raise ValueError('not supported yet.')
        else:
            self.instances['XP0'].design(w=wp, l=lch, nf=segp, intent=thp)
            self.instances['XP1'].design(w=wp, l=lch, nf=segp, intent=thp)
            if segn == 1:
                self.instances['XN0'].design(w=wn, l=lch, nf=1, intent=thn)
                self.instances['XN1'].design(w=wn, l=lch, nf=1, intent=thn)
            else:
                self.delete_instance('XN0')

                # use array notation to denote parallel segments
                seg_str = '<%d:0>' % (segn - 1)
                name_list = ['XN0' + seg_str, 'XN1' + seg_str]
                term_list = [dict(S='VSS', G='in<0>', D='mid' + seg_str),
                             dict(S='mid' + seg_str, G='in<1>', D='out')]

                self.instances['XN1'].design(w=wn, l=lch, nf=1, intent=thn)
                self.array_instance('XN1', name_list, term_list=term_list)

# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info', 'tinv.yaml'))


# noinspection PyPep8Naming
class bag_digital_ec__tinv(Module):
    """Module for library bag_digital_ec cell tinv.

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
        )

    def design(self, lch, wp, wn, thp, thn, segp, segn):
        if segp < 1 or segn < 1:
            raise ValueError('number of segments must be >= 1.')

        self._set_segments('XN', 'XNEN', 'mn', lch, wn, thn, segn)
        self._set_segments('XP', 'XPEN', 'mp', lch, wp, thp, segp)

    def _set_segments(self, bot_name, top_name, mid_name, lch, w, th, seg):
        self.instances[bot_name].design(w=w, l=lch, nf=1, intent=th)
        self.instances[top_name].design(w=w, l=lch, nf=1, intent=th)
        if seg > 1:
            suffix = '<%d:0>' % (seg - 1)
            self.array_instance(bot_name, [bot_name + suffix],
                                term_list=[dict(D=mid_name + suffix)])
            self.array_instance(top_name, [top_name + suffix],
                                term_list=[dict(S=mid_name + suffix)])

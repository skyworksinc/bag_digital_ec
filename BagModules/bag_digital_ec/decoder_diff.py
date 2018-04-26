# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info',
                                                                   'decoder_diff.yaml'))


# noinspection PyPep8Naming
class bag_digital_ec__decoder_diff(Module):
    """Module for library bag_digital_ec cell decoder_diff.

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
            seg_dict='Number of segments dictionary.',
        )

    def design(self, nin, lch, wp, wn, thp, thn, seg_dict):
        # rename pins
        suf = '<%d:0>' % (nin - 1)
        in_name = 'in' + suf
        nout = 1 << nin
        self.rename_pin('in', in_name)
        self.rename_pin('out', 'out<%d:0>' % (nout - 1))
        self.rename_pin('outb', 'outb<%d:0>' % (nout - 1))

        # design AND gates
        and_name = []
        and_term = []
        for idx in range(nout):
            and_name.append('XAND%d' % idx)
            # remove starting comma
            and_term.append({'out': 'out<%d>' % idx,
                             'outb': 'outb<%d>' % idx,
                             in_name: ','.join(self._and_in_name_iter(nin, idx))})
        self.instances['XAND'].design(nin=nin, lch=lch, wp=wp, wn=wn, thp=thp, thn=thn,
                                      seg_dict=seg_dict)
        self.array_instance('XAND', and_name, and_term)

        # design input buffers
        seg = seg_dict['inv']
        self.instances['XINV'].design(lch=lch, wp=wp, wn=wn, thp=thp, thn=thn, segp=seg, segn=seg)
        self.instances['XBUF'].design(lch=lch, wp=wp, wn=wn, thp=thp, thn=thn, segp=seg, segn=seg)
        self.array_instance('XINV', ['XINV' + suf], term_list=[{'in': in_name, 'out': 'inb' + suf}])
        self.array_instance('XBUF', ['XBUF' + suf], term_list=[{'in': 'inb' + suf,
                                                                'out': 'inbuf' + suf}])

    @classmethod
    def _and_in_name_iter(cls, nin, idx):
        for bit_idx in range(nin - 1, -1, -1):
            if ((idx & (1 << bit_idx)) >> bit_idx) == 1:
                yield 'inbuf<%d>' % bit_idx
            else:
                yield 'inb<%d>' % bit_idx

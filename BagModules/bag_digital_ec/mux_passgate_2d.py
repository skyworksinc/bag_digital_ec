# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info',
                                                                   'mux_passgate_2d.yaml'))


# noinspection PyPep8Naming
class bag_digital_ec__mux_passgate_2d(Module):
    """Module for library bag_digital_ec cell mux_passgate_2d.

    Fill in high level description here.
    """

    def __init__(self, bag_config, parent=None, prj=None, **kwargs):
        Module.__init__(self, bag_config, yaml_file, parent=parent, prj=prj, **kwargs)

    @classmethod
    def get_params_info(cls):
        # type: () -> Dict[str, str]
        return dict(
            nin0='number of select bits for mux level 0.',
            nin1='number of select bits for mux level 1.',
            lch='channel length.',
            wp='PMOS width.',
            wn='NMOS width.',
            thp='PMOS threshold.',
            thn='NMOS threshold.',
            seg_dict='Number of segments dictionary.',
        )

    def design(self, nin0, nin1, lch, wp, wn, thp, thn, seg_dict):
        ntot = 1 << (nin0 + nin1)
        in_name = 'in<%d:0>' % (ntot - 1)
        self.rename_pin('in', in_name)
        self.rename_pin('sel', 'sel<%d:0>' % (nin0 + nin1 - 1))

        # design mux
        mux_nin0 = 1 << nin0
        mux_nin1 = 1 << nin1
        seg = seg_dict['mux']
        self.instances['XCORE'].design(nin0=mux_nin0, nin1=mux_nin1, wp=wp, wn=wn,
                                       thp=thp, thn=thn, segp=seg, segn=seg)
        self.reconnect_instance_terminal('XCORE', in_name, in_name)
        suf0 = '<%d:0>' % (mux_nin0 - 1)
        suf1 = '<%d:0>' % (mux_nin1 - 1)
        self.reconnect_instance_terminal('XCORE', 'sel0' + suf0, 'sel0' + suf0)
        self.reconnect_instance_terminal('XCORE', 'selb0' + suf0, 'selb0' + suf0)
        self.reconnect_instance_terminal('XCORE', 'sel1' + suf1, 'sel1' + suf1)
        self.reconnect_instance_terminal('XCORE', 'selb1' + suf1, 'selb1' + suf1)

        # design decoder 0
        self.instances['XDEC0'].design(nin=nin0, lch=lch, wp=wp, wn=wn, thp=thp, thn=thn,
                                       seg_dict=seg_dict)
        self.reconnect_instance_terminal('XDEC0', 'in<%d:0>' % (nin0 - 1), 'sel<%d:0>' % (nin0 - 1))
        self.reconnect_instance_terminal('XDEC0', 'out' + suf0, 'sel0' + suf0)
        self.reconnect_instance_terminal('XDEC0', 'outb' + suf0, 'selb0' + suf0)

        # design decoder 1
        self.instances['XDEC1'].design(nin=nin1, lch=lch, wp=wp, wn=wn, thp=thp, thn=thn,
                                       seg_dict=seg_dict)
        self.reconnect_instance_terminal('XDEC1', 'in<%d:0>' % (nin1 - 1),
                                         'sel<%d:%d>' % (nin0 + nin1 - 1, nin0))
        self.reconnect_instance_terminal('XDEC1', 'out' + suf1, 'sel1' + suf1)
        self.reconnect_instance_terminal('XDEC1', 'outb' + suf1, 'selb1' + suf1)

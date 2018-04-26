# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info', 'and_diff.yaml'))


# noinspection PyPep8Naming
class bag_digital_ec__and_diff(Module):
    """Module for library bag_digital_ec cell and_diff.

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
        if nin < 2:
            raise ValueError('Must have at least 2 inputs.')
        if nin > 9:
            raise ValueError('More than 9 inputs not supported yet.')

        self.rename_pin('in', 'in<%d:0>' % (nin - 1))

        # design NAND
        nand_nin_list = self._get_nand_nin_list(nin)
        num_nand = len(nand_nin_list)
        if num_nand == 1:
            nin_nand = nand_nin_list[0]
            seg = seg_dict['nand%d' % nin_nand]
            nand_in_name = 'in<%d:0>' % (nin_nand - 1)
            self.instances['XNAND'].design(nin=nin_nand, lch=lch, wp=wp, wn=wn, thp=thp, thn=thn,
                                           segp=seg, segn=seg)
            self.reconnect_instance_terminal('XNAND', nand_in_name, nand_in_name)
        else:
            in_idx = 0
            name_list, term_list = [], []
            for cur_idx, nin_nand in enumerate(nand_nin_list):
                nand_in_name = 'in<%d:0>' % (nin_nand - 1)
                term_list.append({nand_in_name: 'in<%d:%d>' % (in_idx + nin_nand - 1, in_idx),
                                  'out': 'mid<%d>' % cur_idx})
                in_idx += nin_nand
                name_list.append('XNAND%d' % cur_idx)

            self.array_instance('XNAND', name_list, term_list)
            for inst, nin_nand in zip(self.instances['XNAND'], nand_nin_list):
                seg = seg_dict['nand%d' % nin_nand]
                inst.design(nin=nin_nand, lch=lch, wp=wp, wn=wn, thp=thp, thn=thn,
                            segp=seg, segn=seg)

        # design NOR
        if num_nand == 1:
            # no need for NOR gate
            self.delete_instance('XNOR')
        else:
            suffix = '<%d:0>' % (num_nand - 1)
            seg = seg_dict['nor%d' % num_nand]
            self.instances['XNOR'].design(nin=num_nand, lch=lch, wp=wp, wn=wn, thp=thp, thn=thn,
                                          segp=seg, segn=seg)
            self.reconnect_instance_terminal('XNOR', 'in' + suffix, 'mid' + suffix)
            self.reconnect_instance_terminal('XNOR', 'out', 'out')

        # design inverter
        seg = seg_dict['inv']
        self.instances['XINV'].design(lch=lch, wp=wp, wn=wn, thp=thp, thn=thn, segp=seg, segn=seg)
        if num_nand == 1:
            self.reconnect_instance_terminal('XINV', 'in', 'outb')
            self.reconnect_instance_terminal('XINV', 'out', 'out')
        else:
            self.reconnect_instance_terminal('XINV', 'in', 'out')
            self.reconnect_instance_terminal('XINV', 'out', 'outb')

    @classmethod
    def _get_nand_nin_list(cls, num_in):
        # only use nand with 2 or 3 inputs.
        remainder = num_in % 3
        if remainder == 0:
            return [3] * (num_in // 3)
        elif remainder == 1:
            return [3] * ((num_in // 3) - 1) + [2, 2]
        else:
            return [3] * (num_in // 3) + [2]

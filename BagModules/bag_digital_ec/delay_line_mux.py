# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info',
                                                                   'delay_line_mux.yaml'))


# noinspection PyPep8Naming
class bag_digital_ec__delay_line_mux(Module):
    """Module for library bag_digital_ec cell delay_line_mux.

    Fill in high level description here.
    """

    def __init__(self, bag_config, parent=None, prj=None, **kwargs):
        Module.__init__(self, bag_config, yaml_file, parent=parent, prj=prj, **kwargs)

    @classmethod
    def get_params_info(cls):
        # type: () -> Dict[str, str]
        return dict(
            num='number of stages.',
            cell_params='delay cell parameters.',
        )

    def design(self, num, cell_params):
        if num <= 0:
            raise ValueError('num = %d <= 0' % num)

        self.instances['XCELL'].design(**cell_params)

        if num > 1:
            suf = '<%d:0>' % (num - 1)
            name_list = ['XCELL' + suf]
            if num == 2:
                in_name = 'mid,in'
                out_name = 'out,mid'
            else:
                in_name = 'mid<%d:0>,in' % (num - 2)
                out_name = 'out,mid<%d:0>' % (num - 2)

            delay_name = 'delay' + suf
            term_list = [{'in': in_name, 'out': out_name, 'delay': delay_name}]
            self.array_instance('XCELL', name_list, term_list)
            self.rename_pin('delay', delay_name)

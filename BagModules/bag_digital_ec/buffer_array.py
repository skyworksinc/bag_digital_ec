# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info',
                                                                   'buffer_array.yaml'))


# noinspection PyPep8Naming
class bag_digital_ec__buffer_array(Module):
    """Module for library bag_digital_ec cell buffer_array.

    Fill in high level description here.
    """

    def __init__(self, bag_config, parent=None, prj=None, **kwargs):
        Module.__init__(self, bag_config, yaml_file, parent=parent, prj=prj, **kwargs)

    @classmethod
    def get_params_info(cls):
        # type: () -> Dict[str, str]
        return dict(
            nbuf='Total number of buffers.',
            buf_params='Buffer parameters.',
        )

    def design(self, nbuf, buf_params):
        if nbuf <= 0:
            raise ValueError('nbuf must be > 0.')

        self.instances['XBUF'].design(**buf_params)
        if nbuf > 1:
            suf = '<%d:0>' % (nbuf - 1)
            in_name = 'in' + suf
            out_name = 'out' + suf
            self.rename_pin('in<0>', in_name)
            self.rename_pin('out<0>', out_name)
            name_list = ['XBUF' + suf]
            term_dict = {'in': in_name, 'out': out_name}
            self.array_instance('XBUF', name_list, term_list=[term_dict])

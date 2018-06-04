# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info',
                                                                   'delay_cell_mux.yaml'))


# noinspection PyPep8Naming
class bag_digital_ec__delay_cell_mux(Module):
    """Module for library bag_digital_ec cell delay_cell_mux.

    Fill in high level description here.
    """

    def __init__(self, bag_config, parent=None, prj=None, **kwargs):
        Module.__init__(self, bag_config, yaml_file, parent=parent, prj=prj, **kwargs)

    @classmethod
    def get_params_info(cls):
        # type: () -> Dict[str, str]
        return dict(
            buf_params='delay buffer parameters.',
            mux_params='mux parameters.',
        )

    def design(self, buf_params, mux_params):
        self.instances['XBUF'].design(**buf_params)
        self.instances['XMUX'].design(**mux_params)

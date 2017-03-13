# -*- coding: utf-8 -*-
########################################################################################################################
#
# Copyright (c) 2014, Regents of the University of California
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#   disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#    following disclaimer in the documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
########################################################################################################################

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# noinspection PyUnresolvedReferences,PyCompatibility
from builtins import *

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info', 'and_diff.yaml'))


# noinspection PyPep8Naming
class digital_ec_templates__and_diff(Module):
    """Module for library digital_ec_templates cell and_diff.

    Fill in high level description here.
    """

    param_list = ['num_in', 'nand2_params', 'nand3_params',
                  'nor2_params', 'nor3_params', 'inv_params', ]

    def __init__(self, bag_config, parent=None, prj=None, **kwargs):
        Module.__init__(self, bag_config, yaml_file, parent=parent, prj=prj, **kwargs)
        for par in self.param_list:
            self.parameters[par] = None

    def design(self):
        """To be overridden by subclasses to design this module.

        This method should fill in values for all parameters in
        self.parameters.  To design instances of this module, you can
        call their design() method or any other ways you coded.

        To modify schematic structure, call:

        rename_pin()
        delete_instance()
        replace_instance_master()
        reconnect_instance_terminal()
        restore_instance()
        array_instance()
        """
        pass

    def design_specs(self, num_in, nand2_params, nand3_params, nor2_params, nor3_params,
                     inv_params, **kwargs):
        """Set the design parameters of this module directly.

        Parameters
        ----------
        num_in : int
            number of inputs.
        nand2_params : Dict[str, Any]
            2-input NAND gate parameters.
        nand3_params : Dict[str, Any]
            3-input NAND gate parameters.
        nor2_params : Dict[str, Any]
            2-input NOR gate parameters.
        nor3_params : Dict[str, Any]
            3-input NOR gate parameters.
        inv_params : Dict[str, Any]
            inverter parameters.
        """
        local_dict = locals()
        for par in self.param_list:
            if par not in local_dict:
                raise Exception('Parameter %s not defined' % par)
            self.parameters[par] = local_dict[par]

        if num_in < 2:
            raise ValueError('Must have at least 2 inputs.')
        if num_in > 9:
            # TODO: add support num_in > 9
            raise ValueError('More than 9 inputs not supported yet.')

        self.rename_pin('in', 'in<%d:0>' % (num_in - 1))

        # design NAND
        nand_num_in_list = self._get_nand_num_in_list(num_in)
        num_nand = len(nand_num_in_list)
        if num_nand == 1:
            params = nand2_params if nand_num_in_list[0] == 2 else nand3_params
            self.instances['XNAND'].design_specs(num_in=nand_num_in_list[0], **params)
        else:
            in_idx = 0
            name_list, term_list = [], []
            for cur_idx, num_in_nand in enumerate(nand_num_in_list):
                term_list.append({'in': 'in<%d:%d>' % (in_idx + num_in_nand - 1, in_idx),
                                  'out': 'mid<%d>' % cur_idx})
                in_idx += num_in_nand
                name_list.append('XNAND%d' % cur_idx)

            self.array_instance('XNAND', name_list, term_list)
            for inst, num_in_nand in zip(self.instances['XNAND'], nand_num_in_list):
                params = nand2_params if num_in_nand == 2 else nand3_params
                inst.design_specs(num_in=num_in_nand, **params)

        # design NOR
        if num_nand == 1:
            # no need for NOR gate
            self.delete_instance('XNOR')
        else:
            self.reconnect_instance_terminal('XNOR', 'in', 'mid<%d:%d>' % (num_nand - 1, 0))
            params = nor2_params if num_nand == 2 else nor3_params
            self.instances['XNOR'].design_specs(num_in=num_nand, **params)

        # design inverter
        if num_nand == 1:
            self.reconnect_instance_terminal('XINV', 'in', 'outb')
            self.reconnect_instance_terminal('XINV', 'out', 'out')
        else:
            self.reconnect_instance_terminal('XINV', 'in', 'out')
            self.reconnect_instance_terminal('XINV', 'out', 'outb')

        self.instances['XINV'].design_specs(**inv_params)

    @staticmethod
    def _get_nand_num_in_list(num_in):
        # only use nand with 2 or 3 inputs.
        remainder = num_in % 3
        if remainder == 0:
            return [3] * (num_in // 3)
        elif remainder == 1:
            return [3] * ((num_in // 3) - 1) + [2, 2]
        else:
            return [3] * (num_in // 3) + [2]

    def get_layout_params(self, **kwargs):
        """Returns a dictionary with layout parameters.

        This method computes the layout parameters used to generate implementation's
        layout.  Subclasses should override this method if you need to run post-extraction
        layout.

        Parameters
        ----------
        kwargs :
            any extra parameters you need to generate the layout parameters dictionary.
            Usually you specify layout-specific parameters here, like metal layers of
            input/output, customizable wire sizes, and so on.

        Returns
        -------
        params : dict[str, any]
            the layout parameters dictionary.
        """
        return {}

    def get_layout_pin_mapping(self):
        """Returns the layout pin mapping dictionary.

        This method returns a dictionary used to rename the layout pins, in case they are different
        than the schematic pins.

        Returns
        -------
        pin_mapping : dict[str, str]
            a dictionary from layout pin names to schematic pin names.
        """
        return {}

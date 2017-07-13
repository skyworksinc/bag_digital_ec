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


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info', 'decoder_diff.yaml'))


# noinspection PyPep8Naming
class digital_ec_templates__decoder_diff(Module):
    """Module for library digital_ec_templates cell decoder_diff.

    Fill in high level description here.
    """

    param_list = ['num_bits', 'nand2_params', 'nand3_params',
                  'nor2_params', 'nor3_params', 'and_inv_params', 'inv_params']

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

    def design_specs(self, num_bits, nand2_params, nand3_params, nor2_params, nor3_params,
                     and_inv_params, inv_params, **kwargs):
        """Set the design parameters of this module directly.

        Parameters
        ----------
        num_bits : int
            number of input bits.
        nand2_params : Dict[str, Any]
            2-input NAND gate parameters.
        nand3_params : Dict[str, Any]
            3-input NAND gate parameters.
        nor2_params : Dict[str, Any]
            2-input NOR gate parameters.
        nor3_params : Dict[str, Any]
            3-input NOR gate parameters.
        and_inv_params : Dict[str, Any]
            AND gate inverter parameters.
        inv_params : Dict[str, Any]
            input inverter parameters.
        """
        local_dict = locals()
        for par in self.param_list:
            if par not in local_dict:
                raise Exception('Parameter %s not defined' % par)
            self.parameters[par] = local_dict[par]

        # rename pins
        in_name = 'in<%d:0>' % (num_bits - 1)
        num_out = 1 << num_bits
        self.rename_pin('in', in_name)
        self.rename_pin('out', 'out<%d:0>' % (num_out - 1))
        self.rename_pin('outb', 'outb<%d:0>' % (num_out - 1))

        # design AND gates
        and_name = []
        and_term = []
        for idx in range(num_out):
            and_name.append('XAND%d' % idx)
            term = {'out': 'out<%d>' % idx, 'outb': 'outb<%d>' % idx}
            cur_in = ''
            for bit_idx in range(num_bits - 1, -1, -1):
                if ((idx & (1 << bit_idx)) >> bit_idx) == 1:
                    cur_in += ',inbuf<%d>' % bit_idx
                else:
                    cur_in += ',inb<%d>' % bit_idx
            # remove starting comma
            term[in_name] = cur_in[1:]
            and_term.append(term)
        self.array_instance('XAND', and_name, and_term)
        inst = self.instances['XAND'][0]
        inst.design_specs(num_bits, nand2_params, nand3_params, nor2_params,
                          nor3_params, and_inv_params)
        self.instances['XAND'] = [inst] * num_out

        # design input buffers
        invb_name, invbuf_name = [], []
        invb_term, invbuf_term = [], []
        for idx in range(num_bits):
            invb_name.append('XINVB%d' % idx)
            invbuf_name.append('XINVBUF%d' % idx)
            invb_term.append({'in': 'in<%d>' % idx, 'out': 'inb<%d>' % idx})
            invbuf_term.append({'in': 'inb<%d>' % idx, 'out': 'inbuf<%d>' % idx})

        self.array_instance('XINVB', invb_name, invb_term, same=True)
        self.array_instance('XINVBUF', invbuf_name, invbuf_term, same=True)

        self.instances['XINVB'][0].design_specs(**inv_params)
        self.instances['XINVBUF'][0].design_specs(**inv_params)

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

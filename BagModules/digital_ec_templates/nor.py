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


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info', 'nor.yaml'))


# noinspection PyPep8Naming
class digital_ec_templates__nor(Module):
    """Module for library digital_ec_templates cell nor.

    Fill in high level description here.
    """

    param_list = ['lch', 'num_in', 'wp', 'wn', 'fg', 'intentp', 'intentn']

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

    def design_specs(self, lch, num_in, wp, wn, fg, intentp, intentn, **kwargs):
        """Set the design parameters of this module directly.

        Parameters
        ----------
        lch : float
            channel length, in meters.
        num_in : int
            number of inputs.
        wp : float or int
            pmos width, in meters or number of fins.
        wn : float or int
            nmos width, in meters or number of fins.
        fg : int
            number of pmos/nmos fingers per transistor.
        intentp : str
            nmos device intent.
        intentn : str
            pmos device intent.
        """
        local_dict = locals()
        for par in self.param_list:
            if par not in local_dict:
                raise Exception('Parameter %s not defined' % par)
            self.parameters[par] = local_dict[par]

        if num_in < 2:
            raise ValueError('Must have at least 2 inputs.')

        self.rename_pin('in', 'in<%d:0>' % (num_in - 1))
        # array transistors
        pname, pterm, nname, nterm = [], [], [], []
        for idx in range(num_in):
            pname.append('XP%d' % idx)
            nname.append('XN%d' % idx)
            nterm.append({'G': 'in<%d>' % idx})

            pdict = {'G': 'in<%d>' % idx}
            if idx == 0:
                pdict['S'] = 'VDD'
            else:
                pdict['S'] = 'mid<%d>' % (idx - 1)

            if idx == num_in - 1:
                pdict['D'] = 'out'
            else:
                pdict['D'] = 'mid<%d>' % idx

            pterm.append(pdict)

        self.array_instance('XP', pname, pterm)
        self.array_instance('XN', nname, nterm)

        pinst = self.instances['XP'][0]
        pinst.design(w=wp, l=lch, nf=fg, intent=intentp)
        ninst = self.instances['XN'][0]
        ninst.design(w=wn, l=lch, nf=fg, intent=intentn)
        self.instances['XP'] = [pinst] * num_in
        self.instances['XN'] = [ninst] * num_in

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

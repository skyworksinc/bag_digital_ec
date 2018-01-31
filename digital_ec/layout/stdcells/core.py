# -*- coding: utf-8 -*-

from typing import TYPE_CHECKING, Dict, Any, Set

import importlib

from abs_templates_ec.digital.core import DigitalBase

if TYPE_CHECKING:
    from bag.layout.template import TemplateDB


class StdCellWrapper(DigitalBase):
    """A class that wraps a given standard cell with proper boundaries.

    This class is usually used just for layout debugging (i.e. DRC checking).

    Parameters
    ----------
    temp_db : TemplateDB
            the template database.
    lib_name : str
        the layout library name.
    params : Dict[str, Any]
        the parameter values.
    used_names : Set[str]
        a set of already used cell names.
    **kwargs
        dictionary of optional parameters.  See documentation of
        :class:`bag.layout.template.TemplateBase` for details.
    """

    def __init__(self, temp_db, lib_name, params, used_names, **kwargs):
        # type: (TemplateDB, str, Dict[str, Any], Set[str], **Any) -> None
        super(StdCellWrapper, self).__init__(temp_db, lib_name, params, used_names, **kwargs)

    @classmethod
    def get_params_info(cls):
        # type: () -> Dict[str, str]
        return {
            'module': 'standard cell module name.',
            'class': 'standard cell class name.',
            'params': 'standard cell layout parameters.',
            'guard_ring_nf': 'number of guard rings in boundary.',
        }

    @classmethod
    def get_default_param_values(cls):
        # type: () -> Dict[str, Any]
        return dict(
            guard_ring_nf=0,
        )

    def draw_layout(self):
        """Draw the layout of a dynamic latch chain.
        """
        mod = self.params['module']
        cls = self.params['class']
        params = self.params['params'].copy()
        guard_ring_nf = self.params['guard_ring_nf']

        cls_mod = importlib.import_module(mod)
        temp_cls = getattr(cls_mod, cls)

        params['show_pins'] = True
        master = self.new_template(params=params, temp_cls=temp_cls)
        row_info = master.get_digital_row_info()

        self.initialize(row_info, 1, True, 15, guard_ring_nf=guard_ring_nf, num_col=master.laygo_size[0])

        self.add_digital_block(master, loc=(0, 0))
        self.set_digital_size(master.laygo_size[0])

        self.fill_space()

# -*- coding: utf-8 -*-


"""This module contains layout generator for various kinds of flip-flops."""

from typing import TYPE_CHECKING, Dict, Any, Set

from bag.layout.routing import TrackManager, TrackID

from .core import StdLaygoTemplate
from .inv import Inverter, InverterTristate

if TYPE_CHECKING:
    from bag.layout.template import TemplateDB


class LatchCK2(StdLaygoTemplate):
    """A transmission gate latch with differential clock inputs.

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
        StdLaygoTemplate.__init__(self, temp_db, lib_name, params, used_names, **kwargs)
        self._sch_params = None

    @property
    def sch_params(self):
        # type: () -> Dict[str, Any]
        return self._sch_params

    @classmethod
    def get_params_info(cls):
        # type: () -> Dict[str, str]
        return dict(
            config='laygo configuration dictionary.',
            wp='pmos widths.',
            wn='nmos widths.',
            seg='number of segments.',
            tr_widths='Track width dictionary.',
            tr_spaces='Track spacing dictionary.',
            sig_locs='Signal track location dictionary.',
            show_pins='True to draw pin geometries.',
        )

    @classmethod
    def get_default_param_values(cls):
        # type: () -> Dict[str, Any]
        return dict(
            sig_locs=None,
            show_pins=True,
        )

    def draw_layout(self):
        blk_sp = 2
        in_fanout = 4
        fb_fanout = 8

        config = self.params['config']
        wp = self.params['wp']
        wn = self.params['wn']
        seg = self.params['seg']
        tr_widths = self.params['tr_widths']
        tr_spaces = self.params['tr_spaces']
        show_pins = self.params['show_pins']
        sig_locs = self.params['sig_locs']

        wp_row = config['wp']
        wn_row = config['wn']

        if wp < 0 or wp > wp_row or wn < 0 or wn > wn_row:
            raise ValueError('Invalid choice of wp and/or wn.')

        # make masters
        sub_params = self.params.copy()
        sub_params['show_pins'] = False
        sub_params['sig_locs'] = None
        inv_master = self.new_template(params=sub_params, temp_cls=Inverter)
        seg_t0 = int(round(seg / (2 * in_fanout))) * 2
        sub_params['seg'] = max(seg_t0, 2)
        t0_master = self.new_template(params=sub_params, temp_cls=InverterTristate)
        seg_t1 = int(round(seg / (2 * fb_fanout))) * 2
        sub_params['seg'] = max(seg_t1, 2)
        t1_master = self.new_template(params=sub_params, temp_cls=InverterTristate)

        t0_ncol = t0_master.num_cols
        t1_ncol = t1_master.num_cols
        inv_ncol = inv_master.num_cols
        num_cols = t0_ncol + t1_ncol + inv_ncol + blk_sp * 2

        self.setup_floorplan(config, num_cols)
        t0 = self.add_laygo_template(t0_master, 0)
        t1 = self.add_laygo_template(t1_master, t0_ncol + blk_sp)
        inv = self.add_laygo_template(inv_master, num_cols - inv_ncol)

        self.fill_space()

        # connect/export VSS/VDD
        vss_list, vdd_list = [], []
        for inst in (t0, t1, inv):
            vss_list.append(inst.get_pin('VSS'))
            vdd_list.append(inst.get_pin('VDD'))
        self.add_pin('VSS', self.connect_wires(vss_list), show=show_pins)
        self.add_pin('VDD', self.connect_wires(vdd_list), show=show_pins)

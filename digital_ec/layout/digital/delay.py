# -*- coding: utf-8 -*-

"""This module contains layout generator for various kinds of delay cells."""

from typing import TYPE_CHECKING, Dict, Any, Set

from ..stdcells.core import StdDigitalTemplate
from ..stdcells.mux import MuxTristate
from ..stdcells.inv import InvChain

if TYPE_CHECKING:
    from bag.layout import TemplateDB


class DelayCellMux(StdDigitalTemplate):
    """A mux-based delay cell

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
        StdDigitalTemplate.__init__(self, temp_db, lib_name, params, used_names, **kwargs)
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
            seg='number of segments.',
            delay_seg_list='delay buffer segment list.',
            tr_widths='Track width dictionary.',
            tr_spaces='Track spacing dictionary.',
            wp='pmos width.',
            wn='nmos width.',
            row_layout_info='Row layout information dictionary.',
            show_pins='True to draw pin geometries.',
        )

    @classmethod
    def get_default_param_values(cls):
        # type: () -> Dict[str, Any]
        return dict(
            wp=None,
            wn=None,
            row_layout_info=None,
            show_pins=True,
        )

    def get_layout_basename(self):
        return 'delay_cell_mux_%dx' % self.params['seg']

    def draw_layout(self):
        blk_sp = 2

        config = self.params['config']

        delay_seg_list = self.params['delay_seg_list']
        wp = self.params['wp']
        wn = self.params['wn']
        show_pins = self.params['show_pins']

        wp_row = config['wp']
        wn_row = config['wn']
        if wp is None:
            wp = wp_row
        if wn is None:
            wn = wn_row
        if wp < 0 or wp > wp_row or wn < 0 or wn > wn_row:
            raise ValueError('Invalid choice of wp and/or wn.')

        # setup floorplan
        params = self.params.copy()
        params['wp'] = wp
        params['wn'] = wn
        params['show_pins'] = False
        params['sig_locs'] = None
        mux_master = self.new_template(params=params, temp_cls=MuxTristate)
        params['row_layout_info'] = row_layout_info = mux_master.row_layout_info
        self.initialize(row_layout_info, 1)

        # compute track locations
        in_tid = mux_master.get_port('in0').get_pins()[0].track_id
        mid_tidx = mux_master.get_port('sel1_hm').get_pins()[0].track_id.base_index

        # make masters
        params['wp_list'] = [wp, wp]
        params['wn_list'] = [wn, wn]
        params['seg_list'] = delay_seg_list
        params['stack_list'] = [True, False]
        params['sig_locs'] = {'in': in_tid.base_index, 'mid': mid_tidx}
        inv_master = self.new_template(params=params, temp_cls=InvChain)

        # set size
        inv_ncol = inv_master.num_cols
        mux_ncol = mux_master.num_cols
        num_cols = inv_ncol + mux_ncol + blk_sp
        self.set_digital_size(num_cols)

        # add instances
        inv = self.add_digital_block(inv_master, (0, 0))
        mux = self.add_digital_block(mux_master, (inv_ncol + blk_sp, 0))

        self.fill_space()

        # connect/export VSS/VDD
        vss_list, vdd_list = [], []
        for inst in (inv, mux):
            vss_list.append(inst.get_pin('VSS'))
            vdd_list.append(inst.get_pin('VDD'))
        self.add_pin('VSS', self.connect_wires(vss_list), show=show_pins)
        self.add_pin('VDD', self.connect_wires(vdd_list), show=show_pins)

        # connect and export pins
        self.connect_to_track_wires(inv.get_pin('out'), mux.get_pin('in1'))
        self.add_pin('in', self.connect_wires([inv.get_pin('in'), mux.get_pin('in0')]),
                     show=show_pins)
        self.add_pin('out', mux.get_pin('out'), show=show_pins)
        self.add_pin('delay', mux.get_pin('sel1'), show=show_pins)

        # set schematic parameters
        self._sch_params = dict(
            buf_params=inv_master.sch_params,
            mux_params=mux_master.sch_params,
        )

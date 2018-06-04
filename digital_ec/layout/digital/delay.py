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


class DelayLineMux(StdDigitalTemplate):
    """A delay line made from mux delay cells.

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

    _blk_sp = 2

    def __init__(self, temp_db, lib_name, params, used_names, **kwargs):
        # type: (TemplateDB, str, Dict[str, Any], Set[str], **kwargs) -> None
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
            nx='number of delay cells in a row.',
            ny='number of delay cell rows.',
            cell_params='delay cell parameters.',
            tr_widths='Track width dictionary.',
            tr_spaces='Track spacing dictionary.',
            row_layout_info='Row layout information dictionary.',
            show_pins='True to draw pin geometries.',
        )

    @classmethod
    def get_default_param_values(cls):
        # type: () -> Dict[str, Any]
        return dict(
            row_layout_info=None,
            show_pins=True,
        )

    def draw_layout(self):
        blk_sp = 2
        nx = self.params['nx']
        ny = self.params['ny']
        config = self.params['config']
        tr_widths = self.params['tr_widths']
        tr_spaces = self.params['tr_spaces']
        row_layout_info = self.params['row_layout_info']
        show_pins = self.params['show_pins']

        cell_params = self.params['cell_params'].copy()
        cell_params['config'] = config
        cell_params['tr_widths'] = tr_widths
        cell_params['tr_spaces'] = tr_spaces
        cell_params['row_layout_info'] = row_layout_info
        cell_params['show_pins'] = False
        master = self.new_template(params=cell_params, temp_cls=DelayCellMux)

        # setup floorplan
        tap_ncol = self.sub_columns
        cell_ncol = master.num_cols
        ncol = tap_ncol * 2 + blk_sp * (nx + 1) + cell_ncol * nx
        row_layout_info = master.row_layout_info
        self.initialize(row_layout_info, ny, num_cols=ncol, draw_boundaries=True, end_mode=15)

        vdd_list, vss_list = [], []
        spx = cell_ncol + blk_sp
        last_out = None
        cnt = 0
        for ridx in range(ny):
            cur_col = tap_ncol + blk_sp
            flip = (ridx % 2 == 1)
            inst = self.add_digital_block(master, (cur_col, ridx), flip=flip, nx=nx, spx=spx)
            # connect internal signals
            if ridx == 0:
                # export input
                self.add_pin('in', inst.get_pin('in', col=0), show=show_pins)
            else:
                if flip:
                    self.connect_to_track_wires(last_out, inst.get_pin('in', col=nx - 1))
                else:
                    self.connect_to_track_wires(last_out, inst.get_pin('in', col=0))

            for cidx in range(nx - 1):
                if flip:
                    self.connect_to_track_wires(inst.get_pin('out', col=nx - 1 - cidx),
                                                inst.get_pin('in', col=nx - 2 - cidx))
                    self.add_pin('delay<%d>' % cnt, inst.get_pin('delay', col=nx - 1 - cidx),
                                 show=show_pins)

                else:
                    self.connect_to_track_wires(inst.get_pin('out', col=cidx),
                                                inst.get_pin('in', col=cidx + 1))
                    self.add_pin('delay<%d>' % cnt, inst.get_pin('delay', col=cidx), show=show_pins)
                cnt += 1

            if flip:
                self.add_pin('delay<%d>' % cnt, inst.get_pin('delay', col=0), show=show_pins)
                last_out = inst.get_pin('out', col=0)
            else:
                self.add_pin('delay<%d>' % cnt, inst.get_pin('delay', col=nx - 1), show=show_pins)
                last_out = inst.get_pin('out', col=nx - 1)
            cnt += 1

            # draw taps and get power wires
            tap = self.add_substrate_tap((0, ridx))
            vdd_list.extend(tap.port_pins_iter('VDD'))
            vss_list.extend(tap.port_pins_iter('VSS'))
            tap = self.add_substrate_tap((ncol - tap_ncol, ridx))
            vdd_list.extend(tap.port_pins_iter('VDD'))
            vss_list.extend(tap.port_pins_iter('VSS'))

        # fill space
        self.fill_space()

        # export output
        self.add_pin('out', last_out, show=show_pins)
        # export supply
        vdd = self.connect_wires(vdd_list)
        vss = self.connect_wires(vss_list)
        self.add_pin('VDD', vdd, show=show_pins)
        self.add_pin('VSS', vss, show=show_pins)

        # set schematic parameters
        self._sch_params = dict(
            nx=nx,
            ny=ny,
            cell_params=master.sch_params,
        )

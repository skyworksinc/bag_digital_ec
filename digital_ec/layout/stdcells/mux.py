# -*- coding: utf-8 -*-

"""This module contains layout generator for various kinds of muxes."""

from typing import TYPE_CHECKING, Dict, Any, Set

from bag.layout.routing import TrackManager, TrackID

from .core import StdLaygoTemplate

if TYPE_CHECKING:
    from bag.layout import TemplateDB


class Passgate(StdLaygoTemplate):
    """A CMOS pass gate

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
            seg='number of segments.',
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

    def draw_layout(self):
        config = self.params['config']
        seg = self.params['seg']
        tr_widths = self.params['tr_widths']
        tr_spaces = self.params['tr_spaces']
        wp = self.params['wp']
        wn = self.params['wn']
        row_layout_info = self.params['row_layout_info']
        show_pins = self.params['show_pins']

        wp_row = config['wp']
        wn_row = config['wn']
        if wp is None:
            wp = wp_row
        if wn is None:
            wn = wn_row
        if wp < 0 or wp > wp_row or wn < 0 or wn > wn_row:
            raise ValueError('Invalid choice of wp and/or wn.')
        if seg % 2 != 0:
            raise ValueError('seg = %d must be even.' % seg)

        vss_tid, vdd_tid = self.setup_floorplan(config, row_layout_info, seg)

        tr_manager = TrackManager(self.grid, tr_widths, tr_spaces, half_space=True)

        # get track information
        hm_layer = self.conn_layer + 1
        vm_layer = hm_layer + 1
        hm_w_out = tr_manager.get_width(hm_layer, 'out')
        vm_w_out = tr_manager.get_width(vm_layer, 'out')
        pg_tid = self.make_track_id(1, 'g', -1, width=hm_w_out)
        ng_tid = self.make_track_id(0, 'g', -1, width=hm_w_out)
        pd_tid = self.make_track_id(1, 'gb', 0, width=hm_w_out)
        nd_tid = self.make_track_id(0, 'gb', 0, width=hm_w_out)
        mid_tidx = self.grid.get_middle_track(pg_tid.base_index, ng_tid.base_index)
        mid_tid = TrackID(hm_layer, mid_tidx, width=hm_w_out)
        vm_coord = self.laygo_info.col_to_coord(seg // 2, unit_mode=True)
        vm_tid = TrackID(vm_layer, self.grid.coord_to_track(vm_layer, vm_coord, unit_mode=True),
                         width=vm_w_out)

        # add blocks
        pmos = self.add_laygo_mos(1, 0, seg, w=wp)
        nmos = self.add_laygo_mos(0, 0, seg, w=wn)
        # compute overall block size and fill spaces
        self.fill_space()

        # connect wires
        s_warr = self.connect_to_tracks([pmos['s'], nmos['s']], mid_tid)
        self.add_pin('s', s_warr, show=show_pins)
        pd = self.connect_to_tracks(pmos['d'], pd_tid, min_len_mode=0)
        nd = self.connect_to_tracks(nmos['d'], nd_tid, min_len_mode=0)
        d_warr = self.connect_to_tracks([pd, nd], vm_tid)
        self.add_pin('pd', pd, show=False)
        self.add_pin('nd', nd, show=False)
        self.add_pin('d', d_warr, show=show_pins)
        en = self.connect_to_tracks(nmos['g'], ng_tid, min_len_mode=0)
        enb = self.connect_to_tracks(pmos['g'], pg_tid, min_len_mode=0)
        self.add_pin('en', en, show=show_pins)
        self.add_pin('enb', enb, show=show_pins)

        # draw VDD/VSS
        sup_w = vss_tid.width
        xl, xr = self.bound_box.left_unit, self.bound_box.right_unit
        vss = self.add_wires(hm_layer, vss_tid.base_index, xl, xr, width=sup_w, unit_mode=True)
        vdd = self.add_wires(hm_layer, vdd_tid.base_index, xl, xr, width=sup_w, unit_mode=True)
        self.add_pin('VSS', vss, show=show_pins)
        self.add_pin('VDD', vdd, show=show_pins)

        # set properties
        self._sch_params = dict(
            lch=config['lch'],
            wp=wp,
            wn=wn,
            thp=config['thp'],
            thn=config['thn'],
            segp=seg,
            segn=seg,
        )

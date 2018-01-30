# -*- coding: utf-8 -*-

from typing import TYPE_CHECKING, Dict, Any, Set

from bag.layout.routing import TrackManager, TrackID
from abs_templates_ec.laygo.core import LaygoBase

if TYPE_CHECKING:
    from bag.layout import TemplateDB


class Inverter(LaygoBase):
    """A single inverter.

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
        super(Inverter, self).__init__(temp_db, lib_name, params, used_names, **kwargs)

    @classmethod
    def get_params_info(cls):
        # type: () -> Dict[str, str]
        return dict(
            config='laygo configuration dictionary.',
            wp='pmos widths.',
            wn='nmos widths.',
            fg='number of fingers.',
            tr_widths='Track width dictionary.',
            tr_spaces='Track spacing dictionary.',
            in_tidx='Input track index.',
            out_tidx='Output track index.',
            outp_tidx='PMOS horizontal output track index.',
            outn_tidx='NMOS horizontal output track index.',
            show_pins='True to draw pin geometries.',
        )

    @classmethod
    def get_default_param_values(cls):
        # type: () -> Dict[str, Any]
        return dict(
            in_tidx=None,
            out_tidx=None,
            outp_tidx=None,
            outn_tidx=None,
            show_pins=True,
        )

    def draw_layout(self):
        """Draw the layout of a dynamic latch chain.
        """

        config = self.params['config']
        wp = self.params['wp']
        wn = self.params['wn']
        fg = self.params['fg']
        tr_widths = self.params['tr_widths']
        tr_spaces = self.params['tr_spaces']
        show_pins = self.params['show_pins']
        in_tidx = self.params['in_tidx']
        out_tidx = self.params['out_tidx']
        outp_tidx = self.params['outp_tidx']
        outn_tidx = self.params['outn_tidx']

        wp_row = config['wp']
        wn_row = config['wn']
        thp = config['thp']
        thn = config['thn']
        row_kwargs = config['row_kwargs']
        num_g_tracks = config['ng_tracks']
        num_gb_tracks = config['ngb_tracks']
        num_ds_tracks = config['nds_tracks']
        tr_w_sup = config['tr_w_supply']

        if wp < 0 or wp > wp_row or wn < 0 or wn > wn_row:
            raise ValueError('Invalid choice of wp and/or wn.')

        tr_manager = TrackManager(self.grid, tr_widths, tr_spaces)

        # get row information
        row_list = ['nch', 'pch']
        orient_list = ['MX', 'R0']
        thres_list = [thn, thp]
        w_list = [wn_row, wp_row]

        # specify row types
        self.set_row_types(row_list, w_list, orient_list, thres_list, False, 0,
                           num_g_tracks, num_gb_tracks, num_ds_tracks, guard_ring_nf=0,
                           row_kwargs=row_kwargs, num_col=fg)

        # get track information
        hm_layer = self.conn_layer + 1
        vm_layer = hm_layer + 1
        tr_w_in = tr_manager.get_width(hm_layer, 'in')
        tr_w_out_h = tr_manager.get_width(hm_layer, 'out')
        tr_w_out_v = tr_manager.get_width(vm_layer, 'out')

        # add blocks and collect wires
        num2 = fg // 2
        num1 = fg - 2 * num2
        p2 = self.add_laygo_primitive('fg2d', loc=(0, 1), nx=num2, spx=2, w=wp)
        n2 = self.add_laygo_primitive('fg2d', loc=(0, 0), nx=num2, spx=2, w=wn)
        vdd_list = p2.get_all_port_pins('s')
        vss_list = n2.get_all_port_pins('s')
        in_list = p2.get_all_port_pins('g')
        in_list.extend(n2.get_all_port_pins('g'))
        outp_list = p2.get_all_port_pins('d')
        outn_list = n2.get_all_port_pins('d')
        if num1 > 0:
            p1 = self.add_laygo_primitive('fg1d', loc=(2 * num2, 1), w=wp)
            n1 = self.add_laygo_primitive('fg1d', loc=(2 * num2, 0), w=wn)
            vdd_list.extend(p1.get_all_port_pins('s'))
            vss_list.extend(n1.get_all_port_pins('s'))
            in_list.extend(p1.get_all_port_pins('g'))
            in_list.extend(n1.get_all_port_pins('g'))
            outp_list.extend(p1.get_all_port_pins('d'))
            outn_list.extend(n1.get_all_port_pins('d'))

        # compute overall block size and fill spaces
        self.fill_space()

        # connect input
        if in_tidx is None:
            loc = tr_manager.place_wires(hm_layer, ['in'])[1][0]
            in_tidx = self.get_track_index(0, 'g', loc)
        tid = TrackID(hm_layer, in_tidx, width=tr_w_in)
        in_warr = self.connect_to_tracks(in_list, tid)

        # connect output
        out_loc = tr_manager.place_wires(hm_layer, ['out'])[1][0]
        if outp_tidx is None:
            outp_tidx = self.get_track_index(1, 'gb', out_loc)
        tid = TrackID(hm_layer, outp_tidx, width=tr_w_out_h)
        outp_warr = self.connect_to_tracks(outp_list, tid, min_len_mode=0)
        if outn_tidx is None:
            outn_tidx = self.get_track_index(0, 'gb', out_loc)
        tid = TrackID(hm_layer, outn_tidx, width=tr_w_out_h)
        outn_warr = self.connect_to_tracks(outn_list, tid, min_len_mode=0)
        if out_tidx is None:
            out_tidx = self.grid.coord_to_nearest_track(vm_layer, outp_warr.middle, half_track=True)
        tid = TrackID(vm_layer, out_tidx, width=tr_w_out_v)
        out_warr = self.connect_to_tracks([outp_warr, outn_warr], tid)

        # connect supplies
        tid = TrackID(hm_layer, -0.5, width=tr_w_sup)
        vss_warr = self.connect_to_tracks(vss_list, tid)
        tid = TrackID(hm_layer, self.grid.coord_to_track(hm_layer, self.bound_box.top_unit, unit_mode=True),
                      width=tr_w_sup)
        vdd_warr = self.connect_to_tracks(vdd_list, tid)

        # export
        self.add_pin('VSS', vss_warr, show=show_pins)
        self.add_pin('VDD', vdd_warr, show=show_pins)
        self.add_pin('in', in_warr, show=show_pins)
        self.add_pin('out', out_warr, show=show_pins)

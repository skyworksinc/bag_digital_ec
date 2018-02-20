# -*- coding: utf-8 -*-

from typing import TYPE_CHECKING, Dict, Any, Set

from bag.layout.routing import TrackManager, TrackID

from .core import StdCellTemplate

if TYPE_CHECKING:
    from bag.layout import TemplateDB


class Inverter(StdCellTemplate):
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
        StdCellTemplate.__init__(self, temp_db, lib_name, params, used_names, **kwargs)

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
        """Draw the layout of an inverter
        """

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

        if sig_locs is None:
            sig_locs = {}
        in_tidx = sig_locs.get('in', None)
        outp_tidx = sig_locs.get('outp', None)
        outn_tidx = sig_locs.get('outn', None)
        out_tidx = sig_locs.get('out', None)

        vss_tid, vdd_tid = self.setup_floorplan(config, seg)

        tr_manager = TrackManager(self.grid, tr_widths, tr_spaces)

        # get track information
        hm_layer = self.conn_layer + 1
        vm_layer = hm_layer + 1
        tr_w_in = tr_manager.get_width(hm_layer, 'in')
        tr_w_out_h = tr_manager.get_width(hm_layer, 'out')
        tr_w_out_v = tr_manager.get_width(vm_layer, 'out')

        # add blocks and collect wires
        num2 = seg // 2
        num1 = seg - 2 * num2
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
        vss_warr = self.connect_to_tracks(vss_list, vss_tid)
        vdd_warr = self.connect_to_tracks(vdd_list, vdd_tid)

        # export
        self.add_pin('VSS', vss_warr, show=show_pins)
        self.add_pin('VDD', vdd_warr, show=show_pins)
        self.add_pin('in', in_warr, show=show_pins)
        self.add_pin('out', out_warr, show=show_pins)


class InverterTristate(StdCellTemplate):
    """A gated inverter with two enable signals.

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
        StdCellTemplate.__init__(self, temp_db, lib_name, params, used_names, **kwargs)

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
        """Draw the layout of an inverter
        """

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

        vss_tid, vdd_tid = self.setup_floorplan(config, seg * 2)

        if sig_locs is None:
            sig_locs = {}
        in_tidx = sig_locs.get('in', None)
        outp_tidx = sig_locs.get('outp', None)
        outn_tidx = sig_locs.get('outn', None)
        out_tidx = sig_locs.get('out', None)
        enb_tidx = sig_locs.get('enb', None)
        en_tidx = sig_locs.get('en', None)

        tr_manager = TrackManager(self.grid, tr_widths, tr_spaces)

        # get track information
        hm_layer = self.conn_layer + 1
        vm_layer = hm_layer + 1
        tr_w_in = tr_manager.get_width(hm_layer, 'in')
        tr_w_en = tr_manager.get_width(hm_layer, 'en')
        tr_w_out_h = tr_manager.get_width(hm_layer, 'out')
        tr_w_out_v = tr_manager.get_width(vm_layer, 'out')

        # add blocks and collect wires
        numr = (seg // 2)
        numl = seg - numr
        pl = self.add_laygo_primitive('stack2s', loc=(0, 1), nx=numl, spx=4, w=wp)
        nl = self.add_laygo_primitive('stack2s', loc=(0, 0), nx=numl, spx=4, w=wn)
        vdd_list = pl.get_all_port_pins('s')
        vss_list = nl.get_all_port_pins('s')
        outp_list = pl.get_all_port_pins('d')
        outn_list = nl.get_all_port_pins('d')
        enb_list = pl.get_all_port_pins('g1')
        en_list = nl.get_all_port_pins('g1')
        in_list = pl.get_all_port_pins('g0')
        in_list.extend(nl.get_all_port_pins('g0'))
        if numr > 0:
            pr = self.add_laygo_primitive('stack2s', loc=(2, 1), nx=numr, flip=True, spx=4, w=wp)
            nr = self.add_laygo_primitive('stack2s', loc=(2, 0), nx=numr, flip=True, spx=4, w=wn)
            vdd_list.extend(pr.get_all_port_pins('s'))
            vss_list.extend(nr.get_all_port_pins('s'))
            outp_list.extend(pr.get_all_port_pins('d'))
            outn_list.extend(nr.get_all_port_pins('d'))
            enb_list.extend(pr.get_all_port_pins('g1'))
            en_list.extend(nr.get_all_port_pins('g1'))
            in_list.extend(pr.get_all_port_pins('g0'))
            in_list.extend(nr.get_all_port_pins('g0'))

        # compute overall block size and fill spaces
        self.fill_space()

        # get track locations
        if en_tidx is None:
            ntr = self.get_num_tracks(0, 'g')
            loc = tr_manager.align_wires(hm_layer, ['en'], ntr, alignment=1)[0]
            en_tidx = self.get_track_index(0, 'g', loc)
        if enb_tidx is None:
            ntr = self.get_num_tracks(1, 'g')
            loc = tr_manager.align_wires(hm_layer, ['en'], ntr, alignment=1)[0]
            enb_tidx = self.get_track_index(1, 'g', loc)
        if in_tidx is None:
            in_tidx2 = int(round(2 * (en_tidx + enb_tidx)))
            if in_tidx2 % 4 == 0:
                in_tidx = in_tidx2 // 4
            elif in_tidx2 % 2 == 0:
                in_tidx = in_tidx2 / 4
            else:
                in_tidx = (in_tidx2 + 1) / 4
        out_loc = tr_manager.place_wires(hm_layer, ['out'])[1][0]
        if outp_tidx is None:
            outp_tidx = self.get_track_index(1, 'gb', out_loc)
        if outn_tidx is None:
            outn_tidx = self.get_track_index(0, 'gb', out_loc)

        # connect wires
        tid = TrackID(hm_layer, in_tidx, width=tr_w_in)
        in_warr = self.connect_to_tracks(in_list, tid)
        tid = TrackID(hm_layer, en_tidx, width=tr_w_en)
        en_warr = self.connect_to_tracks(en_list, tid)
        tid = TrackID(hm_layer, enb_tidx, width=tr_w_en)
        enb_warr = self.connect_to_tracks(enb_list, tid)
        tid = TrackID(hm_layer, outp_tidx, width=tr_w_out_h)
        outp_warr = self.connect_to_tracks(outp_list, tid)
        tid = TrackID(hm_layer, outn_tidx, width=tr_w_out_h)
        outn_warr = self.connect_to_tracks(outn_list, tid)

        # connect output
        if out_tidx is None:
            out_tidx = self.grid.coord_to_nearest_track(vm_layer, outp_warr.middle, half_track=True)
        tid = TrackID(vm_layer, out_tidx, width=tr_w_out_v)
        out_warr = self.connect_to_tracks([outp_warr, outn_warr], tid)

        # connect supplies
        vss_warr = self.connect_to_tracks(vss_list, vss_tid)
        vdd_warr = self.connect_to_tracks(vdd_list, vdd_tid)

        # export
        self.add_pin('VSS', vss_warr, show=show_pins)
        self.add_pin('VDD', vdd_warr, show=show_pins)
        self.add_pin('in', in_warr, show=show_pins)
        self.add_pin('en', en_warr, show=show_pins)
        self.add_pin('enb', enb_warr, show=show_pins)
        self.add_pin('out', out_warr, show=show_pins)

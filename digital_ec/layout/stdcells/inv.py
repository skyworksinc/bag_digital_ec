# -*- coding: utf-8 -*-

"""This module contains layout generator for various kinds of inverters."""

from typing import TYPE_CHECKING, Dict, Any, Set

from bag.layout.routing import TrackManager, TrackID

from .core import StdLaygoTemplate

if TYPE_CHECKING:
    from bag.layout import TemplateDB


class Inverter(StdLaygoTemplate):
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
        pout_tidx = sig_locs.get('pout', None)
        nout_tidx = sig_locs.get('nout', None)
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
        pinv = self.add_laygo_mos(1, 0, seg, w=wp)
        ninv = self.add_laygo_mos(0, 0, seg, w=wn)
        vdd = pinv['s']
        vss = ninv['s']
        pout = pinv['d']
        nout = ninv['d']
        pin = pinv['g']
        nin = ninv['g']

        # compute overall block size and fill spaces
        self.fill_space()

        # connect input
        if in_tidx is None:
            loc = tr_manager.place_wires(hm_layer, ['in'])[1][0]
            in_tidx = self.get_track_index(0, 'g', loc)
        tid = TrackID(hm_layer, in_tidx, width=tr_w_in)
        in_warr = self.connect_to_tracks([pin, nin], tid)

        # connect output
        out_loc = tr_manager.place_wires(hm_layer, ['out'])[1][0]
        if pout_tidx is None:
            pout_tidx = self.get_track_index(1, 'gb', out_loc)
        tid = TrackID(hm_layer, pout_tidx, width=tr_w_out_h)
        pout_warr = self.connect_to_tracks(pout, tid, min_len_mode=0)
        if nout_tidx is None:
            nout_tidx = self.get_track_index(0, 'gb', out_loc)
        tid = TrackID(hm_layer, nout_tidx, width=tr_w_out_h)
        nout_warr = self.connect_to_tracks(nout, tid, min_len_mode=0)
        if out_tidx is None:
            out_tidx = self.grid.coord_to_nearest_track(vm_layer, pout_warr.middle, half_track=True)
        tid = TrackID(vm_layer, out_tidx, width=tr_w_out_v)
        out_warr = self.connect_to_tracks([pout_warr, nout_warr], tid)

        # connect supplies
        vss_warr = self.connect_to_tracks(vss, vss_tid)
        vdd_warr = self.connect_to_tracks(vdd, vdd_tid)

        # export
        self.add_pin('VSS', vss_warr, show=show_pins)
        self.add_pin('VDD', vdd_warr, show=show_pins)
        self.add_pin('in', in_warr, show=show_pins)
        self.add_pin('out', out_warr, show=show_pins)

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


class InverterTristate(StdLaygoTemplate):
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
        pout_tidx = sig_locs.get('pout', None)
        nout_tidx = sig_locs.get('nout', None)
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
        pinv = self.add_laygo_mos(1, 0, seg, gate_loc='s', stack=True, w=wp)
        ninv = self.add_laygo_mos(0, 0, seg, gate_loc='s', stack=True, w=wn)
        vdd = pinv['s']
        vss = ninv['s']
        pout = pinv['d']
        nout = ninv['d']
        enb = pinv['g1']
        en = ninv['g1']
        pin = pinv['g0']
        nin = ninv['g0']

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
        if pout_tidx is None:
            pout_tidx = self.get_track_index(1, 'gb', out_loc)
        if nout_tidx is None:
            nout_tidx = self.get_track_index(0, 'gb', out_loc)

        # connect wires
        tid = TrackID(hm_layer, in_tidx, width=tr_w_in)
        in_warr = self.connect_to_tracks([pin, nin], tid)
        tid = TrackID(hm_layer, en_tidx, width=tr_w_en)
        en_warr = self.connect_to_tracks(en, tid)
        tid = TrackID(hm_layer, enb_tidx, width=tr_w_en)
        enb_warr = self.connect_to_tracks(enb, tid)
        tid = TrackID(hm_layer, pout_tidx, width=tr_w_out_h)
        pout_warr = self.connect_to_tracks(pout, tid, min_len_mode=0)
        tid = TrackID(hm_layer, nout_tidx, width=tr_w_out_h)
        nout_warr = self.connect_to_tracks(nout, tid, min_len_mode=0)

        # connect output
        if out_tidx is None:
            out_tidx = self.grid.coord_to_nearest_track(vm_layer, pout_warr.middle, half_track=True)
        tid = TrackID(vm_layer, out_tidx, width=tr_w_out_v)
        out_warr = self.connect_to_tracks([pout_warr, nout_warr], tid)

        # connect supplies
        vss_warr = self.connect_to_tracks(vss, vss_tid)
        vdd_warr = self.connect_to_tracks(vdd, vdd_tid)

        # export
        self.add_pin('VSS', vss_warr, show=show_pins)
        self.add_pin('VDD', vdd_warr, show=show_pins)
        self.add_pin('in', in_warr, show=show_pins)
        self.add_pin('en', en_warr, show=show_pins)
        self.add_pin('enb', enb_warr, show=show_pins)
        self.add_pin('out', out_warr, show=show_pins)

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

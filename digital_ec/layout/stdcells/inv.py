# -*- coding: utf-8 -*-

"""This module contains layout generator for various kinds of inverters."""

from typing import TYPE_CHECKING, Dict, Any, Set, Union, Iterable

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
            seg='number of segments.',
            tr_widths='Track width dictionary.',
            tr_spaces='Track spacing dictionary.',
            wp='pmos width.',
            wn='nmos width.',
            row_layout_info='Row layout information dictionary.',
            sig_locs='Signal track location dictionary.',
            out_vm='True to draw output on vertical metal layer.',
            show_pins='True to draw pin geometries.',
        )

    @classmethod
    def get_default_param_values(cls):
        # type: () -> Dict[str, Any]
        return dict(
            wp=None,
            wn=None,
            row_layout_info=None,
            sig_locs=None,
            out_vm=True,
            show_pins=True,
        )

    def draw_layout(self):
        config = self.params['config']
        row_layout_info = self.params['row_layout_info']
        wp = self.params['wp']
        wn = self.params['wn']
        seg = self.params['seg']
        tr_widths = self.params['tr_widths']
        tr_spaces = self.params['tr_spaces']
        sig_locs = self.params['sig_locs']
        out_vm = self.params['out_vm']
        show_pins = self.params['show_pins']

        wp_row = config['wp']
        wn_row = config['wn']
        if wp is None:
            wp = wp_row
        if wn is None:
            wn = wn_row
        if wp < 0 or wp > wp_row or wn < 0 or wn > wn_row:
            raise ValueError('Invalid choice of wp and/or wn.')

        if sig_locs is None:
            sig_locs = {}
        in_tidx = sig_locs.get('in', None)
        pout_tidx = sig_locs.get('pout', None)
        nout_tidx = sig_locs.get('nout', None)
        out_tidx = sig_locs.get('out', None)

        vss_tid, vdd_tid = self.setup_floorplan(config, row_layout_info, seg)

        tr_manager = TrackManager(self.grid, tr_widths, tr_spaces, half_space=True)

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
        if out_vm:
            if out_tidx is None:
                out_tidx = self.grid.coord_to_nearest_track(vm_layer, pout_warr.middle,
                                                            half_track=True)
            tid = TrackID(vm_layer, out_tidx, width=tr_w_out_v)
            out_warr = self.connect_to_tracks([pout_warr, nout_warr], tid)
            self.add_pin('out', out_warr, show=show_pins)

        # connect supplies
        vss_warr = self.connect_to_tracks(vss, vss_tid)
        vdd_warr = self.connect_to_tracks(vdd, vdd_tid)

        # export
        self.add_pin('VSS', vss_warr, show=show_pins)
        self.add_pin('VDD', vdd_warr, show=show_pins)
        self.add_pin('in', in_warr, show=show_pins)
        self.add_pin('pout', pout_warr, label='out', show=False)
        self.add_pin('nout', nout_warr, label='out', show=False)

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
            seg='number of segments.',
            tr_widths='Track width dictionary.',
            tr_spaces='Track spacing dictionary.',
            wp='pmos width.',
            wn='nmos width.',
            row_layout_info='Row layout information dictionary.',
            sig_locs='Signal track location dictionary.',
            out_vm='True to draw output on vertical metal layer.',
            show_pins='True to draw pin geometries.',
        )

    @classmethod
    def get_default_param_values(cls):
        # type: () -> Dict[str, Any]
        return dict(
            wp=None,
            wn=None,
            row_layout_info=None,
            sig_locs=None,
            out_vm=True,
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
        sig_locs = self.params['sig_locs']
        out_vm = self.params['out_vm']
        show_pins = self.params['show_pins']

        wp_row = config['wp']
        wn_row = config['wn']
        if wp is None:
            wp = wp_row
        if wn is None:
            wn = wn_row
        if wp < 0 or wp > wp_row or wn < 0 or wn > wn_row:
            raise ValueError('Invalid choice of wp and/or wn.')

        vss_tid, vdd_tid = self.setup_floorplan(config, row_layout_info, seg * 2)

        if sig_locs is None:
            sig_locs = {}
        in_tidx = sig_locs.get('in', None)
        pout_tidx = sig_locs.get('pout', None)
        nout_tidx = sig_locs.get('nout', None)
        out_tidx = sig_locs.get('out', None)
        enb_tidx = sig_locs.get('enb', None)
        en_tidx = sig_locs.get('en', None)

        tr_manager = TrackManager(self.grid, tr_widths, tr_spaces, half_space=True)

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
        if out_vm:
            if out_tidx is None:
                out_tidx = self.grid.coord_to_nearest_track(vm_layer, pout_warr.middle,
                                                            half_track=True)
            tid = TrackID(vm_layer, out_tidx, width=tr_w_out_v)
            out_warr = self.connect_to_tracks([pout_warr, nout_warr], tid)
            self.add_pin('out', out_warr, show=show_pins)

        # connect supplies
        vss_warr = self.connect_to_tracks(vss, vss_tid)
        vdd_warr = self.connect_to_tracks(vdd, vdd_tid)

        # export
        self.add_pin('VSS', vss_warr, show=show_pins)
        self.add_pin('VDD', vdd_warr, show=show_pins)
        self.add_pin('in', in_warr, show=show_pins)
        self.add_pin('en', en_warr, show=show_pins)
        self.add_pin('enb', enb_warr, show=show_pins)
        self.add_pin('pout', pout_warr, label='out', show=False)
        self.add_pin('nout', nout_warr, label='out', show=False)

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


class InvChain(StdLaygoTemplate):
    """An inverter chain.

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
        self._mid_tidx = None

    @property
    def sch_params(self):
        # type: () -> Dict[str, Any]
        return self._sch_params

    @property
    def mid_tidx(self):
        # type: () -> Union[float, int]
        return self._mid_tidx

    @classmethod
    def get_params_info(cls):
        # type: () -> Dict[str, str]
        return dict(
            config='laygo configuration dictionary.',
            seg_list='list of number of segments.',
            tr_widths='Track width dictionary.',
            tr_spaces='Track spacing dictionary.',
            wp_list='list of PMOS widths.',
            wn_list='list of NMOS widths.',
            sig_locs='Signal track location dictionary.',
            row_layout_info='Row layout information dictionary.',
            show_pins='True to draw pin geometries.',
        )

    @classmethod
    def get_default_param_values(cls):
        # type: () -> Dict[str, Any]
        return dict(
            wp_list=None,
            wn_list=None,
            sig_locs=None,
            row_layout_info=None,
            show_pins=True,
        )

    def draw_layout(self):
        config = self.params['config']
        seg_list = self.params['seg_list']
        tr_widths = self.params['tr_widths']
        tr_spaces = self.params['tr_spaces']
        wp_list = self.params['wp_list']
        wn_list = self.params['wn_list']
        sig_locs = self.params['sig_locs']
        row_layout_info = self.params['row_layout_info']
        show_pins = self.params['show_pins']

        ninv = len(seg_list)
        wp_row = config['wp']
        wn_row = config['wn']
        if wp_list is None:
            wp_list = [wp_row] * ninv
        elif len(wp_list) != ninv:
            raise ValueError('length of wp_list != %d' % ninv)
        if wn_list is None:
            wn_list = [wn_row] * ninv
        elif len(wn_list) != ninv:
            raise ValueError('length of wn_list != %d' % ninv)

        # TODO: remove restriction
        if ninv != 2:
            raise ValueError('Now only 2 inverters are supported.')

        seg_in, seg_out = seg_list
        seg_tot = self.compute_num_cols(seg_list)
        vss_tid, vdd_tid = self.setup_floorplan(config, row_layout_info, seg_tot)

        tr_manager = TrackManager(self.grid, tr_widths, tr_spaces, half_space=True)

        if sig_locs is None:
            sig_locs = {}

        # get track information
        hm_layer = self.conn_layer + 1
        vm_layer = hm_layer + 1
        hm_w_g = tr_manager.get_width(hm_layer, 'in')
        hm_w_d = tr_manager.get_width(hm_layer, 'out')
        vm_w_d = tr_manager.get_width(vm_layer, 'out')
        g_locs = tr_manager.place_wires(hm_layer, ['in', 'in'])[1]
        d_locs = tr_manager.place_wires(hm_layer, ['out', 'out'])[1]
        ng0_tid = self.make_track_id(0, 'g', g_locs[0], width=hm_w_g)
        pg0_tid = self.make_track_id(1, 'g', g_locs[0], width=hm_w_g)
        nd0_tid = self.make_track_id(0, 'gb', d_locs[0], width=hm_w_d)
        nd1_tid = self.make_track_id(0, 'gb', d_locs[1], width=hm_w_d)
        pd0_tid = self.make_track_id(1, 'gb', d_locs[0], width=hm_w_d)
        pd1_tid = self.make_track_id(1, 'gb', d_locs[1], width=hm_w_d)

        if 'in' in sig_locs:
            in_tid = TrackID(hm_layer, sig_locs['in'], width=hm_w_g)
            if in_tid.base_index == pg0_tid.base_index:
                mid_tid = ng0_tid
            else:
                mid_tid = pg0_tid
        else:
            in_tid = ng0_tid
            mid_tid = pg0_tid

        # add blocks and collect wires
        pinv0 = self.add_laygo_mos(1, 0, seg_in, w=wp_list[0])
        ninv0 = self.add_laygo_mos(0, 0, seg_in, w=wn_list[0])
        pinv1 = self.add_laygo_mos(1, seg_in, seg_out, w=wp_list[1])
        ninv1 = self.add_laygo_mos(0, seg_in, seg_out, w=wn_list[1])

        # compute overall block size and fill spaces
        self.fill_space()

        # connect input
        in_warr = self.connect_to_tracks([pinv0['g'], ninv0['g']], in_tid, min_len_mode=0)
        self.add_pin('in', in_warr, show=show_pins)

        # connect output
        pout_warr = self.connect_to_tracks(pinv1['d'], pd0_tid, min_len_mode=0)
        nout_warr = self.connect_to_tracks(ninv1['d'], nd0_tid, min_len_mode=0)
        if 'out' in sig_locs:
            out_tidx = sig_locs['out']
        else:
            out_tidx = self.grid.coord_to_nearest_track(vm_layer, pout_warr.middle,
                                                        half_track=True)
        tid = TrackID(vm_layer, out_tidx, width=vm_w_d)
        out_warr = self.connect_to_tracks([pout_warr, nout_warr], tid)
        self.add_pin('out', out_warr, show=show_pins)

        # connect middle
        pout_warr = self.connect_to_tracks(pinv0['d'], pd1_tid, min_len_mode=0)
        nout_warr = self.connect_to_tracks(ninv0['d'], nd1_tid, min_len_mode=0)
        mid_warr = self.connect_to_tracks([pinv1['g'], ninv1['g']], mid_tid, min_len_mode=-1)
        mid_tidx = self.grid.coord_to_nearest_track(vm_layer, pout_warr.middle,
                                                    half_track=True)
        tid = TrackID(vm_layer, mid_tidx, width=vm_w_d)
        self.connect_to_tracks([pout_warr, nout_warr, mid_warr], tid)

        # connect supplies
        vdd = [pinv0['s'], pinv1['s']]
        vss = [ninv0['s'], ninv1['s']]
        vss_warr = self.connect_to_tracks(vss, vss_tid)
        vdd_warr = self.connect_to_tracks(vdd, vdd_tid)
        self.add_pin('VSS', vss_warr, show=show_pins)
        self.add_pin('VDD', vdd_warr, show=show_pins)

        # set properties
        self._sch_params = dict(
            lch=config['lch'],
            thp=config['thp'],
            thn=config['thn'],
            segp_list=seg_list,
            segn_list=seg_list,
            wp_list=wp_list,
            wn_list=wn_list,
        )
        self._mid_tidx = mid_tidx

    @classmethod
    def compute_num_cols(cls, seg_list):
        # type: (Iterable[int]) -> int
        return sum(seg_list)

# -*- coding: utf-8 -*-

"""This module contains layout generator for various kinds of muxes."""

from typing import TYPE_CHECKING, Dict, Any, Set

from bag.layout.routing import TrackManager, TrackID

from .core import StdLaygoTemplate, StdDigitalTemplate
from .inv import Inverter, InverterTristate

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

    def get_layout_basename(self):
        return 'pass_gate_%dx' % self.params['seg']

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


class MuxTristate(StdDigitalTemplate):
    """A mux built with tristate inverters.

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
        self._seg_in = None

    @property
    def sch_params(self):
        # type: () -> Dict[str, Any]
        return self._sch_params

    @property
    def seg_in(self):
        # type: () -> int
        return self._seg_in

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
            show_pins=True,
        )

    def get_layout_basename(self):
        return 'mux_inv_%dx' % self.params['seg']

    def draw_layout(self):
        blk_sp = 2
        fanout = 4

        config = self.params['config']

        seg = self.params['seg']
        tr_widths = self.params['tr_widths']
        tr_spaces = self.params['tr_spaces']
        wp = self.params['wp']
        wn = self.params['wn']
        row_layout_info = self.params['row_layout_info']
        sig_locs = self.params['sig_locs']
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

        # setup floorplan
        params = self.params.copy()
        params['wp'] = wp
        params['wn'] = wn
        params['show_pins'] = False
        params['sig_locs'] = None
        params['out_vm'] = True
        if row_layout_info is not None:
            self.initialize(row_layout_info, 1)
        else:
            inv_master = self.new_template(params=params, temp_cls=Inverter)
            params['row_layout_info'] = row_layout_info = inv_master.row_layout_info
            self.initialize(row_layout_info, 1)

        # compute track locations
        hm_layer = self.conn_layer + 1
        ym_layer = hm_layer + 1
        tr_manager = TrackManager(self.grid, tr_widths, tr_spaces, half_space=True)
        g_locs = tr_manager.place_wires(hm_layer, ['in', 'in'])[1]
        d_locs = tr_manager.place_wires(hm_layer, ['out', 'out'])[1]
        ng0_tidx = self.get_track_index(0, 'g', g_locs[0])
        ng1_tidx = self.get_track_index(0, 'g', g_locs[1])
        pg0_tidx = self.get_track_index(1, 'g', g_locs[0])
        pg1_tidx = self.get_track_index(1, 'g', g_locs[1])
        nd0_tidx = self.get_track_index(0, 'gb', d_locs[0])
        nd1_tidx = self.get_track_index(0, 'gb', d_locs[1])
        pd0_tidx = self.get_track_index(1, 'gb', d_locs[0])
        pd1_tidx = self.get_track_index(1, 'gb', d_locs[1])

        pen_tidx = sig_locs.get('pen', pg1_tidx)
        nen_tidx = sig_locs.get('nen', ng1_tidx)
        in0_tidx = sig_locs.get('in0', pg0_tidx)
        in1_tidx = sig_locs.get('in1', ng0_tidx)
        out_vm_tidx = sig_locs.get('out', None)

        # make masters
        seg_in = max(1, int(round(seg / (fanout // 2))))
        seg_sel = max(1, int(round(seg_in // fanout)))
        params['sig_locs'] = {'in': pen_tidx, 'pout': pd0_tidx, 'nout': nd0_tidx}
        params['out_vm'] = False
        inv_master = self.new_template(params=params, temp_cls=Inverter)

        params['seg'] = seg_sel
        params['sig_locs'] = {'in': pen_tidx, 'pout': pd0_tidx, 'nout': nd0_tidx}
        params['out_vm'] = True
        sel_master = self.new_template(params=params, temp_cls=Inverter)

        params['seg'] = seg_in
        params['sig_locs'] = {'in': in0_tidx, 'pout': pd1_tidx, 'nout': nd1_tidx,
                              'en': nen_tidx, 'enb': pen_tidx}
        params['out_vm'] = False
        t0_master = self.new_template(params=params, temp_cls=InverterTristate)
        params['sig_locs'] = {'in': in1_tidx, 'pout': pd1_tidx, 'nout': nd1_tidx,
                              'en': nen_tidx, 'enb': pen_tidx}
        t1_master = self.new_template(params=params, temp_cls=InverterTristate)

        # set size
        sel_ncol = sel_master.num_cols
        sel_sep = blk_sp + 1 if sel_ncol % 2 == 1 else blk_sp
        t0_ncol = t0_master.num_cols
        t1_ncol = t1_master.num_cols
        inv_ncol = inv_master.num_cols
        num_cols = sel_ncol + t0_ncol + t1_ncol + inv_ncol + 2 * blk_sp + sel_sep
        self.set_digital_size(num_cols)

        # add instances
        t0_col = sel_ncol + sel_sep
        t1_col = t0_col + t0_ncol + blk_sp
        inv_col = num_cols - inv_ncol
        sel = self.add_digital_block(sel_master, (0, 0))
        t0 = self.add_digital_block(t0_master, (t0_col, 0))
        t1 = self.add_digital_block(t1_master, (t1_col, 0))
        inv = self.add_digital_block(inv_master, (inv_col, 0))

        self.fill_space()

        # connect/export VSS/VDD
        vss_list, vdd_list = [], []
        for inst in (sel, t0, t1, inv):
            vss_list.append(inst.get_pin('VSS'))
            vdd_list.append(inst.get_pin('VDD'))
        self.add_pin('VSS', self.connect_wires(vss_list), show=show_pins)
        self.add_pin('VDD', self.connect_wires(vdd_list), show=show_pins)

        # export input/output
        self.add_pin('in0', t0.get_pin('in'), show=show_pins)
        self.add_pin('in1', t1.get_pin('in'), show=show_pins)
        pout = inv.get_pin('pout')
        nout = inv.get_pin('nout')
        if out_vm_tidx is None:
            out_vm_tidx = self.laygo_info.col_to_track(ym_layer, num_cols - 1)

        out = self.connect_to_tracks([pout, nout], TrackID(ym_layer, out_vm_tidx))
        self.add_pin('out', out, show=show_pins)

        # connect middle node
        col_idx = inv_col - blk_sp // 2
        tr_idx = self.laygo_info.col_to_track(ym_layer, col_idx)
        hm_list = [t0.get_pin('pout'), t0.get_pin('nout'), t1.get_pin('pout'), t1.get_pin('nout'),
                   inv.get_pin('in')]
        self.connect_to_tracks(hm_list, TrackID(ym_layer, tr_idx))

        # connect enables
        sel0l = self.extend_wires(t0.get_pin('en'), min_len_mode=0)[0]
        sel0r = self.extend_wires(t1.get_pin('enb'), min_len_mode=0)[0]
        sel1l = self.connect_wires([sel.get_pin('in'), t0.get_pin('enb')])[0]
        sel1r = self.extend_wires(t1.get_pin('en'), min_len_mode=0)[0]
        self.add_pin('sel1_hm', sel1l, label='sel1', show=False)

        self.connect_to_track_wires(sel.get_pin('out'), sel0l)

        ym_tidx = self.grid.coord_to_nearest_track(ym_layer, sel0l.middle_unit, mode=1,
                                                   half_track=True, unit_mode=True)
        ym_tid = TrackID(ym_layer, ym_tidx)
        sel0l = self.connect_to_tracks(sel0l, ym_tid, min_len_mode=-1)
        sel1l = self.connect_to_tracks(sel1l, ym_tid, min_len_mode=1)
        self.add_pin('sel1', sel1l, show=show_pins)
        sel0l = self.connect_to_tracks(sel0l, TrackID(hm_layer, nd0_tidx), min_len_mode=1)
        sel1l = self.connect_to_tracks(sel1l, TrackID(hm_layer, pd0_tidx), min_len_mode=1)

        sel0_tidx = self.grid.find_next_track(ym_layer, sel0r.middle_unit, mode=-1, half_track=True,
                                              unit_mode=True)
        sel1_tidx = sel0_tidx + 1
        self.connect_to_tracks([sel0l, sel0r], TrackID(ym_layer, sel0_tidx))
        self.connect_to_tracks([sel1l, sel1r], TrackID(ym_layer, sel1_tidx))

        # set properties
        pseg_t0 = t0_master.sch_params['segp']
        nseg_t0 = t0_master.sch_params['segn']
        psel = sel_master.sch_params['segp']
        nsel = sel_master.sch_params['segn']
        self._sch_params = dict(
            lch=config['lch'],
            wp=wp,
            wn=wn,
            thp=config['thp'],
            thn=config['thn'],
            seg_dict=dict(pinv=seg, ninv=seg, pt0=pseg_t0, nt0=nseg_t0, psel=psel, nsel=nsel),
        )
        self._seg_in = seg_in

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

        wp_row = config['wp']
        wn_row = config['wn']

        if wp < 0 or wp > wp_row or wn < 0 or wn > wn_row:
            raise ValueError('Invalid choice of wp and/or wn.')

        # make masters
        sub_params = self.params.copy()
        sub_params['show_pins'] = False
        sub_params['sig_locs'] = None
        sub_params['out_vm'] = True
        inv_master = self.new_template(params=sub_params, temp_cls=Inverter)
        seg_t0 = int(round(seg / (2 * in_fanout))) * 2
        sub_params['seg'] = max(seg_t0, 2)
        sub_params['out_vm'] = False
        t0_master = self.new_template(params=sub_params, temp_cls=InverterTristate)
        seg_t1 = int(round(seg / (2 * fb_fanout))) * 2
        sub_params['seg'] = max(seg_t1, 2)
        t1_master = self.new_template(params=sub_params, temp_cls=InverterTristate)

        # setup floorplan
        t0_ncol = t0_master.num_cols
        t1_ncol = t1_master.num_cols
        inv_ncol = inv_master.num_cols
        num_cols = t0_ncol + t1_ncol + inv_ncol + blk_sp * 2
        self.setup_floorplan(config, num_cols)

        # change masters
        hm_layer = self.conn_layer + 1
        ym_layer = hm_layer + 1
        tr_manager = TrackManager(self.grid, tr_widths, tr_spaces, half_space=True)
        hm_w_g = tr_manager.get_width(hm_layer, 'in')
        hm_w_d = tr_manager.get_width(hm_layer, 'out')
        ym_w_in = tr_manager.get_width(ym_layer, 'in')
        g_locs = tr_manager.place_wires(hm_layer, ['in', 'in'])[1]
        d_locs = tr_manager.place_wires(hm_layer, ['out', 'out'])[1]
        ng0_tid = self.make_track_id(0, 'g', g_locs[0], width=hm_w_g)
        ng1_tid = self.make_track_id(0, 'g', g_locs[1], width=hm_w_g)
        pg0_tid = self.make_track_id(1, 'g', g_locs[0], width=hm_w_g)
        pg1_tid = self.make_track_id(1, 'g', g_locs[1], width=hm_w_g)
        nd0_tid = self.make_track_id(0, 'gb', d_locs[0], width=hm_w_d)
        nd1_tid = self.make_track_id(0, 'gb', d_locs[1], width=hm_w_d)
        pd0_tid = self.make_track_id(1, 'gb', d_locs[0], width=hm_w_d)
        pd1_tid = self.make_track_id(1, 'gb', d_locs[1], width=hm_w_d)

        sig_locs = {'in': ng1_tid.base_index, 'pout': pd1_tid.base_index,
                    'nout': nd1_tid.base_index}
        inv_master = inv_master.new_template_with(sig_locs=sig_locs)
        sig_locs = {'in': pg0_tid.base_index, 'pout': pd0_tid.base_index,
                    'nout': nd0_tid.base_index, 'en': ng0_tid.base_index,
                    'enb': pg1_tid.base_index}
        t1_master = t1_master.new_template_with(sig_locs=sig_locs)
        sig_locs = {'in': pg1_tid.base_index, 'pout': pd0_tid.base_index,
                    'nout': nd0_tid.base_index, 'en': ng1_tid.base_index,
                    'enb': pg0_tid.base_index}
        t0_master = t0_master.new_template_with(sig_locs=sig_locs)

        # add instances
        t1_col = t0_ncol + blk_sp
        inv_col = num_cols - inv_ncol
        t0 = self.add_laygo_template(t0_master, 0)
        t1 = self.add_laygo_template(t1_master, t1_col)
        inv = self.add_laygo_template(inv_master, inv_col)

        self.fill_space()

        # connect/export VSS/VDD
        vss_list, vdd_list = [], []
        for inst in (t0, t1, inv):
            vss_list.append(inst.get_pin('VSS'))
            vdd_list.append(inst.get_pin('VDD'))
        self.add_pin('VSS', self.connect_wires(vss_list), show=show_pins)
        self.add_pin('VDD', self.connect_wires(vdd_list), show=show_pins)

        # export input
        self.add_pin('in', t0.get_pin('in'), show=show_pins)

        # connect output
        out = inv.get_pin('out')
        in2 = t1.get_pin('in')
        self.connect_to_track_wires(in2, out)
        self.add_pin('out', out, show=show_pins)

        # connect middle node
        lay_info = self.laygo_info
        col = inv_col - blk_sp // 2
        ym_tid = TrackID(ym_layer, lay_info.col_to_track(ym_layer, col), width=ym_w_in)
        warrs = [t0.get_pin('pout'), t0.get_pin('nout'), t1.get_pin('pout'), t1.get_pin('nout'),
                 inv.get_pin('in')]
        self.connect_to_tracks(warrs, ym_tid)

        # connect clocks
        clk_col = t1_col + 1
        clkb_col = t1_col - blk_sp - 1
        clk_tid = TrackID(ym_layer, lay_info.col_to_track(ym_layer, clk_col), width=ym_w_in)
        clkb_tid = TrackID(ym_layer, lay_info.col_to_track(ym_layer, clkb_col), width=ym_w_in)
        clk = self.connect_to_tracks([t0.get_pin('en'), t1.get_pin('enb')], clk_tid)
        clkb = self.connect_to_tracks([t0.get_pin('enb'), t1.get_pin('en')], clkb_tid)
        self.add_pin('clk', clk, show=show_pins)
        self.add_pin('clkb', clkb, show=show_pins)

        # set properties
        self._sch_params = dict(
            lch=config['lch'],
            wp=wp,
            wn=wn,
            thp=config['thp'],
            thn=config['thn'],
            seg_dict=dict(pinv=seg, ninv=seg, pt0=seg_t0, nt0=seg_t0, pt1=seg_t1, nt1=seg_t1),
        )

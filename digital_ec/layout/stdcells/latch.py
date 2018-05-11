# -*- coding: utf-8 -*-


"""This module contains layout generator for various kinds of flip-flops."""

from typing import TYPE_CHECKING, Dict, Any, Set

from bag.layout.routing import TrackManager, TrackID

from .core import StdDigitalTemplate
from .inv import Inverter, InverterTristate

if TYPE_CHECKING:
    from bag.layout.template import TemplateDB


class LatchCK2(StdDigitalTemplate):
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
            pass_zero='True to allow a 0 input to pass straight through.',
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
            pass_zero=False,
            show_pins=True,
        )

    def get_layout_basename(self):
        if self.params['pass_zero']:
            return 'latch_ck2_pass0'
        else:
            return 'latch_ck2'

    def draw_layout(self):
        blk_sp = 2
        in_fanout = 4
        fb_fanout = 8

        config = self.params['config']

        seg = self.params['seg']
        tr_widths = self.params['tr_widths']
        tr_spaces = self.params['tr_spaces']
        wp = self.params['wp']
        wn = self.params['wn']
        row_layout_info = self.params['row_layout_info']
        sig_locs = self.params['sig_locs']
        pass_zero = self.params['pass_zero']
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
        ym_w_in = tr_manager.get_width(ym_layer, 'in')
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

        t0_in_tidx = sig_locs.get('in', pg1_tidx)
        t0_enb_tidx = sig_locs.get('pclkb', pg0_tidx)
        t0_en_tidx = sig_locs.get('nclk', ng0_tidx)
        t1_en_tidx = sig_locs.get('nclkb', ng1_tidx)
        clk_tidx = sig_locs.get('clk', None)
        clkb_tidx = sig_locs.get('clkb', None)

        # make masters
        seg_t1 = max(1, int(round(seg / (2 * fb_fanout))) * 2)
        seg_t0 = max(2 * seg_t1, max(2, int(round(seg / (2 * in_fanout))) * 2))
        params['sig_locs'] = {'in': t0_en_tidx, 'pout': pd1_tidx, 'nout': nd1_tidx}
        inv_master = self.new_template(params=params, temp_cls=Inverter)
        params['seg'] = seg_t0
        params['out_vm'] = False
        params['sig_locs'] = {'in': t0_in_tidx, 'pout': pd0_tidx, 'nout': nd0_tidx,
                              'en': t0_en_tidx, 'enb': t0_enb_tidx}
        params['pmos_switch'] = not pass_zero
        t0_master = self.new_template(params=params, temp_cls=InverterTristate)
        params['seg'] = seg_t1
        params['sig_locs'] = {'in': t0_enb_tidx, 'pout': pd0_tidx, 'nout': nd0_tidx,
                              'en': t1_en_tidx, 'enb': t0_in_tidx}
        params['pmos_switch'] = True
        t1_master = self.new_template(params=params, temp_cls=InverterTristate)

        # set size
        t0_ncol = t0_master.num_cols
        t1_ncol = t1_master.num_cols
        inv_ncol = inv_master.num_cols
        num_cols = t0_ncol + t1_ncol + inv_ncol + blk_sp * 2
        self.set_digital_size(num_cols)

        # add instances
        t1_col = t0_ncol + blk_sp
        inv_col = num_cols - inv_ncol
        t0 = self.add_digital_block(t0_master, (0, 0))
        t1 = self.add_digital_block(t1_master, (t1_col, 0))
        inv = self.add_digital_block(inv_master, (inv_col, 0))

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
        self.add_pin('out_hm', in2, label='out', show=show_pins)

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
        if clk_tidx is None:
            clk_tidx = lay_info.col_to_track(ym_layer, clk_col)
        clk_tid = TrackID(ym_layer, clk_tidx, width=ym_w_in)
        if clkb_tidx is None:
            clkb_tidx = lay_info.col_to_track(ym_layer, clkb_col)
        clkb_tid = TrackID(ym_layer, clkb_tidx, width=ym_w_in)
        t0_en = t0.get_pin('en')
        t1_en = t1.get_pin('en')
        t1_enb = t1.get_pin('enb')
        t1_enb = self.extend_wires(t1_enb, min_len_mode=-1)[0]
        clk = self.connect_to_tracks([t0_en, t1_enb], clk_tid)
        if not pass_zero:
            t0_enb = t0.get_pin('enb')
            t0_enb = self.extend_wires(t0_enb, min_len_mode=1)[0]
            clkb = self.connect_to_tracks([t0_enb, t1_en], clkb_tid)
            self.add_pin('pclkb', t0_enb, label='clkb', show=False)
        else:
            clkb = self.connect_to_tracks(t1_en, clkb_tid, min_len_mode=0)
        self.add_pin('clk', clk, show=show_pins)
        self.add_pin('clkb', clkb, show=show_pins)
        self.add_pin('nclk', t0_en, label='clk', show=False)
        self.add_pin('pclk', t1_enb, label='clk', show=False)
        self.add_pin('nclkb', t1_en, label='clkb', show=False)

        # set properties
        pseg_t0 = t0_master.sch_params['segp']
        self._sch_params = dict(
            lch=config['lch'],
            wp=wp,
            wn=wn,
            thp=config['thp'],
            thn=config['thn'],
            seg_dict=dict(pinv=seg, ninv=seg, pt0=pseg_t0, nt0=seg_t0, pt1=seg_t1, nt1=seg_t1),
            pass_zero=pass_zero,
        )
        self._seg_in = seg_t0


class DFlipFlopCK2(StdDigitalTemplate):
    """A transmission gate flip-flop with differential clock inputs.

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
            pass_zero='True to allow a 0 input to pass straight through.',
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
            pass_zero=False,
            show_pins=True,
        )

    def get_layout_basename(self):
        if self.params['pass_zero']:
            return 'dff_ck2_pass0'
        else:
            return 'dff_ck2'

    def draw_layout(self):
        blk_sp = 2
        fanout = 4

        config = self.params['config']
        tr_widths = self.params['tr_widths']
        tr_spaces = self.params['tr_spaces']
        wp = self.params['wp']
        wn = self.params['wn']
        row_layout_info = self.params['row_layout_info']
        sig_locs = self.params['sig_locs']
        pass_zero = self.params['pass_zero']
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
        if row_layout_info is not None:
            self.initialize(row_layout_info, 1)
        else:
            m_master = self.new_template(params=params, temp_cls=LatchCK2)
            params['row_layout_info'] = row_layout_info = m_master.row_layout_info
            self.initialize(row_layout_info, 1)

        # compute track locations
        hm_layer = self.conn_layer + 1
        tr_manager = TrackManager(self.grid, tr_widths, tr_spaces, half_space=True)
        g_locs = tr_manager.place_wires(hm_layer, ['in', 'in'])[1]
        ng0_tidx = self.get_track_index(0, 'g', g_locs[0])
        ng1_tidx = self.get_track_index(0, 'g', g_locs[1])
        pg0_tidx = self.get_track_index(1, 'g', g_locs[0])
        pg1_tidx = self.get_track_index(1, 'g', g_locs[1])

        in_tidx = sig_locs.get('in', pg0_tidx)
        pclkb_tidx = sig_locs.get('pclkb', pg1_tidx)

        # make masters
        params['sig_locs'] = {'nclk': ng1_tidx, 'nclkb': ng0_tidx}
        s_master = self.new_template(params=params, temp_cls=LatchCK2)
        seg_m = max(2, int(round(s_master.seg_in / (2 * fanout))) * 2)
        params['seg'] = seg_m
        params['sig_locs'] = {'in': in_tidx, 'pclkb': pclkb_tidx,
                              'clkb': sig_locs.get('clk', None),
                              'clk': sig_locs.get('clkb', None)}
        m_master = self.new_template(params=params, temp_cls=LatchCK2)

        # set size
        m_ncol = m_master.num_cols
        s_ncol = s_master.num_cols
        num_cols = m_ncol + s_ncol + blk_sp
        self.set_digital_size(num_cols)

        # add instances
        s_col = m_ncol + blk_sp
        m_inst = self.add_digital_block(m_master, (0, 0))
        s_inst = self.add_digital_block(s_master, (s_col, 0))

        self.fill_space()

        # connect/export VSS/VDD
        vss_list, vdd_list = [], []
        for inst in (m_inst, s_inst):
            vss_list.append(inst.get_pin('VSS'))
            vdd_list.append(inst.get_pin('VDD'))
        self.add_pin('VSS', self.connect_wires(vss_list), show=show_pins)
        self.add_pin('VDD', self.connect_wires(vdd_list), show=show_pins)

        # connect intermediate node
        self.connect_wires([s_inst.get_pin('in'), m_inst.get_pin('out_hm')])
        # connect clocks
        self.connect_wires([s_inst.get_pin('nclk'), m_inst.get_pin('nclkb')])
        self.connect_wires([s_inst.get_pin('pclkb'), m_inst.get_pin('pclk')])
        # add pins
        self.add_pin('in', m_inst.get_pin('in'), show=show_pins)
        self.add_pin('out', s_inst.get_pin('out'), show=show_pins)
        self.add_pin('clk', m_inst.get_pin('clkb'), show=show_pins)
        self.add_pin('clkb', m_inst.get_pin('clk'), show=show_pins)
        self.add_pin('clkb_hm', m_inst.get_pin('nclk'), label='clkb', show=show_pins)
        self.add_pin('clk_hm', m_inst.get_pin('nclkb'), label='clk', show=show_pins)

        # set properties
        self._sch_params = dict(
            lch=config['lch'],
            wp=wp,
            wn=wn,
            thp=config['thp'],
            thn=config['thn'],
            seg_m=m_master.sch_params['seg_dict'],
            seg_s=s_master.sch_params['seg_dict'],
            pass_zero=pass_zero,
        )
        self._seg_in = m_master.seg_in

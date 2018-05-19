# -*- coding: utf-8 -*-

"""This package defines various passives template classes.
"""

from typing import TYPE_CHECKING, Dict, Set, Any

from bag.layout.routing.base import TrackManager, TrackID

from abs_templates_ec.analog_core.base import AnalogBaseInfo, AnalogBase


if TYPE_CHECKING:
    from bag.layout.template import TemplateDB


class AnaInvChain(AnalogBase):
    """inverter chain using AnalogBase.

    This is mainly used so that we can easily put guard ring around the inverter.

    Parameters
    ----------
    temp_db : :class:`bag.layout.template.TemplateDB`
        the template database.
    lib_name : str
        the layout library name.
    params : Dict[str, Any]
        the parameter values.
    used_names : Set[str]
        a set of already used cell names.
    **kwargs :
        dictionary of optional parameters.  See documentation of
        :class:`bag.layout.template.TemplateBase` for details.
    """

    def __init__(self, temp_db, lib_name, params, used_names, **kwargs):
        # type: (TemplateDB, str, Dict[str, Any], Set[str], **kwargs) -> None
        AnalogBase.__init__(self, temp_db, lib_name, params, used_names, **kwargs)
        self._sch_params = None

    @property
    def sch_params(self):
        # type: () -> Dict[str, Any]
        return self._sch_params

    @classmethod
    def get_params_info(cls):
        # type: () -> Dict[str, str]
        return dict(
            lch='channel length, in meters.',
            ptap_w='NMOS substrate width, in meters/number of fins.',
            ntap_w='PMOS substrate width, in meters/number of fins.',
            wp='PMOS width.',
            wn='NMOS width.',
            thp='PMOS threshold.',
            thn='NMOS threshold.',
            seg_list='list of number of segments for each inverter.',
            tr_widths='Track width dictionary.',
            tr_spaces='Track spacing dictionary.',
            out_tid='Output track ID information.',
            guard_ring_nf='Guard ring width in number of fingers.  0 for no guard ring.',
            show_pins='True to draw pins.',
        )

    @classmethod
    def get_default_param_values(cls):
        return dict(
            out_tid=None,
            guard_ring_nf=0,
            show_pins=True,
        )

    def draw_layout(self):
        lch = self.params['lch']
        ptap_w = self.params['ptap_w']
        ntap_w = self.params['ntap_w']
        wp = self.params['wp']
        wn = self.params['wn']
        thp = self.params['thp']
        thn = self.params['thn']
        seg_list = self.params['seg_list']
        tr_widths = self.params['tr_widths']
        tr_spaces = self.params['tr_spaces']
        out_tid = self.params['out_tid']
        guard_ring_nf = self.params['guard_ring_nf']
        show_pins = self.params['show_pins']

        # get AnalogBaseInfo
        hm_layer = self.mos_conn_layer + 1
        layout_info = AnalogBaseInfo(self.grid, lch, guard_ring_nf, top_layer=hm_layer)
        fg_sep = layout_info.min_fg_sep

        fg_tot = sum(seg_list) + fg_sep * (len(seg_list) - 1)

        # construct track width/space dictionary from EM specs
        tr_manager = TrackManager(self.grid, tr_widths, tr_spaces, half_space=True)

        nw_list = [wn]
        pw_list = [wp]
        nth_list = [thn]
        pth_list = [thp]
        wire_dict_list = [dict(g=['out'])]
        wire_names = dict(nch=wire_dict_list, pch=wire_dict_list)
        # draw transistor rows
        self.draw_base(lch, fg_tot, ptap_w, ntap_w, nw_list, nth_list, pw_list, pth_list,
                       tr_manager=tr_manager, wire_names=wire_names,
                       n_orientations=['MX'], p_orientations=['R0'], guard_ring_nf=guard_ring_nf,
                       pgr_w=ptap_w, ngr_w=ntap_w, top_layer=hm_layer)

        ng_tid = self.get_wire_id('nch', 0, 'g', wire_idx=0)
        pg_tid = self.get_wire_id('pch', 0, 'g', wire_idx=0)
        num = len(seg_list)
        if out_tid is None:
            in0_tid = ng_tid
            out0_tid = pg_tid
        else:
            out0_tid = TrackID(hm_layer, out_tid[0], width=out_tid[1])
            if abs(pg_tid.base_index - out_tid[0]) < abs(ng_tid.base_index - out_tid[0]):
                in0_tid = ng_tid
            else:
                in0_tid = pg_tid

            if num % 2 == 0:
                tmp = in0_tid
                in0_tid = out0_tid
                out0_tid = tmp

        col = 0
        prev_out = None
        for idx, seg in enumerate(seg_list):
            out_name = 'out' if idx == num - 1 else 'mid%d' % idx
            pmos = self.draw_mos_conn('pch', 0, col, seg, 2, 0, d_net=out_name)
            nmos = self.draw_mos_conn('nch', 0, col, seg, 0, 2, d_net=out_name)
            self.connect_to_substrate('ptap', nmos['s'])
            self.connect_to_substrate('ntap', pmos['s'])
            if idx % 2 == 0:
                in_tid = in0_tid
                out_tid = out0_tid
            else:
                in_tid = out0_tid
                out_tid = in0_tid

            if prev_out is None:
                w_in = self.connect_to_tracks([nmos['g'], pmos['g']], in_tid)
                self.add_pin('in', w_in, show=show_pins)
            else:
                self.connect_to_track_wires([nmos['g'], pmos['g']], prev_out)
            prev_out = self.connect_to_tracks([nmos['d'], pmos['d']], out_tid)
            col += seg + fg_sep

        sup_tr_w = tr_manager.get_width(hm_layer, 'sup')
        vss, vdd = self.fill_dummy(vdd_width=sup_tr_w, vss_width=sup_tr_w)
        self.add_pin('VSS', vss, show=show_pins)
        self.add_pin('VDD', vdd, show=show_pins)
        self.add_pin('out', prev_out, show=show_pins)

        # get schematic parameters
        num_seg = len(seg_list)
        self._sch_params = dict(
            lch=lch,
            wp_list=[wp] * num_seg,
            wn_list=[wn] * num_seg,
            thp=thp,
            thn=thn,
            segp_list=seg_list,
            segn_list=seg_list,
            dum_info=self.get_sch_dummy_info(),
        )
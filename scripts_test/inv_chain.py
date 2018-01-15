# -*- coding: utf-8 -*-

from typing import Dict, Any, Set

import yaml

from bag.core import BagProject
from bag.layout import RoutingGrid, TemplateDB
from bag.layout.routing import TrackManager
from abs_templates_ec.laygo.core import LaygoBase


class InvChain(LaygoBase):
    """An inverter chain

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
        super(InvChain, self).__init__(temp_db, lib_name, params, used_names, **kwargs)

    @classmethod
    def get_params_info(cls):
        """Returns a dictionary containing parameter descriptions.

        Override this method to return a dictionary from parameter names to descriptions.

        Returns
        -------
        param_info : dict[str, str]
            dictionary from parameter name to description.
        """
        return dict(
            config='laygo configuration dictionary.',
            wp_list='pmos widths.',
            wn_list='nmos widths.',
            thp='pmos threshold.',
            thn='nmos threshold.',
            fg_list='list of fingers for each inverter.',
            tr_widths='Track width dictionary.',
            tr_spaces='Track spacing dictionary.',
            draw_boundaries='True to draw boundaries.',
            top_layer='the top routing layer.',
            show_pins='True to draw pin geometries.',
        )

    def draw_layout(self):
        """Draw the layout of a dynamic latch chain.
        """

        wp_list = self.params['wp_list']
        wn_list = self.params['wn_list']
        thp = self.params['thp']
        thn = self.params['thn']
        fg_list = self.params['fg_list']
        tr_widths = self.params['tr_widths']
        tr_spaces = self.params['tr_spaces']
        draw_boundaries = self.params['draw_boundaries']
        top_layer = self.params['top_layer']
        show_pins = self.params['show_pins']

        w_sub = self.params['config']['w_sub']
        tr_manager = TrackManager(self.grid, tr_widths, tr_spaces)

        # get row information
        row_list = ['ptap', 'nch', 'pch', 'ntap']
        orient_list = ['R0', 'MX', 'R0', 'MX']
        thres_list = [thn, thn, thp, thp]
        w_list = [w_sub, max(wn_list), max(wp_list), w_sub]
        row_kwargs = [{}] * len(row_list)
        end_mode = 15 if draw_boundaries else 0

        # get track information

        hm_layer = self.conn_layer + 1
        tr_w_io = tr_manager.get_width(hm_layer, 'io')
        tr_w_sup = tr_manager.get_width(hm_layer, 'sup')

        num_g_n, loc_g_n = tr_manager.place_wires(hm_layer, ['io'])
        num_g_p, loc_g_p = tr_manager.place_wires(hm_layer, ['io'])
        num_ds_sub, loc_ds_sub = tr_manager.place_wires(hm_layer, ['sup'])

        num_g_tracks = [0, num_g_n, num_g_p, 0]
        num_gb_tracks = [0, 0, 0, 0]
        num_ds_tracks = [num_ds_sub, 0, 0, num_ds_sub]

        # determine number of blocks
        n_tot = len(fg_list) - 1
        for fg in fg_list:
            n_tot += (fg // 2) + (fg % 2)
        # specify row types
        self.set_row_types(row_list, w_list, orient_list, thres_list, draw_boundaries, end_mode,
                           num_g_tracks, num_gb_tracks, num_ds_tracks, guard_ring_nf=0,
                           top_layer=top_layer, row_kwargs=row_kwargs, num_col=n_tot)

        # add blocks
        # nwell/pwell taps
        nw_tap = self.add_laygo_primitive('sub', loc=(0, 3), nx=n_tot, spx=1)
        pw_tap = self.add_laygo_primitive('sub', loc=(0, 0), nx=n_tot, spx=1)
        # pmos/nmos inverters
        cur_col = 0
        in_list, out_list = [], []
        vss_list, vdd_list = pw_tap.get_all_port_pins('VSS_d'), nw_tap.get_all_port_pins('VDD_d')
        n_tid = self.make_track_id(1, 'g', loc_g_n[0], width=tr_w_io)
        p_tid = self.make_track_id(2, 'g', loc_g_p[0], width=tr_w_io)
        for idx, fg in enumerate(fg_list):
            # create blocks and get ports
            num2 = fg // 2
            num1 = fg - 2 * num2
            cur_in, cur_out = [], []
            p2 = self.add_laygo_primitive('fg2d', loc=(cur_col, 2), nx=num2, spx=1)
            n2 = self.add_laygo_primitive('fg2d', loc=(cur_col, 1), nx=num2, spx=1)
            vss_list.extend(n2.get_all_port_pins('d'))
            vdd_list.extend(p2.get_all_port_pins('d'))
            cur_in.extend(p2.get_all_port_pins('g'))
            cur_in.extend(n2.get_all_port_pins('g'))
            cur_out.extend(p2.get_all_port_pins('s'))
            cur_out.extend(n2.get_all_port_pins('s'))
            if num1 > 0:
                p1 = self.add_laygo_primitive('fg1d', loc=(cur_col + num2, 2))
                n1 = self.add_laygo_primitive('fg1d', loc=(cur_col + num2, 1))
                vss_list.extend(n1.get_all_port_pins('d'))
                vdd_list.extend(p1.get_all_port_pins('d'))
                cur_in.extend(p1.get_all_port_pins('g'))
                cur_in.extend(n1.get_all_port_pins('g'))
                cur_out.extend(p1.get_all_port_pins('s'))
                cur_out.extend(n1.get_all_port_pins('s'))

            # connect io wires
            if idx % 2 == 0:
                in_tid, out_tid = n_tid, p_tid
            else:
                in_tid, out_tid = p_tid, n_tid
            in_warr = self.connect_to_tracks(cur_in, in_tid, min_len_mode=-1)
            out_warr = self.connect_to_tracks(cur_out, out_tid, min_len_mode=1)
            in_list.append(in_warr)
            out_list.append(out_warr)
            cur_col += num2 + num1 + 1

        # compute overall block size and fill spaces
        self.fill_space()

        # connect supplies
        vss_tid = self.make_track_id(0, 'ds', loc_ds_sub[0], width=tr_w_sup)
        vdd_tid = self.make_track_id(3, 'ds', loc_ds_sub[0], width=tr_w_sup)
        vss_warr = self.connect_to_tracks(vss_list, vss_tid)
        vdd_warr = self.connect_to_tracks(vdd_list, vdd_tid)
        self.add_pin('VSS', vss_warr, show=show_pins)
        self.add_pin('VDD', vdd_warr, show=show_pins)

        # connect inputs and outputs
        self.add_pin('in', in_list[0], show=show_pins)
        self.add_pin('out', out_list[-1], show=show_pins)
        for idx in range(len(in_list) - 1):
            self.connect_wires([out_list[idx], in_list[idx + 1]])


def make_tdb(prj, target_lib, specs):
    grid_specs = specs['routing_grid']
    layers = grid_specs['layers']
    spaces = grid_specs['spaces']
    widths = grid_specs['widths']
    bot_dir = grid_specs['bot_dir']

    routing_grid = RoutingGrid(prj.tech_info, layers, spaces, widths, bot_dir)
    tdb = TemplateDB('template_libs.def', routing_grid, target_lib, use_cybagoa=True)
    return tdb


def generate(prj, specs):
    temp_db = make_tdb(prj, impl_lib, specs)
    params = specs['params']

    temp = temp_db.new_template(params=params, temp_cls=InvChain, debug=False)

    print('creating layout')
    temp_db.batch_layout(prj, [temp], ['INV_CHAIN'])
    print('done')


if __name__ == '__main__':

    impl_lib = 'AAAFOO_INVCHAIN'

    with open('specs_test/inv_chain.yaml', 'r') as f:
        block_specs = yaml.load(f)

    local_dict = locals()
    if 'bprj' not in local_dict:
        print('creating BAG project')
        bprj = BagProject()

    else:
        print('loading BAG project')
        bprj = local_dict['bprj']

    generate(bprj, block_specs)

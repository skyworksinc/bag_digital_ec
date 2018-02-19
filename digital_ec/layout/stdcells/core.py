# -*- coding: utf-8 -*-

from typing import TYPE_CHECKING, Dict, Any, Set, Tuple

import abc
import importlib

from bag.layout.routing import TrackID

from abs_templates_ec.laygo.core import LaygoBase
from abs_templates_ec.digital.core import DigitalBase

if TYPE_CHECKING:
    from bag.layout.template import TemplateDB


class StdCellWrapper(DigitalBase):
    """A class that wraps a given standard cell with proper boundaries.

    This class is usually used just for layout debugging (i.e. DRC checking).

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
        DigitalBase.__init__(self, temp_db, lib_name, params, used_names, **kwargs)

    @classmethod
    def get_params_info(cls):
        # type: () -> Dict[str, str]
        return {
            'module': 'standard cell module name.',
            'class': 'standard cell class name.',
            'params': 'standard cell layout parameters.',
            'guard_ring_nf': 'number of guard rings in boundary.',
        }

    @classmethod
    def get_default_param_values(cls):
        # type: () -> Dict[str, Any]
        return dict(
            guard_ring_nf=0,
        )

    def draw_layout(self):
        """Draw the layout of a dynamic latch chain.
        """
        mod = self.params['module']
        cls = self.params['class']
        params = self.params['params'].copy()
        guard_ring_nf = self.params['guard_ring_nf']

        cls_mod = importlib.import_module(mod)
        temp_cls = getattr(cls_mod, cls)

        params['show_pins'] = True
        master = self.new_template(params=params, temp_cls=temp_cls)
        row_info = master.get_digital_row_info()

        self.initialize(row_info, 1, True, 15, guard_ring_nf=guard_ring_nf, num_col=master.laygo_size[0])

        self.add_digital_block(master, loc=(0, 0))
        self.set_digital_size(master.laygo_size[0])

        self.fill_space()


class StdCellTemplate(LaygoBase, metaclass=abc.ABCMeta):
    """The base class of all standard cell generators.

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
        LaygoBase.__init__(self, temp_db, lib_name, params, used_names, **kwargs)

    def setup_floorplan(self, config, num_col, debug=False):
        # type: (Dict[str, Any], int, bool) -> Tuple[TrackID, TrackID]
        """draw the standard cell floorplan.
        """
        wp_row = config['wp']
        wn_row = config['wn']
        thp = config['thp']
        thn = config['thn']
        row_kwargs = config['row_kwargs']
        num_g_tracks = config['ng_tracks']
        num_gb_tracks = config['ngb_tracks']
        num_ds_tracks = config['nds_tracks']
        tr_w_sup = config['tr_w_supply']

        if len(num_g_tracks) != 2 or len(num_gb_tracks) != 2 or len(num_ds_tracks) != 2:
            raise ValueError('Standard cell only have two rows, NMOS followed by PMOS.')

        # get row information
        row_list = ['nch', 'pch']
        orient_list = ['MX', 'R0']
        thres_list = [thn, thp]
        w_list = [wn_row, wp_row]

        # take supply width and spacing into account.
        hm_layer = self.conn_layer + 1
        sp_sup = self.grid.get_num_space_tracks(hm_layer, tr_w_sup, half_space=True)
        # trust me (sorta), we can subtract 1 here.
        inc = int(round(2 * sp_sup + tr_w_sup)) - 1
        if inc % 2 == 0:
            inc = inc // 2
        else:
            inc = inc / 2

        if debug:
            print('num_track increment for supply: %s' % inc)
        num_gb_tracks = [ntr + inc for ntr in num_gb_tracks]
        num_ds_tracks = [ntr + inc for ntr in num_ds_tracks]

        # specify row types
        self.set_row_types(row_list, w_list, orient_list, thres_list, False, 0,
                           num_g_tracks, num_gb_tracks, num_ds_tracks, guard_ring_nf=0,
                           row_kwargs=row_kwargs, num_col=num_col)

        if debug:
            for row_idx, row_name in [(0, 'nch'), (1, 'pch')]:
                for tr_type in ['g', 'gb', 'ds']:
                    num_tr = self.get_num_tracks(row_idx, tr_type)
                    print(row_idx, tr_type, num_tr)
                    for tidx in range(int(num_tr)):
                        tid = self.get_track_index(row_idx, tr_type, tidx)
                        warr = self.add_wires(hm_layer, tid, 0, self.bound_box.right_unit, unit_mode=True)
                        self.add_pin('%s_%s_%d' % (row_name, tr_type, tidx), warr)

        vss_tid = TrackID(hm_layer, -0.5, width=tr_w_sup)
        vdd_tid = TrackID(hm_layer, self.grid.coord_to_track(hm_layer, self.bound_box.top_unit, unit_mode=True),
                          width=tr_w_sup)
        return vss_tid, vdd_tid

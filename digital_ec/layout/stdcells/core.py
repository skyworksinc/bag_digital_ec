# -*- coding: utf-8 -*-

from typing import TYPE_CHECKING, Dict, Any, Set, Tuple

import abc
import importlib

from bag.layout.routing import TrackID

from abs_templates_ec.laygo.core import LaygoBase
from abs_templates_ec.digital.core import DigitalBase

if TYPE_CHECKING:
    from bag.core import BagProject
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
        self._sch_params = None

    @property
    def sch_params(self):
        # type: () -> Dict[str, Any]
        return self._sch_params

    @classmethod
    def generate_cells(cls, prj, specs, **kwargs):
        # type: (BagProject, Dict[str, Any], **kwargs) -> None
        mod_name = specs['module']
        cls_name = specs['class']

        std_params = {'module': mod_name, 'class': cls_name, 'params': specs['params']}
        new_specs = specs.copy()
        new_specs['params'] = std_params
        prj.generate_cell(new_specs, cls, **kwargs)

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
        mod = self.params['module']
        cls = self.params['class']
        params = self.params['params'].copy()
        guard_ring_nf = self.params['guard_ring_nf']

        cls_mod = importlib.import_module(mod)
        temp_cls = getattr(cls_mod, cls)

        params['show_pins'] = False
        master = self.new_template(params=params, temp_cls=temp_cls)
        num_cols = -(-master.num_cols // 2) * 2
        num_rows = master.digital_size[1]

        self.initialize(master.row_layout_info, num_rows, num_cols=num_cols, draw_boundaries=True,
                        end_mode=15, guard_ring_nf=guard_ring_nf)

        inst = self.add_digital_block(master, loc=(0, 0))
        for port_name in inst.port_names_iter():
            if port_name == 'VSS' or port_name == 'VDD':
                label = port_name + ':'
            else:
                label = ''
            self.reexport(inst.get_port(port_name), label=label, show=True)

        vss_warrs, vdd_warrs, [], [] = self.fill_space()
        self.add_pin('VSS', vss_warrs, label='VSS:', show=True)
        self.add_pin('VDD', vdd_warrs, label='VDD:', show=True)
        if hasattr(master, 'sch_params'):
            self._sch_params = master.sch_params
        else:
            self._sch_params = None


class StdLaygoTemplate(LaygoBase, metaclass=abc.ABCMeta):
    """The base class of all laygo standard cell generators.

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
            raise ValueError('Standard cell must have two rows, NMOS followed by PMOS.')

        # get row information
        row_list = ['nch', 'pch']
        orient_list = ['MX', 'R0']
        thres_list = [thn, thp]
        w_list = [wn_row, wp_row]

        # take supply width and spacing into account.
        hm_layer = self.conn_layer + 1
        sp_sup = self.grid.get_num_space_tracks(hm_layer, tr_w_sup, half_space=True)
        inc = int(round(2 * sp_sup + tr_w_sup))
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
                        warr = self.add_wires(hm_layer, tid, 0, self.bound_box.right_unit,
                                              unit_mode=True)
                        self.add_pin('%s_%s_%d' % (row_name, tr_type, tidx), warr)

        vss_tid = TrackID(hm_layer, -0.5, width=tr_w_sup)
        vdd_tid = TrackID(hm_layer, self.grid.coord_to_track(hm_layer, self.bound_box.top_unit,
                                                             unit_mode=True), width=tr_w_sup)
        return vss_tid, vdd_tid

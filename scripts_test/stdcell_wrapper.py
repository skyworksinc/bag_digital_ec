# -*- coding: utf-8 -*-


import yaml

from bag.core import BagProject
from bag.layout import RoutingGrid, TemplateDB

from digital_ec.layout.stdcells.core import StdCellWrapper


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

    temp = temp_db.new_template(params=params, temp_cls=StdCellWrapper, debug=False)

    print('creating layout')
    temp_db.batch_layout(prj, [temp], ['STD_WRAP'])
    print('done')


if __name__ == '__main__':

    impl_lib = 'AAAFOO_STDCELL_TEST'

    with open('specs_test/stdcell_wrapper.yaml', 'r') as f:
        block_specs = yaml.load(f)

    local_dict = locals()
    if 'bprj' not in local_dict:
        print('creating BAG project')
        bprj = BagProject()

    else:
        print('loading BAG project')
        bprj = local_dict['bprj']

    generate(bprj, block_specs)

# -*- coding: utf-8 -*-

import yaml

from bag.core import BagProject

from digital_ec.layout.digital.delay import DelayLineMux


if __name__ == '__main__':
    with open('specs_test/digital_ec/delay/delay_line_mux.yaml', 'r') as f:
        block_specs = yaml.load(f)

    local_dict = locals()
    if 'bprj' not in local_dict:
        print('creating BAG project')
        bprj = BagProject()

    else:
        print('loading BAG project')
        bprj = local_dict['bprj']

    # bprj.generate_cell(block_specs, DelayLineMux, debug=True)
    bprj.generate_cell(block_specs, DelayLineMux, gen_sch=True, debug=True)

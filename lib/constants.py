"""
CSV to XML mappings
"""


MAPPINGS = {
    'bullet': {
        'component': [
            ('./component', 'name', '{component_id}'),
            ('./component/layers/layer/lights/*', 'r', '{red}'),
            ('./component/layers/layer/lights/*', 'g', '{green}'),
            ('./component/layers/layer/lights/*', 'b', '{blue}'),
        ],
        'macro': [
            ('./macro', 'name', '{macro_id}'),
            ('./macro/component', 'ref', '{component_id}'),
            ('./macro/properties/bullet', 'speed', '{speed}'),
            ('./macro/properties/bullet', 'lifetime', '{lifetime}'),
            ('./macro/properties/bullet', 'heat', '{heat}'),
            ('./macro/properties/bullet', 'reload', '{reload}'),
            ('./macro/properties/bullet', 'damage', '{damage}'),
            ('./macro/properties/bullet', 'shield', '{shield}'),
            ('./macro/properties/bullet', 'repair', '{repair}'),
        ],
    },
    'weapon': {
        'component': [
            ('./component', 'name', '{component_id}'),
            ('./component/connections/connection[@name="WeaponCon_01"]', 'tags', '{tags}'),
        ],
        'macro': [
            ('./macro', 'name', '{macro_id}'),
            ('./macro/component', 'ref', '{component_id}'),
            ('./macro/properties/identification', 'name', '{{{page_id}, {t_name_id}}}'),
            ('./macro/properties/identification', 'basename', '{{{page_id}, {t_basename_id}}}'),
            ('./macro/properties/identification', 'shortname', '{{{page_id}, {t_shortname_id}}}'),
            ('./macro/properties/identification', 'description', '{{{page_id}, {t_description_id}}}'),
            ('./macro/properties/identification', 'mk', '{mk}'),
            ('./macro/properties/bullet', 'class', '{bullet_macro}'),
            ('./macro/properties/heat', 'overheat', '{overheat}'),
            ('./macro/properties/heat', 'cooldelay', '{cooldelay}'),
            ('./macro/properties/heat', 'coolrate', '{coolrate}'),
            ('./macro/properties/heat', 'reenable', '{reenable}'),
            ('./macro/properties/rotationspeed', 'max', '{rotation_spd}'),
            ('./macro/properties/rotationacceleration', 'max', '{rotation_acc}'),
            ('./macro/properties/hull', 'max', '{hull}'),
        ],
    },
    'ship': {
        'component': [
            ('./component', 'name', '{component_id}'),
        ],
        'macro': [
            ('./macro', 'name', '{macro_id}'),
            ('./macro/component', 'ref', '{component_id}'),
            ('./macro/properties/identification', 'name', '{{{page_id}, {t_name_id}}}'),
            ('./macro/properties/identification', 'basename', '{{{page_id}, {t_basename_id}}}'),
            ('./macro/properties/identification', 'description', '{{{page_id}, {t_description_id}}}'),
            ('./macro/properties/identification', 'variation', '{{{page_id}, {t_variation_id}}}'),
            ('./macro/properties/identification', 'shortvariation', '{{{page_id}, {t_shortvariation_id}}}'),
            ('./macro/properties/hull', 'max', '{hull}'),
            ('./macro/properties/people', 'capacity', '{people}'),
            ('./macro/properties/physics', 'mass', '{mass}'),
            ('./macro/properties/physics/inertia', 'pitch', '{inertia_pitch}'),
            ('./macro/properties/physics/inertia', 'yaw', '{inertia_yaw}'),
            ('./macro/properties/physics/inertia', 'roll', '{inertia_roll}'),
            ('./macro/properties/physics/drag', 'forward', '{drag_forward}'),
            ('./macro/properties/physics/drag', 'reverse', '{drag_reverse}'),
            ('./macro/properties/physics/drag', 'horizontal', '{drag_horizontal}'),
            ('./macro/properties/physics/drag', 'vertical', '{drag_vertical}'),
            ('./macro/properties/physics/drag', 'pitch', '{drag_pitch}'),
            ('./macro/properties/physics/drag', 'yaw', '{drag_yaw}'),
            ('./macro/properties/physics/drag', 'roll', '{drag_roll}'),
        ],
    },
    'shield': {
        'component': [
            ('./component', 'name', '{component_id}'),
            ('./component/connections/connection[@name="Connection01"]', 'tags', '{tags}'),
        ],
        'macro': [
            ('./macro', 'name', '{macro_id}'),
            ('./macro/component', 'ref', '{component_id}'),
            ('./macro/properties/identification', 'name', '{{{page_id}, {t_name_id}}}'),
            ('./macro/properties/identification', 'basename', '{{{page_id}, {t_basename_id}}}'),
            ('./macro/properties/identification', 'shortname', '{{{page_id}, {t_shortname_id}}}'),
            ('./macro/properties/identification', 'description', '{{{page_id}, {t_description_id}}}'),
            ('./macro/properties/identification', 'mk', '{mk}'),
            ('./macro/properties/recharge', 'max', '{recharge_max}'),
            ('./macro/properties/recharge', 'rate', '{recharge_rate}'),
            ('./macro/properties/recharge', 'delay', '{recharge_delay}'),
        ],
    },
    'ware': [
        ('.', 'id', '{component_id}'),
        ('.', 'name', '{{{page_id}, {t_name_id}}}'),
        ('.', 'description', '{{{page_id}, {t_description_id}}}'),
        ('./price', 'min', '{price_min}'),
        ('./price', 'average', '{price_avg}'),
        ('./price', 'max', '{price_max}'),
        ('./component', 'ref', '{macro_id}'),
        ('./restriction', 'licence', '{restriction}'),
    ]
}


T_LIST = ['name', 'basename', 'description', 'shortname', 'variation', 'shortvariation']

# X4 Foundations modding

###### Development setup

Written and tested in the following environment
OS:Written on Ubuntu 16.04
PWD: ~/x4
GAME DIR ~/.steam/.local/share/Steam/steamapps/common/X4 Foundations
PYTHON3 VERSION: 3.5.2


###### How to mod

Ships, weapons, etc are based on multiple different types of files.
- components define the parts of the object (ex ship has hardpoints for shields, weapons, engines, 
spacesuit docking, cockpit, etc)
- macros define the different configurations/variations of the components
- wares file defines where the ware is available, what price, what is needed to produce it, etc
- t files define the names and labels for the different texts

Example
- component: assets/unit/size_s/ship_par_s_scout_01.xml defines Paranid Pegasus ship
    - connection: con_weapon_01 defines the main weapon, it's position, and the weapon compatibility tags for it
    - connection: con_shield_01 defines the main shield, it's position, and the compatibility tags
    
- macro: assets/unit/size_s/macros/ship_par_s_scout_01_a_macro.xml defines the Pegasus Vanguard variation
    - identification: references the t file, the ship name, etc
    - component ref: links to the ship component
    - physics: affects the ship speed and flight characteristics
- macro: ship_par_s_scout_01_b_macro.xml defines the Pegause Sentinel variation

- wares: libraries/wares.xml ware id="ship_par_s_scout_01_a" defines the Pegasus Vanguard ware
    - price: prices min/avg/max price
    - production: production time and costs/materials needed
    - component ref: links to the ship macro
    - restriction: sets what license you need to buy the ware
    - owner entries: define where (at which factions) the ware can be built/bought


The compile_mod.py script looks at the mods/{mod name}/weapons.csv and mods/{mod name}/ships.csv files.
And based on the base_ship_macro/base_weapon_macro, it finds the macro file, copies it to the mods/{mod name}/mod/ dir,
updating the macro and component values with the ones in the csv file. 


###### Modding Steps

Step 1: Create config.py
run ./setup.sh
(this should create a config.py with paths for present dir, game dir, src dir, mods dir)

Step 2: extract X4 scripts
run python3 extract_x4.py --extract
(this should extract all the scripts/xml from the game cats+dats into src/ dir)

Step 3: make modifications
use:
    mods/rat/content.xml
    mods/rat/ships.csv
    mods/rat/weapons.csv
as a template to create your own mod

Step 4: compile mod
run python3 compile_mod.py {your mod name}
(this should read the csv files and copy the appropriate xml source files, 
 update them with values in csv, and place them in your mod dir.  
 It should create the index, libraries, mod, and t dirs and files in them)

Step 5: make more modifications if need be
the csv files have limited changes, but you can make additional changes to your mod files
(re-running compile mod should update csv values without losing your changes)

Step 6: pack your mod
run python3 pack_mod.py {mod name}
(this should take the files in your mods/{mod name}/, copy the files in root dir and
 pack the files in index, libraries, mod, and t dirs into your {game dir}/extensions/{mod name}/)

Step 7: run game and verify it works
In the game in Extensions you should see the name of your mod.
If there are any issues look at your Debug Log 
(you can assign a key to it in Controls -> General -> Open Debug Log, you can open it without loading any saves, on game start)
Note: if you add a ship or ware, it might not be in the Wharf/Shipyard you are docked at, it depends on the
faction where it's available (this can be controlled in the libraries/wares.xml)


###### Current Features
- auto path configuration via setup.sh
- extracting scripts and/or all files from game files via extract_x4.py
- packing mod files into cat/dat via pack_x4.py or pack_mod.py
- compiling mod from csv files via compile_mod.py
- adding ships
- adding weapons

###### Roadmap

- add adding shields and other components
- searching for base templates
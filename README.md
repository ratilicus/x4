# X4 Foundations modding

###### Description

To allow user of this mod to create their own X4 mod that will allow of adding content based on existing
models to the game.  

This repo has a number of scipts to allow:
- extract_x4.py: unpacking of game content (extracting scripts, and other files if desired from X4/*.cat, into a SRC dir)
- compile_mod.py: using csv files in your MOD dir, and extracted SRC dir macros as xml templates, compile your mod, which will
take those template macros and replace key values specified in the csv file
- you can make further changes to the xml files that were compiled, and re-running the compile script will only
replace the key values from the csv without losing any of the other changes
- pack_mod.py: pack your MOD dir files into cat/dat and place them inside your X4/extensions dir, so you can test
  them right away in your game  
- xmf2obj.py: extracting model data and textures and writing obj files that can be opened in Blender, etc
- search.py: index Ts/labels, and Wares, and search wares to find macros/components

###### Finding Macros

When you extract the scripts with `python3 extract_x4.py --extract` the `src` dir should have all the script files

- all macros are indexed in `./src/index/macros.xml`
- all components are indexed in `./src/index/components.xml`
- ship macros are in `./src/assets/units/*/macros/ship_{arg|par|tel}_*_macro.xml`
- shield macros are in `./src/assets/props/SurfaceElements/macros/shield_*_macro.xml`
- weapon macros are in `./src/assets/props/WeaponSystems/*/macros/*_macros.xml`

The `base_macro` in the csv files should reference the macro name (eg. <macro name="`ship_*_macro`" ...>)


###### Searching

After extracting `python3 extract_x4.py --extract`
- Index ware entries (one time only) using `python3.7 search.py -i`  
  (This should index all the entries in `libraries/wares.xml`)
- `python3.7 search.py <search string>`
   (eg. `python3.7 search.py Pegasus` or `python3.7 search.py factions:paranid AND tags:ship`) 
- for ship results `component` is the macro name

Note: work in progress


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

- Step 1: Create config.py
  run `./setup.py` or `python3.7 setup.py`
  (this should create a config.py with paths for present dir, game dir, src dir, mods dir)

- Step 2: extract X4 scripts
  run `python3 extract_x4.py --extract`
  (this should extract all the scripts/xml from the game cats+dats into src/ dir)
  (run `python3 extract_x4.py --extract --all` if you plan to want to work with the model files)

- Step 3: make modifications
  use:
    mods/rat/content.xml
    mods/rat/ships.csv
    mods/rat/weapons.csv
  as a templates to create your own mod

- Step 4: compile mod
  run `python3 compile_mod.py {your mod name}`
  (this should read the csv files and copy the appropriate xml source files, 
   update them with values in csv, and place them in your mod dir.  
   It should create the index, libraries, mod, and t dirs and files in them)

- Step 5: make more modifications if need be
  the csv files have limited changes, but you can make additional changes to your mod files
  (re-running compile mod should update csv values without losing your changes)

- Step 6: pack your mod
  run `python3 pack_mod.py {mod name}`
  (this should take the files in your mods/{mod name}/, copy the files in root dir and
   pack the files in index, libraries, mod, and t dirs into your {game dir}/extensions/{mod name}/)

- Step 7: run game and verify it works
  In the game in Extensions you should see the name of your mod.
  If there are any issues look at your Debug Log 
  (you can assign a key to it in Controls -> General -> Open Debug Log, you can open it without loading any saves, on game start)
  Note: if you add a ship or ware, it might not be in the Wharf/Shipyard you are docked at, it depends on the
  faction where it's available (this can be controlled in the libraries/wares.xml)


###### Current Features

- auto path configuration via `./setup.py` or `python3.7 setup.py`
- extracting scripts and/or all files from game files via extract_x4.py
- packing mod files into cat/dat via pack_x4.py or pack_mod.py
- compiling mod from csv files via compile_mod.py
    - adding ships
    - adding weapons
    - adding shields
- xmf2obj.py script to extract Wavefront obj (can be imported in Blender)
    - also this generates thumbnails

###### Roadmap

- add other components
- searching for base templates
- add proper error handling and validation
- add proper logging (partially implemented)
- add complete unit test set (full coverage on main scripts already implemented)
- test setting up and using these mod scripts in Windows 10 
  (in Win 10 ubuntu integration, scripts should work if setup correctly, setup.py will probably not be able to find X4 dir as is)
- add integration tests
- add exporting of models (currently experimental xmf2obj.py)
- add importing of models 
    - this might be limited to reshaping exported models without adding or removing vertices/faces/etc, 
      (otherwise there might be issues with texture mapping, etc.)
    - even with this no new vertices/faces/etc limitation there is a big problem that most models consist of 4
      separate model files (collision model, 3 level of detail models).  So applying reshaping of a model would
      either require applying the exact same changes to 4 different files.  Or having an algorithm that would apply
      the changes from one model to the rest of them.  The different level of detail files by their nature don't have
      the same vertices (so that would be very difficult).


###### Development setup

Written and tested in the following environment
- OS:Written on Ubuntu 16.04
- PWD: ~/x4
- GAME DIR ~/.steam/.local/share/Steam/steamapps/common/X4 Foundations
- PYTHON3 VERSION: 3.5.2 (this can run most of the scripts)
- PYTHON3 VERSION: 3.6+ (required for the xmf2obj.py script)


###### Installation

- clone this repo
- if you have ubuntu 16+ you should already have python3.5 installed
- in a terminal in the repo dir run: `./setup.py` which will try to auto detect your X4 game dir and create config.py
- (optional) if `./setup.py` doesn't work, use `config.py.sample` to create your own `config.py` (adjust paths as necessary)
- after this you should be able to run `python3 extract_x4.py --extract` to exract the game scripts for most modding
- (optional) to extract all content, run `python3 extract_x4.py --extract --all` (this is necessary for xmf2obj.py)
- (optional) if you plan on using xmf2obj.py script you will need to upgrade your python3 to 3.6+
  (on ubuntu see this: https://askubuntu.com/questions/865554/how-do-i-install-python-3-6-using-apt-get)
- after the extraction, take a look at the mods/template dir or mods/rat to see examples of how to mod
- you can copy the template dir and create a mod based on it
- you can then run `python3 compile_mod.py {your-mod-name}` and in the mods/{your-mod-name} the script will create
  index, libraries, mod, t directories, and xml files in them (which you can further update as needed)
- you can then run `python3 pack_mod.py {your-mod-name}` and in your game X4/extensions/ {your-mod-name} dir should
  be created with the content.xml file and ext_01.cat and ext_01.dat files, which is your packed mod
- you should be able to run your game after this and use your new content
- if you plan to run the tests or xmf2obj.py, you will need to create a virtualenv with python3.6, source it, and 
  `pip install -r requirements.txt`, then you can run `./run_tests.sh` or './xmf2obj.py --all'
- for `xmf2obj.py` you can extract specific xmf files, or run `xmf2obj.py --all` to extract all ship models

###### Testing
- setup virtualenv (python3)
- source the venv
- `pip install -r requirements.txt`
- `./run_tests.py`


###### Template mods: rat mod and template mod (use this or template mod as a template for your mods)
- testing adding weapons, ships, shields - confirmed
- testing weapon tags (to see if tags can be used to restrict specific ship weapon mounts to specific weapon types) - confirmed
- testing shield tags (seems we can add additional tags, but can't seem to prevent standard shields from being listed, on ships)
- added IRE, PAC weapons
- added 2MJ, 5MJ, 25MJ shields
- added Pegasus Xtra
    - added 2 wing based weapons (primary can now mount pac, ire, wing weps can mount ire only)
    - modified shield tags (shield can support 2MJ, 5MJ shields, can't seem to be able to remove support for small standard shields)
- this differs from the template mod in the following way:
    - it contains pre-compiled index/libraries/mod/t dirs so you could just run `python3 pack_mod.py rat` and run your game
      to see how it works (it adds the Pegasus Xtra to the Holy Order Wharf in Holy Vision sector)
    -  the `mod/ships/ship_pegasus.xml` has been manually modified to:
        - modified shield connection tags to support our new shield types 
            - `<connection name="con_shield_01" tags="small shield 2mj 5mj unhittable ">`
        - modified weapon connection tags to support our new weapon types
            - `<connection name="con_weapon_01" tags="weapon small pac ire platformcollision ">`
        - added 2 new weapon connection elements/hardpoints
            - `<connection name="con_weapon_02" tags="weapon small ire platformcollision ">`
            - `<connection name="con_weapon_03" tags="weapon small ire platformcollision ">`

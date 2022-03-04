# X4 Foundations modding

###### Description

To allow user of this mod to create their own X4 mod that will allow of adding content based on existing
models to the game.  

This repo has a number of scipts to allow:
- extract_x4.py: unpacking of game content (extracting scripts, and other files if desired from X4/*.cat, into a SRC dir)
- compile_mod2.py: using yaml files modify specs of different ships, engines, weapons in existing game
- pack_mod.py: pack your MOD dir files into cat/dat and place them inside your X4/extensions dir, so you can test
  them right away in your game  

###### Finding Macros

When you extract the scripts with `python3 extract_x4.py --extract` the `src` dir should have all the script files

- all macros are indexed in `./src/base/index/macros.xml`
- all components are indexed in `./src/base/index/components.xml`
- ship macros are in `./src/base/assets/units/*/macros/ship_{arg|par|tel}_*_macro.xml`
- shield macros are in `./src/base/assets/props/SurfaceElements/macros/shield_*_macro.xml`
- weapon macros are in `./src/base/assets/props/WeaponSystems/*/macros/*_macros.xml`

Note: base games are in /src/base, the dlc files are in /src/ego_dlc_*



###### How to mod

see mods/rat2 for example

(work in progress)

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
    mods/rat2/content.xml
    mods/rat2/*.yaml
  as a templates to create your own mod

- Step 4: compile mod
  run `python3 compile_mod2.py {your mod name}`
  (this should read the yaml files and copy the appropriate xml source files, 
   update them with values in csv, and place them in your mod dir.  
   It should create the index, macros, components

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

- auto path configuration via `./setup.py` or `python3.7 setup.py` (ubuntu)
- extracting scripts and/or all files from game files via extract_x4.py
- packing mod files into cat/dat via pack_x4.py or pack_mod.py
- compiling mod from csv files via compile_mod2.py


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



# x4
X4 Foundations modding

Written on Ubuntu 16.04

PWD: ~/x4
GAME DIR ~/.steam/.local/share/Steam/steamapps/common/X4 Foundations

Step 1: Create config.py
run ./setup.sh
(this should create a config.py with paths for present dir, game dir, src dir, mods dir)

Step 2: extract X4 scripts
run python extract_x4.py --extract
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



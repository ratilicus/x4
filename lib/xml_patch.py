"""
# XML patching/merging changes in per RFC 5261

Logic to pull in base xml data and patched additions and changes per RFC 5261

ref: https://datatracker.ietf.org/doc/html/rfc5261

Looks like for X4 we only need <Add> tag for assets
but RFC 5261 supports <Replace sel="..."> and <Remove sel="..." /> tags
it might be good to implement those as well at some point


WORK IN PROGRESS


eg.
## Base XML file



eg. base game libraries/wares.xml
<wares>
<ware id="abcd_001">...</ware>
<ware id="abcd_002">...</ware>
<ware id="abcd_003">...</ware>
</wares>


## Patch XML file

eg. ego_dlc_terran libraries/wares.xml
<diff>
    <add sel="/wares/">
        <ware id="abcd_003">Append/Replace? ware to wares</ware>
        <ware id="abcd_004">Append new ware to wares</ware>
    </add>

    <add sel="/wares/ware[@id="abcd_002"]>
        <owner faction="yaki" />        <!-- Append a new tag to existing ware with id=abcd_002 -->
    </add>
</diff>



"""



def patch_xml(base_xml, patch_xml):
    base = base_xml.getroot()
    base_tag = base.tag
    for add_el in patch_xml.findall('./add'):
        sel =  add_el.attrib['sel']
        if not sel.startswith(f'/{base_tag}'):
            print(f'Invalid diff tag path {sel} does not start with /{base_tag}')
            continue
        sel2 = sel.replace(f'/{base_tag}', '.')
        base_el = base.find(sel2)
        #
        if base_el is None:
            if add_el.get('silent') == "1":  
                # this is not part of rfc but seems to be what X4 uses 
                # to suppress errors for missing wares from DLCs player might not have.
                print(f'Element {sel} not found, but allowed to fail silently.')
                continue
            else:
                print(f'Element {sel} not found!')
                break
        print(f'Add {sel}')
        for add_el_child in add_el.findall('./*'):
            base_el.append(add_el_child)

    return base_xml



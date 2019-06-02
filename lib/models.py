from lib.dblib import SchemaClass, prep_model, TEXT, KEYWORD, ID, STORED, NUMERIC


@prep_model
class T(SchemaClass):
    id = ID(unique=True)
    pageid = NUMERIC(stored=True)
    tid = NUMERIC(stored=True)
    value = TEXT(stored=True)
    class Meta:
        name = 'ts'


@prep_model
class Component(SchemaClass):
    name = ID(unique=True)
    klass = ID(stored=True)
    tags = KEYWORD(stored=True)
    file_path = STORED
    geometry_path = STORED
    class Meta:
        name = 'ts'
        search_fields = ['name', 'klass', 'tags']


@prep_model
class Macro(SchemaClass):
    name = ID(unique=True, stored=True)
    klass = ID(stored=True)
    component = ID(stored=True)
    tags = KEYWORD(stored=True)
    file_path = STORED
    id_name = TEXT(stored=True)
    id_basename = TEXT(stored=True)
    id_description = TEXT(stored=True)
    class Meta:
        name = 'macros'
        search_fields = ['name', 'klass', 'tags', 'id_name', 'id_basename', 'id_description']


@prep_model
class Ware(SchemaClass):
    id = ID(unique=True, stored=True)
    name = TEXT(stored=True)
    description = TEXT(stored=True)
    group = ID(stored=True)
    transport = ID(stored=True)
    volume = NUMERIC(stored=True)
    tags = KEYWORD(stored=True)
    production = TEXT(stored=True)
    macro = ID(stored=True)
    license = ID(stored=True)
    factions = KEYWORD(stored=True)
    class Meta:
        name = 'wares'
        search_fields = ['id', 'name', 'description', 'group', 'tags', 'license', 'factions']

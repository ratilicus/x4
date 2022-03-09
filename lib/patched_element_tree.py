import re
from xml.etree import ElementTree

"""
This patches ElementTree so that the find(all) functions allow 
for regex based attribute value searches 
by starting the @attrib value with ^  (note: this isn't per xpath spec)
eg. xml.findall('ware[@id="^ship_.+_scout_"]')   
    (find all wares where id is of a scout ship, would match ship_par_s_scout_01_b, etc)

"""


def prepare_predicate(next, token):
    # this is the original function from xml.etree.ElementPath 
    # FIXME: replace with real parser!!! refs:
    # http://effbot.org/zone/simple-iterator-parser.htm
    # http://javascript.crockford.com/tdop/tdop.html
    signature = []
    predicate = []
    while 1:
        try:
            token = next()
        except StopIteration:
            return
        if token[0] == "]":
            break
        if token == ('', ''):
            # ignore whitespace
            continue
        if token[0] and token[0][:1] in "'\"":
            token = "'", token[0][1:-1]
        signature.append(token[0] or "-")
        predicate.append(token[1])
    signature = "".join(signature)
    # use signature to determine predicate type
    if signature == "@-":
        # [@attribute] predicate
        key = predicate[1]
        def select(context, result):
            for elem in result:
                if elem.get(key) is not None:
                    yield elem
        return select
    if signature == "@-='":
        # [@attribute='value'] or [@attribute='^regex-pattern']
        key = predicate[1]
        value = predicate[-1]

        # allow some custom searching by regex and by space separated list of values
        if value.startswith('^'):
            # [@attribute='^regexpattern.*$']
            cmp_fn = lambda el_val: re.match(value, el_val)
        elif value.startswith('['):
            # tag[@attribute='[val1 val3]']  matches <tag attribute="val1 val2 val3">
            val_set = {v.strip() for v in value.strip(' []').split(' ')}
            cmp_fn = lambda el_val: not val_set - set(el_val.strip().split(' '))
        else:
            cmp_fn = lambda el_val: value == el_val
        def select(context, result):
            for elem in result:
                el_val = elem.get(key)
                if cmp_fn(el_val):
                    yield elem

        return select
    if signature == "-" and not re.match(r"\-?\d+$", predicate[0]):
        # [tag]
        tag = predicate[0]
        def select(context, result):
            for elem in result:
                if elem.find(tag) is not None:
                    yield elem
        return select
    if signature == ".='" or (signature == "-='" and not re.match(r"\-?\d+$", predicate[0])):
        # [.='value'] or [tag='value']
        tag = predicate[0]
        value = predicate[-1]
        if tag:
            def select(context, result):
                for elem in result:
                    for e in elem.findall(tag):
                        if "".join(e.itertext()) == value:
                            yield elem
                            break
        else:
            def select(context, result):
                for elem in result:
                    if "".join(elem.itertext()) == value:
                        yield elem
        return select
    if signature == "-" or signature == "-()" or signature == "-()-":
        # [index] or [last()] or [last()-index]
        if signature == "-":
            # [index]
            index = int(predicate[0]) - 1
            if index < 0:
                raise SyntaxError("XPath position >= 1 expected")
        else:
            if predicate[0] != "last":
                raise SyntaxError("unsupported function")
            if signature == "-()-":
                try:
                    index = int(predicate[2]) - 1
                except ValueError:
                    raise SyntaxError("unsupported expression")
                if index > -2:
                    raise SyntaxError("XPath offset from last() must be negative")
            else:
                index = -1
        def select(context, result):
            parent_map = get_parent_map(context)
            for elem in result:
                try:
                    parent = parent_map[elem]
                    # FIXME: what if the selector is "*" ?
                    elems = list(parent.findall(elem.tag))
                    if elems[index] is elem:
                        yield elem
                except (IndexError, KeyError):
                    pass
        return select
    raise SyntaxError("invalid predicate")
    
    
    
# This overrides the original prepare_predicate in the ElementPathh.ops dict (which is mutable)
ElementTree.ElementPath.ops["["] = prepare_predicate

# clearing cache just in case some searches already happened before the patch
ElementTree.ElementPath._cache.clear()



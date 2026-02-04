def at_pm(elements):
    sdata=""
    if elements:
        for (j,elem) in enumerate(elements):
            indent = "  " * elem['depth']
            ls=f"{j}:{indent}{elem['role']}-{elem['name']}"
            sdata+=ls+"\n"
            if elem['description']:
                lsd=f"{indent}  Description: {elem['description']}"
                sdata+=lsd+"\n"
    return sdata
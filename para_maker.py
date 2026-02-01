def at_pm(elements):
    sdata=""
    if elements:
        for elem in elements:
            indent = "  " * elem['depth']
            ls=f"{indent}{elem['role']}-{elem['name']}"
            sdata+=ls+"\n"
            if elem['description']:
                lsd=f"{indent}  Description: {elem['description']}"
                sdata+=lsd+"\n"
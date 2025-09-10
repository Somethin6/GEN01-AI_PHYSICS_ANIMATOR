def wants_latex(env) -> bool:
    return bool(env["tools"]["latex_ok"])

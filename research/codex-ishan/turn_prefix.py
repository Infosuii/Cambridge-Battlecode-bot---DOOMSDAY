"""Compare actions preceding any official turn-end marker, without hiding faults."""


def action_prefix(data):
    result = []
    for action in data["executed_actions"]:
        # Pinned official PanelChrome: er=e=>e.kind===8||e.kind===26||e.kind===27.
        # Faults and fuel-outs are evaluated independently from native diagnostics.
        if action["kind"] in (8, 26, 27):
            break
        result.append(action)
    return result

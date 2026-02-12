def _normalize_key(key):
    return "_".join(key.strip().lower().replace("/", " ").split())


def _get_value_by_keys(flow, keys):
    for key in flow.keys():
        normalized = _normalize_key(key)
        if normalized in keys:
            return flow[key]
    return None


def extract_hosts(flow, host_count=20):
    src_keys = {
        "src_ip",
        "source_ip",
        "src_addr",
        "source_address",
        "ip_src",
    }
    dst_keys = {
        "dst_ip",
        "dest_ip",
        "destination_ip",
        "dst_addr",
        "destination_address",
        "ip_dst",
    }

    src = _get_value_by_keys(flow, src_keys)
    dst = _get_value_by_keys(flow, dst_keys)

    if src is not None and dst is not None:
        return str(src), str(dst)

    port_keys = {"destination_port", "dest_port", "dst_port"}
    fwd_keys = {"total_fwd_packets", "subflow_fwd_packets"}
    duration_keys = {"flow_duration"}

    dest_port = _get_value_by_keys(flow, port_keys)
    total_fwd = _get_value_by_keys(flow, fwd_keys)
    duration = _get_value_by_keys(flow, duration_keys)

    try:
        dest_port = int(dest_port or 0)
    except (TypeError, ValueError):
        dest_port = 0

    try:
        total_fwd = int(total_fwd or 0)
    except (TypeError, ValueError):
        total_fwd = 0

    try:
        duration = int(duration or 0)
    except (TypeError, ValueError):
        duration = 0

    seed = dest_port + (total_fwd * 31) + (duration * 7)
    src_host = f"host_{seed % host_count}"
    dst_host = f"host_{(seed * 7 + 3) % host_count}"

    return src_host, dst_host

def _normalize_key(key):
    return "_".join(key.strip().lower().replace("/", " ").split())


def _get_value_by_keys(flow, keys):
    for key in flow.keys():
        normalized = _normalize_key(key)
        if normalized in keys:
            return flow[key]
    return None


class HostRoleClassifier:
    def __init__(self):
        self.web_ports = {80, 443, 8080, 8443}
        self.db_ports = {1433, 1521, 3306, 5432}
        self.server_ports = {22, 25, 53, 110, 135, 139, 389, 445, 3389}

    def classify_destination(self, flow):
        port_keys = {"destination_port", "dest_port", "dst_port"}
        dest_port = _get_value_by_keys(flow, port_keys)

        try:
            dest_port = int(dest_port)
        except (TypeError, ValueError):
            return None

        if dest_port in self.db_ports:
            return "database"
        if dest_port in self.web_ports or dest_port in self.server_ports:
            return "server"
        return "workstation"

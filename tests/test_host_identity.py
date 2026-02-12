import unittest

from rapids.reasoning.host_identity import extract_hosts


class TestHostIdentity(unittest.TestCase):
    def test_extract_hosts_with_ips(self):
        flow = {"Src IP": "10.0.0.1", "Dst IP": "10.0.0.9"}
        src, dst = extract_hosts(flow)
        self.assertEqual(src, "10.0.0.1")
        self.assertEqual(dst, "10.0.0.9")

    def test_extract_hosts_synthetic(self):
        flow = {" Destination Port": 80, " Total Fwd Packets": 5, " Flow Duration": 100}
        src, dst = extract_hosts(flow, host_count=10)
        self.assertTrue(src.startswith("host_"))
        self.assertTrue(dst.startswith("host_"))


if __name__ == "__main__":
    unittest.main()

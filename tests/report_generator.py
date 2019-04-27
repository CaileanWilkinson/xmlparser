import os
import time

class TestReportGenerator:
    __reports_root = os.path.join(os.path.dirname(__file__), "reports")
    __failures = None
    __successes = None

    def start_report(self):
        t = str(time.time())
        os.mkdir(os.path.join(TestReportGenerator.__reports_root, t))
        TestReportGenerator.__failures = os.path.join(TestReportGenerator.__reports_root, t,
                                                      "failures")
        TestReportGenerator.__successes = os.path.join(TestReportGenerator.__reports_root, t,
                                                       "successes")

        with open(TestReportGenerator.__failures) as f:
            pass

        with open(TestReportGenerator.__successes) as s:
            pass



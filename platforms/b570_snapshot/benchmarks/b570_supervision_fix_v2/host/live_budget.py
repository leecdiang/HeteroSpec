"""Anchor OS creation age once, then charge live time on a monotonic clock."""
def anchor(created_filetime, wall_ns, monotonic_ns):
    return (max(0, (wall_ns // 100 + 116444736000000000 - created_filetime) / 1e7), monotonic_ns)

def elapsed(sample, monotonic_ns):
    age, start = sample
    if monotonic_ns < start:
        raise ValueError('monotonic clock reversed')
    return age + (monotonic_ns - start) / 1e9


class OuterBudget:
    """Conservative admission charge: accrue each registered outer until task end.

    Early-exited outer processes are deliberately overcharged live. Final accounting
    uses actual OS exits. Missing bootstrap observations prevent command admission.
    """
    def __init__(self, registry, broker_pid, broker_created, wall_ns, monotonic_ns):
        self.start = registry['task_begin_ns']
        if type(self.start) is not int or not 0 <= self.start <= monotonic_ns:
            raise ValueError('invalid prospective task start')
        self.keys = set()
        self.samples = []
        current_filetime = wall_ns // 100 + 116444736000000000
        for row in registry['outer_processes']:
            key = (int(row['pid']), int(row['created_filetime']))
            if key in self.keys or key[0] <= 0 or not 0 < key[1] <= current_filetime:
                raise ValueError('invalid/duplicate outer identity')
            self.keys.add(key)
            self.samples.append(anchor(key[1], wall_ns, monotonic_ns))
        if (broker_pid, broker_created) not in self.keys:
            raise ValueError('executing broker absent from prospective registry')

    def seconds(self, monotonic_ns):
        return sum(elapsed(sample, monotonic_ns) for sample in self.samples)

    def exceeded(self, child_starts, closed_seconds, live_seconds, monotonic_ns):
        return (child_starts + len(self.keys) >= 3000
                or closed_seconds + live_seconds + self.seconds(monotonic_ns) >= 43200
                or (monotonic_ns - self.start) / 1e9 >= 28800)

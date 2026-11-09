class TieBreakService:
    @staticmethod
    def break_ties_icpc(p1, p2):
        # 1. More problems solved
        if p1['solved'] != p2['solved']:
            return -1 if p1['solved'] > p2['solved'] else 1
        # 2. Lower penalty
        if p1['penalty'] != p2['penalty']:
            return -1 if p1['penalty'] < p2['penalty'] else 1
        # 3. Earlier last solved time
        t1 = p1.get('last_ac_time', 0)
        t2 = p2.get('last_ac_time', 0)
        if t1 != t2:
            return -1 if t1 < t2 else 1
        return 0

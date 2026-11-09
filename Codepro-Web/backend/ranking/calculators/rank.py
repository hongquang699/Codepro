class RankCalculator:
    """
    Ranks participants according to competitive programming rules:
    - Primary: Solved count DESC (or Total Score DESC for IOI)
    - Secondary: Total Penalty ASC (or Cumulative Time ASC)
    - Tie-breaking: Earlier last AC time
    """

    @staticmethod
    def rank_icpc(participants):
        """
        participants: list of dicts with:
          - user_id / username
          - solved: int
          - penalty: int
          - last_ac_time: int / datetime (optional)
        Returns: list of participants with 'rank' assigned (1-indexed, handling ties: 1, 2, 2, 4)
        """
        # Sort key: (-solved, penalty, last_ac_time)
        sorted_list = sorted(
            participants,
            key=lambda p: (
                -p.get('solved', 0),
                p.get('penalty', 0),
                p.get('last_ac_time', 0)
            )
        )

        current_rank = 1
        for i, p in enumerate(sorted_list):
            if i > 0:
                prev = sorted_list[i - 1]
                if (p.get('solved', 0) == prev.get('solved', 0) and
                    p.get('penalty', 0) == prev.get('penalty', 0)):
                    p['rank'] = prev['rank']
                else:
                    p['rank'] = i + 1
            else:
                p['rank'] = 1

        return sorted_list

    @staticmethod
    def rank_ioi(participants):
        """
        participants: list of dicts with:
          - score: float
          - cumulative_time: int
        """
        sorted_list = sorted(
            participants,
            key=lambda p: (-p.get('score', 0.0), p.get('cumulative_time', 0))
        )

        for i, p in enumerate(sorted_list):
            if i > 0:
                prev = sorted_list[i - 1]
                if (p.get('score', 0.0) == prev.get('score', 0.0) and
                    p.get('cumulative_time', 0) == prev.get('cumulative_time', 0)):
                    p['rank'] = prev['rank']
                else:
                    p['rank'] = i + 1
            else:
                p['rank'] = 1

        return sorted_list

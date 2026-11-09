class PercentileCalculator:
    """
    Computes percentiles for leaderboard positions.
    """

    @staticmethod
    def calculate_percentile(rank, total_participants):
        if total_participants <= 1:
            return 100.0
        # Percentile: percentage of participants ranked at or below
        percentile = (1.0 - (rank - 1) / total_participants) * 100.0
        return round(max(0.1, min(100.0, percentile)), 1)

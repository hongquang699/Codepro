import math

class CodeforcesRatingCalculator:
    """
    Codeforces / Elo rating recalculator.
    Given a list of contestants with their current rating and their actual contest rank,
    calculates the new rating and rating delta for each contestant.
    """

    @staticmethod
    def get_expected_rank(rating, all_ratings, exclude_idx=None):
        """
        Calculates expected rank of a player with 'rating' against the field of 'all_ratings'.
        E = 1 + sum( 1 / (1 + 10^((rating - r_other) / 400)) )
        """
        expected = 1.0
        for idx, other_rating in enumerate(all_ratings):
            if exclude_idx is not None and idx == exclude_idx:
                continue
            prob = 1.0 / (1.0 + 10.0 ** ((rating - other_rating) / 400.0))
            expected += prob
        return expected

    @classmethod
    def calculate_deltas(cls, contestants):
        """
        contestants: list of dicts:
          [
            {'user_id': 1, 'rating': 1500, 'rank': 1},
            {'user_id': 2, 'rating': 1600, 'rank': 2},
            ...
          ]
        Returns:
          list of dicts with 'new_rating', 'delta', 'performance'
        """
        n = len(contestants)
        if n == 0:
            return []
        if n == 1:
            c = contestants[0].copy()
            c['delta'] = 0
            c['new_rating'] = c['rating']
            c['performance'] = c['rating']
            return [c]

        all_ratings = [c['rating'] for c in contestants]
        results = []

        for idx, c in enumerate(contestants):
            actual_rank = float(c['rank'])
            expected_rank = cls.get_expected_rank(c['rating'], all_ratings, exclude_idx=idx)
            # Geometric mean of actual and expected rank
            target_rank = math.sqrt(actual_rank * expected_rank)

            # Binary search for performance rating
            low = 1
            high = 4000
            for _ in range(30):
                mid = (low + high) / 2.0
                e = cls.get_expected_rank(mid, all_ratings, exclude_idx=idx)
                if e < target_rank:
                    high = mid
                else:
                    low = mid

            perf_rating = (low + high) / 2.0
            raw_delta = (perf_rating - c['rating']) / 2.0

            res = dict(c)
            res['raw_delta'] = raw_delta
            res['performance'] = int(round(perf_rating))
            results.append(res)

        # Anti-inflation correction: sum of deltas should be slightly negative or 0
        total_raw_delta = sum(r['raw_delta'] for r in results)
        shift = -total_raw_delta / n - 1.0 # Slight decay

        for r in results:
            final_delta = int(round(r['raw_delta'] + shift))
            r['delta'] = final_delta
            r['new_rating'] = max(1, r['rating'] + final_delta)

        return results
